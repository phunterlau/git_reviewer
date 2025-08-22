#!/usr/bin/env python3
"""
Enhanced Founding Engineer CLI

This enhanced version integrates all improvements from the enhancement plan:
1. Code content analysis beyond metadata
2. Factual collaboration metrics
3. Repository impact contextualization
4. Golden nuggets for interview preparation

Usage:
    uv run python enhanced_founding_engineer_cli.py --user phunterlau --enhanced
    uv run python enhanced_founding_engineer_cli.py --user user@example.com --months 6 --format detailed --enhanced
"""

import argparse
import os
import json
from datetime import datetime
from founding_engineer_reviewer import FoundingEngineerReviewer, save_review_report
from code_analysis_utils import CodeAnalyzer, get_golden_nuggets_from_commits
from collaboration_analysis_utils import CollaborationAnalyzer, compare_estimated_vs_factual


def save_enhanced_review_report(enhanced_metrics: dict, user: str, output_format: str = 'json') -> str:
    """Save the enhanced founding engineer review report."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if output_format == 'json':
        filename = f"enhanced_founding_engineer_review_{user}_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(enhanced_metrics, f, indent=2, default=str)
        print(f"💾 Enhanced review saved to: {filename}")
        
    elif output_format == 'detailed':
        filename = f"enhanced_founding_engineer_review_{user}_{timestamp}.md"
        
        base_metrics = enhanced_metrics['base_metrics']
        code_analysis = enhanced_metrics.get('code_analysis', {})
        collab_analysis = enhanced_metrics.get('factual_collaboration', {})
        repo_impact = enhanced_metrics.get('repository_impact', [])
        interview_prep = enhanced_metrics.get('interview_preparation', {})
        
        with open(filename, 'w') as f:
            f.write(f"# Enhanced Founding Engineer Review: {user}\n\n")
            f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Enhancement Level:** Complete (Steps 1-4)\n\n")
            
            # Executive Summary
            f.write("## 🎯 Executive Summary\n\n")
            f.write(f"**Overall Score:** {base_metrics.founding_engineer_score:.1f}/100\n")
            f.write(f"**Recommendation:** {base_metrics.recommendation}\n")
            f.write(f"**Code Quality Enhancement:** {code_analysis.get('summary', {}).get('quality_score', 0):.2f}/1.0\n")
            f.write(f"**Factual Collaboration Style:** {collab_analysis.get('collaboration_style', 'Unknown')}\n")
            f.write(f"**High-Impact Repositories:** {len([r for r in repo_impact if r.get('impact_score', 0) > 0.5])}\n\n")
            
            # Enhanced Analysis Results
            f.write("## 📊 Enhanced Analysis Results\n\n")
            
            # Step 1: Code Content Analysis
            f.write("### 🔬 Step 1: Code Content Analysis\n")
            f.write(f"- **Commits Analyzed:** {code_analysis.get('summary', {}).get('total_commits_analyzed', 0)}\n")
            f.write(f"- **Quality Score:** {code_analysis.get('summary', {}).get('quality_score', 0):.2f}/1.0\n")
            f.write(f"- **Avg Complexity:** {code_analysis.get('summary', {}).get('avg_complexity_score', 0):.2f}/1.0\n")
            
            top_concerns = code_analysis.get('summary', {}).get('top_concerns', [])
            if top_concerns:
                f.write(f"- **Top Concerns:** {', '.join(top_concerns)}\n")
            f.write("\n")
            
            # Step 2: Factual Collaboration
            f.write("### 🤝 Step 2: Factual Collaboration Analysis\n")
            f.write(f"- **Reviews Analyzed:** {collab_analysis.get('total_reviews_analyzed', 0)}\n")
            f.write(f"- **Collaboration Style:** {collab_analysis.get('collaboration_style', 'Unknown')}\n")
            f.write(f"- **Review Quality:** {collab_analysis.get('avg_review_quality_score', 0):.2f}/1.0\n")
            f.write(f"- **Mentorship Score:** {collab_analysis.get('mentorship_score', 0):.2f}/1.0\n\n")
            
            # Step 3: Repository Impact
            f.write("### 🌟 Step 3: Repository Impact Analysis\n")
            high_impact_repos = [r for r in repo_impact if r.get('impact_score', 0) > 0.5]
            f.write(f"- **Total Repositories:** {len(repo_impact)}\n")
            f.write(f"- **High-Impact Repositories:** {len(high_impact_repos)}\n")
            
            if high_impact_repos:
                f.write("- **Top Impact Repositories:**\n")
                for repo in high_impact_repos[:3]:
                    f.write(f"  - {repo['name']}: {repo['stars']} ⭐, {repo['forks']} 🍴 (Impact: {repo['impact_score']:.2f})\n")
            f.write("\n")
            
            # Step 4: Interview Preparation
            f.write("### 💎 Step 4: Interview Golden Nuggets\n")
            total_nuggets = interview_prep.get('total_nuggets', 0)
            f.write(f"- **Total Golden Nuggets:** {total_nuggets}\n")
            
            suggested_questions = interview_prep.get('suggested_questions', [])
            if suggested_questions:
                f.write("- **Suggested Interview Questions:**\n")
                for i, question in enumerate(suggested_questions[:5], 1):
                    f.write(f"  {i}. {question}\n")
            f.write("\n")
            
            # Base System Results
            f.write("## 📋 Base System Results\n\n")
            f.write("### Technical Proficiency\n")
            f.write(f"- **AI/ML Frameworks:** {', '.join(base_metrics.ai_ml_frameworks) if base_metrics.ai_ml_frameworks else 'None'}\n")
            f.write(f"- **Performance Languages:** {base_metrics.performance_languages}\n")
            f.write(f"- **Dependency Sophistication:** {base_metrics.dependency_sophistication_score:.2f}\n\n")
            
            f.write("### Engineering Craftsmanship\n")
            f.write(f"- **Commit-Issue Linking:** {base_metrics.commit_issue_linking_ratio:.1%}\n")
            f.write(f"- **Testing Commitment:** {base_metrics.testing_commitment_ratio:.1%}\n")
            f.write(f"- **Structured Workflow:** {base_metrics.structured_workflow_score:.2f}\n\n")
            
            f.write("### Strengths & Risk Factors\n")
            if base_metrics.strengths:
                f.write("**Strengths:**\n")
                for strength in base_metrics.strengths:
                    f.write(f"- {strength}\n")
            
            if base_metrics.risk_factors:
                f.write("\n**Risk Factors:**\n")
                for risk in base_metrics.risk_factors:
                    f.write(f"- {risk}\n")
        
        print(f"📄 Enhanced detailed review saved to: {filename}")
    
    return filename


def run_enhanced_analysis(user_identifier: str, months: int = 12, max_commits: int = 10, max_reviews: int = 15) -> dict:
    """Run the complete enhanced founding engineer analysis."""
    print(f"🚀 Running Enhanced Founding Engineer Analysis for {user_identifier}")
    print("=" * 80)
    
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    
    # Step 0: Base analysis
    print("📋 Step 0: Running base founding engineer analysis...")
    reviewer = FoundingEngineerReviewer(github_token)
    base_metrics = reviewer.generate_comprehensive_review(user_identifier, months)
    
    # Step 1: Enhanced code analysis
    print("\n🔬 Step 1: Running enhanced code content analysis...")
    code_analyzer = CodeAnalyzer(github_token)
    code_analyses = code_analyzer.analyze_user_commits(user_identifier, max_commits=max_commits)
    code_summary = code_analyzer.summarize_code_quality(code_analyses)
    code_nuggets = get_golden_nuggets_from_commits(code_analyses)
    
    # Step 2: Factual collaboration analysis
    print("\n🤝 Step 2: Running factual collaboration analysis...")
    collab_analyzer = CollaborationAnalyzer(github_token)
    factual_collab = collab_analyzer.analyze_user_collaboration_style(user_identifier, max_reviews=max_reviews)
    
    # Compare with estimated collaboration
    estimated_collab = {
        'review_comment_distribution': base_metrics.review_comment_distribution
    }
    collab_comparison = compare_estimated_vs_factual(estimated_collab, factual_collab)
    
    # Step 3: Repository impact analysis
    print("\n🌟 Step 3: Running repository impact analysis...")
    try:
        username = reviewer.resolve_user_login(user_identifier)
        if username:
            user = reviewer.g.get_user(username)
            repos = list(user.get_repos(type='all', sort='updated')[:15])
            
            repo_impact_analysis = []
            for repo in repos:
                impact_score = 0.0
                stars = repo.stargazers_count
                forks = repo.forks_count
                
                if stars >= 100: impact_score += 0.5
                if stars >= 1000: impact_score += 0.3
                if forks >= 50: impact_score += 0.2
                
                repo_impact_analysis.append({
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'stars': stars,
                    'forks': forks,
                    'impact_score': min(impact_score, 1.0),
                    'language': repo.language,
                    'description': repo.description
                })
            
            repo_impact_analysis.sort(key=lambda x: x['impact_score'], reverse=True)
        else:
            repo_impact_analysis = []
    except Exception as e:
        print(f"⚠️ Error in repository impact analysis: {e}")
        repo_impact_analysis = []
    
    # Step 4: Generate interview preparation
    print("\n💎 Step 4: Generating interview preparation materials...")
    all_nuggets = code_nuggets + factual_collab.get('golden_collaboration_nuggets', [])
    interview_prep = {
        'candidate': user_identifier,
        'total_nuggets': len(all_nuggets),
        'code_quality_examples': code_nuggets,
        'collaboration_examples': factual_collab.get('golden_collaboration_nuggets', []),
        'suggested_questions': [nugget.get('question_suggestion', '') for nugget in all_nuggets if nugget.get('question_suggestion')][:10]
    }
    
    # Compile enhanced metrics
    enhanced_metrics = {
        'base_metrics': base_metrics,
        'code_analysis': {
            'summary': code_summary,
            'golden_nuggets': code_nuggets,
            'commit_analyses_count': len(code_analyses)
        },
        'factual_collaboration': factual_collab,
        'collaboration_comparison': collab_comparison,
        'repository_impact': repo_impact_analysis,
        'interview_preparation': interview_prep,
        'enhancement_summary': {
            'total_commits_analyzed': len(code_analyses),
            'total_reviews_analyzed': factual_collab['total_reviews_analyzed'],
            'code_quality_score': code_summary['quality_score'],
            'collaboration_quality_score': factual_collab['avg_review_quality_score'],
            'collaboration_style': factual_collab['collaboration_style'],
            'high_impact_repositories': len([r for r in repo_impact_analysis if r['impact_score'] > 0.5]),
            'actionable_insights': len(interview_prep['suggested_questions'])
        }
    }
    
    return enhanced_metrics


def main():
    """Main function for the Enhanced Founding Engineer Review System."""
    parser = argparse.ArgumentParser(
        description="Enhanced Founding Engineer GitHub Review System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Enhanced Analysis Includes:
  1. Code content analysis beyond metadata
  2. Factual collaboration metrics vs estimates  
  3. Repository impact contextualization
  4. Golden nuggets for interview preparation

Examples:
  %(prog)s --user phunterlau --enhanced
  %(prog)s --user user@example.com --months 6 --format detailed --enhanced
  %(prog)s --user candidate123 --months 18 --format json --enhanced --max-commits 15
        """
    )
    
    parser.add_argument(
        '--user', '-u',
        required=True,
        help='GitHub username or email address of the candidate'
    )
    
    parser.add_argument(
        '--months', '-m',
        type=int,
        default=12,
        help='Number of months to analyze (default: 12)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'detailed'],
        default='detailed',
        help='Output format (default: detailed)'
    )
    
    parser.add_argument(
        '--enhanced',
        action='store_true',
        help='Run enhanced analysis with all improvements'
    )
    
    parser.add_argument(
        '--max-commits',
        type=int,
        default=10,
        help='Maximum commits to analyze for code quality (default: 10)'
    )
    
    parser.add_argument(
        '--max-reviews',
        type=int,
        default=15,
        help='Maximum reviews to analyze for collaboration (default: 15)'
    )
    
    args = parser.parse_args()
    
    print("🎯 Enhanced Founding Engineer Review System")
    print("=" * 60)
    print(f"Candidate: {args.user}")
    print(f"Analysis Period: {args.months} months")
    print(f"Output Format: {args.format}")
    print(f"Enhanced Analysis: {'Yes' if args.enhanced else 'No'}")
    print()
    
    try:
        if args.enhanced:
            # Run enhanced analysis
            enhanced_metrics = run_enhanced_analysis(
                args.user, 
                args.months, 
                args.max_commits, 
                args.max_reviews
            )
            
            # Save results
            output_file = save_enhanced_review_report(enhanced_metrics, args.user, args.format)
            
            # Print enhanced summary
            print(f"\n🎯 ENHANCED FOUNDING ENGINEER ASSESSMENT")
            print("=" * 60)
            enhancement_summary = enhanced_metrics['enhancement_summary']
            base_metrics = enhanced_metrics['base_metrics']
            
            print(f"Overall Score: {base_metrics.founding_engineer_score:.1f}/100")
            print(f"Recommendation: {base_metrics.recommendation}")
            print(f"Code Quality Enhancement: {enhancement_summary['code_quality_score']:.2f}/1.0")
            print(f"Factual Collaboration Style: {enhancement_summary['collaboration_style']}")
            print(f"Commits Analyzed: {enhancement_summary['total_commits_analyzed']}")
            print(f"Reviews Analyzed: {enhancement_summary['total_reviews_analyzed']}")
            print(f"High-Impact Repositories: {enhancement_summary['high_impact_repositories']}")
            print(f"Actionable Interview Insights: {enhancement_summary['actionable_insights']}")
            
        else:
            # Run standard analysis
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                print("❌ ERROR: GITHUB_TOKEN environment variable not set")
                return 1
            
            reviewer = FoundingEngineerReviewer(github_token)
            metrics = reviewer.generate_comprehensive_review(args.user, args.months)
            output_file = save_review_report(metrics, args.user, args.format)
            
            print(f"\n🎯 FOUNDING ENGINEER ASSESSMENT")
            print("=" * 50)
            print(f"Overall Score: {metrics.founding_engineer_score:.1f}/100")
            print(f"Recommendation: {metrics.recommendation}")
        
        print(f"\n📄 Full report: {output_file}")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
