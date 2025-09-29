#!/usr/bin/env python3
"""
Setup Verification Script for Code Quality Intelligence Agent

This script verifies that the installation is working correctly.
Run this after following the setup instructions.
"""

import sys
import subprocess
import os
from pathlib import Path
import importlib.util

def print_status(message, status="INFO"):
    """Print colored status messages."""
    colors = {
        "INFO": "\033[94m",    # Blue
        "SUCCESS": "\033[92m", # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "RESET": "\033[0m"     # Reset
    }
    
    color = colors.get(status, colors["INFO"])
    reset = colors["RESET"]
    print(f"{color}[{status}]{reset} {message}")

def check_python_version():
    """Check Python version."""
    print_status("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - OK", "SUCCESS")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - Need Python 3.9+", "ERROR")
        return False

def check_virtual_environment():
    """Check if running in virtual environment."""
    print_status("Checking virtual environment...")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_status("Virtual environment detected - OK", "SUCCESS")
        return True
    else:
        print_status("Not in virtual environment - RECOMMENDED but not required", "WARNING")
        return True

def check_package_installation():
    """Check if the package is installed."""
    print_status("Checking package installation...")
    try:
        import code_quality_agent
        print_status("Code Quality Agent package found - OK", "SUCCESS")
        return True
    except ImportError:
        print_status("Code Quality Agent package not found - Run 'pip install -e .'", "ERROR")
        return False

def check_dependencies():
    """Check critical dependencies."""
    print_status("Checking critical dependencies...")
    critical_deps = [
        "click", "rich", "tree_sitter", "fastapi", 
        "langchain", "chromadb", "openai", "anthropic"
    ]
    
    missing = []
    for dep in critical_deps:
        try:
            importlib.import_module(dep)
        except ImportError:
            missing.append(dep)
    
    if not missing:
        print_status("All critical dependencies found - OK", "SUCCESS")
        return True
    else:
        print_status(f"Missing dependencies: {', '.join(missing)}", "ERROR")
        print_status("Run: pip install -r requirements.txt", "INFO")
        return False

def check_cli_functionality():
    """Test CLI functionality."""
    print_status("Testing CLI functionality...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "code_quality_agent.cli.main", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print_status("CLI help command works - OK", "SUCCESS")
            return True
        else:
            print_status(f"CLI help failed: {result.stderr}", "ERROR")
            return False
    except Exception as e:
        print_status(f"CLI test failed: {e}", "ERROR")
        return False

def check_test_files():
    """Check if test files exist."""
    print_status("Checking test files...")
    test_files = [
        "test_security/vulnerable_code.py",
        "test_simple_no_tests/simple.py",
        "test_performance/slow_code.py"
    ]
    
    missing_files = []
    for file_path in test_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if not missing_files:
        print_status("All test files found - OK", "SUCCESS")
        return True
    else:
        print_status(f"Missing test files: {', '.join(missing_files)}", "WARNING")
        return True

def test_basic_analysis():
    """Test basic analysis functionality."""
    print_status("Testing basic analysis...")
    
    # Check if test file exists
    test_file = "test_security/vulnerable_code.py"
    if not Path(test_file).exists():
        print_status("Test file not found, skipping analysis test", "WARNING")
        return True
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "code_quality_agent.cli.main", 
            "analyze", test_file, "--max-issues", "3"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and "Analysis Summary" in result.stdout:
            print_status("Basic analysis works - OK", "SUCCESS")
            return True
        else:
            print_status("Basic analysis failed - Check dependencies", "WARNING")
            print_status(f"Error: {result.stderr[:200]}...", "INFO")
            return False
    except Exception as e:
        print_status(f"Analysis test failed: {e}", "WARNING")
        return False

def check_api_keys():
    """Check for API keys."""
    print_status("Checking API keys...")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if openai_key:
        print_status("OpenAI API key found - AI features enabled", "SUCCESS")
        return True
    elif anthropic_key:
        print_status("Anthropic API key found - AI features enabled", "SUCCESS")
        return True
    else:
        print_status("No API keys found - Basic features only", "WARNING")
        print_status("Set OPENAI_API_KEY or ANTHROPIC_API_KEY for AI features", "INFO")
        return True

def check_web_dependencies():
    """Check web interface dependencies."""
    print_status("Checking web interface...")
    
    # Check if Node.js is available
    try:
        result = subprocess.run(["node", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_status(f"Node.js {result.stdout.strip()} found - OK", "SUCCESS")
            
            # Check if frontend dependencies are installed
            frontend_dir = Path("code_quality_agent/web/frontend")
            if frontend_dir.exists() and (frontend_dir / "node_modules").exists():
                print_status("Frontend dependencies installed - OK", "SUCCESS")
                return True
            else:
                print_status("Frontend dependencies not installed", "WARNING")
                print_status("Run: cd code_quality_agent/web/frontend && npm install", "INFO")
                return True
        else:
            print_status("Node.js not found - Web interface unavailable", "WARNING")
            return True
    except Exception:
        print_status("Node.js not found - Web interface unavailable", "WARNING")
        return True

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("🔍 Code Quality Intelligence Agent - Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Package Installation", check_package_installation),
        ("Dependencies", check_dependencies),
        ("CLI Functionality", check_cli_functionality),
        ("Test Files", check_test_files),
        ("Basic Analysis", test_basic_analysis),
        ("API Keys", check_api_keys),
        ("Web Dependencies", check_web_dependencies),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_status(f"Check failed with exception: {e}", "ERROR")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print_status("🎉 All checks passed! Your setup is ready.", "SUCCESS")
        print_status("Try: python3 -m code_quality_agent.cli.main analyze test_security/vulnerable_code.py", "INFO")
    elif passed >= total - 2:
        print_status("✅ Setup is mostly ready! Check warnings above.", "SUCCESS")
    else:
        print_status("⚠️  Setup needs attention. Please fix the errors above.", "WARNING")
    
    print("\n📚 For help, see:")
    print("  - QUICK_START_GUIDE.md (setup instructions)")
    print("  - README.md (complete documentation)")
    print("  - docs/ directory (detailed guides)")

if __name__ == "__main__":
    main()
