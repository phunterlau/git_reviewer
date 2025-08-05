#!/usr/bin/env python3
"""
GitHub Commit Reviewer

This tool fetches commits, issues, and pull requests from a GitHub repository 
for a specific user and uses GPT-4o-mini to provide insights about the programmer's capabilities.

Usage:
    python main.py --user username --repo owner/repo --type commits
    python main.py -u user@example.com -r https://github.com/owner/repo -t all

Arguments:
    --user, -u: GitHub username or email
    --repo, -r: GitHub repository URL or owner/repo format  
    --type, -t: Analysis type (commits, issues, pull_requests, all)
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from github_utils import get_commits, get_issues, get_pull_requests
from gpt_utils import review_commits_with_gpt


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze GitHub contributions using GPT-4o-mini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --user phunterlau --repo phunterlau/yolo_term --type commits
  %(prog)s -u user@example.com -r https://github.com/microsoft/vscode -t all --limit 50
  %(prog)s --user trivialfis --repo dmlc/xgboost --type issues --limit 200
        """
    )
    
    parser.add_argument(
        '--user', '-u',
        required=True,
        help='GitHub username or email address'
    )
    
    parser.add_argument(
        '--repo', '-r', 
        required=True,
        help='GitHub repository URL or owner/repo format'
    )
    
    parser.add_argument(
        '--type', '-t',
        choices=['commits', 'issues', 'pull_requests', 'all'],
        default='commits',
        help='Type of analysis to perform (default: commits)'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=100,
        help='Maximum number of records to fetch (default: 100)'
    )
    
    return parser.parse_args()


def main():
    """Main function to run the GitHub commit reviewer."""
    args = parse_arguments()
    
    print("=" * 60)
    print("GitHub Commit Reviewer")
    print("=" * 60)
    print(f"User: {args.user}")
    print(f"Repository: {args.repo}")
    print(f"Analysis type: {args.type}")
    print(f"Record limit: {args.limit}")
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
    
    files_generated = []
    
    # Fetch data based on analysis type
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
