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
from datetime import datetime, timedelta
from collections import Counter, defaultdict

# Optional dependency handling
try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover
    def load_dotenv():  # fallback no-op
        pass

try:
    from github import Github  # type: ignore
    from github.GithubException import GithubException, RateLimitExceededException  # type: ignore
except ImportError:  # pragma: no cover
    Github = None  # type: ignore
    class GithubException(Exception):
        pass
    class RateLimitExceededException(GithubException):
        pass
from github_integration import (
    get_commits,
    get_issues,
    get_pull_requests,
    fetch_all_contributions,
    benchmark_contribution_methods,
)
from ai_analysis import (
    review_commits_with_gpt,
    get_contribution_heatmap,
    review_contributions_with_gpt,
)
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
        choices=['commits', 'issues', 'pull_requests', 'all', 'founding_engineer', 'recent_quality'],
        default='commits',
        help='Analysis type: commits/issues/pull_requests/all/founding_engineer/recent_quality'
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

    parser.add_argument(
        '--recent-days',
        type=int,
        default=30,
        help='Time window in days for recent_quality analysis (default: 30)'
    )

    parser.add_argument(
        '--max-commits',
        type=int,
        default=250,
        help='Maximum commits to inspect per user for recent_quality (default: 250)'
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


def run_recent_code_quality_review(user_arg: str, days: int = 30, max_commits: int = 250):
    """Analyze recent commit code quality for one or multiple GitHub users.

    Pulls commits (last N days) across ALL public repos for each user, fetches diffs, filters
    out non-code changes, computes quality & engineering capability indicators, and
    summarizes attributes relevant to founding engineer potential.

    Args:
        user_arg: A single username or comma-separated list of usernames.
        days: Lookback window (default 30 days)
        max_commits: Safety cap on number of commits (per user)
    """
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ GITHUB_TOKEN not set.")
        return 1

    gh = Github(token, per_page=100)
    usernames = [u.strip() for u in user_arg.split(',') if u.strip()]
    since = datetime.utcnow() - timedelta(days=days)

    # Simple code file extensions (can expand)
    code_exts = {
        '.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.cpp', '.cc', '.c', '.h', '.hpp',
        '.java', '.kt', '.rb', '.php', '.swift', '.scala', '.cs', '.sh', '.bash', '.zsh',
        '.ps1', '.sql', '.html', '.css', '.scss', '.lua', '.mdx'
    }
    non_code_exts = {'.md', '.rst', '.txt', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf', '.lock'}

    def is_code_file(filename: str) -> bool:
        fn = filename.lower()
        for ext in non_code_exts:
            if fn.endswith(ext):
                return False
        return any(fn.endswith(ext) for ext in code_exts)

    def classify_commit(msg: str):
        lower = msg.lower()
        if any(k in lower for k in ['refactor', 'cleanup', 'restructure']):
            return 'refactor'
        if any(k in lower for k in ['feat', 'feature', 'add', 'implement']):
            return 'feature'
        if any(k in lower for k in ['fix', 'bug', 'patch']):
            return 'bugfix'
        if any(k in lower for k in ['perf', 'optimiz', 'speed', 'latency']):
            return 'performance'
        if any(k in lower for k in ['test', 'ci', 'coverage']):
            return 'testing'
        if any(k in lower for k in ['doc', 'readme']):
            return 'docs'
        return 'other'

    for username in usernames:
        print("=" * 60)
        print(f"🧪 Recent Code Quality Review: {username} (last {days} days)")
        print("=" * 60)
        try:
            user = gh.get_user(username)
        except GithubException as e:
            print(f"❌ Failed to fetch user {username}: {e}")
            continue

        # Collect commits across repos
        all_commits_meta = []  # (repo_name, commit)
        try:
            repos = list(user.get_repos())
        except RateLimitExceededException:
            print("❌ Rate limit exceeded while listing repos.")
            return 1
        except GithubException as e:
            print(f"❌ Error fetching repos: {e}")
            continue

        for repo in repos:
            try:
                commits = repo.get_commits(author=user, since=since)
                for c in commits:
                    all_commits_meta.append((repo, c))
                    if len(all_commits_meta) >= max_commits:
                        break
                if len(all_commits_meta) >= max_commits:
                    break
            except GithubException:
                continue  # skip private/inaccessible

        total_found = len(all_commits_meta)
        if total_found == 0:
            print(f"⚠️  No commits found in the last {days} days.")
            continue

        print(f"🔍 Found {total_found} commits (pre-filter). Fetching diffs & analyzing...")

        # Metrics containers
        commit_type_counter = Counter()
        language_counter = Counter()
        test_commits = 0
        perf_commits = 0
        refactor_commits = 0
        total_adds = 0
        total_dels = 0
        code_commits = 0
        large_changes = 0
        commits_detail = []              # lightweight summary list used for top commit selection
        full_commit_records = []         # full enriched commit data for JSON output

        def render_progress(i, n, bar_len=30):
            filled = int(bar_len * (i + 1) / n)
            bar = '█' * filled + '░' * (bar_len - filled)
            print(f"\rProgress: [{bar}] {i + 1}/{n}", end='')

        for idx, (repo, commit_stub) in enumerate(all_commits_meta):
            render_progress(idx, total_found)
            try:
                # Need full commit to access files/diff
                full_commit = repo.get_commit(commit_stub.sha)
            except GithubException:
                continue

            files = getattr(full_commit, 'files', []) or []
            code_files = [f for f in files if is_code_file(f.filename)]
            if not code_files:
                continue  # ignore non-code change commits

            code_commits += 1
            adds = sum(f.additions for f in code_files)
            dels = sum(f.deletions for f in code_files)
            total_adds += adds
            total_dels += dels
            if adds + dels > 400:  # heuristic threshold for large / architectural change
                large_changes += 1

            message = full_commit.commit.message.split('\n')[0]
            ctype = classify_commit(message)
            commit_type_counter[ctype] += 1
            if ctype == 'testing':
                test_commits += 1
            if ctype == 'performance':
                perf_commits += 1
            if ctype == 'refactor':
                refactor_commits += 1

            # Approximate languages by extension
            exts = {os.path.splitext(f.filename)[1].lower() for f in code_files}
            for ext in exts:
                language_counter[ext] += 1

            # Build per-file details
            file_details = []
            for f in code_files:
                patch_text = getattr(f, 'patch', None)
                if patch_text and len(patch_text) > 15000:  # safety truncate
                    patch_text = patch_text[:15000] + '\n...TRUNCATED...'
                file_details.append({
                    'filename': f.filename,
                    'status': getattr(f, 'status', None),
                    'additions': getattr(f, 'additions', 0),
                    'deletions': getattr(f, 'deletions', 0),
                    'changes': getattr(f, 'changes', None),
                    'patch': patch_text,
                })

            is_merge = len(getattr(full_commit, 'parents', []) or []) > 1
            authored_date = None
            committed_date = None
            try:
                authored_date = full_commit.commit.author.date.isoformat() if full_commit.commit.author and full_commit.commit.author.date else None
            except Exception:
                pass
            try:
                committed_date = full_commit.commit.committer.date.isoformat() if full_commit.commit.committer and full_commit.commit.committer.date else None
            except Exception:
                pass

            commit_summary = {
                'repo': repo.full_name,
                'sha': full_commit.sha,
                'message': message,
                'additions': adds,
                'deletions': dels,
                'files_changed': len(code_files),
                'type': ctype,
            }
            commits_detail.append(commit_summary)

            full_commit_records.append({
                'repo': repo.full_name,
                'sha': full_commit.sha,
                'html_url': getattr(full_commit, 'html_url', None),
                'url': getattr(full_commit, 'url', None),
                'is_merge': is_merge,
                'authored_date': authored_date,
                'committed_date': committed_date,
                'author': getattr(full_commit.commit.author, 'name', None) if getattr(full_commit, 'commit', None) else None,
                'author_email': getattr(full_commit.commit.author, 'email', None) if getattr(full_commit, 'commit', None) else None,
                'committer': getattr(full_commit.commit.committer, 'name', None) if getattr(full_commit, 'commit', None) else None,
                'committer_email': getattr(full_commit.commit.committer, 'email', None) if getattr(full_commit, 'commit', None) else None,
                'message_full': full_commit.commit.message if getattr(full_commit, 'commit', None) else message,
                'summary': commit_summary,
                'additions': adds,
                'deletions': dels,
                'total_changes': adds + dels,
                'files': file_details,
                'languages_ext': list(exts),
                'classification': ctype,
                'verification': (lambda v: {
                    'verified': getattr(v, 'verified', None),
                    'reason': getattr(v, 'reason', None),
                    'signature': getattr(v, 'signature', None),
                    'payload': getattr(v, 'payload', None),
                } if v else None)(getattr(getattr(full_commit, 'commit', None), 'verification', None) if getattr(full_commit, 'commit', None) else None),
            })

        print()  # newline after progress bar
        if code_commits == 0:
            print("⚠️  No code commits after filtering non-code changes.")
            continue

        avg_adds = total_adds / code_commits
        avg_dels = total_dels / code_commits
        test_ratio = test_commits / code_commits
        refactor_ratio = refactor_commits / code_commits
        perf_ratio = perf_commits / code_commits
        large_ratio = large_changes / code_commits

        # Derive capability attributes
        capability_attrs = []
        if refactor_ratio >= 0.15:
            capability_attrs.append("Architectural Stewardship (significant refactoring activity)")
        if test_ratio >= 0.2:
            capability_attrs.append("Quality Discipline (meaningful share of test-focused commits)")
        if len(language_counter) >= 4:
            capability_attrs.append("Polyglot Execution (works across multiple stacks)")
        if perf_ratio >= 0.05:
            capability_attrs.append("Performance Awareness (explicit optimization work)")
        if large_ratio >= 0.1:
            capability_attrs.append("Systems Thinking (handles large / structural changes)")
        if not capability_attrs:
            capability_attrs.append("Focused Delivery (consistent incremental feature / bug work)")

        print(f"📊 SUMMARY (Code Commits Only)")
        print(f"   Total code commits: {code_commits} (from {total_found} raw commits)")
        print(f"   Lines added: {total_adds} | Lines deleted: {total_dels}")
        print(f"   Avg additions/commit: {avg_adds:.1f} | Avg deletions/commit: {avg_dels:.1f}")
        print(f"   Commit type distribution: {dict(commit_type_counter)}")
        print(f"   Test commit ratio: {test_ratio:.1%} | Refactor ratio: {refactor_ratio:.1%} | Perf ratio: {perf_ratio:.1%}")
        print(f"   Large structural change ratio: {large_ratio:.1%}")
        print(f"   Languages (by extension indicators): {', '.join(sorted(language_counter.keys()))}")

        print("\n🧠 FOUNDING ENGINEER ATTRIBUTE SIGNALS:")
        for attr in capability_attrs:
            print(f"   • {attr}")

        # Show top 5 significant commits (by size) for inspection
        top_commits = sorted(commits_detail, key=lambda c: c['additions'] + c['deletions'], reverse=True)[:5]
        print("\n🔍 Top Significant Commits:")
        for c in top_commits:
            print(f"   - {c['repo']}@{c['sha'][:7]} [{c['type']}] +{c['additions']}/-{c['deletions']} {c['message'][:70]}")

        # Simple heuristic overall assessment
        score = 0
        score += refactor_ratio * 30
        score += test_ratio * 20
        score += perf_ratio * 15
        score += min(len(language_counter), 6) * 3
        score += large_ratio * 25
        if score >= 35:
            rec = "🌟 Strong Founding Engineer Signals"
        elif score >= 22:
            rec = "✅ Solid Engineering Potential"
        elif score >= 12:
            rec = "⚠️ Emerging – Needs Broader Impact"
        else:
            rec = "❌ Limited Recent Differentiators"
        print(f"\n🏆 RECENT ACTIVITY ASSESSMENT: {rec} (score: {score:.1f})")

        # Persist JSON output
        ts_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        out_name = f"recent_quality_{username}_{ts_str}.json"
        commits_file = f"recent_quality_commits_{username}_{ts_str}.json"
        import json
        # Metrics / summary file
        with open(out_name, 'w') as f:
            json.dump({
                'username': username,
                'window_days': days,
                'generated_at': datetime.utcnow().isoformat(),
                'raw_commit_count': total_found,
                'code_commit_count': code_commits,
                'totals': {
                    'additions': total_adds,
                    'deletions': total_dels,
                },
                'averages': {
                    'adds_per_commit': avg_adds,
                    'dels_per_commit': avg_dels,
                },
                'ratios': {
                    'test_ratio': test_ratio,
                    'refactor_ratio': refactor_ratio,
                    'performance_ratio': perf_ratio,
                    'large_change_ratio': large_ratio,
                },
                'languages_ext': list(language_counter.keys()),
                'commit_type_distribution': dict(commit_type_counter),
                'capability_attributes': capability_attrs,
                'top_commits': top_commits,
                'assessment': {
                    'score': score,
                    'recommendation': rec,
                },
                'artifacts': {
                    'full_commit_details_file': commits_file
                }
            }, f, indent=2)

        # Full commit record file
        with open(commits_file, 'w') as f:
            json.dump({
                'username': username,
                'generated_at': datetime.utcnow().isoformat(),
                'window_start': (datetime.utcnow() - timedelta(days=days)).isoformat(),
                'window_days': days,
                'commit_records_count': len(full_commit_records),
                'commits': full_commit_records,
            }, f, indent=2)

        print(f"💾 Saved detailed metrics to {out_name}")
        print(f"💾 Saved full commit records to {commits_file}\n")
    return 0


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
    
    if args.type == 'recent_quality':
        return run_recent_code_quality_review(args.user, days=args.recent_days, max_commits=args.max_commits)
    
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
