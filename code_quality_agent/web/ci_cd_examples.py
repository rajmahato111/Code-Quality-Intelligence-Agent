"""CI/CD integration examples and configurations."""

import os
from typing import Dict, Any, Optional
import yaml
import json


class CICDConfigGenerator:
    """Generate CI/CD configuration files for different platforms."""
    
    @staticmethod
    def generate_github_actions_config(
        webhook_url: str,
        webhook_secret: Optional[str] = None,
        api_key: Optional[str] = None,
        trigger_on_pr: bool = True,
        trigger_on_push: bool = True,
        branches: list = None
    ) -> str:
        """Generate GitHub Actions workflow configuration.
        
        Args:
            webhook_url: URL of the webhook endpoint
            webhook_secret: Webhook secret for verification
            api_key: API key for authenticated requests
            trigger_on_pr: Whether to trigger on pull requests
            trigger_on_push: Whether to trigger on pushes
            branches: List of branches to monitor
            
        Returns:
            YAML configuration string
        """
        if branches is None:
            branches = ["main", "master", "develop"]
        
        config = {
            "name": "Code Quality Analysis",
            "on": {}
        }
        
        if trigger_on_pr:
            config["on"]["pull_request"] = {
                "types": ["opened", "synchronize", "reopened"]
            }
        
        if trigger_on_push:
            config["on"]["push"] = {
                "branches": branches
            }
        
        # Job configuration
        config["jobs"] = {
            "code-quality": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {
                        "name": "Checkout code",
                        "uses": "actions/checkout@v3"
                    },
                    {
                        "name": "Trigger Code Quality Analysis",
                        "run": self._generate_curl_command(
                            webhook_url, 
                            webhook_secret,
                            api_key,
                            "github"
                        )
                    },
                    {
                        "name": "Wait for Analysis",
                        "run": "sleep 30"  # Simple wait, could be improved
                    }
                ]
            }
        }
        
        return yaml.dump(config, default_flow_style=False)
    
    @staticmethod
    def generate_gitlab_ci_config(
        webhook_url: str,
        webhook_secret: Optional[str] = None,
        api_key: Optional[str] = None,
        trigger_on_mr: bool = True,
        trigger_on_push: bool = True
    ) -> str:
        """Generate GitLab CI configuration.
        
        Args:
            webhook_url: URL of the webhook endpoint
            webhook_secret: Webhook secret for verification
            api_key: API key for authenticated requests
            trigger_on_mr: Whether to trigger on merge requests
            trigger_on_push: Whether to trigger on pushes
            
        Returns:
            YAML configuration string
        """
        config = {
            "stages": ["quality"],
            "code-quality": {
                "stage": "quality",
                "image": "curlimages/curl:latest",
                "script": [
                    self._generate_curl_command(
                        webhook_url,
                        webhook_secret,
                        api_key,
                        "gitlab"
                    )
                ]
            }
        }
        
        # Add rules for when to run
        rules = []
        if trigger_on_mr:
            rules.append({"if": "$CI_PIPELINE_SOURCE == 'merge_request_event'"})
        if trigger_on_push:
            rules.append({"if": "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH"})
        
        if rules:
            config["code-quality"]["rules"] = rules
        
        return yaml.dump(config, default_flow_style=False)
    
    @staticmethod
    def generate_jenkins_pipeline(
        webhook_url: str,
        webhook_secret: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> str:
        """Generate Jenkins pipeline configuration.
        
        Args:
            webhook_url: URL of the webhook endpoint
            webhook_secret: Webhook secret for verification
            api_key: API key for authenticated requests
            
        Returns:
            Jenkinsfile content
        """
        pipeline = f'''
pipeline {{
    agent any
    
    triggers {{
        githubPush()
    }}
    
    stages {{
        stage('Code Quality Analysis') {{
            steps {{
                script {{
                    sh '''
{CICDConfigGenerator._generate_curl_command(webhook_url, webhook_secret, api_key, "github")}
                    '''
                }}
            }}
        }}
    }}
    
    post {{
        always {{
            echo 'Code quality analysis completed'
        }}
        failure {{
            echo 'Code quality analysis failed'
        }}
    }}
}}
'''
        return pipeline.strip()
    
    @staticmethod
    def _generate_curl_command(
        webhook_url: str,
        webhook_secret: Optional[str] = None,
        api_key: Optional[str] = None,
        platform: str = "github"
    ) -> str:
        """Generate curl command for webhook trigger."""
        headers = [
            f'-H "Content-Type: application/json"',
            f'-H "User-Agent: CI-CD-Integration/1.0"'
        ]
        
        if webhook_secret:
            if platform == "github":
                headers.append(f'-H "X-Hub-Signature-256: $WEBHOOK_SIGNATURE"')
            elif platform == "gitlab":
                headers.append(f'-H "X-Gitlab-Token: {webhook_secret}"')
        
        if api_key:
            headers.append(f'-H "Authorization: Bearer {api_key}"')
        
        # Add platform-specific event headers
        if platform == "github":
            headers.append('-H "X-GitHub-Event: push"')
        elif platform == "gitlab":
            headers.append('-H "X-Gitlab-Event: Push Hook"')
        
        headers_str = " ".join(headers)
        
        # Create payload based on platform
        if platform == "github":
            payload = ''''{
                "ref": "$GITHUB_REF",
                "repository": {
                    "full_name": "$GITHUB_REPOSITORY",
                    "clone_url": "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY.git",
                    "default_branch": "main"
                },
                "head_commit": {
                    "id": "$GITHUB_SHA"
                },
                "sender": {
                    "login": "$GITHUB_ACTOR"
                }
            }' '''
        else:  # gitlab
            payload = ''''{
                "object_kind": "push",
                "ref": "$CI_COMMIT_REF_NAME",
                "project": {
                    "path_with_namespace": "$CI_PROJECT_PATH",
                    "http_url_to_repo": "$CI_PROJECT_URL.git",
                    "default_branch": "$CI_DEFAULT_BRANCH"
                },
                "commits": [{
                    "id": "$CI_COMMIT_SHA"
                }],
                "user": {
                    "username": "$GITLAB_USER_LOGIN"
                }
            }' '''
        
        return f'curl -X POST {headers_str} -d {payload} {webhook_url}'


class WebhookConfigurationGuide:
    """Guide for setting up webhooks on different platforms."""
    
    @staticmethod
    def get_github_webhook_setup_guide(webhook_url: str, secret: Optional[str] = None) -> Dict[str, Any]:
        """Get GitHub webhook setup guide.
        
        Args:
            webhook_url: URL of the webhook endpoint
            secret: Optional webhook secret
            
        Returns:
            Dictionary with setup instructions
        """
        return {
            "title": "GitHub Webhook Setup",
            "steps": [
                {
                    "step": 1,
                    "title": "Navigate to Repository Settings",
                    "description": "Go to your GitHub repository and click on 'Settings'"
                },
                {
                    "step": 2,
                    "title": "Access Webhooks",
                    "description": "In the left sidebar, click on 'Webhooks'"
                },
                {
                    "step": 3,
                    "title": "Add Webhook",
                    "description": "Click 'Add webhook' button"
                },
                {
                    "step": 4,
                    "title": "Configure Webhook",
                    "description": "Fill in the webhook configuration",
                    "configuration": {
                        "payload_url": webhook_url,
                        "content_type": "application/json",
                        "secret": secret or "your_webhook_secret_here",
                        "events": [
                            "Pull requests",
                            "Pushes"
                        ],
                        "active": True
                    }
                },
                {
                    "step": 5,
                    "title": "Test Webhook",
                    "description": "Create a test pull request or push to verify the webhook is working"
                }
            ],
            "events_supported": [
                "pull_request (opened, synchronize, reopened)",
                "push (to main/master/develop branches)"
            ],
            "security_notes": [
                "Always use a webhook secret for security",
                "Verify webhook signatures in your application",
                "Use HTTPS for webhook URLs"
            ]
        }
    
    @staticmethod
    def get_gitlab_webhook_setup_guide(webhook_url: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Get GitLab webhook setup guide.
        
        Args:
            webhook_url: URL of the webhook endpoint
            token: Optional webhook token
            
        Returns:
            Dictionary with setup instructions
        """
        return {
            "title": "GitLab Webhook Setup",
            "steps": [
                {
                    "step": 1,
                    "title": "Navigate to Project Settings",
                    "description": "Go to your GitLab project and click on 'Settings'"
                },
                {
                    "step": 2,
                    "title": "Access Webhooks",
                    "description": "In the left sidebar, click on 'Webhooks'"
                },
                {
                    "step": 3,
                    "title": "Add Webhook",
                    "description": "Fill in the webhook form"
                },
                {
                    "step": 4,
                    "title": "Configure Webhook",
                    "description": "Set up the webhook configuration",
                    "configuration": {
                        "url": webhook_url,
                        "secret_token": token or "your_webhook_token_here",
                        "trigger_events": [
                            "Push events",
                            "Merge request events"
                        ],
                        "enable_ssl_verification": True
                    }
                },
                {
                    "step": 5,
                    "title": "Test Webhook",
                    "description": "Use the 'Test' button or create a test merge request"
                }
            ],
            "events_supported": [
                "merge_request (open, update, reopen)",
                "push (to main/master/develop branches)"
            ],
            "security_notes": [
                "Always use a secret token for security",
                "Enable SSL verification",
                "Use HTTPS for webhook URLs"
            ]
        }


def generate_webhook_documentation(base_url: str) -> str:
    """Generate comprehensive webhook documentation.
    
    Args:
        base_url: Base URL of the webhook service
        
    Returns:
        Markdown documentation string
    """
    github_guide = WebhookConfigurationGuide.get_github_webhook_setup_guide(
        f"{base_url}/webhooks/github"
    )
    gitlab_guide = WebhookConfigurationGuide.get_gitlab_webhook_setup_guide(
        f"{base_url}/webhooks/gitlab"
    )
    
    doc = f"""# Git Platform Integration Guide

## Overview

The Code Quality Intelligence Agent supports integration with GitHub and GitLab through webhooks and API access. This enables automatic code quality analysis on pull requests and pushes.

## Supported Platforms

- **GitHub**: Full support for pull request analysis and commit status updates
- **GitLab**: Full support for merge request analysis and commit status updates

## Webhook Endpoints

### GitHub Webhook
- **URL**: `{base_url}/webhooks/github`
- **Method**: POST
- **Content-Type**: application/json
- **Headers**: 
  - `X-GitHub-Event`: Event type (pull_request, push)
  - `X-Hub-Signature-256`: HMAC signature for verification

### GitLab Webhook
- **URL**: `{base_url}/webhooks/gitlab`
- **Method**: POST
- **Content-Type**: application/json
- **Headers**:
  - `X-Gitlab-Event`: Event type (Push Hook, Merge Request Hook)
  - `X-Gitlab-Token`: Token for verification

## Setup Instructions

### GitHub Setup

{_format_setup_steps(github_guide['steps'])}

### GitLab Setup

{_format_setup_steps(gitlab_guide['steps'])}

## Supported Events

### GitHub Events
- **pull_request**: Triggered on PR open, synchronize, reopen
- **push**: Triggered on pushes to main branches

### GitLab Events
- **merge_request**: Triggered on MR open, update, reopen
- **push**: Triggered on pushes to main branches

## API Endpoints

### Manual PR Analysis
```
POST /pr/analyze/{{owner}}/{{repo}}/{{pr_number}}?platform={{github|gitlab}}
```

### Get PR Information
```
GET /pr/{{owner}}/{{repo}}/{{pr_number}}?platform={{github|gitlab}}
```

## Environment Variables

Set these environment variables for proper integration:

```bash
# GitHub Integration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# GitLab Integration
GITLAB_TOKEN=your_gitlab_personal_access_token
GITLAB_WEBHOOK_SECRET=your_webhook_token
```

## Security Considerations

1. **Always use webhook secrets/tokens** for verification
2. **Use HTTPS** for all webhook URLs
3. **Verify signatures** on incoming webhooks
4. **Limit token permissions** to minimum required scope
5. **Rotate tokens regularly**

## CI/CD Integration Examples

### GitHub Actions

```yaml
{CICDConfigGenerator.generate_github_actions_config(f"{base_url}/webhooks/github")}
```

### GitLab CI

```yaml
{CICDConfigGenerator.generate_gitlab_ci_config(f"{base_url}/webhooks/gitlab")}
```

### Jenkins Pipeline

```groovy
{CICDConfigGenerator.generate_jenkins_pipeline(f"{base_url}/webhooks/github")}
```

## Troubleshooting

### Common Issues

1. **Webhook not triggering**
   - Check webhook URL is accessible
   - Verify webhook secret/token
   - Check event types are configured correctly

2. **Authentication errors**
   - Verify API tokens have correct permissions
   - Check token expiration
   - Ensure tokens are set in environment variables

3. **Analysis not appearing on PR**
   - Check webhook payload includes correct repository info
   - Verify PR analysis is enabled
   - Check logs for processing errors

### Debug Endpoints

- `GET /health` - Check service health
- `GET /test/github` - Test GitHub integration
- `GET /test/components` - Test all components

## Rate Limits

- **GitHub API**: 5000 requests/hour (authenticated)
- **GitLab API**: 2000 requests/hour (authenticated)
- **Webhook processing**: No specific limits

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review service logs
3. Test individual components using debug endpoints
4. Verify environment configuration
"""
    
    return doc


def _format_setup_steps(steps: list) -> str:
    """Format setup steps as markdown."""
    formatted = []
    for step in steps:
        formatted.append(f"#### Step {step['step']}: {step['title']}")
        formatted.append(f"{step['description']}")
        
        if 'configuration' in step:
            formatted.append("\n**Configuration:**")
            config = step['configuration']
            for key, value in config.items():
                if isinstance(value, list):
                    formatted.append(f"- **{key}**: {', '.join(value)}")
                else:
                    formatted.append(f"- **{key}**: `{value}`")
        
        formatted.append("")  # Empty line
    
    return "\n".join(formatted)


if __name__ == "__main__":
    # Example usage
    generator = CICDConfigGenerator()
    
    # Generate GitHub Actions config
    github_config = generator.generate_github_actions_config(
        webhook_url="https://your-domain.com/webhooks/github",
        webhook_secret="your_secret"
    )
    print("GitHub Actions Config:")
    print(github_config)
    
    # Generate GitLab CI config
    gitlab_config = generator.generate_gitlab_ci_config(
        webhook_url="https://your-domain.com/webhooks/gitlab",
        webhook_secret="your_token"
    )
    print("\nGitLab CI Config:")
    print(gitlab_config)
    
    # Generate documentation
    docs = generate_webhook_documentation("https://your-domain.com")
    print("\nWebhook Documentation:")
    print(docs[:500] + "...")  # Print first 500 chars