"""Unit tests for CLI interface."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from code_quality_agent.cli.main import cli, create_analysis_options
from code_quality_agent.core.models import AnalysisOptions, AnalysisResult, QualityMetrics, Severity, IssueCategory


class TestCLIArgumentParsing:
    """Test CLI argument parsing and validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.py"
        self.test_file.write_text("def hello():\n    print('Hello, World!')")
    
    def test_cli_help(self):
        """Test CLI help output."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Code Quality Intelligence Agent" in result.output
        assert "analyze" in result.output
    
    def test_analyze_help(self):
        """Test analyze command help."""
        result = self.runner.invoke(cli, ['analyze', '--help'])
        assert result.exit_code == 0
        assert "Analyze code quality" in result.output
        assert "--output-format" in result.output
        assert "--languages" in result.output
    
    def test_analyze_basic_command(self):
        """Test basic analyze command with mocked orchestrator."""
        with patch('code_quality_agent.cli.main.AnalysisOrchestrator') as mock_orchestrator_class:
            # Mock the orchestrator and its methods
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Create a mock analysis result
            mock_result = AnalysisResult(
                analysis_id="test-123",
                codebase_path=str(self.test_file),
                parsed_files=[],
                issues=[],
                metrics=QualityMetrics(overall_score=85.0)
            )
            mock_orchestrator.analyze_codebase.return_value = mock_result
            
            # Mock report generator
            with patch('code_quality_agent.cli.main.ReportGenerator') as mock_report_gen:
                mock_report = Mock()
                mock_report_gen.return_value.generate_report.return_value = mock_report
                
                # Mock formatters
                with patch('code_quality_agent.cli.main.TextFormatter') as mock_formatter:
                    mock_formatter.return_value.format_report.return_value = "Test report"
                    
                    result = self.runner.invoke(cli, ['analyze', str(self.test_file)])
                    
                    assert result.exit_code == 0
                    assert "Analysis Started" in result.output
                    assert "Analysis complete!" in result.output
    
    def test_analyze_with_output_format_json(self):
        """Test analyze command with JSON output format."""
        with patch('code_quality_agent.cli.main.AnalysisOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_result = AnalysisResult(
                analysis_id="test-123",
                codebase_path=str(self.test_file),
                parsed_files=[],
                issues=[],
                metrics=QualityMetrics(overall_score=85.0)
            )
            mock_orchestrator.analyze_codebase.return_value = mock_result
            
            with patch('code_quality_agent.cli.main.ReportGenerator') as mock_report_gen:
                mock_report = Mock()
                mock_report_gen.return_value.generate_report.return_value = mock_report
                
                with patch('code_quality_agent.cli.main.JSONFormatter') as mock_formatter:
                    mock_formatter.return_value.format_report.return_value = '{"test": "report"}'
                    
                    result = self.runner.invoke(cli, [
                        'analyze', str(self.test_file),
                        '--output-format', 'json'
                    ])
                    
                    assert result.exit_code == 0
                    assert "JSON report saved to:" in result.output
    
    def test_analyze_with_languages_filter(self):
        """Test analyze command with language filtering."""
        with patch('code_quality_agent.cli.main.AnalysisOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_result = AnalysisResult(
                analysis_id="test-123",
                codebase_path=str(self.test_file),
                parsed_files=[],
                issues=[],
                metrics=QualityMetrics(overall_score=85.0)
            )
            mock_orchestrator.analyze_codebase.return_value = mock_result
            
            with patch('code_quality_agent.cli.main.ReportGenerator') as mock_report_gen:
                mock_report = Mock()
                mock_report_gen.return_value.generate_report.return_value = mock_report
                
                with patch('code_quality_agent.cli.main.TextFormatter') as mock_formatter:
                    mock_formatter.return_value.format_report.return_value = "Test report"
                    
                    result = self.runner.invoke(cli, [
                        'analyze', str(self.test_file),
                        '--languages', 'python',
                        '--languages', 'javascript'
                    ])
                    
                    assert result.exit_code == 0
                    # Verify that the orchestrator was called with the right options
                    mock_orchestrator.analyze_codebase.assert_called_once()
                    call_args = mock_orchestrator.analyze_codebase.call_args
                    options = call_args[0][1]  # Second argument is options
                    assert '*.py' in options.include_patterns
                    assert '*.js' in options.include_patterns
                    assert '*.jsx' in options.include_patterns
    
    def test_analyze_with_custom_patterns(self):
        """Test analyze command with custom include/exclude patterns."""
        with patch('code_quality_agent.cli.main.AnalysisOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_result = AnalysisResult(
                analysis_id="test-123",
                codebase_path=str(self.test_file),
                parsed_files=[],
                issues=[],
                metrics=QualityMetrics(overall_score=85.0)
            )
            mock_orchestrator.analyze_codebase.return_value = mock_result
            
            with patch('code_quality_agent.cli.main.ReportGenerator') as mock_report_gen:
                mock_report = Mock()
                mock_report_gen.return_value.generate_report.return_value = mock_report
                
                with patch('code_quality_agent.cli.main.TextFormatter') as mock_formatter:
                    mock_formatter.return_value.format_report.return_value = "Test report"
                    
                    result = self.runner.invoke(cli, [
                        'analyze', str(self.test_file),
                        '--include-patterns', 'src/**/*.py',
                        '--exclude-patterns', '*.test.py'
                    ])
                    
                    assert result.exit_code == 0
                    # Verify patterns were passed correctly
                    mock_orchestrator.analyze_codebase.assert_called_once()
                    call_args = mock_orchestrator.analyze_codebase.call_args
                    options = call_args[0][1]
                    assert 'src/**/*.py' in options.include_patterns
                    assert '*.test.py' in options.exclude_patterns
    
    def test_analyze_with_severity_and_categories(self):
        """Test analyze command with severity and category filters."""
        with patch('code_quality_agent.cli.main.AnalysisOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_result = AnalysisResult(
                analysis_id="test-123",
                codebase_path=str(self.test_file),
                parsed_files=[],
                issues=[],
                metrics=QualityMetrics(overall_score=85.0)
            )
            mock_orchestrator.analyze_codebase.return_value = mock_result
            
            with patch('code_quality_agent.cli.main.ReportGenerator') as mock_report_gen:
                mock_report = Mock()
                mock_report_gen.return_value.generate_report.return_value = mock_report
                
                with patch('code_quality_agent.cli.main.TextFormatter') as mock_formatter:
                    mock_formatter.return_value.format_report.return_value = "Test report"
                    
                    result = self.runner.invoke(cli, [
                        'analyze', str(self.test_file),
                        '--min-severity', 'high',
                        '--categories', 'security',
                        '--categories', 'performance'
                    ])
                    
                    assert result.exit_code == 0
    
    def test_analyze_with_performance_options(self):
        """Test analyze command with performance-related options."""
        with patch('code_quality_agent.cli.main.AnalysisOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_result = AnalysisResult(
                analysis_id="test-123",
                codebase_path=str(self.test_file),
                parsed_files=[],
                issues=[],
                metrics=QualityMetrics(overall_score=85.0)
            )
            mock_orchestrator.analyze_codebase.return_value = mock_result
            
            with patch('code_quality_agent.cli.main.ReportGenerator') as mock_report_gen:
                mock_report = Mock()
                mock_report_gen.return_value.generate_report.return_value = mock_report
                
                with patch('code_quality_agent.cli.main.TextFormatter') as mock_formatter:
                    mock_formatter.return_value.format_report.return_value = "Test report"
                    
                    result = self.runner.invoke(cli, [
                        'analyze', str(self.test_file),
                        '--max-workers', '8',
                        '--confidence-threshold', '0.8',
                        '--no-cache',
                        '--no-explanations',
                        '--no-suggestions'
                    ])
                    
                    assert result.exit_code == 0
                    # Verify options were set correctly
                    mock_orchestrator.analyze_codebase.assert_called_once()
                    call_args = mock_orchestrator.analyze_codebase.call_args
                    options = call_args[0][1]
                    assert options.max_workers == 8
                    assert options.confidence_threshold == 0.8
                    assert not options.include_explanations
                    assert not options.include_suggestions
    
    def test_analyze_invalid_confidence_threshold(self):
        """Test analyze command with invalid confidence threshold."""
        result = self.runner.invoke(cli, [
            'analyze', str(self.test_file),
            '--confidence-threshold', '1.5'
        ])
        
        assert result.exit_code == 1
        assert "Confidence threshold must be between 0.0 and 1.0" in result.output
    
    def test_analyze_invalid_max_workers(self):
        """Test analyze command with invalid max workers."""
        result = self.runner.invoke(cli, [
            'analyze', str(self.test_file),
            '--max-workers', '0'
        ])
        
        assert result.exit_code == 1
        assert "Max workers must be at least 1" in result.output
    
    def test_analyze_nonexistent_path(self):
        """Test analyze command with non-existent path."""
        result = self.runner.invoke(cli, ['analyze', '/nonexistent/path'])
        
        assert result.exit_code == 2  # Click's exit code for bad parameter
        assert "does not exist" in result.output
    
    def test_info_command(self):
        """Test info command."""
        with patch('code_quality_agent.core.file_discovery.discover_files') as mock_discover:
            mock_discover.return_value = [str(self.test_file)]
            
            result = self.runner.invoke(cli, ['info', str(self.test_file.parent)])
            
            assert result.exit_code == 0
            assert "Codebase Information" in result.output
            assert "Total Files" in result.output
    
    def test_verbose_flag(self):
        """Test verbose flag functionality."""
        with patch('code_quality_agent.cli.main.AnalysisOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_result = AnalysisResult(
                analysis_id="test-123",
                codebase_path=str(self.test_file),
                parsed_files=[],
                issues=[],
                metrics=QualityMetrics(overall_score=85.0)
            )
            mock_orchestrator.analyze_codebase.return_value = mock_result
            
            with patch('code_quality_agent.cli.main.ReportGenerator') as mock_report_gen:
                mock_report = Mock()
                mock_report_gen.return_value.generate_report.return_value = mock_report
                
                with patch('code_quality_agent.cli.main.TextFormatter') as mock_formatter:
                    mock_formatter.return_value.format_report.return_value = "Test report"
                    
                    result = self.runner.invoke(cli, [
                        '--verbose',
                        'analyze', str(self.test_file)
                    ])
                    
                    assert result.exit_code == 0
    
    def test_qa_command(self):
        """Test Q&A command functionality."""
        with patch('code_quality_agent.cli.main.AnalysisOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_result = AnalysisResult(
                analysis_id="test-qa",
                codebase_path=str(self.test_file),
                parsed_files=[],
                issues=[],
                metrics=QualityMetrics(overall_score=85.0)
            )
            mock_orchestrator.analyze_codebase.return_value = mock_result
            
            with patch('code_quality_agent.cli.main.start_interactive_qa') as mock_qa:
                result = self.runner.invoke(cli, ['qa', str(self.test_file)])
                
                assert result.exit_code == 0
                mock_qa.assert_called_once_with(mock_result)
                assert "Analysis & Q&A Setup" in result.output
                assert "Starting interactive Q&A session" in result.output


class TestAnalysisOptionsCreation:
    """Test analysis options creation from CLI parameters."""
    
    def test_default_options(self):
        """Test creating default analysis options."""
        options = create_analysis_options()
        
        assert options.include_patterns == ['*.py', '*.js', '*.ts', '*.jsx', '*.tsx']
        assert 'node_modules/**' in options.exclude_patterns
        assert '.git/**' in options.exclude_patterns
        assert options.max_workers == 4
        assert options.confidence_threshold == 0.7
        assert options.include_explanations is True
        assert options.include_suggestions is True
    
    def test_language_filtering(self):
        """Test language-specific pattern filtering."""
        options = create_analysis_options(languages=['python'])
        
        assert options.include_patterns == ['*.py']
        
        options = create_analysis_options(languages=['javascript', 'typescript'])
        
        expected_patterns = ['*.js', '*.jsx', '*.ts', '*.tsx']
        assert all(pattern in options.include_patterns for pattern in expected_patterns)
    
    def test_custom_patterns(self):
        """Test custom include/exclude patterns."""
        options = create_analysis_options(
            include_patterns=['src/**/*.py'],
            exclude_patterns=['*.test.py']
        )
        
        assert 'src/**/*.py' in options.include_patterns
        assert '*.test.py' in options.exclude_patterns
        # Should still include default exclude patterns
        assert 'node_modules/**' in options.exclude_patterns
    
    def test_performance_options(self):
        """Test performance-related options."""
        options = create_analysis_options(
            max_workers=8,
            confidence_threshold=0.9,
            include_explanations=False,
            include_suggestions=False
        )
        
        assert options.max_workers == 8
        assert options.confidence_threshold == 0.9
        assert options.include_explanations is False
        assert options.include_suggestions is False
        assert options.parallel_processing is True  # Should be True when max_workers > 1
        
        # Test single worker
        options = create_analysis_options(max_workers=1)
        assert options.parallel_processing is False


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a small test project
        self.project_dir = Path(self.temp_dir) / "test_project"
        self.project_dir.mkdir()
        
        # Create test files
        (self.project_dir / "main.py").write_text("""
