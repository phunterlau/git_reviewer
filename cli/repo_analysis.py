import json
from datetime import datetime
from github_integration import get_commits, get_issues, get_pull_requests, fetch_all_contributions, benchmark_contribution_methods
from ai_analysis import review_commits_with_gpt, get_contribution_heatmap, review_contributions_with_gpt

def run_repository_mode(args):
    if args.benchmark:
        print('🏁 Running performance benchmark...')
        res = benchmark_contribution_methods(args.user, args.repo, args.limit)
        if res:
            print('✅ Benchmark completed successfully!')
            return 0
        print('❌ Benchmark failed!')
        return 1

    if args.optimized:
        print('🚀 Using optimized analysis approach...')
        print('Phase 1: Fetching all contribution data...')
        contributions = fetch_all_contributions(args.user, args.repo, args.limit)
        if not contributions:
            print('❌ Failed to fetch contribution data')
            return 1
        stats = contributions['summary_stats']
        print('✅ Fetched comprehensive data:')
        print(f"   - {stats['total_commits']} commits")
        print(f"   - {stats['total_prs']} pull requests")
        print(f"   - {stats['total_issues']} issues")
        print(f"   - {stats['total_reviews']} code reviews")
        print('\nPhase 2: Running optimized GPT analysis...')
        analysis = review_contributions_with_gpt(contributions)
        if 'error' in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
            return 1
        result_file = f"optimized_analysis_{args.user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file,'w') as f:
            json.dump({
                'contributions': contributions,
                'analysis': analysis,
                'metadata': {
                    'user': args.user,
                    'repo': args.repo,
                    'analysis_type': 'optimized',
                    'timestamp': datetime.now().isoformat()
                }
            }, f, indent=2)
        print('\n✅ Analysis completed successfully!')
        print(f'💾 Results saved to: {result_file}')
        meta = analysis.get('analysis_metadata', {})
        if meta:
            print(f"🤖 Model used: {meta.get('model_used','Unknown')}")
            print(f"💰 Tokens used: {meta.get('tokens_used','Unknown')}")
        if 'professional_summary' in analysis:
            summary = analysis['professional_summary']
            if isinstance(summary,str):
                sentences = summary.split('. ')[:2]
                print('\n🎯 Quick Summary:')
                print('   ' + '. '.join(sentences) + '.')
        return 0

    files_generated = []
    if args.type in ['commits','all']:
        print('Phase 1a: Fetching commits from GitHub...')
        commit_file = get_commits(args.user, args.repo, args.limit)
        if commit_file: files_generated.append(commit_file)
        else: print('Failed to fetch commits.')
    if args.type in ['issues','all']:
        print('Phase 1b: Fetching issues from GitHub...')
        issues_file = get_issues(args.user, args.repo, args.limit)
        if issues_file: files_generated.append(issues_file)
        else: print('No issues found or failed to fetch issues.')
    if args.type in ['pull_requests','all']:
        print('Phase 1c: Fetching pull requests from GitHub...')
        prs_file = get_pull_requests(args.user, args.repo, args.limit)
        if prs_file: files_generated.append(prs_file)
        else: print('No pull requests found or failed to fetch pull requests.')
    if not files_generated:
        print('No data was found. Please check your inputs and try again.')
        return 1
    if args.heatmap:
        print('\n' + '-'*60)
        print('Phase 1d: Fetching contribution heatmap...')
        heatmap_result = get_contribution_heatmap(args.user, days=args.heatmap_days, output_format=args.heatmap_format)
        if heatmap_result:
            heatmap_file = f"heatmap_{args.user.replace('@','_at_').replace('.','_')}.{args.heatmap_format}"
            files_generated.append(heatmap_file)
            print(f"Heatmap shows {heatmap_result['totalContributions']} total contributions in last {args.heatmap_days} days")
        else:
            print('Failed to fetch heatmap data.')
    if args.type in ['commits','all'] and any('commits_' in f for f in files_generated):
        commit_file = next(f for f in files_generated if 'commits_' in f)
        print('\n' + '-'*60)
        print('Phase 2: Analyzing commits with GPT-4o-mini...')
        review = review_commits_with_gpt(commit_file)
        if review:
            print('\n' + '='*60)
            print('REVIEW COMPLETE')
            print('='*60 + '\n')
            print('📊 PROGRAMMER REVIEW SUMMARY')
            print('-'*40)
            if 'overallRating' in review: print(f"Overall Rating: {review['overallRating']}")
            if 'programmingLanguageExpertise' in review: print(f"Programming Expertise: {review['programmingLanguageExpertise']}")
            if 'reviewHighlights' in review and isinstance(review['reviewHighlights'], list):
                print('\nKey Highlights:')
                for i,h in enumerate(review['reviewHighlights'],1):
                    print(f'{i}. {h}')
            print(f"\nDetailed review saved in: {commit_file.replace('.md','_review.json')}")
        else:
            print('Failed to get review from GPT-4o-mini.')
    print('\n📁 GENERATED FILES:')
    print('-'*40)
    for f in files_generated:
        print(f'✅ {f}')
    return 0
