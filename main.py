#!/usr/bin/env python3
"""Thin CLI orchestrator for GitHub contribution analysis.

The heavy lifting has been modularized into the `cli` package:
  - `cli.arg_parser.parse_arguments` : argument parsing
  - `cli.utils.load_and_validate_env` : .env loading & token validation
  - `cli.founding_engineer.run` : founding engineer (cross-repo) analysis
  - `cli.recent_quality.run` : recent multi-repo commit quality window
  - `cli.repo_analysis.run_repository_mode` : repo-scoped commits/issues/PRs & optimized/benchmark flows

This file now only:
  1. Parses arguments
  2. Loads & validates environment
  3. Dispatches to the correct module
  4. Handles high-level user-facing banners / basic validation

Backwards compatibility: existing flags & behaviors preserved.
"""

from __future__ import annotations

import sys
from typing import Optional

from cli.arg_parser import parse_arguments
from cli.utils import load_and_validate_env
from cli.founding_engineer import run as run_founding_engineer
from cli.recent_quality import run as run_recent_quality
from cli.repo_analysis import run_repository_mode


def _print_banner(args) -> None:
    print("=" * 60)
    if args.type == 'founding_engineer':
        print("🚀 Founding Engineer Analysis")
    elif args.type == 'recent_quality':
        print("🧪 Recent Code Quality Window")
    else:
        print("GitHub Commit Reviewer")
    print("=" * 60)
    print(f"User: {args.user}")
    if args.repo:
        print(f"Repository: {args.repo}")
    print(f"Analysis type: {args.type}")
    if hasattr(args, 'limit'):
        print(f"Record limit: {args.limit}")
    if getattr(args, 'heatmap', False):
        print(f"Heatmap: {args.heatmap_days} days ({args.heatmap_format} format)")
    if getattr(args, 'optimized', False):
        print("🚀 Mode: Optimized analysis (unified + cached + token-efficient)")
    if getattr(args, 'benchmark', False):
        print("🏁 Mode: Performance benchmark")
    if args.type == 'recent_quality':
        print(f"Window: last {args.recent_days} days (max {args.max_commits} commits)")
    print()


def main() -> int:
    args = parse_arguments()

    # Basic validation for repo-scoped modes
    if args.type in ['commits', 'issues', 'pull_requests', 'all'] and not args.repo and not (args.optimized or args.benchmark):
        print("ERROR: --repo is required for repository-specific analysis (commits/issues/pull_requests/all)")
        print("Use --type founding_engineer or --type recent_quality for cross-repository user modes")
        return 1

    _print_banner(args)

    # Load environment & ensure required tokens present
    env_ok = load_and_validate_env()
    if not env_ok:
        return 1

    # Dispatch
    if args.type == 'founding_engineer':
        return run_founding_engineer(args.user, args.limit)
    if args.type == 'recent_quality':
        return run_recent_quality(args.user, days=args.recent_days, max_commits=args.max_commits)

    # Repository mode (includes standard, optimized, benchmark)
    return run_repository_mode(args)


if __name__ == '__main__':
    sys.exit(main())
