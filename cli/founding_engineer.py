import os, json
from datetime import datetime
from core_analysis import OptimizedHybridAnalyzer

def run(username: str, limit: int):
    token = os.getenv('GITHUB_TOKEN')
    analyzer = OptimizedHybridAnalyzer(token)
    print(f"🔍 Running comprehensive founding engineer analysis for {username}...\n")
    start = __import__('time').time()
    result = analyzer.analyze_contributor(username, max_contributions=limit)
    elapsed = __import__('time').time() - start
    g_index = result.get('g_index',0)
    analysis_type = result.get('analysis_type','standard')

    print("🎯 FOUNDING ENGINEER ASSESSMENT:")
    print("="*50)
    print(f"👤 User: {result.get('username', username)}")
    print(f"🧠 G-Index: {g_index}")
    print(f"🔍 Analysis Type: {analysis_type}")

    external_count = 0
    own_count = 0
    if analysis_type == 'maintainer_leadership':
        print(f"👑 Leadership Score: {result.get('leadership_score',0):.2f}")
        print(f"⭐ Stars Managed: {result.get('total_stars_managed',0):,}")
        for project in result.get('major_projects',[])[:3]:
            print(f"   - {project['name']}: {project['stars']:,} stars")
    else:
        contributions = result.get('contributions', [])
        if contributions:
            for contrib in contributions:
                if getattr(contrib,'type',None) == 'external_pr':
                    external_count += 1
                else:
                    own_count += 1
            print(f"📈 Contributions Analyzed: {len(contributions)}")
            print(f"📤 External contributions: {external_count}")
            print(f"📦 Own projects: {own_count}")
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
    print(f"⏱️ Analysis completed in {elapsed:.1f}s | API calls: {result.get('api_calls_made','N/A')}")

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_file = f"founding_engineer_analysis_{username}_{ts}.json"
    with open(out_file,'w') as f:
        json.dump({
            'analysis_results': result,
            'assessment': {
                'g_index': g_index,
                'recommendation': recommendation,
                'external_contributions': external_count,
                'own_projects': own_count,
                'analysis_time_seconds': elapsed
            },
            'metadata': {
                'username': username,
                'analysis_type': 'founding_engineer',
                'timestamp': datetime.now().isoformat(),
                'analyzer_version': 'OptimizedHybridAnalyzer'
            }
        }, f, indent=2, default=str)
    print(f"💾 Saved results -> {out_file}")
    return 0
