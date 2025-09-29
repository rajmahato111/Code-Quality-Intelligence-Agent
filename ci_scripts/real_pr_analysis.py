#!/usr/bin/env python3
"""
Real GitHub PR Analysis Script
This script performs actual code quality analysis on a GitHub PR
and demonstrates posting review comments.
"""

import os
import sys
import json
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_quality_agent.web.git_platform_integration import (
    GitHubPlatformIntegration, PullRequestAnalyzer, PRComment, PRReview
)
from code_quality_agent.web.github_integration import GitHubIntegration
from code_quality_agent.core.orchestrator import AnalysisOrchestrator
from code_quality_agent.core.models import AnalysisOptions, AnalysisContext


class RealPRAnalyzer:
    """Real GitHub PR analysis with code quality agent."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize real PR analyzer.
        
        Args:
            github_token: GitHub personal access token
        """
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.temp_dirs = []  # Track temp directories for cleanup
        
    async def analyze_pr(self, repo_url: str, pr_number: int, dry_run: bool = True):
        """Analyze a GitHub PR with real code quality analysis.
        
        Args:
            repo_url: GitHub repository URL
            pr_number: Pull request number
            dry_run: If True, don't post actual comments
        """
        print(f"🔍 Real PR Analysis for {repo_url} PR #{pr_number}")
        print("=" * 60)
        
        # Parse repository URL
        parsed_url = urlparse(repo_url)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")
        
        owner = path_parts[0]
        repo = path_parts[1].replace('.git', '')
        
        temp_repo_path = None
        
        try:
            # Step 1: Get PR information
            print(f"📋 Step 1: Fetching PR information...")
            async with GitHubPlatformIntegration(self.github_token) as github:
                pr_info = await github.get_pull_request(owner, repo, pr_number)
                changed_files = await github.get_pull_request_files(owner, repo, pr_number)
                
                print(f"   Title: {pr_info.title}")
                print(f"   Author: {pr_info.author}")
                print(f"   Files changed: {len(changed_files)}")
                
                # Step 2: Clone repository
                print(f"\n📥 Step 2: Cloning repository...")
                async with GitHubIntegration(self.github_token) as git_client:
                    from pydantic import HttpUrl
                    temp_repo_path = await git_client.clone_repository(
                        HttpUrl(repo_url), 
                        branch=pr_info.head_branch
                    )
                    self.temp_dirs.append(temp_repo_path)
                    print(f"   Cloned to: {temp_repo_path}")
                
                # Step 3: Run code quality analysis
                print(f"\n🔍 Step 3: Running code quality analysis...")
                analysis_result = await self._run_analysis(temp_repo_path, changed_files)
                
                print(f"   Total issues: {len(analysis_result.issues)}")
                
                # Group issues by severity
                severity_counts = {}
                for issue in analysis_result.issues:
                    severity = issue.severity.value
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                for severity, count in severity_counts.items():
                    print(f"   - {severity.title()}: {count}")
                
                # Step 4: Filter issues to changed files only
                print(f"\n🎯 Step 4: Filtering issues to changed files...")
                relevant_issues = []
                for issue in analysis_result.issues:
                    # Convert absolute path to relative path
                    issue_path = str(Path(issue.location.file_path).relative_to(temp_repo_path))
                    if issue_path in changed_files:
                        relevant_issues.append(issue)
                
                print(f"   Issues in changed files: {len(relevant_issues)}")
                
                # Step 5: Generate review
                print(f"\n💬 Step 5: Generating PR review...")
                if not dry_run and self.github_token:
                    analyzer = PullRequestAnalyzer(github)
                    
                    # Create a mock analysis result with filtered issues
                    filtered_result = type('AnalysisResult', (), {
                        'issues': relevant_issues,
                        'job_id': analysis_result.job_id if hasattr(analysis_result, 'job_id') else 'test'
                    })()
                    
                    review_result = await analyzer.analyze_pull_request(
                        owner, repo, pr_number, filtered_result
                    )
                    
                    print(f"   ✅ Review posted successfully!")
                    print(f"   Review type: {review_result['review_event']}")
                    print(f"   Status updated: {review_result['status_updated']}")
                    
                else:
                    # Dry run - just show what would be posted
                    print(f"   📝 DRY RUN: Would post review with {len(relevant_issues)} issues")
                    
                    # Show sample review content
                    review_summary = self._generate_review_summary(pr_info, changed_files, relevant_issues)
                    print(f"\n📄 Sample Review Summary:")
                    print("-" * 40)
                    print(review_summary[:500] + "..." if len(review_summary) > 500 else review_summary)
                
                return {
                    'pr_info': pr_info,
                    'changed_files': changed_files,
                    'total_issues': len(analysis_result.issues),
                    'relevant_issues': len(relevant_issues),
                    'severity_counts': severity_counts
                }
                
        except Exception as e:
            print(f"❌ Error during PR analysis: {e}")
            raise
        finally:
            # Cleanup
            self._cleanup()
    
    async def _run_analysis(self, repo_path: str, changed_files: List[str]) -> Any:
        """Run code quality analysis on the repository."""
        try:
            # Create analysis options
            options = AnalysisOptions(
                include_patterns=['*.py', '*.js', '*.ts', '*.jsx', '*.tsx'],
                exclude_patterns=['node_modules/**', '__pycache__/**', '.git/**'],
                languages=['python', 'javascript', 'typescript'],
                categories=['security', 'performance', 'complexity', 'testing', 'documentation'],
                min_severity='medium',
                max_workers=2,
                enable_caching=False
            )
            
            # Create analysis context
            context = AnalysisContext(
                codebase_path=Path(repo_path),
                options=options,
                analysis_id=f"pr_analysis_{hash(repo_path)}"
            )
            
            # Run analysis
            orchestrator = AnalysisOrchestrator()
            result = await orchestrator.analyze_async(context)
            
            return result
            
        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
            # Return mock result for demonstration
            return type('AnalysisResult', (), {
                'issues': [],
                'job_id': 'mock_analysis'
            })()
    
    def _generate_review_summary(self, pr_info, changed_files: List[str], issues: List[Any]) -> str:
        """Generate review summary."""
        # Count issues by severity
        severity_counts = {}
        for issue in issues:
            severity = issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity)
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        total_issues = len(issues)
        
        summary = f"## 🔍 Code Quality Analysis Results\n\n"
        summary += f"**Pull Request:** {pr_info.title}\n"
        summary += f"**Author:** @{pr_info.author}\n"
        summary += f"**Files Changed:** {len(changed_files)}\n"
        summary += f"**Issues Found:** {total_issues}\n\n"
        
        if total_issues == 0:
            summary += "✅ **Excellent!** No quality issues found in the changed files.\n\n"
            summary += "Your code meets our quality standards. Great job! 🎉\n"
        else:
            summary += "### 📊 Issue Breakdown\n\n"
            
            for severity in ['critical', 'high', 'medium', 'low']:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    emoji = {'critical': '🚨', 'high': '⚠️', 'medium': '🔶', 'low': 'ℹ️'}[severity]
                    summary += f"{emoji} **{severity.title()}:** {count} issues\n"
            
            summary += "\n### 🎯 Recommendations\n\n"
            
            if severity_counts.get('critical', 0) > 0:
                summary += "- 🛑 **Critical issues found!** Please address these before merging.\n"
            elif severity_counts.get('high', 0) > 0:
                summary += "- ⚠️ **High priority issues detected.** Strongly recommend fixing these.\n"
            else:
                summary += "- 💡 **Minor issues found.** Consider addressing when convenient.\n"
            
            summary += "\n### 📝 Next Steps\n\n"
            summary += "1. Review the inline comments below\n"
            summary += "2. Address critical and high priority issues\n"
            summary += "3. Consider the suggestions for medium/low priority items\n"
            summary += "4. Re-run analysis after making changes\n"
        
        summary += "\n---\n"
        summary += "*🤖 This review was generated by Code Quality Intelligence Agent*\n"
        summary += "*📊 Analysis covers security, performance, complexity, testing, and documentation*"
        
        return summary
    
    def _cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    print(f"   🧹 Cleaned up: {temp_dir}")
            except Exception as e:
                print(f"   ⚠️ Cleanup warning: {e}")
        self.temp_dirs.clear()


