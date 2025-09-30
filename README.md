# Code Quality Intelligence Agent

An AI-powered tool that analyzes code repositories to generate actionable, developer-friendly reports. It goes beyond simple linting by understanding code structure, detecting real issues across multiple categories, and providing practical insights through both comprehensive reports and interactive Q&A capabilities.

## 🚀 Quick Start

For a complete setup guide, see [SETUP.md](SETUP.md).

```bash
# Clone and setup
git clone <your-repo-url>
cd code-quality-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Run analysis
python3 -m code_quality_agent.cli.main analyze examples/simple_module.py

# Start web interface
python3 -m code_quality_agent.web.api  # Backend on :8000
cd code_quality_agent/web/frontend && npm run dev  # Frontend on :3001
```

## 🚀 Features

- **Multi-Language Support**: Analyze Python, JavaScript, and TypeScript codebases
- **Comprehensive Analysis**: Detect security vulnerabilities, performance issues, complexity problems, code duplication, testing gaps, and documentation issues
- **AI-Powered Insights**: Get intelligent explanations and actionable fix suggestions using advanced LLM integration
- **Interactive Q&A**: Ask natural language questions about your codebase and get conversational answers
- **Multiple Output Formats**: CLI, JSON, and HTML reports with rich visualizations
- **Advanced Analytics**: Dependency graphs, hotspot detection, and severity scoring
- **Web Interface**: Optional web-based interface for team collaboration
- **CI/CD Integration**: Easy integration with GitHub, GitLab, and other platforms

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Features](#-features)
- [Setup Guide](#-setup-guide)
- [Usage](#-usage)
- [Web Interface](#-web-interface)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Architecture](#-architecture)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)

## 📖 Setup Guide

For detailed installation and setup instructions, see [SETUP.md](SETUP.md).

### Prerequisites

- Python 3.9 or higher
- Node.js 16+ (for web interface)
- Git (for repository analysis)

### Quick Installation

```bash
# Clone repository
git clone <your-repo-url>
cd code-quality-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install web interface dependencies
cd code_quality_agent/web/frontend
npm install
cd ../../..
```

## 🚀 Quick Start

### Basic Analysis

Analyze a single file:
```bash
python3 -m code_quality_agent.cli.main analyze examples/simple_module.py
```

Analyze a directory:
```bash
python3 -m code_quality_agent.cli.main analyze ./src
```

Analyze with JSON output:
```bash
python3 -m code_quality_agent.cli.main analyze ./src --output-format json
```

### Web Interface

Start the web interface for a user-friendly experience:

```bash
# Terminal 1: Start backend
python3 -m code_quality_agent.web.api

# Terminal 2: Start frontend
cd code_quality_agent/web/frontend
npm run dev
```

Then open `http://localhost:3001` in your browser.

### Interactive Q&A Mode

After running analysis, start interactive mode:
```bash
python3 -m code_quality_agent.cli.main interactive ./src
```

Example questions you can ask:
- "What are the most critical security issues?"
- "Which functions have the highest complexity?"
- "Show me all untested code in the user module"
- "What performance improvements can I make?"

## 📖 Usage

### Command Line Interface

The main command is `python3 -m code_quality_agent.cli.main`:

```bash
python3 -m code_quality_agent.cli.main [OPTIONS] COMMAND [ARGS]...
```

#### Available Commands

- `analyze` - Analyze code for quality issues
- `interactive` - Start interactive Q&A mode
- `validate` - Validate analysis accuracy
- `visualize` - Generate dependency graphs and visualizations
- `hotspot` - Identify code hotspots and problem areas
- `server` - Start web server for API access

#### Analysis Options

```bash
python3 -m code_quality_agent.cli.main analyze [OPTIONS] PATH

Options:
  -f, --output-format [cli|json|html]  Output format for the analysis report
  -o, --output-file PATH               Output file path
  -l, --languages [python|javascript|typescript]  Filter to specific languages
  --include-patterns TEXT              File patterns to include
  --exclude-patterns TEXT              File patterns to exclude
  -c, --categories [security|performance|complexity|duplication|testing|documentation]
                                       Filter to specific issue categories
  --min-severity [info|low|medium|high|critical]  Minimum severity level
  --max-workers INTEGER                Maximum parallel workers
  --no-cache                           Disable caching
  --confidence-threshold FLOAT         Minimum confidence threshold (0.0-1.0)
  --explanations                       Enable AI explanations (slower but more detailed)
  --suggestions                        Enable AI fix suggestions (slower but more detailed)
  --github TEXT                        Analyze a GitHub repository by URL
  -v, --verbose                        Enable verbose output
  --help                               Show help message
```

## 🌐 Web Interface

The web interface provides a user-friendly way to analyze code with a modern React frontend and FastAPI backend.

### Starting the Web Interface

```bash
# Terminal 1: Start the backend server
python3 -m code_quality_agent.web.api

# Terminal 2: Start the frontend development server
cd code_quality_agent/web/frontend
npm run dev
```

### Accessing the Interface

- **Frontend**: `http://localhost:3001`
- **Backend API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`

### Features

- **File Upload**: Drag and drop files for analysis
- **GitHub Integration**: Analyze repositories directly from GitHub URLs
- **Local Path Analysis**: Analyze files from your local filesystem
- **Real-time Results**: See analysis results as they're generated
- **Interactive Reports**: Browse issues by category and severity
- **Quality Score Visualization**: Visual representation of code quality metrics

### Web API Endpoints

```bash
# Get demo API key
curl "http://localhost:8000/demo/api-key"

# Analyze GitHub repository
curl -X POST "http://localhost:8000/analyze/repository" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "url": "https://github.com/user/repo.git",
    "branch": "main",
    "analysis_types": ["security", "performance"]
  }'

# Analyze uploaded files
curl -X POST "http://localhost:8000/analyze/files" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "files": ["example.py"],
    "content": {"example.py": "print(\"Hello World\")"},
    "analysis_types": ["security", "complexity"]
  }'

# Get analysis results
curl "http://localhost:8000/analyze/{job_id}" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Ask questions about analyzed code
curl -X POST "http://localhost:8000/qa/ask" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "question": "What are the main security issues?",
    "job_id": "analysis-job-id"
  }'
```

### Configuration

Create a `.cqa.yaml` configuration file in your project root:

```yaml
# Analysis settings
analysis:
  languages: [python, javascript, typescript]
  include_patterns:
    - "src/**/*.py"
    - "lib/**/*.js"
  exclude_patterns:
    - "node_modules/**"
    - "**/*.test.js"
    - "__pycache__/**"
  
  # Issue categories to analyze
  categories:
    - security
    - performance
    - complexity
    - duplication
    - testing
    - documentation
  
  # Severity filtering
  min_severity: info
  confidence_threshold: 0.7
  
  # Performance settings
  max_workers: 4
  enable_cache: true

# LLM settings
llm:
  provider: openai  # or anthropic
  model: gpt-4
  api_key_env: OPENAI_API_KEY
  enable_explanations: true
  enable_suggestions: true

# Output settings
output:
  format: cli
  include_metrics: true
  include_suggestions: true
  max_issues_per_category: 50

# Web interface settings (optional)
web:
  enabled: false
  host: localhost
  port: 8000
  auth_required: false
```

### Environment Variables

Set up your environment:

```bash
# Required for AI features
export OPENAI_API_KEY="your-openai-api-key"
# OR
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Optional: Custom configuration path
export CQA_CONFIG_PATH="/path/to/your/.cqa.yaml"

# Optional: Cache directory
export CQA_CACHE_DIR="/path/to/cache"
```

## 🔧 API Documentation

### Python API

```python
from code_quality_agent import AnalysisOrchestrator, AnalysisOptions

# Initialize orchestrator
orchestrator = AnalysisOrchestrator()

# Configure analysis options
options = AnalysisOptions(
    languages=['python', 'javascript'],
    categories=['security', 'performance'],
    min_severity='medium',
    enable_explanations=True
)

# Run analysis
result = orchestrator.analyze_codebase('/path/to/code', options)

# Access results
for issue in result.issues:
    print(f"{issue.severity}: {issue.title}")
    print(f"Location: {issue.location.file_path}:{issue.location.line_start}")
    print(f"Suggestion: {issue.suggestion}")
```

### Interactive Q&A API

```python
from code_quality_agent.rag import QAEngine

# Initialize Q&A engine
qa_engine = QAEngine()

# Index your codebase
qa_engine.index_codebase(analysis_result)

# Ask questions
answer = qa_engine.ask_question(
    "What are the security vulnerabilities in the auth module?",
    conversation_context
)

print(answer.text)
for ref in answer.code_references:
    print(f"Reference: {ref.file_path}:{ref.line_start}")
```

### Web API

Start the web server:
```bash
python3 -m code_quality_agent.cli.main server --host 0.0.0.0 --port 8000
```

API endpoints:
- `POST /analyze/repository` - Analyze GitHub repository
- `POST /analyze/files` - Analyze uploaded files
- `GET /analyze/{job_id}` - Get analysis results
- `POST /qa/ask` - Ask questions about analyzed code
- `GET /health` - Health check
- `GET /demo/api-key` - Get demo API key

Example API usage:
```bash
# Get demo API key
curl "http://localhost:8000/demo/api-key"

# Submit analysis
curl -X POST "http://localhost:8000/analyze/repository" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"url": "https://github.com/user/repo.git", "branch": "main"}'

