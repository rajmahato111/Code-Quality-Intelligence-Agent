# Test Fixtures for Code Quality Intelligence Agent

This directory contains test data and fixtures for comprehensive testing of the Code Quality Intelligence Agent.

## Structure

- `synthetic_samples/` - Synthetic code samples with known quality issues
- `real_world_samples/` - Curated real-world code samples
- `analysis_scenarios/` - Test fixtures for different analysis scenarios
- `expected_results/` - Expected analysis results for validation

## Usage

These fixtures are used by the test suite to validate analyzer accuracy, test different scenarios, and ensure consistent behavior across different types of codebases.

## Test Data Categories

### Security Issues
- SQL injection vulnerabilities
- Cross-site scripting (XSS) vulnerabilities
- Hardcoded credentials
- Unsafe deserialization
- Command injection

### Performance Issues
- Inefficient algorithms
- Memory leaks
- Unnecessary computations
- Poor data structure choices

### Code Quality Issues
- High complexity functions
- Code duplication
- Missing documentation
- Unused variables/functions
- Poor naming conventions

### Testing Issues
- Missing test coverage
- Inadequate test cases
- Test code smells