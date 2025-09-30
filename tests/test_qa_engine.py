"""Tests for Q&A Engine functionality."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from code_quality_agent.rag import (
    QAEngine, QuestionType, QAPair, CodebaseContext, ConversationContext,
    QuestionClassifier, create_qa_engine, VectorStoreManager, SearchResult, CodeChunk
)
from code_quality_agent.llm import create_llm_service
from code_quality_agent.core.models import (
    AnalysisResult, ParsedFile, Function, Class, Issue, IssueCategory, 
    Severity, CodeLocation, QualityMetrics
)


class TestQuestionClassifier:
    """Test cases for QuestionClassifier."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = QuestionClassifier()
    
    def test_file_specific_classification(self):
        """Test classification of file-specific questions."""
        questions = [
            "What issues are in the auth.py file?",
            "Show me this file's problems",
            "Which file has the most bugs?"
        ]
        
        for question in questions:
            result = self.classifier.classify_question(question)
            assert result == QuestionType.FILE_SPECIFIC
    
    def test_function_specific_classification(self):
        """Test classification of function-specific questions."""
        questions = [
            "What does this function do?",
            "How complex is the calculate_sum method?",
            "Show me the function called process_data"
        ]
        
        for question in questions:
            result = self.classifier.classify_question(question)
            assert result == QuestionType.FUNCTION_SPECIFIC
    
    def test_class_specific_classification(self):
        """Test classification of class-specific questions."""
        questions = [
            "What methods does this class have?",
            "Show me the UserManager class",
            "Which class handles authentication?"
        ]
        
        for question in questions:
            result = self.classifier.classify_question(question)
            assert result == QuestionType.CLASS_SPECIFIC
    
    def test_issue_related_classification(self):
        """Test classification of issue-related questions."""
        questions = [
            "What security vulnerabilities were found?",
            "Show me the performance issues",
            "Are there any bugs in the code?"
        ]
        
        for question in questions:
            result = self.classifier.classify_question(question)
            assert result == QuestionType.ISSUE_RELATED
    
    def test_metrics_classification(self):
        """Test classification of metrics questions."""
        questions = [
            "What's the quality score?",
            "How complex is this codebase?",
            "What are the coverage metrics?"
        ]
        
        for question in questions:
            result = self.classifier.classify_question(question)
            assert result == QuestionType.METRICS
    
    def test_general_classification(self):
        """Test classification of general questions."""
        questions = [
            "Hello, how are you?",
            "What can you help me with?",
            "Tell me about this project"
        ]
        
        for question in questions:
            result = self.classifier.classify_question(question)
            assert result == QuestionType.GENERAL


class TestCodebaseContext:
    """Test cases for CodebaseContext."""
    
    def test_codebase_context_creation(self):
        """Test CodebaseContext creation."""
        context = CodebaseContext(
            codebase_path="/test/project",
            total_files=25,
            total_issues=15,
            languages=["python", "javascript"],
            quality_score=75.5
        )
        
        assert context.codebase_path == "/test/project"
        assert context.total_files == 25
        assert context.total_issues == 15
        assert "python" in context.languages
        assert context.quality_score == 75.5
    
    def test_to_summary(self):
        """Test summary generation."""
        context = CodebaseContext(
            codebase_path="/test/project",
            total_files=25,
            total_issues=15,
            languages=["python", "javascript"],
            quality_score=75.5
        )
        
        summary = context.to_summary()
        
        assert "/test/project" in summary
        assert "25" in summary
        assert "15" in summary
        assert "python, javascript" in summary
        assert "75.5" in summary