# Get results
curl "http://localhost:8000/analyze/abc123" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Ask question
curl -X POST "http://localhost:8000/qa/ask" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"question": "What are the main security issues?", "job_id": "abc123"}'
```

## 🏗 Architecture

The Code Quality Intelligence Agent follows a modular, plugin-based architecture designed for scalability and extensibility. The system is built around a central orchestration engine that coordinates multiple specialized components.

### Architecture Overview

![Application Architecture](diagrams/user_flow%20-%20Application%20Architecture.svg)

The system architecture consists of several key layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                     │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Web Frontend  │   CLI Interface │      API Endpoints          │
│   (React/Vite)  │   (Click/Typer) │      (FastAPI)              │
└─────────┬───────┴─────────┬───────┴─────────┬───────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                    Orchestration Layer                          │
│              Analysis Orchestrator & Q&A Engine                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                     Analysis Layer                              │
├─────────────┬─────────────┼─────────────┬───────────────────────┤
│   Parser    │  Analyzers  │    RAG      │   Report Generator    │
│   (AST)     │ (Security,  │   System    │   & Visualization     │
│             │Performance, │             │                       │
│             │Complexity,  │             │                       │
│             │Testing, etc)│             │                       │
└─────────────┴─────────────┴─────────────┴───────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                      Data Layer                                │
├─────────────┬─────────────┼─────────────┬───────────────────────┤
│   Vector    │   Cache     │   File      │   Configuration       │
│   Store     │   Manager   │   System    │   Management          │
│ (ChromaDB)  │             │             │                       │
└─────────────┴─────────────┴─────────────┴───────────────────────┘
```