def calculate_sum(a, b):
    '''Calculate sum of two numbers'''
    return a + b

if __name__ == '__main__':
    print(calculate_sum(1, 2))
""")
        
        (self.project_dir / "utils.js").write_text("""
function multiply(a, b) {
    return a * b;
}

module.exports = { multiply };
""")
    
    def test_analyze_project_directory(self):
        """Test analyzing a project directory."""
        with patch('code_quality_agent.cli.main.AnalysisOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Create mock parsed files
            from code_quality_agent.core.models import ParsedFile
            mock_parsed_files = [
                ParsedFile(
                    path=str(self.project_dir / "main.py"),
                    language="python",
                    content="def calculate_sum(a, b):\n    return a + b",
                    ast=None
                ),
                ParsedFile(
                    path=str(self.project_dir / "utils.js"),
                    language="javascript", 
                    content="function multiply(a, b) {\n    return a * b;\n}",
                    ast=None
                )
            ]
            
            mock_result = AnalysisResult(
                analysis_id="test-integration",
                codebase_path=str(self.project_dir),
                parsed_files=mock_parsed_files,
                issues=[],
                metrics=QualityMetrics(overall_score=90.0)
            )
            mock_orchestrator.analyze_codebase.return_value = mock_result
            
            with patch('code_quality_agent.cli.main.ReportGenerator') as mock_report_gen:
                mock_report = Mock()
                mock_report_gen.return_value.generate_report.return_value = mock_report
                
                with patch('code_quality_agent.cli.main.TextFormatter') as mock_formatter:
                    mock_formatter.return_value.format_report.return_value = "Integration test report"
                    
                    result = self.runner.invoke(cli, ['analyze', str(self.project_dir)])
                    
                    assert result.exit_code == 0
                    assert "Files Analyzed" in result.output
                    assert "Overall Quality Score" in result.output
    
    def test_output_file_creation(self):
        """Test that output files are created correctly."""
        with patch('code_quality_agent.cli.main.AnalysisOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_result = AnalysisResult(
                analysis_id="test-output",
                codebase_path=str(self.project_dir),
                parsed_files=[],
                issues=[],
                metrics=QualityMetrics(overall_score=85.0)
            )
            mock_orchestrator.analyze_codebase.return_value = mock_result
            
            with patch('code_quality_agent.cli.main.ReportGenerator') as mock_report_gen:
                mock_report = Mock()
                mock_report_gen.return_value.generate_report.return_value = mock_report
                
                with patch('code_quality_agent.cli.main.JSONFormatter') as mock_formatter:
                    mock_formatter.return_value.format_report.return_value = '{"test": "output"}'
                    
                    output_file = self.project_dir / "test_report.json"
                    
                    result = self.runner.invoke(cli, [
                        'analyze', str(self.project_dir),
                        '--output-format', 'json',
                        '--output-file', str(output_file)
                    ])
                    
                    assert result.exit_code == 0
                    assert output_file.exists()
                    assert json.loads(output_file.read_text()) == {"test": "output"}


if __name__ == "__main__":
    pytest.main([__file__])