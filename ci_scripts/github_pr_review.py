#!/usr/bin/env python3
"""
GitHub PR Review Simulation Script
This script demonstrates how the code quality agent can analyze a GitHub PR
and post comments with issues directly on the pull request.
"""

import os
import sys
import json
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from urllib.parse import urlparse

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_quality_agent.web.git_platform_integration import (
    GitHubPlatformIntegration, PullRequestAnalyzer, PRComment, PRReview
)
from code_quality_agent.core.orchestrator import AnalysisOrchestrator
from code_quality_agent.core.models import AnalysisOptions, AnalysisContext


class PRReviewSimulator:
    """Simulate GitHub PR review functionality."""
    
    def __init__(self, github_token: str = None):
        """Initialize PR review simulator.
        
        Args:
            github_token: GitHub personal access token (optional for public repos)
        """
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.github_integration = GitHubPlatformIntegration(self.github_token)
        
    async def simulate_pr_review(self, repo_url: str, pr_number: int, dry_run: bool = True):
        """Simulate analyzing a GitHub PR and posting review comments.
        
        Args:
            repo_url: GitHub repository URL
            pr_number: Pull request number
            dry_run: If True, only simulate without actually posting comments
        """
        print(f"🔍 Simulating PR Review for {repo_url} PR #{pr_number}")
        print("=" * 60)
        
        # Parse repository URL
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        owner = path_parts[0]
        repo = path_parts[1].replace('.git', '')
        
        async with self.github_integration as github:
            try:
                # Step 1: Get PR information
                print(f"📋 Step 1: Fetching PR information...")
                pr_info = await github.get_pull_request(owner, repo, pr_number)
                
                print(f"   Title: {pr_info.title}")
                print(f"   Author: {pr_info.author}")
                print(f"   Base: {pr_info.base_branch} ← Head: {pr_info.head_branch}")
                print(f"   State: {pr_info.state}")
                print(f"   URL: {pr_info.url}")
                
                # Step 2: Get changed files
                print(f"\n📁 Step 2: Fetching changed files...")
                changed_files = await github.get_pull_request_files(owner, repo, pr_number)
                
                print(f"   Files changed: {len(changed_files)}")
                for file_path in changed_files[:10]:  # Show first 10 files
                    print(f"   - {file_path}")
                if len(changed_files) > 10:
                    print(f"   ... and {len(changed_files) - 10} more files")
                
                # Step 3: Simulate code quality analysis
                print(f"\n🔍 Step 3: Simulating code quality analysis...")
                analysis_results = self._simulate_analysis_results(changed_files)
                
                print(f"   Issues found: {len(analysis_results['issues'])}")
                for severity, count in analysis_results['summary'].items():
                    if count > 0:
                        print(f"   - {severity.title()}: {count}")
                
                # Step 4: Generate review comments
                print(f"\n💬 Step 4: Generating review comments...")
                review_summary, inline_comments = self._generate_review_comments(
                    pr_info, changed_files, analysis_results
                )
                
                print(f"   Review summary length: {len(review_summary)} characters")
                print(f"   Inline comments: {len(inline_comments)}")
                
                # Step 5: Display review content (simulation)
                print(f"\n📝 Step 5: Review Content Preview")
                print("-" * 40)
                print("REVIEW SUMMARY:")
                print(review_summary)
                print("\nINLINE COMMENTS:")
                for i, comment in enumerate(inline_comments[:3], 1):  # Show first 3
                    print(f"\n{i}. File: {comment.path}, Line: {comment.line}")
                    print(f"   Comment: {comment.body[:100]}...")
                
                if len(inline_comments) > 3:
                    print(f"\n   ... and {len(inline_comments) - 3} more comments")
                
                # Step 6: Post review (or simulate)
                print(f"\n🚀 Step 6: {'Simulating' if dry_run else 'Posting'} PR review...")
                
                if dry_run:
                    print("   ✅ DRY RUN: Review content generated successfully")
                    print("   📝 To actually post the review, set dry_run=False")
                    print("   🔑 Ensure GITHUB_TOKEN environment variable is set")
                else:
                    # Determine review event based on issues
                    critical_issues = analysis_results['summary']['critical']
                    high_issues = analysis_results['summary']['high']
                    
                    if critical_issues > 0:
                        review_event = "REQUEST_CHANGES"
                    elif high_issues > 0:
                        review_event = "COMMENT"
                    else:
                        review_event = "APPROVE"
                    
                    # Create and submit review
                    review = PRReview(
                        event=review_event,
                        body=review_summary,
                        comments=inline_comments
                    )
                    
                    success = await github.create_pull_request_review(owner, repo, pr_number, review)
                    
                    if success:
                        print(f"   ✅ Review posted successfully!")
                        print(f"   📝 Review type: {review_event}")
                    else:
                        print(f"   ❌ Failed to post review")
                
                # Step 7: Update commit status
                print(f"\n📊 Step 7: {'Simulating' if dry_run else 'Updating'} commit status...")
                
                critical_issues = analysis_results['summary']['critical']
                high_issues = analysis_results['summary']['high']
                total_issues = sum(analysis_results['summary'].values())
                
                if critical_issues > 0:
                    status_state = "failure"
                    status_description = f"❌ {critical_issues} critical issues found"
                elif high_issues > 0:
                    status_state = "error"
                    status_description = f"⚠️ {high_issues} high severity issues found"
                elif total_issues > 0:
                    status_state = "success"
                    status_description = f"✅ {total_issues} minor issues found"
                else:
                    status_state = "success"
                    status_description = "✅ No quality issues found"
                
                if dry_run:
                    print(f"   Status: {status_state}")
                    print(f"   Description: {status_description}")
                else:
                    success = await github.update_commit_status(
                        owner, repo, pr_info.head_sha, status_state,
                        status_description, "code-quality/analysis"
                    )
                    
                    if success:
                        print(f"   ✅ Commit status updated: {status_state}")
                    else:
                        print(f"   ❌ Failed to update commit status")
                
                print(f"\n🎉 PR Review Simulation Complete!")
                
                return {
                    "pr_info": pr_info,
                    "changed_files": changed_files,
                    "analysis_results": analysis_results,
                    "review_summary": review_summary,
                    "inline_comments": len(inline_comments),
                    "status": status_state
                }
                
            except Exception as e:
                print(f"❌ Error during PR review simulation: {e}")
                raise
    
    def _simulate_analysis_results(self, changed_files: List[str]) -> Dict[str, Any]:
        """Simulate code quality analysis results for changed files."""
        # Simulate different types of issues based on file types and names
        issues = []
        
        for file_path in changed_files:
            file_ext = Path(file_path).suffix.lower()
            
            # Simulate issues based on file characteristics
            if file_ext in ['.py', '.js', '.ts', '.jsx', '.tsx']:
                # Simulate common issues for code files
                if 'test' not in file_path.lower():
                    issues.append({
                        'severity': 'high',
                        'category': 'testing',
                        'title': 'No Test Files Found',
                        'description': f'No test files found for {file_path}',
                        'file_path': file_path,
                        'line': 1
                    })
                
                if 'legacy' in file_path.lower() or 'old' in file_path.lower():
                    issues.append({
                        'severity': 'critical',
                        'category': 'security',
                        'title': 'Potential Security Vulnerability',
                        'description': 'Legacy code may contain security vulnerabilities',
                        'file_path': file_path,
                        'line': 10
                    })
                
                if len(file_path) > 50:  # Long file paths might indicate complexity
                    issues.append({
                        'severity': 'medium',
                        'category': 'complexity',
                        'title': 'High Complexity Detected',
                        'description': 'File structure suggests high complexity',
                        'file_path': file_path,
                        'line': 25
                    })
                
                # Random additional issues for demonstration
                import random
                if random.random() < 0.3:  # 30% chance
                    issues.append({
                        'severity': 'low',
                        'category': 'documentation',
                        'title': 'Missing Documentation',
                        'description': 'Consider adding more documentation',
                        'file_path': file_path,
                        'line': 5
                    })
        
        # Count issues by severity
        summary = {
            'critical': len([i for i in issues if i['severity'] == 'critical']),
            'high': len([i for i in issues if i['severity'] == 'high']),
            'medium': len([i for i in issues if i['severity'] == 'medium']),
            'low': len([i for i in issues if i['severity'] == 'low'])
        }
        
        return {
            'issues': issues,
            'summary': summary
        }
    
    def _generate_review_comments(self, pr_info, changed_files: List[str], 
                                analysis_results: Dict[str, Any]) -> tuple:
        """Generate review summary and inline comments."""
        issues = analysis_results['issues']
        summary = analysis_results['summary']
        
        # Generate review summary
        total_issues = sum(summary.values())
        
        review_summary = f"## 🔍 Code Quality Analysis Results\n\n"
        review_summary += f"**Pull Request:** {pr_info.title}\n"
        review_summary += f"**Files Changed:** {len(changed_files)}\n"
        review_summary += f"**Total Issues Found:** {total_issues}\n\n"
        
        if total_issues == 0:
            review_summary += "✅ **Excellent!** No quality issues found in the changed files.\n"
        else:
            review_summary += "### Issue Breakdown\n\n"
            
            if summary['critical'] > 0:
                review_summary += f"🚨 **Critical:** {summary['critical']} issues - Must be fixed before merging\n"
            if summary['high'] > 0:
                review_summary += f"⚠️ **High:** {summary['high']} issues - Strongly recommended to fix\n"
            if summary['medium'] > 0:
                review_summary += f"🔶 **Medium:** {summary['medium']} issues - Consider fixing\n"
            if summary['low'] > 0:
                review_summary += f"ℹ️ **Low:** {summary['low']} issues - Optional improvements\n"
            
            review_summary += "\n### Recommendations\n\n"
            
            if summary['critical'] > 0:
                review_summary += "- 🛑 **Action Required:** Critical issues must be resolved before merging\n"
            elif summary['high'] > 0:
                review_summary += "- ⚠️ **Recommended:** Please address high-priority issues\n"
            else:
                review_summary += "- 💡 **Suggestions:** Consider the recommendations when convenient\n"
        
        review_summary += "\n---\n*🤖 Generated by Code Quality Intelligence Agent*"
        
        # Generate inline comments for critical and high severity issues
        inline_comments = []
        for issue in issues:
            if issue['severity'] in ['critical', 'high']:
                severity_emoji = "🚨" if issue['severity'] == 'critical' else "⚠️"
                
                comment_body = f"{severity_emoji} **{issue['severity'].upper()}:** {issue['title']}\n\n"
                comment_body += f"{issue['description']}\n\n"
                comment_body += f"**Category:** {issue['category'].title()}\n"
                comment_body += f"**Severity:** {issue['severity'].title()}\n\n"
                comment_body += "Please review and address this issue before merging.\n\n"
                comment_body += "*🤖 Detected by Code Quality Intelligence Agent*"
                
                inline_comments.append(PRComment(
                    body=comment_body,
                    path=issue['file_path'],
                    line=issue['line'],
                    side="RIGHT"
                ))
        
        return review_summary, inline_comments


