import os
import json
import requests
from openai import OpenAI
from datetime import datetime, timezone, timedelta


def review_commits_with_gpt(commit_file_path):
    """
    Use GPT-4o to review commits and provide insights about the programmer.
    
    Args:
        commit_file_path (str): Path to the markdown file containing commits
    
    Returns:
        dict: JSON response from GPT-4o with review insights
    """
    try:
        # Initialize OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        client = OpenAI(api_key=openai_api_key)
        
        # Read commit content
        with open(commit_file_path, 'r', encoding='utf-8') as f:
            commit_content = f.read()
        
        # Construct prompt
        prompt = create_review_prompt(commit_content)
        
        print("Sending commits to GPT-4o-mini for review...")
        
        # Make API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert code reviewer and technical hiring manager. Analyze the provided commit history and provide insights about the programmer's capabilities."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse response
        review_json = json.loads(response.choices[0].message.content)
        
        # Save review to file
        review_filename = commit_file_path.replace('.md', '_review.json')
        with open(review_filename, 'w', encoding='utf-8') as f:
            json.dump(review_json, f, indent=2, ensure_ascii=False)
        
        print(f"Review saved to {review_filename}")
        
        return review_json
        
    except Exception as e:
        print(f"Error reviewing commits with GPT: {str(e)}")
        return None


def create_review_prompt(commit_content):
    """
    Create a detailed prompt for GPT-4o-mini to review commits with time-based analysis.
    
    Args:
        commit_content (str): The markdown content of commits
    
    Returns:
        str: The formatted prompt
    """
    from datetime import datetime, timezone
    current_time = datetime.now(timezone.utc)
    
    prompt = f"""
Please analyze the following commit history and provide a comprehensive review of the programmer's capabilities. Pay special attention to temporal patterns, activity frequency, and recent vs. historical contributions.

CURRENT ANALYSIS DATE: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}

COMMIT HISTORY:
{commit_content}

Please provide your analysis in JSON format with the following structure:

{{
  "programmingLanguageExpertise": "Assessment of programming languages used and proficiency level demonstrated",
  "commitQuality": "Analysis of commit message quality, frequency, and patterns",
  "codingStyle": "Observations about coding style, best practices, and code organization",
  "contributionSummary": "Overall summary of the types of contributions and their impact",
  "technicalSkills": "Specific technical skills demonstrated (frameworks, tools, patterns, etc.)",
  "codeReviewability": "Assessment of how well the code changes can be reviewed and understood",
  "problemSolvingApproach": "Analysis of how the programmer approaches and solves problems",
  "temporalAnalysis": "Analysis of commit timing, frequency patterns, recent activity vs. historical contributions, and development velocity",
  "activityPatterns": "Assessment of consistency, work habits, and contribution rhythm over time",
  "recentVsHistorical": "Comparison of recent contributions (last 3-6 months) vs older ones, showing growth or changes in approach",
  "reviewHighlights": [
    "Specific highlight 1 - reference to particular commits or patterns with timestamps",
    "Specific highlight 2 - notable technical achievements or approaches with timeframe context",
    "Specific highlight 3 - areas of strength or improvement opportunities with temporal relevance"
  ],
  "overallRating": "Professional assessment (e.g., Junior/Mid-level/Senior) with reasoning including recent activity assessment",
  "recommendations": "Suggestions for interview focus areas or technical discussion topics, considering both historical and recent work"
}}

Focus on:
1. Technical depth and breadth
2. Code quality and maintainability
3. Problem-solving approach
4. Communication through commit messages
5. Consistency and professionalism
6. Notable patterns or practices
7. **TIME-BASED ANALYSIS:**
   - Frequency of contributions (daily, weekly, monthly patterns)
   - Recent activity level vs. historical activity
   - Evolution of code quality over time
   - Response time and urgency in fixes/features
   - Work consistency and professional habits
   - Gaps in activity and potential reasons
   - Development velocity and productivity trends

Pay attention to the timestamps provided (e.g., "3 months ago", "1 year ago") to understand:
- Current vs. past activity levels
- Evolution of technical skills
- Recent engagement with the project
- Consistency of contribution patterns
- Professional development trajectory

Provide specific examples from the commits with their temporal context when possible.
"""
    return prompt