class TestConversationContext:
    """Test cases for ConversationContext."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.codebase_context = CodebaseContext(
            codebase_path="/test/project",
            total_files=10,
            total_issues=5,
            languages=["python"],
            quality_score=80.0
        )
        
        self.conversation = ConversationContext(
            conversation_id="test-conv-1",
            codebase_context=self.codebase_context
        )
    
    def test_conversation_creation(self):
        """Test ConversationContext creation."""
        assert self.conversation.conversation_id == "test-conv-1"
        assert self.conversation.codebase_context == self.codebase_context
        assert len(self.conversation.previous_questions) == 0
        assert self.conversation.current_focus is None
    
    def test_add_qa_pair(self):
        """Test adding Q&A pairs to conversation."""
        qa_pair = QAPair(
            question="What is this?",
            answer="This is a test",
            question_type=QuestionType.GENERAL,
            timestamp=datetime.now(),
            confidence=0.8
        )
        
        self.conversation.add_qa_pair(qa_pair)
        
        assert len(self.conversation.previous_questions) == 1
        assert self.conversation.previous_questions[0] == qa_pair
    
    def test_qa_pair_limit(self):
        """Test that conversation keeps only recent Q&A pairs."""
        # Add 15 Q&A pairs (more than the limit of 10)
        for i in range(15):
            qa_pair = QAPair(
                question=f"Question {i}",
                answer=f"Answer {i}",
                question_type=QuestionType.GENERAL,
                timestamp=datetime.now(),
                confidence=0.8
            )
            self.conversation.add_qa_pair(qa_pair)
        
        # Should keep only the last 15
        assert len(self.conversation.previous_questions) == 15
        assert self.conversation.previous_questions[0].question == "Question 0"
        assert self.conversation.previous_questions[-1].question == "Question 14"
    
    def test_get_recent_context(self):
        """Test getting recent conversation context."""
        # Add some Q&A pairs
        for i in range(5):
            qa_pair = QAPair(
                question=f"Question {i}",
                answer=f"This is a longer answer {i} that should be truncated when used in context",
                question_type=QuestionType.GENERAL,
                timestamp=datetime.now(),
                confidence=0.8
            )
            self.conversation.add_qa_pair(qa_pair)
        
        context = self.conversation.get_recent_context(3)
        
        # Should contain the last 3 Q&A pairs
        assert "Question 2" in context
        assert "Question 3" in context
        assert "Question 4" in context
        assert "Question 0" not in context  # Should not include older ones
        
        # Answers should be present (may be truncated if over 150 chars)
        assert "answer" in context


class TestQAEngine:
    """Test cases for QAEngine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock vector store manager
        self.mock_vector_store = Mock(spec=VectorStoreManager)
        self.mock_vector_store.get_statistics.return_value = {"total_chunks": 10}
        
        # Create mock LLM service
        self.mock_llm_service = create_llm_service(provider="mock")
        
        # Create Q&A engine
        self.qa_engine = QAEngine(
            vector_store_manager=self.mock_vector_store,
            llm_service=self.mock_llm_service,
            max_context_chunks=3
        )
        
        # Create test analysis result
        self.test_parsed_file = ParsedFile(
            path="test.py",
            language="python",
            content="""def calculate_sum(a, b):
    '''Calculate sum of two numbers'''
    return a + b

class Calculator:
    '''Simple calculator class'''
    def add(self, x, y):
        return x + y""",
            functions=[
                Function(name="calculate_sum", line_start=1, line_end=3, 
                        parameters=["a", "b"], docstring="Calculate sum of two numbers")
            ],
            classes=[
                Class(name="Calculator", line_start=5, line_end=8,
                     docstring="Simple calculator class")
            ]
        )
        
        self.test_issue = Issue(
            id="test-issue",
            category=IssueCategory.SECURITY,
            severity=Severity.HIGH,
            title="SQL Injection Vulnerability",
            description="Potential SQL injection",
            location=CodeLocation("test.py", 10, 12),
            affected_files=["test.py"],
            suggestion="Use parameterized queries",
            confidence=0.9
        )
        
        self.test_analysis_result = AnalysisResult(
            analysis_id="test-analysis",
            codebase_path="/test/project",
            parsed_files=[self.test_parsed_file],
            issues=[self.test_issue],
            metrics=QualityMetrics(overall_score=75.0)
        )
    
    def test_qa_engine_initialization(self):
        """Test Q&A engine initialization."""
        assert self.qa_engine.vector_store == self.mock_vector_store
        assert self.qa_engine.llm_service == self.mock_llm_service
        assert self.qa_engine.max_context_chunks == 3
        assert isinstance(self.qa_engine.classifier, QuestionClassifier)
        assert len(self.qa_engine.conversations) == 0
    
    def test_index_codebase(self):
        """Test indexing a codebase for Q&A."""
        # Mock vector store indexing
        self.mock_vector_store.index_analysis_result.return_value = 5
        
        conversation_id = self.qa_engine.index_codebase(self.test_analysis_result)
        
        # Verify conversation was created
        assert conversation_id in self.qa_engine.conversations
        conversation = self.qa_engine.conversations[conversation_id]
        
        assert conversation.codebase_context.codebase_path == "/test/project"
        assert conversation.codebase_context.total_files == 1
        assert conversation.codebase_context.total_issues == 1
        assert "python" in conversation.codebase_context.languages
        assert conversation.codebase_context.quality_score == 75.0
        
        # Verify vector store was called
        self.mock_vector_store.index_analysis_result.assert_called_once_with(self.test_analysis_result)
    
    def test_ask_question_without_conversation(self):
        """Test asking a question without a valid conversation."""
        answer, confidence = self.qa_engine.ask_question(
            "What is this?", 
            "nonexistent-conversation"
        )
        
        assert "Conversation not found" in answer
        assert confidence == 0.0
    
    def test_ask_question_with_context(self):
        """Test asking a question with code context."""
        # Index codebase first
        conversation_id = self.qa_engine.index_codebase(self.test_analysis_result)
        
        # Mock vector store search results
        mock_chunk = CodeChunk(
            id="test-chunk",
            content="def calculate_sum(a, b):\n    return a + b",
            chunk_type="function",
            file_path="test.py",
            start_line=1,
            end_line=3,
            metadata={"function_name": "calculate_sum"}
        )
        
        mock_search_result = SearchResult(
            chunk=mock_chunk,
            similarity_score=0.8,
            distance=0.2
        )
        
        self.mock_vector_store.search_code.return_value = [mock_search_result]
        
        # Ask a question
        answer, confidence = self.qa_engine.ask_question(
            "What does the calculate_sum function do?",
            conversation_id
        )
        
        # Verify answer was generated
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert confidence > 0.0
        
        # Verify conversation was updated
        conversation = self.qa_engine.conversations[conversation_id]
        assert len(conversation.previous_questions) == 1
        
        qa_pair = conversation.previous_questions[0]
        assert qa_pair.question == "What does the calculate_sum function do?"
        assert qa_pair.question_type == QuestionType.FUNCTION_SPECIFIC
        assert "test.py" in qa_pair.sources
    
    def test_ask_question_without_context(self):
        """Test asking a question without code context."""
        # Index codebase first
        conversation_id = self.qa_engine.index_codebase(self.test_analysis_result)
        
        # Mock empty search results
        self.mock_vector_store.search_code.return_value = []
        
        # Ask a question
        answer, confidence = self.qa_engine.ask_question(
            "What is the meaning of life?",
            conversation_id,
            include_code_context=False
        )
        
        # Should still get an answer, but with lower confidence
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert confidence >= 0.1  # Minimum confidence
    
    def test_conversation_history(self):
        """Test getting conversation history."""
        # Index codebase and ask questions
        conversation_id = self.qa_engine.index_codebase(self.test_analysis_result)
        
        self.mock_vector_store.search_code.return_value = []
        
        # Ask multiple questions
        self.qa_engine.ask_question("Question 1", conversation_id, include_code_context=False)
        self.qa_engine.ask_question("Question 2", conversation_id, include_code_context=False)
        
        # Get history
        history = self.qa_engine.get_conversation_history(conversation_id)
        
        assert len(history) == 2
        assert history[0].question == "Question 1"
        assert history[1].question == "Question 2"
    
    def test_clear_conversation(self):
        """Test clearing a conversation."""
        # Create conversation
        conversation_id = self.qa_engine.index_codebase(self.test_analysis_result)
        assert conversation_id in self.qa_engine.conversations
        
        # Clear conversation
        result = self.qa_engine.clear_conversation(conversation_id)
        
        assert result is True
        assert conversation_id not in self.qa_engine.conversations
        
        # Try to clear non-existent conversation
        result = self.qa_engine.clear_conversation("nonexistent")
        assert result is False
    
    def test_conversation_summary(self):
        """Test getting conversation summary."""
        # Index codebase
        conversation_id = self.qa_engine.index_codebase(self.test_analysis_result)
        
        # Ask a question
        self.mock_vector_store.search_code.return_value = []
        self.qa_engine.ask_question("Test question", conversation_id, include_code_context=False)
        
        # Get summary
        summary = self.qa_engine.get_conversation_summary(conversation_id)
        
        assert conversation_id in summary
        assert "/test/project" in summary
        assert "Questions Asked: 1" in summary
        assert "Test question" in summary
    
    def test_statistics(self):
        """Test getting Q&A engine statistics."""
        # Index codebase and ask questions
        conversation_id = self.qa_engine.index_codebase(self.test_analysis_result)
        
        self.mock_vector_store.search_code.return_value = []
        self.qa_engine.ask_question("Question 1", conversation_id, include_code_context=False)
        self.qa_engine.ask_question("Question 2", conversation_id, include_code_context=False)
        
        # Get statistics
        stats = self.qa_engine.get_statistics()
        
        assert stats["active_conversations"] == 1
        assert stats["total_questions"] == 2
        assert "average_confidence" in stats
        assert "question_types" in stats
        assert "vector_store_stats" in stats
    
    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        # Test with high similarity chunks
        high_sim_chunk = SearchResult(
            chunk=CodeChunk("id1", "content", "function", "file.py", 1, 5, {}),
            similarity_score=0.9,
            distance=0.1
        )
        
        confidence = self.qa_engine._calculate_confidence([high_sim_chunk], QuestionType.FUNCTION_SPECIFIC)
        assert confidence > 0.8
        
        # Test with low similarity chunks
        low_sim_chunk = SearchResult(
            chunk=CodeChunk("id2", "content", "function", "file.py", 1, 5, {}),
            similarity_score=0.2,
            distance=0.8
        )
        
        confidence = self.qa_engine._calculate_confidence([low_sim_chunk], QuestionType.GENERAL)
        assert confidence < 0.5
        
        # Test with no chunks
        confidence = self.qa_engine._calculate_confidence([], QuestionType.GENERAL)
        assert confidence == 0.3
    
    def test_conversation_focus_update(self):
        """Test updating conversation focus."""
        conversation_id = self.qa_engine.index_codebase(self.test_analysis_result)
        conversation = self.qa_engine.conversations[conversation_id]
        
        # Mock search result
        mock_chunk = CodeChunk("id", "content", "function", "focus_file.py", 1, 5, {})
        search_result = SearchResult(mock_chunk, 0.8, 0.2)
        
        # Update focus
        self.qa_engine._update_conversation_focus(
            conversation, 
            "What's in this file?", 
            [search_result]
        )
        
        assert conversation.current_focus is not None
        assert conversation.current_focus.file_path == "focus_file.py"


