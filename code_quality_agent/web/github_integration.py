"""GitHub repository integration for the web API."""

import os
import tempfile
import shutil
import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import subprocess
import asyncio
from urllib.parse import urlparse

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import aiofiles
except ImportError:
    aiofiles = None

from pydantic import HttpUrl

logger = logging.getLogger(__name__)


class GitHubIntegration:
    """Handle GitHub repository operations."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize GitHub integration.
        
        Args:
            github_token: Optional GitHub personal access token for private repos
        """
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not aiohttp:
            raise RuntimeError("aiohttp is required for GitHub integration. Install with: pip install aiohttp")
        
        # Create SSL context using certifi's CA bundle
        import ssl
        import certifi
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Create aiohttp connector with SSL context
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def parse_repository_url(self, url: HttpUrl) -> Tuple[str, str]:
        """Parse GitHub repository URL to extract owner and repo name.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            Tuple of (owner, repo_name)
            
        Raises:
            ValueError: If URL is not a valid GitHub repository URL
        """
        parsed = urlparse(str(url))
        
        if parsed.netloc not in ['github.com', 'www.github.com']:
            raise ValueError(f"Unsupported repository host: {parsed.netloc}")
        
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError(f"Invalid repository URL format: {url}")
        
        owner = path_parts[0]
        repo_name = path_parts[1]
        
        # Remove .git suffix if present
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        return owner, repo_name
    
    async def get_repository_info(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """Get repository information from GitHub API.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            
        Returns:
            Repository information dictionary
        """
        if not self.session:
            raise RuntimeError("GitHub integration not initialized. Use async context manager.")
        
        if not aiohttp:
            raise RuntimeError("aiohttp is required for GitHub integration")
        
        url = f"https://api.github.com/repos/{owner}/{repo_name}"
        headers = {}
        
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 404:
                    raise ValueError(f"Repository {owner}/{repo_name} not found")
                elif response.status == 403:
                    raise ValueError("GitHub API rate limit exceeded or access denied")
                elif response.status != 200:
                    raise ValueError(f"GitHub API error: {response.status}")
                
                return await response.json()
        
        except aiohttp.ClientError as e:
            raise ValueError(f"Failed to fetch repository info: {e}")
    
    async def get_default_branch(self, owner: str, repo_name: str) -> str:
        """Get the default branch of a repository.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            
        Returns:
            Default branch name
        """
        repo_info = await self.get_repository_info(owner, repo_name)
        return repo_info.get('default_branch', 'main')
    
    async def clone_repository(self, url: HttpUrl, branch: Optional[str] = None, 
                             target_dir: Optional[str] = None) -> str:
        """Clone a GitHub repository.
        
        Args:
            url: Repository URL
            branch: Branch to clone (defaults to repository default branch)
            target_dir: Target directory (creates temp dir if None)
            
        Returns:
            Path to cloned repository
        """
        owner, repo_name = self.parse_repository_url(url)
        
        # Get default branch if not specified
        if not branch:
            branch = await self.get_default_branch(owner, repo_name)
        
        # Create target directory
        if not target_dir:
            target_dir = tempfile.mkdtemp(prefix=f"{repo_name}_")
        else:
            os.makedirs(target_dir, exist_ok=True)
        
        # Construct clone URL
        clone_url = str(url)
        if self.github_token:
            # Use token for authentication
            parsed = urlparse(clone_url)
            clone_url = f"https://{self.github_token}@{parsed.netloc}{parsed.path}"
        
        # Clone repository
        try:
            cmd = [
                'git', 'clone',
                '--branch', branch,
                '--depth', '1',  # Shallow clone for faster download
                '--single-branch',
                clone_url,
                target_dir
            ]
            
            logger.info(f"Cloning repository {owner}/{repo_name} (branch: {branch})")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown git error"
                raise RuntimeError(f"Git clone failed: {error_msg}")
            
            logger.info(f"Successfully cloned repository to {target_dir}")
            return target_dir
            
        except FileNotFoundError:
            raise RuntimeError("Git is not installed or not available in PATH")
        except Exception as e:
            # Clean up on failure
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to clone repository: {e}")
    
    async def get_repository_files(self, repo_path: str, 
                                 include_patterns: Optional[list] = None,
                                 exclude_patterns: Optional[list] = None) -> list:
        """Get list of files in the repository.
        
        Args:
            repo_path: Path to cloned repository
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            
        Returns:
            List of file paths relative to repository root
        """
        import fnmatch
        
        files = []
        repo_path = Path(repo_path)
        
        # Default patterns
        if not include_patterns:
            include_patterns = ['*.py', '*.js', '*.ts', '*.jsx', '*.tsx']
        
        if not exclude_patterns:
            exclude_patterns = [
                '.git/*', 'node_modules/*', '__pycache__/*', '*.pyc',
                '.pytest_cache/*', 'venv/*', 'env/*', '.env/*',
                'dist/*', 'build/*', '*.min.js', '*.bundle.js'
            ]
        
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(repo_path)
                relative_str = str(relative_path)
                
                # Check include patterns
                if include_patterns:
                    if not any(fnmatch.fnmatch(relative_str, pattern) for pattern in include_patterns):
                        continue
                
                # Check exclude patterns
                if exclude_patterns:
                    if any(fnmatch.fnmatch(relative_str, pattern) for pattern in exclude_patterns):
                        continue
                
                files.append(relative_str)
        
        return sorted(files)
    
    async def get_commit_info(self, repo_path: str) -> Dict[str, Any]:
        """Get commit information for the cloned repository.
        
        Args:
            repo_path: Path to cloned repository
            
        Returns:
            Commit information dictionary
        """
        try:
            # Get commit hash
            process = await asyncio.create_subprocess_exec(
                'git', 'rev-parse', 'HEAD',
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            commit_hash = stdout.decode().strip() if process.returncode == 0 else None
            
            # Get commit message
            process = await asyncio.create_subprocess_exec(
                'git', 'log', '-1', '--pretty=format:%s',
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            commit_message = stdout.decode().strip() if process.returncode == 0 else None
            
            # Get commit author and date
            process = await asyncio.create_subprocess_exec(
                'git', 'log', '-1', '--pretty=format:%an|%ae|%ad',
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                author_info = stdout.decode().strip().split('|')
                author_name = author_info[0] if len(author_info) > 0 else None
                author_email = author_info[1] if len(author_info) > 1 else None
                commit_date = author_info[2] if len(author_info) > 2 else None
            else:
                author_name = author_email = commit_date = None
            
            return {
                'commit_hash': commit_hash,
                'commit_message': commit_message,
                'author_name': author_name,
                'author_email': author_email,
                'commit_date': commit_date
            }
            
        except Exception as e:
            logger.warning(f"Failed to get commit info: {e}")
            return {}
    
    def cleanup_repository(self, repo_path: str):
        """Clean up cloned repository.
        
        Args:
            repo_path: Path to repository to clean up
        """
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                logger.info(f"Cleaned up repository at {repo_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup repository {repo_path}: {e}")


class GitLabIntegration:
    """Handle GitLab repository operations (basic implementation)."""
    
    def __init__(self, gitlab_token: Optional[str] = None):
        """Initialize GitLab integration.
        
        Args:
            gitlab_token: Optional GitLab personal access token
        """
        self.gitlab_token = gitlab_token or os.getenv('GITLAB_TOKEN')
    
    def parse_repository_url(self, url: HttpUrl) -> Tuple[str, str]:
        """Parse GitLab repository URL."""
        parsed = urlparse(str(url))
        
        if parsed.netloc not in ['gitlab.com', 'www.gitlab.com']:
            raise ValueError(f"Unsupported repository host: {parsed.netloc}")
        
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError(f"Invalid repository URL format: {url}")
        
        # GitLab can have nested groups, so we need to handle this differently
        # For now, assume owner/repo format
        owner = path_parts[0]
        repo_name = path_parts[1]
        
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        return owner, repo_name


def get_repository_integration(url: HttpUrl) -> GitHubIntegration:
    """Get appropriate repository integration based on URL.
    
    Args:
        url: Repository URL
        
    Returns:
        Repository integration instance
        
    Raises:
        ValueError: If repository host is not supported
    """
    parsed = urlparse(str(url))
    
    if parsed.netloc in ['github.com', 'www.github.com']:
        return GitHubIntegration()
    elif parsed.netloc in ['gitlab.com', 'www.gitlab.com']:
        return GitLabIntegration()
    else:
        raise ValueError(f"Unsupported repository host: {parsed.netloc}")