async def main():
    """Main function to demonstrate PR review functionality."""
    print("🚀 GitHub PR Review Simulation")
    print("=" * 50)
    
    # Configuration
    repo_url = "https://github.com/rajmahato111/Full_Stack_Development_tarifflo"
    pr_number = 1
    dry_run = True  # Set to False to actually post comments (requires GITHUB_TOKEN)
    
    print(f"Repository: {repo_url}")
    print(f"PR Number: #{pr_number}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()
    
    # Check for GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token and not dry_run:
        print("❌ GITHUB_TOKEN environment variable not set!")
        print("   Set it with: export GITHUB_TOKEN=your_token_here")
        print("   Or run in dry-run mode for simulation")
        return
    
    if dry_run:
        print("ℹ️  Running in DRY RUN mode - no actual comments will be posted")
        print()
    
    # Create simulator and run
    simulator = PRReviewSimulator(github_token)
    
    try:
        result = await simulator.simulate_pr_review(repo_url, pr_number, dry_run)
        
        print("\n📊 Summary:")
        print(f"   PR: {result['pr_info'].title}")
        print(f"   Files changed: {len(result['changed_files'])}")
        print(f"   Issues found: {sum(result['analysis_results']['summary'].values())}")
        print(f"   Inline comments: {result['inline_comments']}")
        print(f"   Status: {result['status']}")
        
    except Exception as e:
        print(f"\n❌ Simulation failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the simulation
    exit_code = asyncio.run(main())
    sys.exit(exit_code)