class TestFactoryFunction:
    """Test cases for factory functions."""
    
    def test_create_qa_engine(self):
        """Test factory function for creating Q&A engine."""
        mock_vector_store = Mock(spec=VectorStoreManager)
        mock_llm_service = create_llm_service(provider="mock")
        
        qa_engine = create_qa_engine(
            vector_store_manager=mock_vector_store,
            llm_service=mock_llm_service,
            max_context_chunks=8
        )
        
        assert isinstance(qa_engine, QAEngine)
        assert qa_engine.vector_store == mock_vector_store
        assert qa_engine.llm_service == mock_llm_service
        assert qa_engine.max_context_chunks == 8


class TestIntegration:
    """Integration tests for Q&A engine with real components."""
    
    def test_end_to_end_qa_workflow(self):
        """Test complete Q&A workflow with real components."""
        # Create real components
        vector_store = VectorStoreManager(use_chromadb=False)  # Use mock store
        llm_service = create_llm_service(provider="mock")
        qa_engine = create_qa_engine(vector_store, llm_service)
        
        # Create test data
        parsed_file = ParsedFile(
            path="calculator.py",
            language="python",
            content="""def add(a, b):
    '''Add two numbers'''
    return a + b

def multiply(x, y):
    '''Multiply two numbers'''
    return x * y

class MathUtils:
    '''Utility class for math operations'''
    
    def power(self, base, exp):
        return base ** exp""",
            functions=[
                Function(name="add", line_start=1, line_end=3, parameters=["a", "b"]),
                Function(name="multiply", line_start=5, line_end=7, parameters=["x", "y"]),
            ],
            classes=[
                Class(name="MathUtils", line_start=9, line_end=13)
            ]
        )
        
        analysis_result = AnalysisResult(
            analysis_id="integration-test",
            codebase_path="/test/math",
            parsed_files=[parsed_file],
            issues=[],
            metrics=QualityMetrics(overall_score=85.0)
        )
        
        # Index codebase
        conversation_id = qa_engine.index_codebase(analysis_result)
        assert conversation_id is not None
        
        # Ask questions
        questions = [
            "What functions are available?",
            "How does the add function work?",
            "What classes are defined?",
            "What's the quality score?"
        ]
        
        for question in questions:
            answer, confidence = qa_engine.ask_question(question, conversation_id)
            
            assert isinstance(answer, str)
            assert len(answer) > 0
            assert 0.0 <= confidence <= 1.0
        
        # Verify conversation history
        history = qa_engine.get_conversation_history(conversation_id)
        assert len(history) == len(questions)
        
        # Verify statistics
        stats = qa_engine.get_statistics()
        assert stats["active_conversations"] == 1
        assert stats["total_questions"] == len(questions)


if __name__ == "__main__":
    pytest.main([__file__])