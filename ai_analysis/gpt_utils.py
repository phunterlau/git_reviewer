import os
import json
from openai import OpenAI


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
