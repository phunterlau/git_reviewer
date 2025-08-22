#!/usr/bin/env python3
"""
Comprehensive phunterlau analysis report using the optimized hybrid analyzer
"""

import asyncio
import os
import time
import sys
# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_analysis.optimized_hybrid_analyzer import OptimizedHybridAnalyzer


def generate_phunterlau_report():
    """Generate comprehensive report for phunterlau."""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("Please set GITHUB_TOKEN environment variable")
        return
    
    analyzer = OptimizedHybridAnalyzer(token)
    
    print("👤 PHUNTERLAU (Hongliang Liu) - FOUNDING ENGINEER ANALYSIS")
    print("=" * 70)
    
    results = analyzer.analyze_contributor("phunterlau")
    
    # Basic metrics
    g_index = results.get('g_index', 0)
    total_contribs = results.get('total_contributions', 0)
    top_score = results.get('top_score', 0)
    analysis_time = results.get('analysis_time', 0)
    api_calls = results.get('api_calls_made', 0)
    
    print(f"\n📊 EXECUTIVE SUMMARY:")
    print(f"   🎯 G-Index: {g_index}")
    print(f"   📈 Total Contributions: {total_contribs}")
    print(f"   🏆 Top Contribution Score: {top_score:.2f}")
    print(f"   ⚡ Analysis Time: {analysis_time:.1f}s with {api_calls} API calls")
    
    # Process contributions
    contributions = results.get('contributions', [])
    
    external_contribs = [c for c in contributions if c.type == 'external_pr']
    own_contribs = [c for c in contributions if c.type == 'own_repo_commit']
    
    print(f"\n🤝 COLLABORATION PROFILE:")
    print(f"   📤 External PRs: {len(external_contribs)}")
    print(f"   🏠 Own Repository Commits: {len(own_contribs)}")
    print(f"   📊 Collaboration Ratio: {len(external_contribs)}/{len(own_contribs)} (External/Own)")
    
    # External contributions analysis
    if external_contribs:
        print(f"\n🌟 EXTERNAL CONTRIBUTIONS (High-Impact):")
        external_repos = {}
        for contrib in external_contribs:
            repo = contrib.repo_name
            if repo not in external_repos:
                external_repos[repo] = []
            external_repos[repo].append(contrib)
        
        print(f"   🏢 Organizations contributed to: {len(external_repos)}")
        
        for i, contrib in enumerate(external_contribs[:5], 1):
            year = contrib.created_at[:4]
            print(f"   {i}. {contrib.repo_name} ({year})")
            print(f"      📝 {contrib.title}")
            print(f"      🔗 {contrib.url}")
            print(f"      📊 Score: {contrib.score:.2f}")
            print()
        
        # Analyze organizations
        print(f"   🏆 ORGANIZATIONS:")
        for repo, contribs in external_repos.items():
            org = repo.split('/')[0]
            print(f"      - {org}: {len(contribs)} contribution(s) to {repo}")
    
    # Own project analysis
    if own_contribs:
        print(f"\n🏗️  PROJECT OWNERSHIP & LEADERSHIP:")
        own_repos = {}
        for contrib in own_contribs:
            repo = contrib.repo_name
            if repo not in own_repos:
                own_repos[repo] = []
            own_repos[repo].append(contrib)
        
        print(f"   📁 Active projects: {len(own_repos)}")
        
        for repo, contribs in own_repos.items():
            project_name = repo.split('/')[-1]
            latest_date = max(c.created_at for c in contribs)[:10]
            print(f"      - {project_name}: {len(contribs)} recent commit(s), latest: {latest_date}")
            
            # Show most recent significant commit
            significant_commit = max(contribs, key=lambda c: c.score)
            if significant_commit.score > 1.0:
                print(f"        💡 Key work: {significant_commit.title}")
    
    print(f"\n💎 GOLDEN NUGGETS FOR INTERVIEW:")
    
    # Top contribution insights
    if contributions:
        top_contrib = max(contributions, key=lambda c: c.score)
        print(f"   1. 🏆 Highest-impact work: '{top_contrib.title}' in {top_contrib.repo_name}")
        print(f"      Score: {top_contrib.score:.2f} | {top_contrib.url}")
    
    # Apache MXNet contributions (if any)
    apache_contribs = [c for c in external_contribs if 'apache' in c.repo_name.lower()]
    if apache_contribs:
        print(f"   2. 🚀 Apache Foundation contributor: {len(apache_contribs)} contributions to Apache MXNet")
        print(f"      Shows engagement with major open-source projects")
    
    # Recent vs historical work
    recent_contribs = [c for c in contributions if c.created_at.startswith('2025')]
    historical_contribs = [c for c in contributions if not c.created_at.startswith('2025')]
    
    if recent_contribs and historical_contribs:
        print(f"   3. ⏱️  Sustained activity: {len(historical_contribs)} historical + {len(recent_contribs)} recent (2025) contributions")
        print(f"      Demonstrates long-term commitment to software development")
    
    # Project diversity
    all_repos = set(c.repo_name for c in contributions)
    if len(all_repos) >= 5:
        print(f"   4. 🌐 Technology breadth: Active across {len(all_repos)} different repositories")
        print(f"      Indicates versatility and broad technical interests")
    
    # Specific technical areas
    ml_ai_repos = [r for r in all_repos if any(term in r.lower() for term in ['mxnet', 'llm', 'token', 'ai', 'ml'])]
    if ml_ai_repos:
        print(f"   5. 🤖 AI/ML expertise: Contributions to {len(ml_ai_repos)} AI/ML-related projects")
        print(f"      Projects: {', '.join(r.split('/')[-1] for r in ml_ai_repos)}")
    
    print(f"\n🎯 FOUNDING ENGINEER ASSESSMENT:")
    
    # Technical competency
    tech_score = "Strong" if g_index >= 4 else "Solid" if g_index >= 3 else "Developing"
    print(f"   🧠 Technical Competency: {tech_score} (G-Index: {g_index})")
    
    # Collaboration evidence
    collab_score = "Excellent" if len(external_contribs) >= 5 else "Good" if len(external_contribs) >= 3 else "Moderate"
    print(f"   🤝 Collaboration Skills: {collab_score} ({len(external_contribs)} external contributions)")
    
    # Initiative/Leadership
    leadership_score = "Strong" if len(own_contribs) >= 5 else "Moderate" if len(own_contribs) >= 2 else "Limited"
    print(f"   🏗️  Initiative/Leadership: {leadership_score} ({len(own_contribs)} own projects)")
    
    # Overall recommendation
    total_score = g_index + len(external_contribs) + len(own_contribs)
    if total_score >= 10:
        recommendation = "HIGHLY RECOMMENDED"
        reasoning = "Strong across all dimensions"
    elif total_score >= 7:
        recommendation = "RECOMMENDED"
        reasoning = "Solid foundation with good experience"
    elif total_score >= 4:
        recommendation = "CONSIDER"
        reasoning = "Some strengths, may need support in certain areas"
    else:
        recommendation = "NEEDS DEVELOPMENT"
        reasoning = "Limited evidence of founding engineer capabilities"
    
    print(f"\n🏆 OVERALL RECOMMENDATION: {recommendation}")
    print(f"   📝 Reasoning: {reasoning}")
    print(f"   📊 Composite Score: {total_score} (G-Index + External + Own)")
    
    print(f"\n💬 SUGGESTED INTERVIEW QUESTIONS:")
    if apache_contribs:
        print(f"   1. 'Tell me about your contributions to Apache MXNet and your experience with the Apache community'")
    if any('llm' in c.repo_name.lower() for c in contributions):
        print(f"   2. 'I see you've worked on LLM optimization projects. What's your approach to AI/ML performance?'")
    if own_contribs:
        latest_project = max(own_contribs, key=lambda c: c.created_at).repo_name.split('/')[-1]
        print(f"   3. 'Walk me through your {latest_project} project. What problem does it solve?'")
    print(f"   4. 'You have a G-Index of {g_index}. What do you consider your most impactful technical contribution?'")
    
    return results


if __name__ == "__main__":
    generate_phunterlau_report()
