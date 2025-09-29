# Code Quality Intelligence Agent - Setup Guide

This guide will help you set up and run the Code Quality Intelligence Agent on your local machine.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9 or higher**
- **Node.js 16+** (for JavaScript/TypeScript analysis and web frontend)
- **Git** (for repository analysis)
- **pip** (Python package manager)

### Check Your Environment

```bash
# Check Python version
python3 --version

# Check Node.js version
node --version

# Check npm version
npm --version

# Check Git version
git --version
```

## 🚀 Installation Steps

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd code-quality-agent
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

### Step 4: Install Node.js Dependencies (for Web Interface)

```bash
# Navigate to web frontend directory
cd code_quality_agent/web/frontend

# Install npm dependencies
npm install

# Go back to project root
cd ../../..
```

## 🔧 Configuration

### Step 1: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example environment file
cp .env.example .env
```

Edit the `.env` file with your API keys:

```env
# OpenAI API Key (for AI-powered insights)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key (alternative to OpenAI)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Custom cache directory
CQA_CACHE_DIR=./cache

# Optional: Debug mode
CQA_DEBUG=0
```

### Step 2: Get API Keys

#### OpenAI API Key (Recommended)
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

#### Anthropic API Key (Alternative)
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Create an API key
4. Copy the key to your `.env` file

**Note**: You only need one API key. OpenAI is recommended for better performance.

## 🧪 Testing the Installation

### Step 1: Test CLI Installation

```bash
# Test basic CLI functionality
python3 -m code_quality_agent.cli.main --help

# Test analysis on example file
python3 -m code_quality_agent.cli.main analyze examples/simple_module.py
```

Expected output should show:
- Analysis summary with issues found
- Quality score
- Recommendations

### Step 2: Test Web Interface

#### Start the Backend Server

```bash
# Start FastAPI backend
python3 -m code_quality_agent.web.api
```

The backend will start on `http://localhost:8000`

#### Start the Frontend (in a new terminal)

```bash
# Navigate to frontend directory
cd code_quality_agent/web/frontend

# Start development server
npm run dev
```

The frontend will start on `http://localhost:3001`

#### Test Web Interface

1. Open your browser and go to `http://localhost:3001`
2. Upload the `examples/simple_module.py` file
3. Click "Start Analysis"
4. Verify you get the same results as CLI

## 📁 Project Structure

```
code-quality-agent/
├── code_quality_agent/          # Main package
│   ├── analyzers/               # Quality analyzers
│   ├── cli/                     # Command line interface
│   ├── core/                    # Core functionality
│   ├── llm/                     # LLM integration
│   ├── parsers/                 # Code parsers
│   ├── web/                     # Web interface
│   │   ├── api.py              # FastAPI backend
│   │   └── frontend/           # React frontend
│   └── ...
├── examples/                    # Example files
├── docs/                        # Documentation
├── tests/                       # Test files
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project configuration
└── README.md                   # Main documentation
```

## 🔍 Usage Examples

### Command Line Interface

```bash
# Analyze a single file
python3 -m code_quality_agent.cli.main analyze examples/simple_module.py

# Analyze with JSON output
python3 -m code_quality_agent.cli.main analyze examples/simple_module.py --output-format json

# Analyze without cache
python3 -m code_quality_agent.cli.main analyze examples/simple_module.py --no-cache

# Analyze with specific categories
python3 -m code_quality_agent.cli.main analyze examples/simple_module.py --categories security,performance
```

### Web Interface

1. **Local File Analysis**:
   - Click "Upload Files"
   - Select your Python/JavaScript files
   - Click "Start Analysis"

2. **GitHub Repository Analysis**:
   - Select "GitHub Repository"
   - Enter repository URL
   - Click "Start Analysis"

3. **Local Path Analysis**:
   - Select "Local Path"
   - Enter path to your code directory
   - Click "Start Analysis"

## 🐛 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# If you get import errors, ensure you're in the virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Reinstall the package
pip install -e .
```

#### 2. API Key Issues
```bash
# Check if API key is set
echo $OPENAI_API_KEY

# If not set, add to your .env file or export directly
export OPENAI_API_KEY="your_key_here"
```

#### 3. Port Conflicts
```bash
# If port 8000 is busy, kill existing processes
lsof -ti:8000 | xargs kill -9

# If port 3001 is busy, kill existing processes
lsof -ti:3001 | xargs kill -9
```

#### 4. Node.js Issues
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules
npm install
```

#### 5. Python Dependencies Issues
```bash
# Update pip and reinstall
pip install --upgrade pip
pip install --upgrade -r requirements.txt
```

### Debug Mode

Enable debug mode for more detailed output:

```bash
# Set debug environment variable
export CQA_DEBUG=1

# Run with verbose output
python3 -m code_quality_agent.cli.main analyze examples/simple_module.py --verbose
```

## 🔄 Development Setup

If you want to contribute to the project:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black .
flake8 .
mypy .

# Run type checking
mypy code_quality_agent/
```

## 📚 Next Steps

1. **Read the Documentation**: Check out `docs/` directory for detailed guides
2. **Try Examples**: Analyze the files in `examples/` directory
3. **Explore Features**: Try different analysis options and categories
4. **Web Interface**: Use the web UI for team collaboration
5. **CI/CD Integration**: Set up automated analysis in your pipeline

## 🆘 Getting Help

If you encounter issues:

1. Check this setup guide first
2. Look at the [FAQ](README.md#faq) in the main README
3. Check existing [GitHub Issues](https://github.com/your-repo/issues)
4. Create a new issue with:
   - Your operating system and Python version
   - Complete error message
   - Steps to reproduce the issue

## ✅ Verification Checklist

Before proceeding, ensure you can:

- [ ] Run CLI analysis successfully
- [ ] Access web interface at `http://localhost:3001`
- [ ] Upload and analyze files through web interface
- [ ] Get consistent results between CLI and web interface
- [ ] See quality scores and issue recommendations

Once all items are checked, you're ready to use the Code Quality Intelligence Agent! 🎉
