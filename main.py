#!/usr/bin/env python3
"""
GitHub Commit Reviewer & Founding Engineer Analyzer

This tool can:
1. Analyze commits, issues, and pull requests from a specific GitHub repository 
2. Run comprehensive founding engineer analysis across ALL user repositories
3. Use GPT-4o-mini to provide insights about programmer capabilities

Repository Analysis Usage:
    python main.py --user username --repo owner/repo --type commits
    python main.py -u user@example.com -r https://github.com/owner/repo -t all

Founding Engineer Analysis Usage:
    python main.py --user username --type founding_engineer
    python main.py -u phunterlau -t founding_engineer --limit 20

Arguments:
    --user, -u: GitHub username or email
    --repo, -r: GitHub repository URL (required for repo analysis, optional for founding engineer)
    --type, -t: Analysis type (commits, issues, pull_requests, all, founding_engineer)
"""

import os
import sys
import argparse
import asyncio
from dotenv import load_dotenv
from github_integration import get_commits, get_issues, get_pull_requests, fetch_all_contributions, benchmark_contribution_methods
from ai_analysis import review_commits_with_gpt, get_contribution_heatmap, review_contributions_with_gpt
from core_analysis import OptimizedHybridAnalyzer, ContributionImpactScorer


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze GitHub contributions using GPT-4o-mini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
Repository Analysis:
  %(prog)s --user phunterlau --repo phunterlau/yolo_term --type commits
  %(prog)s -u user@example.com -r https://github.com/microsoft/vscode -t all --limit 50
  %(prog)s --user trivialfis --repo dmlc/xgboost --type issues --limit 200
  %(prog)s --user trivialfis --repo dmlc/xgboost --type commits --heatmap

Founding Engineer Analysis (Cross-Repository):
  %(prog)s --user phunterlau --type founding_engineer
  %(prog)s -u trivialfis -t founding_engineer --limit 20
  
