# Git Platform Integration Guide

## Overview

The Code Quality Intelligence Agent provides comprehensive integration with Git platforms (GitHub and GitLab) to enable automated code quality analysis on pull requests and commits. This integration supports:

- **Webhook-triggered analysis** on PR events and pushes
- **Automated PR reviews** with inline comments
- **Commit status updates** to show analysis results
- **CI/CD integration** for continuous quality monitoring

## Features

### Supported Platforms

- **GitHub**: Full API integration with webhooks, PR reviews, and commit statuses
- **GitLab**: Full API integration with webhooks, MR notes, and commit statuses

### Supported Events

#### GitHub Events
- `pull_request` (opened, synchronize, reopened)
- `push` (to main/master/develop branches)

#### GitLab Events
- `merge_request` (open, update, reopen)
- `push` (to main/master/develop branches)

### Analysis Features

- **Automatic PR Analysis**: Triggered when PRs are opened or updated
- **Inline Comments**: Issues are commented directly on the relevant lines
- **Review Summaries**: Comprehensive overview of all quality issues found
- **Commit Status Updates**: Pass/fail status based on critical issues
- **Severity-based Actions**: Different actions based on issue severity levels

## Setup Instructions

### 1. Environment Variables

Set the following environment variables for proper integration:

```bash
# GitHub Integration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# GitLab Integration
GITLAB_TOKEN=your_gitlab_personal_access_token
GITLAB_WEBHOOK_SECRET=your_webhook_token
```

### 2. GitHub Setup

#### Step 1: Create Personal Access Token
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with these scopes:
   - `repo` (for private repositories)
   - `public_repo` (for public repositories)
   - `pull_requests:write` (to create reviews)
   - `statuses:write` (to update commit statuses)

#### Step 2: Configure Webhook
1. Navigate to your repository settings
2. Go to Webhooks → Add webhook
3. Configure:
   - **Payload URL**: `https://your-domain.com/webhooks/github`
   - **Content type**: `application/json`
   - **Secret**: Your webhook secret
   - **Events**: Select "Pull requests" and "Pushes"

### 3. GitLab Setup

#### Step 1: Create Personal Access Token
1. Go to GitLab Settings → Access Tokens
2. Create token with these scopes:
   - `api` (full API access)
   - `read_repository` (read repository data)
   - `write_repository` (write commit statuses)

#### Step 2: Configure Webhook
1. Navigate to your project settings
2. Go to Webhooks → Add webhook
3. Configure:
   - **URL**: `https://your-domain.com/webhooks/gitlab`
   - **Secret token**: Your webhook token
   - **Trigger events**: Select "Push events" and "Merge request events"
   - **SSL verification**: Enable

## API Endpoints

### Webhook Endpoints

#### GitHub Webhook
```
POST /webhooks/github
Content-Type: application/json
X-GitHub-Event: pull_request|push
X-Hub-Signature-256: sha256=<signature>
```

#### GitLab Webhook
```
POST /webhooks/gitlab
Content-Type: application/json
X-Gitlab-Event: Push Hook|Merge Request Hook
X-Gitlab-Token: <token>
```

### Manual Analysis Endpoints

#### Analyze Pull Request
```
POST /pr/analyze/{owner}/{repo}/{pr_number}?platform=github|gitlab
Authorization: Bearer <api_key>
```

#### Get Pull Request Info
```
GET /pr/{owner}/{repo}/{pr_number}?platform=github|gitlab
Authorization: Bearer <api_key>
```

## Integration Workflow

### 1. Webhook Reception
1. Webhook payload is received and verified
2. Event type and repository information are extracted
3. Analysis trigger conditions are evaluated

### 2. Repository Analysis
1. Repository is cloned to temporary directory
2. Code quality analysis is performed
3. Issues are categorized and prioritized

### 3. PR Review Creation
1. Issues are filtered to only those in changed files
2. Inline comments are created for critical/high severity issues
3. Review summary is generated with overall assessment
4. Review is submitted with appropriate approval status

### 4. Commit Status Update
1. Commit status is updated based on analysis results
2. Status includes link to detailed report
3. Status reflects overall quality assessment

## Code Examples

### Basic Webhook Handler Usage

```python
from code_quality_agent.web.git_platform_integration import WebhookHandler

# Initialize handler
handler = WebhookHandler(
    github_secret="your_github_secret",
    gitlab_secret="your_gitlab_secret"
)

# Parse GitHub webhook
github_event = handler.parse_github_webhook(payload, "pull_request")

# Check if analysis should be triggered
if handler.should_trigger_analysis(github_event):
    repo_info = handler.extract_repository_info(github_event)
    # Trigger analysis...
```

### PR Analysis Example

```python
from code_quality_agent.web.git_platform_integration import (
    GitHubPlatformIntegration, PullRequestAnalyzer
)

async def analyze_pr():
    async with GitHubPlatformIntegration() as github:
        # Create analyzer
        analyzer = PullRequestAnalyzer(github)
        
        # Analyze PR and create review
        result = await analyzer.analyze_pull_request(
            "owner", "repo", 123, analysis_result
        )
        
        print(f"Created review with {result['issues_found']} issues")
```