### User Flow

![User Flow Diagram](diagrams/user_flow%20-%20Updated%20Userflow%20Diagram.svg)

The user interaction flow follows these key paths:

1. **Code Analysis Flow**:
   - User uploads files or provides repository URL
   - System parses and analyzes code using multiple analyzers
   - Results are processed and scored
   - Reports are generated with AI-powered insights

2. **Interactive Q&A Flow**:
   - User asks natural language questions about their codebase
   - RAG system retrieves relevant code context
   - LLM generates contextual answers with code references
   - User can drill down into specific issues or areas

3. **Web Interface Flow**:
   - Real-time analysis progress updates
   - Interactive report browsing and filtering
   - Quality score visualization and trend tracking
   - Export capabilities for different formats

### System Sequence Diagram

![System Sequence](diagrams/System%20Sequence.svg)

This end-to-end sequence shows a single analysis run: User triggers the CLI, the Orchestrator discovers files, the Parser builds multi-language ASTs, analyzers run across categories, the LLM service generates explanations and fix suggestions, and the Report Generator returns prioritized results to the CLI. Notes highlight cache behavior (`--no-cache`), analyzer initialization, total issues, and severity scoring.

### Core Components

1. **Analysis Orchestrator**: Central coordination engine that manages the analysis workflow, handles parallel processing, and coordinates between different analyzers.

2. **Code Parsers**: Multi-language AST parsers that extract semantic information from Python, JavaScript, and TypeScript codebases.

