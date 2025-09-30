"""Integration tests for conversation context management in Q&A Engine."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from code_quality_agent.rag.qa_engine import (
    QAEngine, ConversationContext, CodeLocationFocus, QAPair, QuestionType,
    CodebaseContext, QuestionClassifier
)
from code_quality_agent.rag.vector_store import VectorStoreManager, SearchResult, CodeChunk
from code_quality_agent.llm.llm_service import LLMService
from code_quality_agent.core.models import AnalysisResult, ParsedFile, QualityMetrics


class TestConversationContext:
    """Test conversation context management functionality."""
    
    def test_conversation_context_creation(self):
        """Test creating a conversation context."""
        codebase_context = CodebaseContext(
            codebase_path="/test/project",
            total_files=10,
            total_issues=5,
            languages=["python", "javascript"],
            quality_score=85.0
        )
        
        context = ConversationContext(
            conversation_id="test-123",
            codebase_context=codebase_context
        )
        
        assert context.conversation_id == "test-123"
        assert context.codebase_context.codebase_path == "/test/project"
        assert len(context.previous_questions) == 0
        assert context.current_focus is None
        assert len(context.focus_history) == 0
    
    def test_qa_pair_management(self):
        """Test adding and managing Q&A pairs."""
        codebase_context = CodebaseContext(
            codebase_path="/test/project",
            total_files=10,
            total_issues=5,
            languages=["python"],
            quality_score=85.0
        )
        
        context = ConversationContext(
            conversation_id="test-123",
            codebase_context=codebase_context
        )
        
        # Add Q&A pairs
        for i in range(20):  # Add more than the limit to test truncation
            qa_pair = QAPair(
                question=f"Question {i}",
                answer=f"Answer {i}",
                question_type=QuestionType.GENERAL,
                timestamp=datetime.now(),
                confidence=0.8
            )
            context.add_qa_pair(qa_pair)
        
        # Should keep only last 15 Q&A pairs
        assert len(context.previous_questions) == 15
        assert context.previous_questions[0].question == "Question 5"
        assert context.previous_questions[-1].question == "Question 19"
    
    def test_focus_management(self):
        """Test code location focus management."""
        codebase_context = CodebaseContext(
            codebase_path="/test/project",
            total_files=10,
            total_issues=5,
            languages=["python"],
            quality_score=85.0
        )
        
        context = ConversationContext(
            conversation_id="test-123",
            codebase_context=codebase_context
        )
        
        # Set initial focus
        focus1 = CodeLocationFocus(
            file_path="/test/file1.py",
            function_name="test_function",
            context_type="function"
        )
        context.set_focus(focus1)
        
        assert context.current_focus == focus1
        assert len(context.focus_history) == 0
        
        # Set another focus
        focus2 = CodeLocationFocus(
            file_path="/test/file2.py",
            class_name="TestClass",
            context_type="class"
        )
        context.set_focus(focus2)
        
        assert context.current_focus == focus2
        assert len(context.focus_history) == 1
        assert context.focus_history[0] == focus1
        
        # Test focus history limit
        for i in range(12):  # Add more than the limit
            focus = CodeLocationFocus(
                file_path=f"/test/file{i}.py",
                context_type="file"
            )
            context.set_focus(focus)
        
        # Should keep only last 10 focus locations
        assert len(context.focus_history) == 10
    
    def test_contextual_keywords_extraction(self):
        """Test extraction of contextual keywords from conversation."""
        codebase_context = CodebaseContext(
            codebase_path="/test/project",
            total_files=10,
            total_issues=5,
            languages=["python"],
            quality_score=85.0
        )
        
        context = ConversationContext(
            conversation_id="test-123",
            codebase_context=codebase_context
        )
        
        # Add Q&A pairs with technical terms
        qa_pairs = [
            QAPair(
                question="What does the authentication function do?",
                answer="The authentication function validates user credentials using JWT tokens",
                question_type=QuestionType.FUNCTION_SPECIFIC,
                timestamp=datetime.now(),
                confidence=0.9
            ),
            QAPair(
                question="How does the database connection work?",
                answer="The database connection uses SQLAlchemy ORM with connection pooling",
                question_type=QuestionType.CODE_SPECIFIC,
                timestamp=datetime.now(),
                confidence=0.8
            )
        ]
        
        for qa in qa_pairs:
            context.add_qa_pair(qa)
        
        # Set current focus
        focus = CodeLocationFocus(
            file_path="/test/auth.py",
            function_name="validate_token",
            context_type="function"
        )
        context.set_focus(focus)
        
        keywords = context.get_contextual_keywords()
        
        # Should extract technical terms and current focus
        # Check for presence of key technical terms (case insensitive)
        keywords_lower = [kw.lower() for kw in keywords]
        assert any("auth" in kw or "credential" in kw for kw in keywords_lower)  # authentication or auth-related
        assert any("database" == kw or "connection" in kw for kw in keywords_lower)  # exact match for database
        # The function name should be added from current focus
        assert "validate_token" in keywords or any("validate" in kw for kw in keywords)
        assert len(keywords) <= 10  # Respects limit


class TestQuestionClassifier:
    """Test question classification functionality."""
    
    def test_question_classification(self):
        """Test classification of different question types."""
        classifier = QuestionClassifier()
        
        test_cases = [
            ("What does this function do?", QuestionType.FUNCTION_SPECIFIC),
            ("Show me the class definition", QuestionType.CLASS_SPECIFIC),
            ("What's in this file?", QuestionType.FILE_SPECIFIC),
            ("What security issues are there?", QuestionType.ISSUE_RELATED),
            ("What's the quality score?", QuestionType.METRICS),
            ("How does this code work?", QuestionType.CODE_SPECIFIC),
            ("Tell me about the project", QuestionType.GENERAL)
        ]
        
        for question, expected_type in test_cases:
            result = classifier.classify_question(question)
            assert result == expected_type, f"Question '{question}' should be classified as {expected_type}, got {result}"


class TestQAEngineConversationManagement:
    """Test Q&A Engine conversation management features."""
    
    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store."""
        mock_store = Mock(spec=VectorStoreManager)
        
        # Mock search results
        mock_chunk = CodeChunk(
            id="test-chunk-1",
            file_path="/test/example.py",
            chunk_type="function",
            content="def test_function():\n    return True",
            start_line=10,
            end_line=12,
            metadata={"function_name": "test_function"}
        )
        
        mock_result = SearchResult(
            chunk=mock_chunk,
            similarity_score=0.8,
            distance=0.2
        )
        
        mock_store.search_code.return_value = [mock_result]
        mock_store.index_analysis_result.return_value = 5
        mock_store.get_statistics.return_value = {"total_chunks": 5}
        
        return mock_store
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service."""
        mock_llm = Mock(spec=LLMService)
        mock_llm.answer_question.return_value = "This is a test function that returns True."
        return mock_llm
    
    @pytest.fixture
    def qa_engine(self, mock_vector_store, mock_llm_service):
        """Create a Q&A engine with mocked dependencies."""
        return QAEngine(
            vector_store_manager=mock_vector_store,
            llm_service=mock_llm_service,
            max_context_chunks=5
        )
    
    @pytest.fixture
    def sample_analysis_result(self):
        """Create a sample analysis result."""
        parsed_file = ParsedFile(
            path="/test/example.py",
            language="python",
            content="def test_function():\n    return True",
            ast=None,
            functions=[],
            classes=[],
            imports=[]
        )
        
        return AnalysisResult(
            analysis_id="test-analysis",
            codebase_path="/test/project",
            parsed_files=[parsed_file],
            issues=[],
            metrics=QualityMetrics(overall_score=85.0)
        )
    
    def test_conversation_creation_and_indexing(self, qa_engine, sample_analysis_result):
        """Test creating a conversation and indexing codebase."""
        conversation_id = qa_engine.index_codebase(sample_analysis_result)
        
        assert conversation_id in qa_engine.conversations
        conversation = qa_engine.conversations[conversation_id]
        
        assert conversation.codebase_context.codebase_path == "/test/project"
        assert conversation.codebase_context.total_files == 1
        assert conversation.codebase_context.quality_score == 85.0
        assert "python" in conversation.codebase_context.languages
    
    def test_multi_turn_conversation(self, qa_engine, sample_analysis_result):
        """Test multi-turn conversation with context awareness."""
        # Index codebase
        conversation_id = qa_engine.index_codebase(sample_analysis_result)
        
        # First question
        answer1, confidence1 = qa_engine.ask_question(
            "What does the test_function do?",
            conversation_id
        )
        
        assert answer1 == "This is a test function that returns True."
        assert confidence1 > 0.0
        
        conversation = qa_engine.conversations[conversation_id]
        assert len(conversation.previous_questions) == 1
        assert conversation.previous_questions[0].question_type == QuestionType.FUNCTION_SPECIFIC
        
        # Follow-up question (should use context)
        answer2, confidence2 = qa_engine.ask_question(
            "What about its return value?",
            conversation_id
        )
        
        assert len(conversation.previous_questions) == 2
        # Should have detected this as a follow-up question
        assert qa_engine._is_followup_question("What about its return value?")
    
    def test_focus_navigation(self, qa_engine, sample_analysis_result):
        """Test code location focus and navigation."""
        conversation_id = qa_engine.index_codebase(sample_analysis_result)
        
        # Navigate to specific code location
        success = qa_engine.navigate_to_code(
            conversation_id,
            "/test/example.py",
            function_name="test_function"
        )
        
        assert success
        
        current_focus = qa_engine.get_current_focus(conversation_id)
        assert current_focus is not None
        assert current_focus.file_path == "/test/example.py"
        assert current_focus.function_name == "test_function"
        assert current_focus.context_type == "function"
        
        # Navigate to another location
        qa_engine.navigate_to_code(
            conversation_id,
            "/test/another.py",
            class_name="TestClass"
        )
        
        # Check focus history
        focus_history = qa_engine.get_focus_history(conversation_id)
        assert len(focus_history) == 1
        assert focus_history[0].function_name == "test_function"
        
        # Navigate back
        success = qa_engine.navigate_back(conversation_id)
        assert success
        
        current_focus = qa_engine.get_current_focus(conversation_id)
        assert current_focus.function_name == "test_function"
    
    def test_context_aware_search(self, qa_engine, sample_analysis_result, mock_vector_store):
        """Test that search queries are enhanced with conversation context."""
        conversation_id = qa_engine.index_codebase(sample_analysis_result)
        
        # Set up conversation context
        qa_engine.navigate_to_code(
            conversation_id,
            "/test/example.py",
            function_name="test_function"
        )
        
        # Ask a question that should use context
        qa_engine.ask_question("How does this work?", conversation_id)
        
        # Verify that search was called with enhanced query
        mock_vector_store.search_code.assert_called()
        call_args = mock_vector_store.search_code.call_args
        
        # The query should be enhanced with context
        enhanced_query = call_args[0][0]  # First positional argument
        assert "How does this work?" in enhanced_query
    
    def test_followup_question_detection(self, qa_engine):
        """Test detection of follow-up questions."""
        test_cases = [
            ("What about this function?", True),
            ("How does it work?", True),
            ("And what about performance?", True),
            ("But there's also another issue", True),
            ("What is the main function?", False),
            ("Analyze the security issues", False)
        ]
        
        for question, expected in test_cases:
            result = qa_engine._is_followup_question(question)
            assert result == expected, f"Question '{question}' followup detection failed"
    
    def test_conversation_summary(self, qa_engine, sample_analysis_result):
        """Test conversation context summary generation."""
        conversation_id = qa_engine.index_codebase(sample_analysis_result)
        
        # Add some conversation history
        qa_engine.ask_question("What does test_function do?", conversation_id)
        qa_engine.navigate_to_code(conversation_id, "/test/example.py", function_name="test_function")
        qa_engine.ask_question("How complex is this function?", conversation_id)
        
        # Get summary
        summary = qa_engine.get_conversation_context_summary(conversation_id)
        
        assert summary is not None
        assert "Conversation Context Summary" in summary
        assert "/test/project" in summary
        assert "Questions Asked: 2" in summary
        assert "Current Focus:" in summary
        assert "test_function" in summary
    
    def test_related_code_suggestions(self, qa_engine, sample_analysis_result, mock_vector_store):
        """Test related code suggestions based on current focus."""
        conversation_id = qa_engine.index_codebase(sample_analysis_result)
        
        # Set focus
        qa_engine.navigate_to_code(
            conversation_id,
            "/test/example.py",
            function_name="test_function"
        )
        
        # Mock additional search results for suggestions
        mock_chunk2 = CodeChunk(
            id="test-chunk-2",
            file_path="/test/related.py",
            chunk_type="function",
            content="def related_function():\n    pass",
            start_line=5,
            end_line=7,
            metadata={"function_name": "related_function"}
        )
        
        mock_result2 = SearchResult(chunk=mock_chunk2, similarity_score=0.7, distance=0.3)
        mock_vector_store.search_code.return_value = [mock_result2]
        
        suggestions = qa_engine.suggest_related_code(conversation_id, limit=3)
        
        assert len(suggestions) > 0
        assert "/test/related.py:5" in suggestions
    
    def test_conversation_cleanup(self, qa_engine, sample_analysis_result):
        """Test conversation cleanup and management."""
        conversation_id = qa_engine.index_codebase(sample_analysis_result)
        
        # Verify conversation exists
        assert conversation_id in qa_engine.conversations
        
        # Clear conversation
        success = qa_engine.clear_conversation(conversation_id)
        assert success
        assert conversation_id not in qa_engine.conversations
        
        # Try to clear non-existent conversation
        success = qa_engine.clear_conversation("non-existent")
        assert not success
    
    def test_statistics_with_conversation_data(self, qa_engine, sample_analysis_result):
        """Test statistics collection with conversation data."""
        conversation_id = qa_engine.index_codebase(sample_analysis_result)
        
        # Add some conversation activity
        qa_engine.ask_question("What does this do?", conversation_id)
        qa_engine.navigate_to_code(conversation_id, "/test/example.py", function_name="test_function")
        qa_engine.ask_question("How complex is it?", conversation_id)
        
        stats = qa_engine.get_statistics()
        
        assert stats["active_conversations"] == 1
        assert stats["total_questions"] == 2
        assert stats["average_confidence"] > 0.0
        assert "question_types" in stats
        assert "focus_types" in stats
        assert stats["total_focus_changes"] >= 0


class TestCodeLocationFocus:
    """Test CodeLocationFocus functionality."""
    
    def test_focus_string_representation(self):
        """Test string representation of different focus types."""
        # Function focus
        focus1 = CodeLocationFocus(
            file_path="/test/example.py",
            function_name="test_func",
            context_type="function"
        )
        assert str(focus1) == "/test/example.py::test_func()"
        
        # Class focus
        focus2 = CodeLocationFocus(
            file_path="/test/example.py",
            class_name="TestClass",
            context_type="class"
        )
        assert str(focus2) == "/test/example.py::TestClass"
        
        # Line range focus
        focus3 = CodeLocationFocus(
            file_path="/test/example.py",
            line_range=(10, 20),
            context_type="line_range"
        )
        assert str(focus3) == "/test/example.py:10-20"
        
        # File focus
        focus4 = CodeLocationFocus(
            file_path="/test/example.py",
            context_type="file"
        )
        assert str(focus4) == "/test/example.py"


if __name__ == "__main__":
    pytest.main([__file__])