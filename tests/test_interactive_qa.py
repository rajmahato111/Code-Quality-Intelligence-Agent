"""Integration tests for interactive Q&A mode."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import sys

from code_quality_agent.cli.interactive import InteractiveQAShell, start_interactive_qa
from code_quality_agent.core.models import AnalysisResult, ParsedFile, QualityMetrics, Issue, IssueCategory, Severity, CodeLocation
from code_quality_agent.rag.qa_engine import QAEngine, ConversationContext, CodebaseContext, QAPair, QuestionType


class TestInteractiveQAShell:
    """Test interactive Q&A shell functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create sample analysis result
        self.parsed_file = ParsedFile(
            path="/test/example.py",
            language="python",
            content="def test_function():\n    return True",
            ast=None
        )
        
        self.sample_issue = Issue(
            id="test-issue-1",
            category=IssueCategory.SECURITY,
            severity=Severity.HIGH,
            title="Test Security Issue",
            description="This is a test security issue",
            location=CodeLocation(
                file_path="/test/example.py",
                line_start=1,
                line_end=2
            ),
            affected_files=["/test/example.py"],
            suggestion="Fix this issue by doing X",
            confidence=0.9
        )
        
        self.analysis_result = AnalysisResult(
            analysis_id="test-analysis",
            codebase_path="/test/project",
            parsed_files=[self.parsed_file],
            issues=[self.sample_issue],
            metrics=QualityMetrics(overall_score=75.0)
        )
    
    def test_shell_initialization(self):
        """Test shell initialization with mocked Q&A engine."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    with patch('code_quality_agent.cli.interactive.console'):  # Suppress output during init
                        # Mock Q&A engine
                        mock_qa_engine = Mock(spec=QAEngine)
                        mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                        mock_create_qa.return_value = mock_qa_engine
                        
                        shell = InteractiveQAShell(self.analysis_result)
                        
                        assert shell.analysis_result == self.analysis_result
                        assert shell.conversation_id == "test-conversation-id"
                        assert shell.qa_engine == mock_qa_engine
                        assert not shell.running
                        assert len(shell.commands) > 0
    
    def test_command_processing(self):
        """Test command processing functionality."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    with patch('code_quality_agent.cli.interactive.console'):  # Suppress output during init
                        mock_qa_engine = Mock(spec=QAEngine)
                        mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                        mock_create_qa.return_value = mock_qa_engine
                        
                        shell = InteractiveQAShell(self.analysis_result)
                        
                        # Test help command by mocking the commands dictionary
                        mock_help = Mock()
                        shell.commands['help'] = mock_help
                        shell._process_input('/help')
                        mock_help.assert_called_once_with([])
                        
                        # Test command with arguments
                        mock_focus = Mock()
                        shell.commands['focus'] = mock_focus
                        shell._process_input('/focus example.py')
                        mock_focus.assert_called_once_with(['example.py'])
                        
                        # Test unknown command
                        with patch('code_quality_agent.cli.interactive.console') as mock_console:
                            shell._process_input('/unknown')
                            mock_console.print.assert_called()
    
    def test_question_handling(self):
        """Test question handling functionality."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    mock_qa_engine = Mock(spec=QAEngine)
                    mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                    mock_qa_engine.ask_question.return_value = ("This is a test answer", 0.85)
                    mock_create_qa.return_value = mock_qa_engine
                    
                    shell = InteractiveQAShell(self.analysis_result)
                    
                    with patch.object(shell, '_display_answer') as mock_display:
                        shell._handle_question("What security issues were found?")
                        
                        mock_qa_engine.ask_question.assert_called_once_with(
                            "What security issues were found?", "test-conversation-id"
                        )
                        mock_display.assert_called_once_with(
                            "What security issues were found?", "This is a test answer", 0.85
                        )
    
    def test_navigation_commands(self):
        """Test navigation command functionality."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    mock_qa_engine = Mock(spec=QAEngine)
                    mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                    mock_qa_engine.navigate_to_code.return_value = True
                    mock_qa_engine.navigate_back.return_value = True
                    mock_qa_engine.get_current_focus.return_value = None
                    mock_create_qa.return_value = mock_qa_engine
                    
                    shell = InteractiveQAShell(self.analysis_result)
                    
                    # Test focus command
                    with patch('code_quality_agent.cli.interactive.console') as mock_console:
                        shell._cmd_focus(['example.py'])
                        mock_qa_engine.navigate_to_code.assert_called_once_with(
                            "test-conversation-id", "example.py"
                        )
                    
                    # Test navigate command
                    shell._cmd_navigate(['example.py', 'test_function'])
                    mock_qa_engine.navigate_to_code.assert_called_with(
                        "test-conversation-id", "example.py", "test_function", None
                    )
                    
                    # Test back command
                    shell._cmd_back([])
                    mock_qa_engine.navigate_back.assert_called_once_with("test-conversation-id")
    
    def test_history_and_stats_commands(self):
        """Test history and statistics commands."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    mock_qa_engine = Mock(spec=QAEngine)
                    mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                    
                    # Mock conversation history
                    mock_qa_pair = QAPair(
                        question="Test question",
                        answer="Test answer",
                        question_type=QuestionType.GENERAL,
                        timestamp=Mock(),
                        confidence=0.8
                    )
                    mock_qa_engine.get_conversation_history.return_value = [mock_qa_pair]
                    
                    # Mock statistics
                    mock_qa_engine.get_statistics.return_value = {
                        "active_conversations": 1,
                        "total_questions": 5,
                        "average_confidence": 0.75,
                        "question_types": {"general": 3, "code_specific": 2}
                    }
                    
                    mock_create_qa.return_value = mock_qa_engine
                    
                    shell = InteractiveQAShell(self.analysis_result)
                    
                    # Test history command
                    with patch('code_quality_agent.cli.interactive.console') as mock_console:
                        shell._cmd_history([])
                        mock_qa_engine.get_conversation_history.assert_called_once_with("test-conversation-id")
                        mock_console.print.assert_called()
                    
                    # Test stats command
                    with patch('code_quality_agent.cli.interactive.console') as mock_console:
                        shell._cmd_stats([])
                        mock_qa_engine.get_statistics.assert_called_once()
                        mock_console.print.assert_called()
    
    def test_help_command(self):
        """Test help command functionality."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    mock_qa_engine = Mock(spec=QAEngine)
                    mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                    mock_create_qa.return_value = mock_qa_engine
                    
                    shell = InteractiveQAShell(self.analysis_result)
                    
                    with patch('code_quality_agent.cli.interactive.console') as mock_console:
                        shell._cmd_help([])
                        
                        # Verify that help information was displayed
                        assert mock_console.print.call_count >= 2  # Table + examples
    
    def test_exit_command(self):
        """Test exit command functionality."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    mock_qa_engine = Mock(spec=QAEngine)
                    mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                    mock_create_qa.return_value = mock_qa_engine
                    
                    shell = InteractiveQAShell(self.analysis_result)
                    shell.running = True
                    
                    shell._cmd_exit([])
                    
                    assert not shell.running
    
    def test_suggestions_command(self):
        """Test suggestions command functionality."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    mock_qa_engine = Mock(spec=QAEngine)
                    mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                    mock_qa_engine.suggest_related_code.return_value = [
                        "/test/example.py:10",
                        "/test/utils.py:25"
                    ]
                    mock_create_qa.return_value = mock_qa_engine
                    
                    shell = InteractiveQAShell(self.analysis_result)
                    
                    with patch('code_quality_agent.cli.interactive.console') as mock_console:
                        shell._cmd_suggestions([])
                        
                        mock_qa_engine.suggest_related_code.assert_called_once_with("test-conversation-id")
                        mock_console.print.assert_called()
    
    def test_answer_display_with_different_confidence_levels(self):
        """Test answer display with different confidence levels."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    mock_qa_engine = Mock(spec=QAEngine)
                    mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                    mock_create_qa.return_value = mock_qa_engine
                    
                    shell = InteractiveQAShell(self.analysis_result)
                    
                    with patch('code_quality_agent.cli.interactive.console') as mock_console:
                        # Test high confidence
                        shell._display_answer("Test question", "Test answer", 0.9)
                        mock_console.print.assert_called()
                        
                        # Test low confidence (should show suggestions)
                        with patch.object(shell, '_show_suggestions') as mock_suggestions:
                            shell._display_answer("Test question", "Test answer", 0.4)
                            mock_suggestions.assert_called_once()
    
    def test_readline_setup(self):
        """Test readline setup functionality."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    with patch('code_quality_agent.cli.interactive.READLINE_AVAILABLE', True):
                        with patch('code_quality_agent.cli.interactive.readline') as mock_readline:
                            mock_qa_engine = Mock(spec=QAEngine)
                            mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                            mock_create_qa.return_value = mock_qa_engine
                            
                            shell = InteractiveQAShell(self.analysis_result)
                            
                            # Verify readline was configured
                            mock_readline.set_history_length.assert_called_once_with(1000)
                            mock_readline.set_completer.assert_called_once()
                            mock_readline.parse_and_bind.assert_called()
    
    def test_completer_functionality(self):
        """Test auto-completion functionality."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    mock_qa_engine = Mock(spec=QAEngine)
                    mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                    mock_create_qa.return_value = mock_qa_engine
                    
                    shell = InteractiveQAShell(self.analysis_result)
                    
                    # Test command completion
                    result = shell._completer('/he', 0)
                    assert result == '/help'
                    
                    # Test question starter completion
                    result = shell._completer('What', 0)
                    assert result == 'What is'
                    
                    # Test completion with non-matching text
                    result = shell._completer('/xyz', 0)
                    assert result is None
                    
                    # Test completion beyond available matches
                    result = shell._completer('Xyz', 0)
                    assert result is None


class TestInteractiveQAIntegration:
    """Integration tests for interactive Q&A functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "test_project"
        self.project_dir.mkdir()
        
        # Create test files
        (self.project_dir / "main.py").write_text("""
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")
        
        # Create sample analysis result
        parsed_file = ParsedFile(
            path=str(self.project_dir / "main.py"),
            language="python",
            content="def main():\n    print('Hello, World!')",
            ast=None
        )
        
        self.analysis_result = AnalysisResult(
            analysis_id="integration-test",
            codebase_path=str(self.project_dir),
            parsed_files=[parsed_file],
            issues=[],
            metrics=QualityMetrics(overall_score=90.0)
        )
    
    def test_start_interactive_qa_success(self):
        """Test successful start of interactive Q&A session."""
        with patch('code_quality_agent.cli.interactive.InteractiveQAShell') as mock_shell_class:
            mock_shell = Mock()
            mock_shell_class.return_value = mock_shell
            
            start_interactive_qa(self.analysis_result)
            
            mock_shell_class.assert_called_once_with(self.analysis_result)
            mock_shell.start.assert_called_once()
    
    def test_start_interactive_qa_keyboard_interrupt(self):
        """Test handling of keyboard interrupt during Q&A session."""
        with patch('code_quality_agent.cli.interactive.InteractiveQAShell') as mock_shell_class:
            mock_shell = Mock()
            mock_shell.start.side_effect = KeyboardInterrupt()
            mock_shell_class.return_value = mock_shell
            
            with patch('code_quality_agent.cli.interactive.console') as mock_console:
                start_interactive_qa(self.analysis_result)
                
                mock_console.print.assert_called_with("\n[yellow]Q&A session interrupted[/yellow]")
    
    def test_start_interactive_qa_error_handling(self):
        """Test error handling during Q&A session start."""
        with patch('code_quality_agent.cli.interactive.InteractiveQAShell') as mock_shell_class:
            mock_shell_class.side_effect = Exception("Test error")
            
            with patch('code_quality_agent.cli.interactive.console') as mock_console:
                with pytest.raises(Exception):
                    start_interactive_qa(self.analysis_result)
                
                mock_console.print.assert_called()


class TestInteractiveQACommands:
    """Test specific interactive Q&A commands in detail."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analysis_result = AnalysisResult(
            analysis_id="command-test",
            codebase_path="/test/project",
            parsed_files=[],
            issues=[],
            metrics=QualityMetrics(overall_score=80.0)
        )
    
    def test_clear_command(self):
        """Test clear command functionality."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    with patch('code_quality_agent.cli.interactive.os.system') as mock_system:
                        mock_qa_engine = Mock(spec=QAEngine)
                        mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                        mock_create_qa.return_value = mock_qa_engine
                        
                        shell = InteractiveQAShell(self.analysis_result)
                        
                        with patch.object(shell, '_display_welcome') as mock_welcome:
                            shell._cmd_clear([])
                            
                            mock_system.assert_called_once()
                            mock_welcome.assert_called_once()
    
    def test_summary_command(self):
        """Test summary command functionality."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    mock_qa_engine = Mock(spec=QAEngine)
                    mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                    mock_qa_engine.get_conversation_context_summary.return_value = "Test summary"
                    mock_create_qa.return_value = mock_qa_engine
                    
                    shell = InteractiveQAShell(self.analysis_result)
                    
                    with patch('code_quality_agent.cli.interactive.console') as mock_console:
                        shell._cmd_summary([])
                        
                        mock_qa_engine.get_conversation_context_summary.assert_called_once_with("test-conversation-id")
                        mock_console.print.assert_called()
    
    def test_focus_command_without_args(self):
        """Test focus command without arguments (show current focus)."""
        with patch('code_quality_agent.cli.interactive.create_qa_engine') as mock_create_qa:
            with patch('code_quality_agent.cli.interactive.VectorStoreManager'):
                with patch('code_quality_agent.cli.interactive.create_llm_service'):
                    from code_quality_agent.rag.qa_engine import CodeLocationFocus
                    
                    mock_qa_engine = Mock(spec=QAEngine)
                    mock_qa_engine.index_codebase.return_value = "test-conversation-id"
                    mock_focus = CodeLocationFocus(
                        file_path="/test/example.py",
                        function_name="test_func",
                        context_type="function"
                    )
                    mock_qa_engine.get_current_focus.return_value = mock_focus
                    mock_create_qa.return_value = mock_qa_engine
                    
                    shell = InteractiveQAShell(self.analysis_result)
                    
                    with patch('code_quality_agent.cli.interactive.console') as mock_console:
                        shell._cmd_focus([])
                        
                        mock_qa_engine.get_current_focus.assert_called_once_with("test-conversation-id")
                        mock_console.print.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])