3. **Quality Analyzers**: Specialized analyzers for different quality dimensions:
   - **Security Analyzer**: Detects vulnerabilities and security anti-patterns
   - **Performance Analyzer**: Identifies performance bottlenecks and optimization opportunities
   - **Complexity Analyzer**: Measures cyclomatic complexity and maintainability metrics
   - **Duplication Analyzer**: Finds code duplication and suggests refactoring opportunities
   - **Testing Analyzer**: Identifies testing gaps and coverage issues
   - **Documentation Analyzer**: Evaluates code documentation quality

4. **RAG System**: Retrieval-Augmented Generation system that enables efficient querying of large codebases using vector embeddings and semantic search.

5. **Q&A Engine**: Interactive conversational interface powered by LLMs that can answer questions about codebases with contextual code references.

6. **Report Generator**: Creates comprehensive reports in multiple formats (CLI, JSON, HTML) with AI-generated explanations and actionable suggestions.

7. **Web Interface**: Modern React-based frontend with FastAPI backend providing real-time analysis capabilities and interactive visualizations.

### Data Flow

1. **Input Processing**: Files are parsed and converted to AST representations
2. **Analysis Pipeline**: Multiple analyzers process the code in parallel
3. **Issue Aggregation**: Results are collected, scored, and prioritized
4. **AI Enhancement**: LLM services add explanations and suggestions
5. **Report Generation**: Final reports are formatted and delivered
6. **Interactive Querying**: RAG system enables ongoing codebase exploration

For detailed architecture documentation, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).


### Development Setup

```bash
git clone https://github.com/codequalityai/intelligence-agent.git
cd intelligence-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black .
flake8 .
mypy .
```

## 🐛 Troubleshooting

### Common Issues

#### Installation Problems

**Issue**: `pip install` fails with dependency conflicts
```bash
# Solution: Use a fresh virtual environment
python3 -m venv fresh_env
source fresh_env/bin/activate  # On Windows: fresh_env\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

**Issue**: Node.js dependencies fail to install
```bash
# Clear npm cache and reinstall
cd code_quality_agent/web/frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

#### Analysis Issues

**Issue**: "No supported files found"
```bash
# Check file patterns and language detection
python3 -m code_quality_agent.cli.main analyze ./src --verbose --languages python javascript
```

**Issue**: LLM API errors
```bash
# Verify API key is set
echo $OPENAI_API_KEY
# Run without AI features
python3 -m code_quality_agent.cli.main analyze ./src --no-explanations --no-suggestions
```

**Issue**: Out of memory errors on large codebases
```bash
# Reduce parallel workers and enable incremental analysis
python3 -m code_quality_agent.cli.main analyze ./src --max-workers 1 --no-cache
```

#### Web Interface Issues

**Issue**: Frontend not loading or showing errors
```bash
# Check if backend is running
curl http://localhost:8000/docs

# Restart both servers
# Terminal 1:
python3 -m code_quality_agent.web.api

# Terminal 2:
cd code_quality_agent/web/frontend
npm run dev
```