Advanced Features:
  %(prog)s --user hliu --repo microsoft/vscode --optimized --limit 30    (NEW: optimized analysis)
  %(prog)s --user hliu --repo microsoft/vscode --benchmark --limit 20     (NEW: performance benchmark)
        """
    )
    
    parser.add_argument(
        '--user', '-u',
        required=True,
        help='GitHub username or email address'
    )
    
    parser.add_argument(
        '--repo', '-r', 
        required=False,
        help='GitHub repository URL or owner/repo format (required for commits/issues/PRs analysis, optional for founding_engineer)'
    )
    
    parser.add_argument(
        '--type', '-t',
        choices=['commits', 'issues', 'pull_requests', 'all', 'founding_engineer'],
        default='commits',
        help='Type of analysis to perform (default: commits). Use "founding_engineer" for comprehensive cross-repository founding engineer analysis'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=100,
        help='Maximum number of records to fetch (default: 100)'
    )
    
    parser.add_argument(
        '--heatmap',
        action='store_true',
        help='Also fetch contribution heatmap data for the user'
    )
    
    parser.add_argument(
        '--heatmap-days',
        type=int,
        default=365,
        help='Number of days for heatmap data (default: 365, max: 365)'
    )
    
    parser.add_argument(
        '--heatmap-format',
        choices=['json', 'md'],
        default='json',
        help='Output format for heatmap data (default: json)'
    )
    
    parser.add_argument(
        '--optimized',
        action='store_true',
        help='Use the new optimized analysis approach (unified fetching + caching + token optimization)'
    )
    
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Run performance benchmark comparing old vs new approaches'
    )
    
    return parser.parse_args()


def run_founding_engineer_analysis(username: str, limit: int):
    """
    Run comprehensive founding engineer analysis across all repositories.
    
    Args:
        username (str): GitHub username to analyze
        max_contributions (int): Maximum contributions to analyze
        
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    print(f"🔍 Running comprehensive founding engineer analysis for {username}...")
    print("This analyzes contributions across ALL repositories, not just one.")
    print()
    
    try:
        # Initialize the hybrid analyzer
        token = os.getenv('GITHUB_TOKEN')
        analyzer = OptimizedHybridAnalyzer(token)
        
        # Initialize counters
        external_count = 0
        own_count = 0
        
        print("📊 Phase 1: Hybrid Analysis (Cross-Repository)")
        start_time = __import__('time').time()
        
        # Run the analysis (synchronous, not async)
        result = analyzer.analyze_contributor(username, max_contributions=limit)
        
        analysis_time = __import__('time').time() - start_time
        
        print(f"⏱️ Analysis completed in {analysis_time:.1f} seconds")
        print(f"📊 API calls made: {result.get('api_calls_made', 'N/A')}")
        print()
        
        # Display results
        print("🎯 FOUNDING ENGINEER ASSESSMENT:")
        print("=" * 50)
        print(f"👤 User: {result.get('username', username)}")
        print(f"🧠 G-Index: {result.get('g_index', 0)}")
        print(f"🔍 Analysis Type: {result.get('analysis_type', 'standard')}")
        
        # Check if we have contributions or leadership mode
        if result.get('analysis_type') == 'maintainer_leadership':
            print(f"👑 Leadership Score: {result.get('leadership_score', 0):.2f}")
            print(f"⭐ Stars Managed: {result.get('total_stars_managed', 0):,}")
            
            projects = result.get('major_projects', [])
            if projects:
                print(f"\n🏆 Major Projects:")
                for project in projects[:3]:
                    print(f"   - {project['name']}: {project['stars']:,} stars")
        else:
            # Check if contributions exist (different result structure)
            contributions = result.get('contributions', [])
            if contributions:
                print(f"📈 Contributions Analyzed: {len(contributions)}")
                
                # Count external vs own contributions
                external_count = 0
                own_count = 0
                for contrib in contributions:
                    if hasattr(contrib, 'type') and contrib.type == 'external_pr':
                        external_count += 1
                    else:
                        own_count += 1
                
                print(f"📤 External contributions: {external_count}")
                print(f"📦 Own projects: {own_count}")
                
                # Show top contributions
                print(f"\n🏆 Top Contributions:")
                for i, contrib in enumerate(contributions[:3], 1):
                    repo_name = getattr(contrib, 'repo_name', 'Unknown')
                    title = getattr(contrib, 'title', 'No title')
                    score = getattr(contrib, 'score', 0)
                    print(f"   {i}. {repo_name}")
                    print(f"      {title[:60]}...")
                    print(f"      Score: {score:.2f}")
            else:
                print("📈 No contributions found or different result format")
        
        # Generate recommendation
        g_index = result.get('g_index', 0)
        if g_index >= 3:
            recommendation = "🌟 HIGHLY RECOMMENDED"
        elif g_index >= 2:
            recommendation = "✅ RECOMMENDED"
        elif g_index >= 1:
            recommendation = "⚠️ CONSIDER"
        else:
            recommendation = "❌ NEEDS MORE VALIDATION"
            
        print(f"\n🏆 FOUNDING ENGINEER RECOMMENDATION: {recommendation}")
        print(f"💡 Reasoning: G-Index of {g_index} indicates founding engineer potential")
        print()
        
        # Save results
        import json
        from datetime import datetime
        
        result_file = f"founding_engineer_analysis_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_data = {
            "analysis_results": result,
            "assessment": {
                "g_index": g_index,
                "recommendation": recommendation,
                "external_contributions": external_count,
                "own_projects": own_count,
                "analysis_time_seconds": analysis_time
            },
            "metadata": {
                "username": username,
                "analysis_type": "founding_engineer",
                "timestamp": datetime.now().isoformat(),
                "analyzer_version": "OptimizedHybridAnalyzer"
            }
        }
        
        with open(result_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"💾 Detailed results saved to: {result_file}")
        print(f"🎯 Quick recommendation: {recommendation}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during founding engineer analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main function to run the GitHub commit reviewer."""
    args = parse_arguments()
    
    # Validate arguments
    if args.type in ['commits', 'issues', 'pull_requests', 'all', 'benchmark'] and not args.repo:
        print("ERROR: --repo is required for repository-specific analysis")
        print("Use --type founding_engineer for cross-repository founding engineer analysis")
        return 1
    
    print("=" * 60)
    if args.type == 'founding_engineer':
        print("🚀 Founding Engineer Analysis")
    else:
        print("GitHub Commit Reviewer")
    print("=" * 60)
    print(f"User: {args.user}")
    if args.repo:
        print(f"Repository: {args.repo}")
    print(f"Analysis type: {args.type}")
    print(f"Record limit: {args.limit}")
    if args.heatmap:
        print(f"Heatmap: {args.heatmap_days} days ({args.heatmap_format} format)")
    if args.optimized:
        print("🚀 Mode: Optimized analysis (unified + cached + token-efficient)")
    if args.benchmark:
        print("🏁 Mode: Performance benchmark")
    print()
    
    # Load environment variables
    load_dotenv()
    
    # Check if required environment variables are set
    if not os.getenv("GITHUB_TOKEN"):
        print("ERROR: GITHUB_TOKEN not found in .env file")
        print("Please add your GitHub Personal Access Token to the .env file")
        print("Generate one at: https://github.com/settings/tokens")
        return 1
    
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in .env file")
        print("Please add your OpenAI API key to the .env file")
        print("Get one at: https://platform.openai.com/api-keys")
        return 1
    
    print("-" * 60)
    
    # Handle founding engineer analysis
    if args.type == 'founding_engineer':
        return run_founding_engineer_analysis(args.user, args.limit)
    
    # Handle benchmark mode
    if args.benchmark:
        print("🏁 Running performance benchmark...")
        benchmark_results = benchmark_contribution_methods(args.user, args.repo, args.limit)
        if benchmark_results:
            print("✅ Benchmark completed successfully!")
            return 0
        else:
            print("❌ Benchmark failed!")
            return 1
    
    # Handle optimized analysis mode
    if args.optimized:
        print("🚀 Using optimized analysis approach...")
        print("Phase 1: Fetching all contribution data...")
        
        contributions = fetch_all_contributions(args.user, args.repo, args.limit)
        if not contributions:
            print("❌ Failed to fetch contribution data")
            return 1
        
        print(f"✅ Fetched comprehensive data:")
        stats = contributions['summary_stats']
        print(f"   - {stats['total_commits']} commits")
        print(f"   - {stats['total_prs']} pull requests")
        print(f"   - {stats['total_issues']} issues") 
        print(f"   - {stats['total_reviews']} code reviews")
        
        print("\nPhase 2: Running optimized GPT analysis...")
        analysis = review_contributions_with_gpt(contributions)
        
        if "error" in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
            return 1
            
        # Save results
        import json
        from datetime import datetime
        
        result_file = f"optimized_analysis_{args.user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w') as f:
            json.dump({
                "contributions": contributions,
                "analysis": analysis,
                "metadata": {
                    "user": args.user,
                    "repo": args.repo,
                    "analysis_type": "optimized",
                    "timestamp": datetime.now().isoformat()
                }
            }, f, indent=2)
        
        print(f"\n✅ Analysis completed successfully!")
        print(f"💾 Results saved to: {result_file}")
        
        if "analysis_metadata" in analysis:
            metadata = analysis["analysis_metadata"]
            print(f"🤖 Model used: {metadata.get('model_used', 'Unknown')}")
            print(f"💰 Tokens used: {metadata.get('tokens_used', 'Unknown')}")
        
        # Show brief summary
        if "professional_summary" in analysis:
            print(f"\n🎯 Quick Summary:")
            summary = analysis["professional_summary"]
            if isinstance(summary, str):
                sentences = summary.split('. ')[:2]
                print('   ' + '. '.join(sentences) + '.' if sentences else summary[:200])
        
        return 0

    files_generated = []    # Fetch data based on analysis type
    if args.type in ['commits', 'all']:
        print("Phase 1a: Fetching commits from GitHub...")
        commit_file = get_commits(args.user, args.repo, args.limit)
        if commit_file:
            files_generated.append(commit_file)
        else:
            print("Failed to fetch commits.")
    
    if args.type in ['issues', 'all']:
        print("Phase 1b: Fetching issues from GitHub...")
        issues_file = get_issues(args.user, args.repo, args.limit)
        if issues_file:
            files_generated.append(issues_file)
        else:
            print("No issues found or failed to fetch issues.")
    
    if args.type in ['pull_requests', 'all']:
        print("Phase 1c: Fetching pull requests from GitHub...")
        prs_file = get_pull_requests(args.user, args.repo, args.limit)
        if prs_file:
            files_generated.append(prs_file)
        else:
            print("No pull requests found or failed to fetch pull requests.")
    
    if not files_generated:
        print("No data was found. Please check your inputs and try again.")
        return 1
    
    # Fetch heatmap data if requested
    if args.heatmap:
        print()
        print("-" * 60)
        print("Phase 1d: Fetching contribution heatmap...")
        heatmap_result = get_contribution_heatmap(
            args.user, 
            days=args.heatmap_days, 
            output_format=args.heatmap_format
        )
        if heatmap_result:
            heatmap_file = f"heatmap_{args.user.replace('@', '_at_').replace('.', '_')}.{args.heatmap_format}"
            files_generated.append(heatmap_file)
            print(f"Heatmap shows {heatmap_result['totalContributions']} total contributions in last {args.heatmap_days} days")
        else:
            print("Failed to fetch heatmap data.")

    # Analyze commits with GPT-4o-mini if commits were fetched
    if args.type in ['commits', 'all'] and any('commits_' in f for f in files_generated):
        commit_file = next(f for f in files_generated if 'commits_' in f)
        
        print()
        print("-" * 60)
        
        print("Phase 2: Analyzing commits with GPT-4o-mini...")
        review = review_commits_with_gpt(commit_file)
        
        if not review:
            print("Failed to get review from GPT-4o-mini.")
        else:
            print()
            print("=" * 60)
            print("REVIEW COMPLETE")
            print("=" * 60)
            print()
            
            # Display summary
            print("📊 PROGRAMMER REVIEW SUMMARY")
            print("-" * 40)
            
            if "overallRating" in review:
                print(f"Overall Rating: {review['overallRating']}")
            
            if "programmingLanguageExpertise" in review:
                print(f"Programming Expertise: {review['programmingLanguageExpertise']}")
            
            if "reviewHighlights" in review and isinstance(review["reviewHighlights"], list):
                print("\nKey Highlights:")
                for i, highlight in enumerate(review["reviewHighlights"], 1):
                    print(f"{i}. {highlight}")
            
            print(f"\nDetailed review saved in: {commit_file.replace('.md', '_review.json')}")
    
    # Display all generated files
    print()
    print("📁 GENERATED FILES:")
    print("-" * 40)
    for file_path in files_generated:
        print(f"✅ {file_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
