import os, json
from datetime import datetime, timedelta
from collections import Counter

try:
    from github import Github  # type: ignore
    from github.GithubException import GithubException, RateLimitExceededException  # type: ignore
except ImportError:
    Github = None  # type: ignore
    class GithubException(Exception):
        pass
    class RateLimitExceededException(GithubException):
        pass

CODE_EXTS = {'.py','.js','.ts','.tsx','.jsx','.go','.rs','.cpp','.cc','.c','.h','.hpp','.java','.kt','.rb','.php','.swift','.scala','.cs','.sh','.bash','.zsh','.ps1','.sql','.html','.css','.scss','.lua','.mdx'}
NON_CODE_EXTS = {'.md','.rst','.txt','.png','.jpg','.jpeg','.gif','.svg','.pdf','.lock'}

def is_code_file(fn: str) -> bool:
    l = fn.lower()
    if any(l.endswith(ext) for ext in NON_CODE_EXTS):
        return False
    return any(l.endswith(ext) for ext in CODE_EXTS)

def classify(message: str) -> str:
    m = message.lower()
    if any(k in m for k in ['refactor','cleanup','restructure']): return 'refactor'
    if any(k in m for k in ['feat','feature','add','implement']): return 'feature'
    if any(k in m for k in ['fix','bug','patch']): return 'bugfix'
    if any(k in m for k in ['perf','optimiz','speed','latency']): return 'performance'
    if any(k in m for k in ['test','ci','coverage']): return 'testing'
    if any(k in m for k in ['doc','readme']): return 'docs'
    return 'other'