def _resolve_login_from_email(email, gh_client, max_attempts=5):
    """
    Attempt to resolve a GitHub login from an author email using commit search.
    Returns login or None.
    """
    try:
        query = f"author-email:{email}"
        results = gh_client.search_commits(query)
        count = 0
        for c in results:
            if c.author and c.author.login:
                return c.author.login
            count += 1
            if count >= max_attempts:
                break
    except Exception:
        return None
    return None


def get_contribution_heatmap(github_identifier, days=365, output_format="json", output_path=None):
    """
    Fetch last `days` days (default 365) of contribution calendar data (GitHub heatmap).
    
    Uses GitHub GraphQL API:
      - Counts include commits to default & non-fork repos, PRs opened, issues opened,
        code reviews, and (if token has permission) private contributions aggregated.
    
    Args:
        github_identifier (str): GitHub username OR author email.
        days (int): Number of days to look back (max 365 typical for heatmap).
        output_format (str): 'json' or 'md'.
        output_path (str|None): Optional explicit output file path. If None a default is used.
    
    Returns:
        dict: {
            "login": str,
            "from": ISO datetime,
            "to": ISO datetime,
            "totalContributions": int,
            "days": [{"date": "YYYY-MM-DD", "count": int, "color": "#hex"}]
        } or None on failure.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not found in environment variables")
        return None

    from_dt = (datetime.now(timezone.utc) - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    to_dt = datetime.now(timezone.utc)

    # Determine login
    login = github_identifier
    is_email = "@" in github_identifier
    
    if is_email:
        from github import Github  # Import here to avoid circular imports
        gh_client = Github(token)
        resolved = _resolve_login_from_email(github_identifier, gh_client)
        if not resolved:
            print(f"Could not resolve login from email {github_identifier}")
            return None
        login = resolved
        print(f"Resolved email {github_identifier} -> login {login}")

    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                color
              }
            }
          }
        }
      }
    }
    """

    variables = {
        "login": login,
        "from": from_dt.isoformat(),
        "to": to_dt.isoformat()
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    try:
        print(f"Fetching contribution heatmap for {login} (last {days} days)...")
        resp = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=30
        )
        
        if resp.status_code != 200:
            print(f"GraphQL request failed: {resp.status_code} {resp.text}")
            return None
            
        data = resp.json()
        if "errors" in data:
            print(f"GraphQL errors: {data['errors']}")
            return None
            
        user = data.get("data", {}).get("user")
        if not user:
            print("User not found in GraphQL response.")
            return None

        calendar = user["contributionsCollection"]["contributionCalendar"]
        total = calendar["totalContributions"]

        # Flatten days
        days_list = []
        for week in calendar["weeks"]:
            for day in week["contributionDays"]:
                days_list.append({
                    "date": day["date"],
                    "count": day["contributionCount"],
                    "color": day.get("color")
                })

        # Filter strictly last `days` days (GraphQL might include overlap)
        cutoff_date = from_dt.date()
        filtered_days = [d for d in days_list if datetime.fromisoformat(d["date"]).date() >= cutoff_date]

        result = {
            "login": login,
            "from": variables["from"],
            "to": variables["to"],
            "totalContributions": total,
            "days": filtered_days
        }

        # Output
        safe_ident = login.replace("@", "_at_").replace(".", "_")
        if not output_path:
            ext = "json" if output_format == "json" else "md"
            output_path = f"heatmap_{safe_ident}.{ext}"

        if output_format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        elif output_format == "md":
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# Contribution Heatmap (last {days} days) for {login}\n\n")
                f.write(f"**Analysis Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
                f.write(f"**Period:** {variables['from']} to {variables['to']}\n")
                f.write(f"**Total contributions:** {total}\n\n")
                f.write("## Daily Activity\n\n")
                f.write("| Date | Contributions | Activity Level |\n")
                f.write("|------|---------------|----------------|\n")
                for d in filtered_days:
                    count = d['count']
                    if count == 0:
                        level = "None"
                    elif count <= 3:
                        level = "Low"
                    elif count <= 6:
                        level = "Medium"
                    else:
                        level = "High"
                    f.write(f"| {d['date']} | {count} | {level} |\n")
        else:
            print(f"Unknown output_format '{output_format}', skipping file write.")

        print(f"Contribution heatmap data saved to {output_path}")
        return result

    except requests.exceptions.Timeout:
        print("GraphQL request timed out.")
    except Exception as e:
        print(f"Error fetching contribution heatmap: {e}")
    return None


def summarize_contributions(contributions_data):
    """
    Creates a concise summary of contribution data to optimize token usage.
    
    Args:
        contributions_data (dict): Raw contributions data from fetch_all_contributions
        
    Returns:
        str: Concise summary for GPT analysis
    """
    if not contributions_data:
        return "No contribution data available."
    
    user = contributions_data.get("user", "Unknown")
    repo = contributions_data.get("repo", "Unknown")
    stats = contributions_data.get("summary_stats", {})
    
    summary = f"# Contribution Summary for {user} in {repo}\n\n"
    summary += f"**Activity Overview:**\n"
    summary += f"- {stats.get('total_commits', 0)} commits\n"
    summary += f"- {stats.get('total_prs', 0)} pull requests\n"
    summary += f"- {stats.get('total_issues', 0)} issues\n"
    summary += f"- {stats.get('total_reviews', 0)} code reviews\n\n"
    
    # Sample recent commits (top 5)
    commits = contributions_data.get("commits", [])[:5]
    if commits:
        summary += f"**Recent Commit Messages:**\n"
        for commit in commits:
            msg = commit.get("message", "").split('\n')[0][:80]  # First line, truncated
            summary += f"- `{commit.get('sha', '')}`: {msg}\n"
        summary += "\n"
    
    # Sample PRs
    prs = contributions_data.get("pull_requests", [])[:3]
    if prs:
        summary += f"**Pull Request Highlights:**\n"
        for pr in prs:
            summary += f"- #{pr.get('number', '')}: {pr.get('title', '')[:60]} ({pr.get('state', '')})\n"
        summary += "\n"
    
    # Issues
    issues = contributions_data.get("issues", [])[:3]
    if issues:
        summary += f"**Issue Reports:**\n"
        for issue in issues:
            summary += f"- #{issue.get('number', '')}: {issue.get('title', '')[:60]} ({issue.get('state', '')})\n"
        summary += "\n"
    
    # Review activity
    reviews = contributions_data.get("reviews", [])
    if reviews:
        review_states = {}
        for review in reviews:
            state = review.get("state", "COMMENTED")
            review_states[state] = review_states.get(state, 0) + 1
        summary += f"**Code Review Activity:**\n"
        for state, count in review_states.items():
            summary += f"- {state}: {count} reviews\n"
    
    return summary


def review_contributions_with_gpt(contributions_data):
    """
    Analyzes comprehensive contribution data using GPT-4o-mini with optimized prompts.
    
    Args:
        contributions_data (dict): Full contribution data from fetch_all_contributions
        
    Returns:
        dict: Analysis results from GPT
    """
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        client = OpenAI(api_key=openai_api_key)
        
        # Create optimized summary
        summary = summarize_contributions(contributions_data)
        
        # Enhanced prompt for comprehensive analysis
        prompt = f"""You are an expert software engineering analyst. Based on this GitHub contribution summary, provide a comprehensive assessment of the developer's profile:

{summary}

Analyze and provide insights on:

1. **Technical Competency**
   - Code quality patterns from commit messages
   - Problem-solving approach
   - Technical communication skills

2. **Collaboration & Leadership**
   - Code review quality and style
   - Issue reporting and discussion patterns
   - Community engagement level

3. **Project Contribution Patterns**
   - Feature development vs bug fixes
   - Documentation and maintenance work
   - Initiative and ownership indicators

4. **Development Practices**
   - Commit frequency and consistency
   - PR size and focus
   - Testing and quality assurance habits

5. **Professional Assessment**
   - Strengths and areas for improvement
   - Suitability for different team roles
   - Growth trajectory indicators

Provide specific examples from the data to support your analysis. Focus on actionable insights for technical hiring or team formation decisions.

Format your response as a structured JSON with the following keys:
- technical_competency: detailed assessment
- collaboration_skills: team interaction analysis  
- contribution_patterns: development habits and focus areas
- professional_summary: overall evaluation with specific recommendations
- risk_factors: potential concerns or areas needing attention
- growth_potential: indicators of learning and adaptation"""

        # Make API call with optimized model
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-optimized model
            messages=[
                {"role": "system", "content": "You are an expert technical recruiter and software engineering analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,  # Controlled token usage
            temperature=0.3   # Consistent analysis
        )
        
        response_content = response.choices[0].message.content
        
        # Try to parse as JSON, fallback to text
        try:
            analysis = json.loads(response_content)
        except json.JSONDecodeError:
            analysis = {"raw_analysis": response_content}
        
        # Add metadata
        analysis["analysis_metadata"] = {
            "model_used": "gpt-4o-mini",
            "tokens_used": response.usage.total_tokens,
            "analyzed_user": contributions_data.get("user", "Unknown"),
            "analyzed_repo": contributions_data.get("repo", "Unknown"),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return analysis
        
    except Exception as e:
        return {"error": f"Failed to analyze contributions: {str(e)}"}


def generate_founding_engineer_tags(metrics_data):
    """
    Generate AI-powered founding engineer skill and attribute tags with justifications.
    
    Args:
        metrics_data (dict): Complete founding engineer metrics data
        
    Returns:
        dict: Generated tags with categories, justifications, and supporting evidence
    """
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        client = OpenAI(api_key=openai_api_key)
        
        # Create structured summary of metrics for GPT
        metrics_summary = _format_metrics_for_tag_generation(metrics_data)
        
        # Craft specialized prompt for tag generation
        prompt = f"""You are an experienced CTO at a fast-growing AI startup. Your task is to generate concise, insightful tags (3-5 words max) that capture the candidate's key skills, attributes, and potential risks based on their GitHub activity analysis.

CANDIDATE METRICS SUMMARY:
{metrics_summary}

Generate tags in the following categories:
- **Technical DNA**: Core technical skills and expertise areas
- **Engineering Craft**: Code quality, testing, and process habits  
- **Founder DNA**: Initiative, ownership, and product sense signals
- **Collaboration Style**: Communication and teamwork patterns
- **Work Ethic & Rhythm**: Dedication and passion indicators
- **⚠️ Red Flags**: Potential risks or concerning patterns

For each tag, provide:
1. The tag name (include relevant emoji for visual appeal)
2. A concise justification (1-2 sentences explaining why this tag applies)
3. Supporting evidence (specific metric values or patterns that justify the tag)

IMPORTANT GUIDELINES:
- Keep tag names short and punchy (3-5 words maximum)
- Focus on actionable insights a founder would care about
- Be specific - link each tag to concrete evidence from the data
- Include both strengths and potential concerns
- Prioritize tags that differentiate this candidate from others

Provide your response in this exact JSON format:
{{
  "Technical DNA": [
    {{
      "tag": "🧠 AI Core Expert",
      "justification": "Demonstrates deep expertise in foundational ML frameworks",
      "supporting_evidence": "Uses 5+ AI/ML frameworks including PyTorch and Transformers"
    }}
  ],
  "Engineering Craft": [
    {{
      "tag": "✅ Test-Driven Developer", 
      "justification": "Consistently includes tests in development workflow",
      "supporting_evidence": "Testing commitment ratio of 0.25 (25% of work includes tests)"
    }}
  ],
  "Founder DNA": [
    {{
      "tag": "🚀 Self-Starter",
      "justification": "Demonstrates ability to identify and solve problems independently", 
      "supporting_evidence": "Completed 3 self-directed work cycles from problem to solution"
    }}
  ],
  "Collaboration Style": [
    {{
      "tag": "🤝 Thoughtful Reviewer",
      "justification": "Provides constructive, educational code review feedback",
      "supporting_evidence": "70% of review comments are suggestions vs corrections"
    }}
  ],
  "Work Ethic & Rhythm": [
    {{
      "tag": "🏆 Weekend Warrior",
      "justification": "Shows passion by coding during personal time",
      "supporting_evidence": "40% of commits occur on weekends, indicating personal dedication"
    }}
  ],
  "⚠️ Red Flags": [
    {{
      "tag": "📦 Limited Test Coverage",
      "justification": "May produce code that is harder to maintain and debug",
      "supporting_evidence": "Testing commitment ratio of only 0.05 (5%)"
    }}
  ]
}}"""

        # Make API call with GPT-4o-mini
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert CTO and technical recruiter specializing in founding engineer assessment. Generate insightful, evidence-based tags for candidates."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent output
            max_tokens=1500
        )
        
        # Parse response
        tags_data = json.loads(response.choices[0].message.content)
        
        # Convert JSON response to SkillTag objects
        from founding_engineer_reviewer import SkillTag
        skill_tags = []
        
        for category, tags_list in tags_data.items():
            if category == "generation_metadata":
                continue
            if isinstance(tags_list, list):
                for tag_dict in tags_list:
                    if isinstance(tag_dict, dict) and all(key in tag_dict for key in ['tag', 'justification', 'supporting_evidence']):
                        skill_tag = SkillTag(
                            tag=tag_dict['tag'],
                            category=category,
                            justification=tag_dict['justification'],
                            supporting_evidence=tag_dict['supporting_evidence']
                        )
                        skill_tags.append(skill_tag)
        
        return skill_tags
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse GPT response as JSON: {str(e)}")
        return []
    except Exception as e:
        print(f"Failed to generate tags: {str(e)}")
        return []


def _format_metrics_for_tag_generation(metrics_data):
    """
    Format founding engineer metrics into a concise, readable summary for GPT tag generation.
    
    Args:
        metrics_data (dict or FoundingEngineerMetrics): Raw metrics from founding engineer analysis
        
    Returns:
        str: Formatted summary optimized for tag generation
    """
    if metrics_data is None:
        return "No metrics data available."
    
    # Convert dataclass to dict if needed
    if hasattr(metrics_data, '__dataclass_fields__'):
        from dataclasses import asdict
        metrics_data = asdict(metrics_data)
    
    summary = "=== FOUNDING ENGINEER ANALYSIS SUMMARY ===\n\n"
    
    # Technical Proficiency
    summary += "TECHNICAL PROFICIENCY:\n"
    ai_frameworks = metrics_data.get('ai_ml_frameworks', [])
    summary += f"- AI/ML Frameworks: {len(ai_frameworks)} detected ({', '.join(ai_frameworks[:5])})\n"
    
    perf_langs = metrics_data.get('performance_languages', {})
    if perf_langs:
        lang_summary = [f"{lang}: {lines} lines" for lang, lines in perf_langs.items()]
        summary += f"- Performance Languages: {', '.join(lang_summary)}\n"
    else:
        summary += f"- Performance Languages: None detected\n"
    
    full_stack = metrics_data.get('full_stack_evidence', [])
    summary += f"- Full-Stack Evidence: {len(full_stack)} indicators ({', '.join(full_stack[:3])})\n"
    
    dep_score = metrics_data.get('dependency_sophistication_score', 0)
    summary += f"- Dependency Sophistication Score: {dep_score:.2f}\n"
    
    complexity = metrics_data.get('code_complexity_indicators', [])
    summary += f"- Code Complexity Indicators: {', '.join(complexity[:3])}\n\n"
    
    # Engineering Craftsmanship
    summary += "ENGINEERING CRAFTSMANSHIP:\n"
    commit_ratio = metrics_data.get('commit_issue_linking_ratio', 0)
    summary += f"- Commit-Issue Linking Ratio: {commit_ratio:.2f} ({commit_ratio*100:.0f}%)\n"
    
    pr_times = metrics_data.get('pr_turnaround_times', {})
    if pr_times:
        avg_time = sum(pr_times.values()) / len(pr_times)
        summary += f"- Average PR Turnaround: {avg_time:.1f} hours\n"
    else:
        summary += f"- Average PR Turnaround: No data\n"
    
    test_ratio = metrics_data.get('testing_commitment_ratio', 0)
    summary += f"- Testing Commitment Ratio: {test_ratio:.2f} ({test_ratio*100:.0f}%)\n"
    
    workflow_score = metrics_data.get('structured_workflow_score', 0)
    summary += f"- Structured Workflow Score: {workflow_score:.2f}\n\n"
    
    # Initiative & Ownership
    summary += "INITIATIVE & OWNERSHIP:\n"
    self_directed = metrics_data.get('self_directed_work_cycles', 0)
    summary += f"- Self-Directed Work Cycles: {self_directed}\n"
    
    first_responder = metrics_data.get('first_responder_instances', 0)
    summary += f"- First Responder Instances: {first_responder}\n"
    
    project_quality = metrics_data.get('personal_project_quality', 0)
    summary += f"- Personal Project Quality Score: {project_quality:.2f}\n"
    
    oss_contrib = metrics_data.get('open_source_contributions', 0)
    summary += f"- Open Source Contributions: {oss_contrib}\n"
    
    ownership = metrics_data.get('ownership_indicators', [])
    summary += f"- Ownership Indicators: {', '.join(ownership[:3])}\n\n"
    
    # Collaboration & Communication
    summary += "COLLABORATION & COMMUNICATION:\n"
    review_dist = metrics_data.get('review_comment_distribution', {})
    if review_dist:
        summary += f"- Review Comment Types: {dict(review_dist)}\n"
    else:
        summary += f"- Review Comment Types: No data\n"
    
    feedback_score = metrics_data.get('feedback_receptiveness_score', 0)
    summary += f"- Feedback Receptiveness Score: {feedback_score:.2f}\n"
    
    work_rhythm = metrics_data.get('work_rhythm_pattern', 'Unknown')
    summary += f"- Work Rhythm Pattern: {work_rhythm}\n"
    
    dedication_score = metrics_data.get('temporal_dedication_score', 0)
    summary += f"- Temporal Dedication Score: {dedication_score:.2f}\n\n"
    
    # Overall Assessment
    summary += "OVERALL ASSESSMENT:\n"
    overall_score = metrics_data.get('founding_engineer_score', 0)
    summary += f"- Founding Engineer Score: {overall_score:.1f}/100\n"
    
    risks = metrics_data.get('risk_factors', [])
    summary += f"- Risk Factors: {', '.join(risks[:3])}\n"
    
    strengths = metrics_data.get('strengths', [])
    summary += f"- Key Strengths: {', '.join(strengths[:3])}\n"
    
    recommendation = metrics_data.get('recommendation', 'Unknown')
    summary += f"- Recommendation: {recommendation}\n"
    
    return summary