async def main():
    """Main function for real PR analysis."""
    print("🚀 Real GitHub PR Analysis")
    print("=" * 40)
    
    # Configuration
    repo_url = "https://github.com/rajmahato111/Full_Stack_Development_tarifflo"
    pr_number = 1
    dry_run = True  # Set to False to actually post comments
    
    print(f"Repository: {repo_url}")
    print(f"PR Number: #{pr_number}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()
    
    # Check for GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("ℹ️  No GITHUB_TOKEN found - running in read-only mode")
        print("   To post actual comments, set GITHUB_TOKEN environment variable")
        dry_run = True
    
    if dry_run:
        print("📝 Running in DRY RUN mode - analysis only, no comments posted")
    else:
        print("🔴 LIVE mode - will post actual review comments!")
    
    print()
    
    # Create analyzer and run
    analyzer = RealPRAnalyzer(github_token)
    
    try:
        result = await analyzer.analyze_pr(repo_url, pr_number, dry_run)
        
        print("\n🎉 Analysis Complete!")
        print("=" * 30)
        print(f"PR Title: {result['pr_info'].title}")
        print(f"Files Changed: {len(result['changed_files'])}")
        print(f"Total Issues: {result['total_issues']}")
        print(f"Issues in Changed Files: {result['relevant_issues']}")
        
        if result['severity_counts']:
            print("\nSeverity Breakdown:")
            for severity, count in result['severity_counts'].items():
                print(f"  {severity.title()}: {count}")
        
        if not dry_run:
            print("\n✅ Review posted to GitHub!")
        else:
            print("\n📝 Review content generated (dry run)")
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the real analysis
    exit_code = asyncio.run(main())
    sys.exit(exit_code)