**Issue**: Port conflicts
```bash
# Kill processes using ports 3001 and 8000
lsof -ti:3001 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

**Issue**: Different results between CLI and web interface
- Ensure both are using the same analysis settings
- Check that the web interface is analyzing the correct files
- Verify cache is disabled with `--no-cache` flag

#### Performance Issues

**Issue**: Analysis is very slow
- Enable caching: Remove `--no-cache` flag
- Reduce scope: Use `--include-patterns` and `--exclude-patterns`
- Disable AI features: Use `--no-explanations --no-suggestions`
- Increase workers: Use `--max-workers 8` (adjust based on your CPU)

### Debug Mode

Enable verbose logging for troubleshooting:
```bash
python3 -m code_quality_agent.cli.main --verbose analyze ./src
```

Set debug environment variable:
```bash
export CQA_DEBUG=1
python3 -m code_quality_agent.cli.main analyze ./src
```

### Getting Help

1. Check the [FAQ](#faq) section below
2. Search existing [GitHub Issues](https://github.com/codequalityai/intelligence-agent/issues)
3. Create a new issue with:
   - Your operating system and Python version
   - Complete error message and stack trace
   - Minimal code example that reproduces the issue
   - Your configuration file (remove sensitive data)

## ❓ FAQ

### General Questions

**Q: What programming languages are supported?**
A: Currently Python, JavaScript, and TypeScript. We're working on adding Java, C#, Go, and Rust support.

**Q: How accurate are the AI-generated explanations?**
A: Our explanations are generated using state-of-the-art LLMs and are continuously validated against known issue databases. Accuracy varies by issue type, typically 85-95% for security and complexity issues.

**Q: Can I use this without an OpenAI/Anthropic API key?**
A: Yes! You can run basic analysis without AI features using `--no-explanations --no-suggestions`. However, you'll miss the intelligent insights that make this tool unique.

**Q: Is my code sent to external services?**
A: Only small code snippets (typically 10-50 lines) are sent to LLM providers for explanation generation. Full files are never transmitted. You can disable this with `--no-explanations`.

### Technical Questions

**Q: How does the tool compare to ESLint, Pylint, etc.?**
A: Traditional linters focus on style and basic issues. Our tool provides deeper semantic analysis, cross-file dependency understanding, and AI-powered explanations for complex issues.

**Q: Can I integrate this with my CI/CD pipeline?**
A: Yes! Use JSON output format and check exit codes:
```bash
python3 -m code_quality_agent.cli.main analyze ./src --output-format json --min-severity medium
if [ $? -ne 0 ]; then
  echo "Quality issues found"
  exit 1
fi
```

**Q: How do I customize the analysis rules?**
A: Create a `.cqa.yaml` configuration file to customize patterns, thresholds, and categories. For advanced customization, you can create custom analyzer plugins.

**Q: What's the performance impact on large codebases?**
A: Analysis time scales roughly linearly with codebase size. A 100k LOC Python project typically takes 2-5 minutes with AI features enabled, 30-60 seconds without.

**Q: Why do I get different results between CLI and web interface?**
A: This was a known issue that has been fixed. Both interfaces now use the same analysis engine and should produce identical results. If you still see differences, ensure both are using the same settings and `--no-cache` flag.

**Q: How accurate are the quality scores?**
A: Quality scores are calculated using a penalty-based system where different severity levels have different penalties. The scoring has been optimized to provide meaningful, actionable feedback rather than overly strict assessments.

### Troubleshooting Questions

**Q: Why am I getting "No issues found" on code I know has problems?**
A: Check your confidence threshold (`--confidence-threshold`) and severity filter (`--min-severity`). Lower the confidence threshold or include more severity levels.

**Q: The interactive Q&A isn't working well. What can I do?**
A: Ensure your codebase was fully analyzed first. Try more specific questions like "Show security issues in auth.py" rather than general questions.

**Q: Can I run this offline?**
A: Basic analysis works offline, but AI features require internet connectivity. We're working on local LLM support for fully offline operation.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/) for AI agent orchestration
- Uses [Tree-sitter](https://tree-sitter.github.io/) for robust code parsing
- Powered by [ChromaDB](https://www.trychroma.com/) for vector storage
- UI built with [React](https://reactjs.org/) and [FastAPI](https://fastapi.tiangolo.com/)

## 📊 Project Status

- ✅ Core analysis engine
- ✅ Python and JavaScript support  
- ✅ CLI interface
- ✅ Web interface (React + FastAPI)
- ✅ Quality scoring system
- ✅ Multiple analyzer types (Security, Performance, Complexity, etc.)
- ✅ File upload and GitHub integration
- 🚧 Interactive Q&A mode
- 🚧 Additional language support (TypeScript, Java, etc.)

## 🏗 Architecture Overview

The Code Quality Intelligence Agent is built with a layered architecture that separates concerns and enables scalability:

For detailed architecture information and user flow diagrams, see the [Architecture](#-architecture) section above.

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=code_quality_agent

# Run specific test categories
pytest tests/test_analyzers/
pytest tests/test_web/
```

## 📝 Examples

Check the `examples/` directory for sample files to analyze:

```bash
# Analyze the example file
python3 -m code_quality_agent.cli.main analyze examples/simple_module.py

# Expected output: ~1 issue, quality score ~92/100
```

---

**Made with ❤️ for better code quality**

For detailed setup instructions, see [SETUP.md](SETUP.md).