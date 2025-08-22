#!/usr/bin/env python3
"""
Founding Engineer Review CLI

Command-line interface for the Founding Engineer Review System.
Provides easy access to analyze GitHub profiles for founding engineer potential.

Usage:
    uv run python founding_engineer_cli.py --user phunterlau
    uv run python founding_engineer_cli.py --user user@example.com --months 6 --format executive
    uv run python founding_engineer_cli.py --user candidate123 --months 18 --include-patches
"""

import argparse
import sys
from pathlib import Path

from founding_engineer_review import FoundingEngineerReviewer, ReportGenerator


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Founding Engineer GitHub Review System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --user phunterlau
  %(prog)s --user user@example.com --months 6 --format executive
  %(prog)s --user candidate123 --months 18 --include-patches
  %(prog)s --user john_doe --format json --output-dir ./reports
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
        choices=['executive', 'detailed', 'json'],
        default='detailed',
        help='Output format (default: detailed)'
    )
    
    parser.add_argument(
        '--include-patches',
        action='store_true',
        help='Include code patches for deeper analysis (increases processing time)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        default='.',
        help='Output directory for reports (default: current directory)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    print("🎯 Founding Engineer Review System")
    print("=" * 50)
    print(f"Candidate: {args.user}")
    print(f"Analysis Period: {args.months} months")
    print(f"Output Format: {args.format}")
    print(f"Include Patches: {args.include_patches}")
    print(f"Output Directory: {args.output_dir}")
    print()
    
    try:
        # Initialize reviewer
        reviewer = FoundingEngineerReviewer.create_from_env()
        
        # Generate comprehensive review
        assessment = reviewer.generate_comprehensive_review(
            args.user, 
            args.months, 
            args.include_patches
        )
        
        # Generate and save report
        report_generator = ReportGenerator()
        output_file = report_generator.save_report(
            assessment, 
            args.format, 
            args.output_dir
        )
        
        # Print summary to console
        print(f"\n🎯 FOUNDING ENGINEER ASSESSMENT COMPLETE")
        print("=" * 60)
        print(f"Candidate: {assessment.candidate_username}")
        print(f"Overall Score: {assessment.overall_score:.1f}/100")
        print(f"Recommendation: {assessment.recommendation.value}")
        print(f"Confidence: {assessment.confidence_level:.0%}")
        
        if assessment.top_strengths:
            print(f"\nTop Strengths:")
            for i, strength in enumerate(assessment.top_strengths[:3], 1):
                print(f"  {i}. {strength.description}")
        
        if assessment.critical_risks:
            print(f"\nKey Risks:")
            for i, risk in enumerate(assessment.critical_risks[:3], 1):
                print(f"  {i}. {risk.description}")
        
        print(f"\n📄 Full report: {output_file}")
        
        # Set exit code based on recommendation
        if assessment.recommendation.value in ["Strongly Recommended", "Recommended"]:
            return 0
        elif assessment.recommendation.value == "Conditional":
            return 1
        else:
            return 2
        
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        return 130
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