### Manual API Integration

```python
import aiohttp

async def trigger_analysis():
    webhook_url = "https://your-domain.com/webhooks/github"
    
    payload = {
        "action": "opened",
        "pull_request": {"number": 123},
        "repository": {
            "full_name": "owner/repo",
            "clone_url": "https://github.com/owner/repo.git"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "pull_request"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=payload, headers=headers) as resp:
            result = await resp.json()
            print(f"Analysis triggered: {result}")
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Code Quality Analysis
on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main, master, develop]

jobs:
  code-quality:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Analysis
        run: |
          curl -X POST \
            -H "Content-Type: application/json" \
            -H "X-GitHub-Event: ${{ github.event_name }}" \
            -d '{"repository": {"full_name": "${{ github.repository }}"}}' \
            https://your-domain.com/webhooks/github
```

### GitLab CI

```yaml
stages:
  - quality

code-quality:
  stage: quality
  image: curlimages/curl:latest
  script:
    - |
      curl -X POST \
        -H "Content-Type: application/json" \
        -H "X-Gitlab-Event: Push Hook" \
        -d '{"project": {"path_with_namespace": "$CI_PROJECT_PATH"}}' \
        https://your-domain.com/webhooks/gitlab
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

## Security Considerations

### Webhook Security
- **Always use webhook secrets** for signature verification
- **Verify signatures** on all incoming webhooks
- **Use HTTPS** for all webhook URLs
- **Validate payload structure** before processing

### API Token Security
- **Use minimal required scopes** for API tokens
- **Rotate tokens regularly** (every 90 days recommended)
- **Store tokens securely** in environment variables
- **Monitor token usage** for suspicious activity

### Network Security
- **Whitelist webhook IPs** if possible
- **Use firewall rules** to restrict access
- **Enable rate limiting** to prevent abuse
- **Log all webhook events** for audit trails

## Troubleshooting

### Common Issues

#### Webhook Not Triggering
- **Check webhook URL** is publicly accessible
- **Verify webhook secret** matches configuration
- **Check event types** are configured correctly
- **Review webhook delivery logs** in platform settings

#### Authentication Errors
- **Verify API token** has correct permissions
- **Check token expiration** date
- **Ensure token is set** in environment variables
- **Test token manually** with API calls

#### Analysis Not Appearing on PR
- **Check webhook payload** includes repository info
- **Verify PR analysis** is enabled for the repository
- **Review application logs** for processing errors
- **Check file patterns** match changed files

#### Rate Limiting
- **Monitor API usage** against platform limits
- **Implement exponential backoff** for retries
- **Use authenticated requests** for higher limits
- **Cache results** when possible

### Debug Endpoints

Use these endpoints to debug integration issues:

- `GET /health` - Check overall service health
- `GET /test/github` - Test GitHub API connectivity
- `GET /test/gitlab` - Test GitLab API connectivity
- `GET /test/components` - Test all system components

### Logging

Enable debug logging to troubleshoot issues:

```python
import logging

# Enable debug logging for Git integration
logging.getLogger('code_quality_agent.web.git_platform_integration').setLevel(logging.DEBUG)
```

## Rate Limits

### GitHub API Limits
- **Authenticated requests**: 5,000 per hour
- **Unauthenticated requests**: 60 per hour
- **Search API**: 30 per minute
- **GraphQL API**: 5,000 points per hour

### GitLab API Limits
- **Authenticated requests**: 2,000 per hour
- **Unauthenticated requests**: 10 per minute
- **Import/Export**: 6 per minute
- **Raw file access**: 300 per minute

## Best Practices

### Performance Optimization
- **Use shallow clones** for repository analysis
- **Cache analysis results** for unchanged files
- **Process webhooks asynchronously** to avoid timeouts
- **Implement request queuing** for high-volume repositories

### Quality Assurance
- **Test webhook integration** thoroughly before production
- **Monitor analysis accuracy** and adjust thresholds
- **Provide clear feedback** to developers
- **Document integration setup** for team members

### Maintenance
- **Monitor webhook delivery success** rates
- **Update API tokens** before expiration
- **Review and update** webhook configurations
- **Keep integration code** up to date with platform changes

## Support and Resources

### Documentation Links
- [GitHub Webhooks Documentation](https://docs.github.com/en/developers/webhooks-and-events/webhooks)
- [GitLab Webhooks Documentation](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [GitLab API Documentation](https://docs.gitlab.com/ee/api/)

### Example Repositories
- [GitHub Integration Example](https://github.com/example/github-integration)
- [GitLab Integration Example](https://gitlab.com/example/gitlab-integration)

### Community Support
- [GitHub Discussions](https://github.com/discussions)
- [GitLab Community Forum](https://forum.gitlab.com/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/github-api+gitlab-api)

For additional support or questions about the Code Quality Intelligence Agent Git platform integration, please refer to the main project documentation or create an issue in the project repository.