def run(user_arg: str, days: int = 30, max_commits: int = 250):
    token = os.getenv('GITHUB_TOKEN')
    if Github is None:
        print('❌ PyGithub not installed. Install with: uv pip install PyGithub')
        return 1
    if not token:
        print('❌ Missing GITHUB_TOKEN environment variable.')
        return 1
    gh = Github(token, per_page=100)
    usernames = [u.strip() for u in user_arg.split(',') if u.strip()]
    since = datetime.utcnow() - timedelta(days=days)

    for username in usernames:
        print('='*60)
        print(f'🧪 Recent Code Quality Review: {username} (last {days} days)')
        print('='*60)
        try:
            user = gh.get_user(username)
        except GithubException as e:
            print(f'❌ Failed to fetch user {username}: {e}')
            continue
        try:
            repos = list(user.get_repos())
        except RateLimitExceededException:
            print('❌ Rate limit exceeded listing repos.')
            return 1
        except GithubException as e:
            print(f'❌ Error listing repos: {e}')
            continue
        all_commits = []
        for repo in repos:
            try:
                for c in repo.get_commits(author=user, since=since):
                    all_commits.append((repo,c))
                    if len(all_commits) >= max_commits: break
                if len(all_commits) >= max_commits: break
            except GithubException:
                continue
        total = len(all_commits)
        if total == 0:
            print(f'⚠️  No commits found in last {days} days.')
            continue
        print(f'🔍 Found {total} commits (pre-filter). Fetching diffs & analyzing...')
        commit_type_counter = Counter()
        language_counter = Counter()
        test_commits = perf_commits = refactor_commits = 0
        total_adds = total_dels = code_commits = large_changes = 0
        commits_detail = []
        full_records = []

        def progress(i,n,bar_len=30):
            filled = int(bar_len * (i+1)/n)
            print(f"\rProgress: [{'█'*filled+'░'*(bar_len-filled)}] {i+1}/{n}",end='')

        for idx,(repo,stub) in enumerate(all_commits):
            progress(idx,total)
            try:
                full = repo.get_commit(stub.sha)
            except GithubException:
                continue
            files = getattr(full,'files',[]) or []
            code_files = [f for f in files if is_code_file(f.filename)]
            if not code_files: continue
            code_commits += 1
            adds = sum(f.additions for f in code_files)
            dels = sum(f.deletions for f in code_files)
            total_adds += adds; total_dels += dels
            if adds + dels > 400: large_changes += 1
            message = full.commit.message.split('\n')[0]
            ctype = classify(message)
            commit_type_counter[ctype] += 1
            if ctype == 'testing': test_commits += 1
            if ctype == 'performance': perf_commits += 1
            if ctype == 'refactor': refactor_commits += 1
            exts = {os.path.splitext(f.filename)[1].lower() for f in code_files}
            for ext in exts: language_counter[ext] += 1
            file_details = []
            for f in code_files:
                patch = getattr(f,'patch',None)
                if patch and len(patch) > 15000:
                    patch = patch[:15000] + '\n...TRUNCATED...'
                file_details.append({
                    'filename': f.filename,
                    'status': getattr(f,'status',None),
                    'additions': getattr(f,'additions',0),
                    'deletions': getattr(f,'deletions',0),
                    'changes': getattr(f,'changes',None),
                    'patch': patch,
                })
            is_merge = len(getattr(full,'parents',[]) or []) > 1
            authored_date = None
            committed_date = None
            try:
                authored_date = full.commit.author.date.isoformat() if full.commit.author and full.commit.author.date else None
            except Exception: pass
            try:
                committed_date = full.commit.committer.date.isoformat() if full.commit.committer and full.commit.committer.date else None
            except Exception: pass
            summary = {
                'repo': repo.full_name,
                'sha': full.sha,
                'message': message,
                'additions': adds,
                'deletions': dels,
                'files_changed': len(code_files),
                'type': ctype,
            }
            commits_detail.append(summary)
            verification_obj = getattr(getattr(full,'commit',None),'verification',None)
            verification = None
            if verification_obj:
                verification = {
                    'verified': getattr(verification_obj,'verified',None),
                    'reason': getattr(verification_obj,'reason',None),
                    'signature': getattr(verification_obj,'signature',None),
                    'payload': getattr(verification_obj,'payload',None),
                }
            full_records.append({
                'repo': repo.full_name,
                'sha': full.sha,
                'html_url': getattr(full,'html_url',None),
                'url': getattr(full,'url',None),
                'is_merge': is_merge,
                'authored_date': authored_date,
                'committed_date': committed_date,
                'author': getattr(full.commit.author,'name',None) if getattr(full,'commit',None) else None,
                'author_email': getattr(full.commit.author,'email',None) if getattr(full,'commit',None) else None,
                'committer': getattr(full.commit.committer,'name',None) if getattr(full,'commit',None) else None,
                'committer_email': getattr(full.commit.committer,'email',None) if getattr(full,'commit',None) else None,
                'message_full': full.commit.message if getattr(full,'commit',None) else message,
                'summary': summary,
                'additions': adds,
                'deletions': dels,
                'total_changes': adds + dels,
                'files': file_details,
                'languages_ext': list(exts),
                'classification': ctype,
                'verification': verification,
            })
        print()
        if code_commits == 0:
            print('⚠️  No code commits after filtering non-code changes.')
            continue
        avg_adds = total_adds / code_commits
        avg_dels = total_dels / code_commits
        test_ratio = test_commits / code_commits
        refactor_ratio = refactor_commits / code_commits
        perf_ratio = perf_commits / code_commits
        large_ratio = large_changes / code_commits
        capability = []
        if refactor_ratio >= 0.15: capability.append('Architectural Stewardship (refactoring)')
        if test_ratio >= 0.2: capability.append('Quality Discipline (tests)')
        if len(language_counter) >= 4: capability.append('Polyglot Execution')
        if perf_ratio >= 0.05: capability.append('Performance Awareness')
        if large_ratio >= 0.1: capability.append('Systems Thinking (structural changes)')
        if not capability: capability.append('Focused Delivery (incremental)')
        print('📊 SUMMARY (Code Commits Only)')
        print(f'   Total code commits: {code_commits} (from {total} raw commits)')
        print(f'   Lines added: {total_adds} | Lines deleted: {total_dels}')
        print(f'   Avg additions/commit: {avg_adds:.1f} | Avg deletions/commit: {avg_dels:.1f}')
        print(f'   Commit type distribution: {dict(commit_type_counter)}')
        print(f'   Test commit ratio: {test_ratio:.1%} | Refactor ratio: {refactor_ratio:.1%} | Perf ratio: {perf_ratio:.1%}')
        print(f'   Large structural change ratio: {large_ratio:.1%}')
        print(f"   Languages (extensions): {', '.join(sorted(language_counter.keys()))}")
        print('\n🧠 FOUNDING ENGINEER ATTRIBUTE SIGNALS:')
        for attr in capability:
            print(f'   • {attr}')
        top = sorted(commits_detail, key=lambda c: c['additions'] + c['deletions'], reverse=True)[:5]
        print('\n🔍 Top Significant Commits:')
        for c in top:
            print(f"   - {c['repo']}@{c['sha'][:7]} [{c['type']}] +{c['additions']}/-{c['deletions']} {c['message'][:70]}")
        score = 0
        score += refactor_ratio * 30
        score += test_ratio * 20
        score += perf_ratio * 15
        score += min(len(language_counter),6) * 3
        score += large_ratio * 25
        if score >= 35: rec = '🌟 Strong Founding Engineer Signals'
        elif score >= 22: rec = '✅ Solid Engineering Potential'
        elif score >= 12: rec = '⚠️ Emerging – Needs Broader Impact'
        else: rec = '❌ Limited Recent Differentiators'
        print(f'\n🏆 RECENT ACTIVITY ASSESSMENT: {rec} (score: {score:.1f})')
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        summary_file = f'recent_quality_{username}_{ts}.json'
        commits_file = f'recent_quality_commits_{username}_{ts}.json'
        with open(summary_file,'w') as f:
            json.dump({
                'username': username,
                'window_days': days,
                'generated_at': datetime.utcnow().isoformat(),
                'raw_commit_count': total,
                'code_commit_count': code_commits,
                'totals': {'additions': total_adds, 'deletions': total_dels},
                'averages': {'adds_per_commit': avg_adds, 'dels_per_commit': avg_dels},
                'ratios': {
                    'test_ratio': test_ratio,
                    'refactor_ratio': refactor_ratio,
                    'performance_ratio': perf_ratio,
                    'large_change_ratio': large_ratio,
                },
                'languages_ext': list(language_counter.keys()),
                'commit_type_distribution': dict(commit_type_counter),
                'capability_attributes': capability,
                'top_commits': top,
                'assessment': {'score': score, 'recommendation': rec},
                'artifacts': {'full_commit_details_file': commits_file}
            }, f, indent=2)
        with open(commits_file,'w') as f:
            json.dump({
                'username': username,
                'generated_at': datetime.utcnow().isoformat(),
                'window_start': (datetime.utcnow() - timedelta(days=days)).isoformat(),
                'window_days': days,
                'commit_records_count': len(full_records),
                'commits': full_records,
            }, f, indent=2)
        print(f'💾 Saved detailed metrics -> {summary_file}')
        print(f'💾 Saved full commit records -> {commits_file}\n')
    return 0
