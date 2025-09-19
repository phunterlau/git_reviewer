import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze GitHub contributions (founding engineer, repo, recent quality)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:\n  founding engineer: main.py --type founding_engineer --user octocat\n  repo commits:      main.py --user octocat --repo owner/repo --type commits --limit 50\n  recent quality:    main.py --type recent_quality --user octocat --recent-days 30\n"""
    )
    parser.add_argument('--user','-u',required=True,help='GitHub username (comma separated for recent_quality)')
    parser.add_argument('--repo','-r',required=False,help='Repository URL or owner/repo (required for repo analysis)')
    parser.add_argument('--type','-t',choices=['commits','issues','pull_requests','all','founding_engineer','recent_quality','benchmark'],default='commits',help='Analysis type')
    parser.add_argument('--limit','-l',type=int,default=100,help='Record limit for repo/founding engineer modes')
    parser.add_argument('--heatmap',action='store_true',help='Include contribution heatmap (repo modes)')
    parser.add_argument('--heatmap-days',type=int,default=365,help='Days for heatmap (default 365)')
    parser.add_argument('--heatmap-format',choices=['json','md'],default='json',help='Heatmap output format')
    parser.add_argument('--optimized',action='store_true',help='Use optimized unified analysis mode')
    parser.add_argument('--benchmark',action='store_true',help='Run performance benchmark (repo + --benchmark)')
    parser.add_argument('--recent-days',type=int,default=30,help='Lookback window for recent_quality')
    parser.add_argument('--max-commits',type=int,default=250,help='Max commits per user recent_quality')
    return parser

def parse_arguments():
    return build_parser().parse_args()
