# Code Quality Intelligence Agent Web API

This document provides comprehensive documentation for the FastAPI web server that powers the Code Quality Intelligence Agent.

## Overview

The web API provides REST endpoints for:
- Analyzing GitHub repositories
- Analyzing individual files
- Interactive Q&A about code quality
- Batch analysis of multiple repositories
- Authentication and rate limiting
- Real-time progress tracking

## Quick Start

### 1. Start the Server

```bash
# Development mode
python -m code_quality_agent.web.api

# Production mode
uvicorn code_quality_agent.web.api:app --host 0.0.0.0 --port 8000
```

### 2. Get API Key

```bash
curl http://localhost:8000/demo/api-key
```

### 3. Analyze a Repository

```bash
curl -X POST "http://localhost:8000/analyze/repository" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://github.com/octocat/Hello-World",
    "branch": "main"
  }'
```

## Authentication

The API supports multiple authentication methods:

### API Keys
- **Endpoint**: `POST /auth/api-key`
- **Usage**: Include in `Authorization: Bearer <api_key>` header
- **Permissions**: Configurable per key

### Sessions
- **Endpoint**: `POST /auth/session`
- **Usage**: Automatic cookie-based authentication
- **Duration**: 24 hours by default

### Anonymous Access
- Limited functionality with stricter rate limits
- Suitable for testing and demos

## Core Endpoints

### Repository Analysis

#### Start Analysis
```http
POST /analyze/repository
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "url": "https://github.com/owner/repo",
  "branch": "main",
  "include_patterns": ["*.py", "*.js"],
  "exclude_patterns": ["test_*", "*.min.js"],
  "analysis_types": ["security", "performance"],
  "config": {
    "enable_security_analysis": true,
    "severity_threshold": "medium",
    "max_issues_per_file": 50
  }
}
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "pending",
  "repository_url": "https://github.com/owner/repo",
  "branch": "main",
  "started_at": "2024-01-01T12:00:00Z"
}
```

#### Get Results
```http
GET /analyze/{job_id}
Authorization: Bearer <api_key>
```

#### Track Progress
```http
GET /analyze/{job_id}/progress
Authorization: Bearer <api_key>
```

### File Analysis

```http
POST /analyze/files
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "files": ["app.py", "utils.py"],
  "content": {
    "app.py": "def main(): pass",
    "utils.py": "def helper(): return True"
  },
  "analysis_types": ["security", "maintainability"]
}
```

### Interactive Q&A

```http
POST /qa/ask
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "question": "What are the main security issues in this code?",
  "job_id": "analysis-job-id",
  "file_path": "app.py",
  "context": {"project_type": "web_application"}
}
```

### Batch Analysis

```http
POST /analyze/batch
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "repositories": [
    {
      "url": "https://github.com/owner/repo1",
      "branch": "main"
    },
    {
      "url": "https://github.com/owner/repo2",
      "branch": "develop"
    }
  ],
  "configuration": {
    "enable_security_analysis": true,
    "severity_threshold": "high"
  },
  "callback_url": "https://your-app.com/webhook"
}
```

## Configuration Options

### Analysis Configuration

```json
{
  "enable_security_analysis": true,
  "enable_performance_analysis": true,
  "enable_maintainability_analysis": true,
  "enable_complexity_analysis": true,
  "enable_duplication_analysis": true,
  "enable_ai_explanations": true,
  "enable_severity_scoring": true,
  "severity_threshold": "low|medium|high|critical",
  "max_issues_per_file": 50,
  "timeout_seconds": 300
}
```

### Supported Repository Hosts

- **GitHub**: `https://github.com/owner/repo`
- **GitLab**: `https://gitlab.com/owner/repo` (basic support)
- **Bitbucket**: `https://bitbucket.org/owner/repo` (planned)

## Rate Limiting

### Limits by User Type

| User Type | Requests/Hour | Analysis/Hour |
|-----------|---------------|---------------|
| Anonymous | 100 | 5 |
| Authenticated | 1000 | 50 |
| Premium | 5000 | 200 |

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Error Handling

### Standard Error Response

```json
{
  "error": "ValidationError",
  "message": "Invalid repository URL format",
  "details": {
    "field": "url",
    "value": "invalid-url"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "uuid-string"
}
```

### Common Error Codes

- **400**: Bad Request - Invalid input data
- **401**: Unauthorized - Missing or invalid authentication
- **403**: Forbidden - Insufficient permissions
- **404**: Not Found - Resource not found
- **422**: Unprocessable Entity - Validation error
- **429**: Too Many Requests - Rate limit exceeded
- **500**: Internal Server Error - Server error

## Security Features

### Security Headers

All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`
- `Content-Security-Policy: default-src 'self'`

### CORS Configuration

CORS is configured for web browser access:
```python
allow_origins=["*"]  # Configure for production
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

### Input Validation

All inputs are validated using Pydantic models:
- URL format validation
- File size limits
- Content sanitization
- SQL injection prevention

## Monitoring and Health

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00Z",
  "components": {
    "orchestrator": "healthy",
    "qa_engine": "healthy",
    "scoring_engine": "healthy"
  }
}
```

### Usage Statistics
```http
GET /stats
```

### Component Testing
```http
GET /test/components
```

## Development and Testing

### Test Endpoints

- `GET /demo/api-key` - Get demo API key
- `POST /test/simple` - Test request parsing
- `POST /test/github` - Test GitHub integration
- `GET /test/components` - Test all components

### Running Tests

```bash
# Run all web API tests
pytest tests/test_web_api.py -v

# Run specific test class
pytest tests/test_web_api.py::TestWebAPI -v

# Run with coverage
pytest tests/test_web_api.py --cov=code_quality_agent.web
```

### Development Server

```bash
# Auto-reload on changes
uvicorn code_quality_agent.web.api:app --reload --host 0.0.0.0 --port 8000

# Debug mode
uvicorn code_quality_agent.web.api:app --reload --log-level debug
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "code_quality_agent.web.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```bash
# GitHub integration
GITHUB_TOKEN=your_github_token

# LLM providers
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Database (if using persistent storage)
DATABASE_URL=postgresql://user:pass@localhost/db

# Security
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=localhost,your-domain.com
```

### Production Configuration

```python
# Disable debug mode
app.debug = False

# Configure CORS for production
allow_origins=["https://your-domain.com"]

# Use production database
DATABASE_URL = os.getenv("DATABASE_URL")

# Enable HTTPS redirect
app.add_middleware(HTTPSRedirectMiddleware)
```

## API Documentation

### Interactive Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### SDK and Client Libraries

Client libraries are available for:
- Python: `pip install code-quality-agent-client`
- JavaScript: `npm install code-quality-agent-client`
- CLI: Built-in CLI client

## Support and Troubleshooting

### Common Issues

1. **Git not found**: Install Git and ensure it's in PATH
2. **Rate limit exceeded**: Use authentication or wait for reset
3. **Repository access denied**: Check repository permissions
4. **Analysis timeout**: Increase timeout or reduce scope

### Logging

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("code_quality_agent.web")
```

### Performance Tuning

- Use Redis for caching analysis results
- Configure worker processes for concurrent analysis
- Implement result pagination for large repositories
- Use CDN for static assets

## Contributing

See the main project README for contribution guidelines.

## License

See the main project LICENSE file.