"""Q&A Engine for interactive codebase exploration using RAG."""

import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .vector_store import VectorStoreManager, SearchResult
from ..llm.llm_service import LLMService
from ..core.models import AnalysisResult, Issue, ParsedFile


logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Types of questions the Q&A engine can handle."""
    GENERAL = "general"
    CODE_SPECIFIC = "code_specific"
    ISSUE_RELATED = "issue_related"
    METRICS = "metrics"
    FILE_SPECIFIC = "file_specific"
    FUNCTION_SPECIFIC = "function_specific"
    CLASS_SPECIFIC = "class_specific"


@dataclass
class QAPair:
    """Question-Answer pair with metadata."""
    question: str
    answer: str
    question_type: QuestionType
    timestamp: datetime
    confidence: float
    sources: List[str] = field(default_factory=list)
    code_references: List[str] = field(default_factory=list)


@dataclass
class CodebaseContext:
    """Context about the analyzed codebase."""
    codebase_path: str
    total_files: int
    total_issues: int
    languages: List[str]
    quality_score: float
    analysis_result: Optional[AnalysisResult] = None
    
    def to_summary(self) -> str:
        """Generate a summary string of the codebase context."""
        return f"""Codebase: {self.codebase_path}
Files: {self.total_files}
Issues: {self.total_issues}
Languages: {', '.join(self.languages)}
Quality Score: {self.quality_score:.1f}/100"""


@dataclass
class CodeLocationFocus:
    """Represents the current focus location in code."""
    file_path: str
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    line_range: Optional[Tuple[int, int]] = None
    context_type: str = "file"  # 'file', 'function', 'class', 'line_range'
    
    def __str__(self) -> str:
        """String representation of the focus."""
        if self.context_type == "function" and self.function_name:
            return f"{self.file_path}::{self.function_name}()"
        elif self.context_type == "class" and self.class_name:
            return f"{self.file_path}::{self.class_name}"
        elif self.context_type == "line_range" and self.line_range:
            return f"{self.file_path}:{self.line_range[0]}-{self.line_range[1]}"
        else:
            return self.file_path


@dataclass
class ConversationContext:
    """Enhanced context for maintaining conversation state with navigation."""
    conversation_id: str
    codebase_context: CodebaseContext
    previous_questions: List[QAPair] = field(default_factory=list)
    current_focus: Optional[CodeLocationFocus] = None
    focus_history: List[CodeLocationFocus] = field(default_factory=list)
    session_start: datetime = field(default_factory=datetime.now)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    def add_qa_pair(self, qa_pair: QAPair) -> None:
        """Add a Q&A pair to the conversation history."""
        self.previous_questions.append(qa_pair)
        
        # Keep only last 15 Q&A pairs to manage context size
        if len(self.previous_questions) > 15:
            self.previous_questions = self.previous_questions[-15:]
    
    def set_focus(self, focus: CodeLocationFocus) -> None:
        """Set the current focus and add to history."""
        if self.current_focus:
            self.focus_history.append(self.current_focus)
        
        self.current_focus = focus
        
        # Keep only last 10 focus locations
        if len(self.focus_history) > 10:
            self.focus_history = self.focus_history[-10:]
    
    def get_focus_context(self) -> str:
        """Get current focus context as a string."""
        if not self.current_focus:
            return "No current focus"
        
        context_parts = [f"Current focus: {self.current_focus}"]
        
        if self.focus_history:
            context_parts.append("Recent focus history:")
            for focus in self.focus_history[-3:]:
                context_parts.append(f"  - {focus}")
        
        return "\n".join(context_parts)
    
    def get_recent_context(self, limit: int = 3) -> str:
        """Get recent conversation context as a string."""
        if not self.previous_questions:
            return "No previous conversation."
        
        recent_qa = self.previous_questions[-limit:]
        context_parts = []
        
        for qa in recent_qa:
            context_parts.append(f"Q: {qa.question}")
            # Truncate long answers but preserve key information
            answer_preview = qa.answer[:150] + "..." if len(qa.answer) > 150 else qa.answer
            context_parts.append(f"A: {answer_preview}")
            
            # Add code references if available
            if qa.code_references:
                context_parts.append(f"   Referenced: {', '.join(qa.code_references[:3])}")
        
        return "\n".join(context_parts)
    
    def get_contextual_keywords(self) -> List[str]:
        """Extract keywords from recent conversation for context-aware responses."""
        keywords = set()
        
        # Extract from recent questions
        for qa in self.previous_questions[-5:]:
            # Simple keyword extraction
            question_words = qa.question.lower().split()
            answer_words = qa.answer.lower().split()
            
            # Add technical terms and identifiers
            for word in question_words + answer_words:
                if (len(word) > 3 and 
                    any(char.isalnum() for char in word) and
                    word not in ['what', 'how', 'where', 'when', 'why', 'this', 'that', 'with', 'from']):
                    keywords.add(word)
        
        # Add current focus keywords
        if self.current_focus:
            if self.current_focus.function_name:
                keywords.add(self.current_focus.function_name)
            if self.current_focus.class_name:
                keywords.add(self.current_focus.class_name)
        
        return list(keywords)[:10]  # Limit to top 10 keywords


class QuestionClassifier:
    """Classifies questions to determine the best response strategy."""
    
    def __init__(self):
        self.patterns = {
            QuestionType.FILE_SPECIFIC: [
                "file", "in the file", "this file", "which file", "what file"
            ],
            QuestionType.FUNCTION_SPECIFIC: [
                "function", "method", "def ", "function called", "this function"
            ],
            QuestionType.CLASS_SPECIFIC: [
                "class", "this class", "which class", "class definition"
            ],
            QuestionType.ISSUE_RELATED: [
                "issue", "problem", "bug", "error", "vulnerability", "security", "performance"
            ],
            QuestionType.METRICS: [
                "score", "quality", "metrics", "complexity", "complex", "coverage", "debt"
            ],
            QuestionType.CODE_SPECIFIC: [
                "code", "implementation", "how does", "what does", "where is"
            ]
        }
    
    def classify_question(self, question: str) -> QuestionType:
        """
        Classify a question to determine the best response strategy.
        
        Args:
            question: User's question
            
        Returns:
            Classified question type
        """
        question_lower = question.lower()
        
        # Count matches for each type
        type_scores = {}
        for question_type, patterns in self.patterns.items():
            score = sum(1 for pattern in patterns if pattern in question_lower)
            if score > 0:
                type_scores[question_type] = score
        
        # Prioritize METRICS over CODE_SPECIFIC for questions about complexity, quality, etc.
        if (QuestionType.METRICS in type_scores and 
            QuestionType.CODE_SPECIFIC in type_scores and
            any(word in question_lower for word in ["complex", "quality", "score", "metrics", "coverage"])):
            return QuestionType.METRICS
        
        # Return the type with the highest score, or GENERAL if no matches
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        
        return QuestionType.GENERAL


class QAEngine:
    """Interactive Q&A engine for codebase exploration using RAG."""
    
    def __init__(
        self,
        vector_store_manager: VectorStoreManager,
        llm_service: LLMService,
        max_context_chunks: int = 5,
        similarity_threshold: float = 0.1
    ):
        """
        Initialize Q&A engine.
        
        Args:
            vector_store_manager: Vector store for code retrieval
            llm_service: LLM service for generating answers
            max_context_chunks: Maximum number of code chunks to include in context
            similarity_threshold: Minimum similarity score for relevant chunks
        """
        self.vector_store = vector_store_manager
        self.llm_service = llm_service
        self.max_context_chunks = max_context_chunks
        self.similarity_threshold = similarity_threshold
        self.classifier = QuestionClassifier()
        
        # Active conversations
        self.conversations: Dict[str, ConversationContext] = {}
        
        logger.info("Q&A Engine initialized")
    
    def index_codebase(self, analysis_result: AnalysisResult) -> str:
        """
        Index a codebase for Q&A and create a conversation context.
        
        Args:
            analysis_result: Analysis result to index
            
        Returns:
            Conversation ID for future interactions
        """
        # Index in vector store
        chunk_count = self.vector_store.index_analysis_result(analysis_result)
        logger.info(f"Indexed {chunk_count} chunks for Q&A")
        
        # Create codebase context
        languages = list(set(f.language for f in analysis_result.parsed_files))
        codebase_context = CodebaseContext(
            codebase_path=analysis_result.codebase_path,
            total_files=len(analysis_result.parsed_files),
            total_issues=len(analysis_result.issues),
            languages=languages,
            quality_score=analysis_result.metrics.overall_score,
            analysis_result=analysis_result
        )
        
        # Create conversation
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = ConversationContext(
            conversation_id=conversation_id,
            codebase_context=codebase_context
        )
        
        logger.info(f"Created conversation {conversation_id} for codebase {analysis_result.codebase_path}")
        return conversation_id
    
    def ask_question(
        self,
        question: str,
        conversation_id: str,
        include_code_context: bool = True
    ) -> Tuple[str, float]:
        """
        Ask a question about the codebase.
        
        Args:
            question: User's question
            conversation_id: ID of the conversation context
            include_code_context: Whether to include code context in the answer
            
        Returns:
            Tuple of (answer, confidence_score)
        """
        if conversation_id not in self.conversations:
            return "Conversation not found. Please index a codebase first.", 0.0
        
        conversation = self.conversations[conversation_id]
        
        try:
            # Classify the question
            question_type = self.classifier.classify_question(question)
            logger.debug(f"Classified question as: {question_type}")
            
            # Retrieve relevant context
            context_chunks = []
            code_references = []
            
            if include_code_context:
                context_chunks, code_references = self._retrieve_relevant_context(
                    question, conversation, question_type
                )
            
            # Generate answer using LLM
            answer, confidence = self._generate_answer(
                question, conversation, context_chunks, question_type
            )
            
            # Create Q&A pair and add to conversation
            qa_pair = QAPair(
                question=question,
                answer=answer,
                question_type=question_type,
                timestamp=datetime.now(),
                confidence=confidence,
                sources=[chunk.chunk.file_path for chunk in context_chunks],
                code_references=code_references
            )
            
            conversation.add_qa_pair(qa_pair)
            
            # Update current focus if question is about specific code
            self._update_conversation_focus(conversation, question, context_chunks)
            
            logger.info(f"Answered question with {confidence:.2f} confidence")
            return answer, confidence
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"I encountered an error while processing your question: {str(e)}", 0.0
    
    def _retrieve_relevant_context(
        self,
        question: str,
        conversation: ConversationContext,
        question_type: QuestionType
    ) -> Tuple[List[SearchResult], List[str]]:
        """Retrieve relevant code context for the question with conversation awareness."""
        context_chunks = []
        code_references = []
        
        # Enhance question with conversation context for better retrieval
        enhanced_query = self._enhance_query_with_context(question, conversation)
        
        # Determine search filters based on question type and current focus
        chunk_types = None
        file_paths = None
        
        if question_type == QuestionType.FUNCTION_SPECIFIC:
            chunk_types = ["function"]
        elif question_type == QuestionType.CLASS_SPECIFIC:
            chunk_types = ["class"]
        elif question_type == QuestionType.FILE_SPECIFIC and conversation.current_focus:
            file_paths = [conversation.current_focus.file_path]
        
        # Handle follow-up questions by considering current focus
        if self._is_followup_question(question) and conversation.current_focus:
            # For follow-up questions, prioritize current focus area
            if conversation.current_focus.context_type == "function":
                chunk_types = ["function"]
                file_paths = [conversation.current_focus.file_path]
            elif conversation.current_focus.context_type == "class":
                chunk_types = ["class"]
                file_paths = [conversation.current_focus.file_path]
            elif conversation.current_focus.context_type == "file":
                file_paths = [conversation.current_focus.file_path]
        
        # Perform vector search with enhanced query
        search_results = self.vector_store.search_code(
            enhanced_query,
            limit=self.max_context_chunks,
            chunk_types=chunk_types,
            file_paths=file_paths
        )
        
        # If focused search yields few results, broaden the search
        if len(search_results) < 2 and (chunk_types or file_paths):
            logger.debug("Broadening search due to limited focused results")
            broader_results = self.vector_store.search_code(
                enhanced_query,
                limit=self.max_context_chunks
            )
            # Merge results, prioritizing focused ones
            search_results.extend(broader_results)
            # Remove duplicates while preserving order
            seen = set()
            unique_results = []
            for result in search_results:
                key = (result.chunk.file_path, result.chunk.start_line, result.chunk.end_line)
                if key not in seen:
                    seen.add(key)
                    unique_results.append(result)
            search_results = unique_results[:self.max_context_chunks]
        
        # Filter by similarity threshold
        for result in search_results:
            if result.similarity_score >= self.similarity_threshold:
                context_chunks.append(result)
                code_references.append(f"{result.chunk.file_path}:{result.chunk.start_line}")
        
        logger.debug(f"Retrieved {len(context_chunks)} relevant code chunks")
        return context_chunks, code_references
    
    def _enhance_query_with_context(self, question: str, conversation: ConversationContext) -> str:
        """Enhance the search query with conversation context."""
        enhanced_parts = [question]
        
        # Add keywords from recent conversation
        contextual_keywords = conversation.get_contextual_keywords()
        if contextual_keywords:
            # Add top 3 most relevant keywords
            enhanced_parts.extend(contextual_keywords[:3])
        
        # Add current focus context
        if conversation.current_focus:
            if conversation.current_focus.function_name:
                enhanced_parts.append(conversation.current_focus.function_name)
            if conversation.current_focus.class_name:
                enhanced_parts.append(conversation.current_focus.class_name)
        
        return " ".join(enhanced_parts)
    
    def _is_followup_question(self, question: str) -> bool:
        """Determine if a question is a follow-up to previous conversation."""
        question_lower = question.lower().strip()
        question_words = question_lower.split()
        
        if not question_words:
            return False
        
        # Check for specific followup patterns
        followup_patterns = [
            "what about this", "what about that", "what about its", "what about it",
            "how about this", "how about that", "how about its", "how about it",
            "and this", "and that", "but this", "but that", "also this", "also that"
        ]
        
        for pattern in followup_patterns:
            if pattern in question_lower:
                return True
        
        # Check for pronouns that suggest reference to previous context (as whole words)
        pronouns = ["it", "here", "there"]
        if any(pronoun in question_words for pronoun in pronouns):
            return True
        
        # Check for sentence starters that suggest continuation
        first_word = question_words[0]
        if first_word in ["and", "but", "however", "additionally", "furthermore"]:
            return True
        
        # Check for "this" or "that" when used as demonstrative pronouns
        # (not when used as determiners like "this function" in a new question)
        if first_word in ["this", "that"]:
            # If it's just "this" or "that" followed by a verb, it's likely a followup
            if len(question_words) > 1:
                second_word = question_words[1]
                # Common verbs that suggest reference to previous context
                if second_word in ["is", "was", "does", "did", "can", "will", "would", "should"]:
                    return True
        
        return False
    
    def _generate_answer(
        self,
        question: str,
        conversation: ConversationContext,
        context_chunks: List[SearchResult],
        question_type: QuestionType
    ) -> Tuple[str, float]:
        """Generate an answer using the LLM with retrieved context."""
        
        # Build context for LLM
        context_parts = []
        
        # Add codebase summary
        context_parts.append("CODEBASE CONTEXT:")
        context_parts.append(conversation.codebase_context.to_summary())
        context_parts.append("")
        
        # Add recent conversation context
        if conversation.previous_questions:
            context_parts.append("RECENT CONVERSATION:")
            context_parts.append(conversation.get_recent_context(3))
            context_parts.append("")
        
        # Add retrieved code context
        if context_chunks:
            context_parts.append("RELEVANT CODE:")
            for i, result in enumerate(context_chunks, 1):
                chunk = result.chunk
                context_parts.append(f"{i}. File: {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line})")
                context_parts.append(f"   Type: {chunk.chunk_type}")
                context_parts.append(f"   Content:")
                context_parts.append(f"   {chunk.content}")
                context_parts.append("")
        
        # Add issue context if relevant
        if question_type == QuestionType.ISSUE_RELATED and conversation.codebase_context.analysis_result:
            issues = conversation.codebase_context.analysis_result.issues[:5]  # Top 5 issues
            if issues:
                context_parts.append("RECENT ISSUES:")
                for issue in issues:
                    context_parts.append(f"- {issue.title} ({issue.severity.value}) in {issue.location.file_path}")
                context_parts.append("")
        
        # Create the full context
        full_context = "\n".join(context_parts)
        
        # Generate answer using LLM service
        try:
            answer = self.llm_service.answer_question(
                question,
                conversation.codebase_context.analysis_result or AnalysisResult(
                    analysis_id="qa-session",
                    codebase_path=conversation.codebase_context.codebase_path,
                    parsed_files=[],
                    issues=[]
                ),
                additional_context=full_context
            )
            
            if answer:
                # Calculate confidence based on context relevance
                confidence = self._calculate_confidence(context_chunks, question_type)
                return answer, confidence
            else:
                return "I'm sorry, I couldn't generate a helpful answer to your question.", 0.1
                
        except Exception as e:
            logger.error(f"LLM answer generation failed: {e}")
            return "I encountered an issue while generating an answer. Please try rephrasing your question.", 0.1
    
    def _calculate_confidence(self, context_chunks: List[SearchResult], question_type: QuestionType) -> float:
        """Calculate confidence score for the answer."""
        if not context_chunks:
            return 0.3  # Low confidence without context
        
        # Base confidence on similarity scores
        avg_similarity = sum(chunk.similarity_score for chunk in context_chunks) / len(context_chunks)
        
        # Adjust based on question type
        type_multipliers = {
            QuestionType.CODE_SPECIFIC: 1.0,
            QuestionType.FUNCTION_SPECIFIC: 1.1,
            QuestionType.CLASS_SPECIFIC: 1.1,
            QuestionType.FILE_SPECIFIC: 1.0,
            QuestionType.ISSUE_RELATED: 0.9,
            QuestionType.METRICS: 0.8,
            QuestionType.GENERAL: 0.7
        }
        
        multiplier = type_multipliers.get(question_type, 0.8)
        confidence = min(avg_similarity * multiplier, 1.0)
        
        return max(confidence, 0.1)  # Minimum confidence
    
    def _update_conversation_focus(
        self,
        conversation: ConversationContext,
        question: str,
        context_chunks: List[SearchResult]
    ) -> None:
        """Update the conversation focus based on the question and context."""
        question_lower = question.lower()
        
        # Extract focus from context chunks based on question type
        if not context_chunks:
            return
        
        # Find the most relevant chunk
        best_chunk = context_chunks[0]  # Highest similarity
        
        # Create focus based on chunk type and question content
        if "function" in question_lower and best_chunk.chunk.chunk_type == "function":
            focus = CodeLocationFocus(
                file_path=best_chunk.chunk.file_path,
                function_name=best_chunk.chunk.metadata.get("function_name"),
                line_range=(best_chunk.chunk.start_line, best_chunk.chunk.end_line),
                context_type="function"
            )
        elif "class" in question_lower and best_chunk.chunk.chunk_type == "class":
            focus = CodeLocationFocus(
                file_path=best_chunk.chunk.file_path,
                class_name=best_chunk.chunk.metadata.get("class_name"),
                line_range=(best_chunk.chunk.start_line, best_chunk.chunk.end_line),
                context_type="class"
            )
        elif any(keyword in question_lower for keyword in ["file", "in this", "this file"]):
            focus = CodeLocationFocus(
                file_path=best_chunk.chunk.file_path,
                context_type="file"
            )
        else:
            # Default to line range focus
            focus = CodeLocationFocus(
                file_path=best_chunk.chunk.file_path,
                line_range=(best_chunk.chunk.start_line, best_chunk.chunk.end_line),
                context_type="line_range"
            )
        
        conversation.set_focus(focus)
    
    def get_conversation_history(self, conversation_id: str) -> List[QAPair]:
        """Get the conversation history for a given conversation ID."""
        if conversation_id not in self.conversations:
            return []
        
        return self.conversations[conversation_id].previous_questions
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a conversation and its history."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Cleared conversation {conversation_id}")
            return True
        return False
    
    def get_conversation_summary(self, conversation_id: str) -> Optional[str]:
        """Get a summary of the conversation."""
        if conversation_id not in self.conversations:
            return None
        
        conversation = self.conversations[conversation_id]
        
        summary_parts = [
            f"Conversation ID: {conversation_id}",
            f"Codebase: {conversation.codebase_context.codebase_path}",
            f"Started: {conversation.session_start.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Questions Asked: {len(conversation.previous_questions)}",
        ]
        
        if conversation.current_focus:
            summary_parts.append(f"Current Focus: {conversation.current_focus}")
        
        if conversation.previous_questions:
            summary_parts.append("\nRecent Questions:")
            for qa in conversation.previous_questions[-3:]:
                summary_parts.append(f"- {qa.question}")
        
        return "\n".join(summary_parts)
    
    def navigate_to_code(
        self,
        conversation_id: str,
        file_path: str,
        function_name: Optional[str] = None,
        class_name: Optional[str] = None,
        line_number: Optional[int] = None
    ) -> bool:
        """
        Navigate to a specific code location in the conversation.
        
        Args:
            conversation_id: ID of the conversation
            file_path: Path to the file
            function_name: Optional function name to focus on
            class_name: Optional class name to focus on
            line_number: Optional line number to focus on
            
        Returns:
            True if navigation was successful
        """
        if conversation_id not in self.conversations:
            return False
        
        conversation = self.conversations[conversation_id]
        
        # Determine context type and create focus
        if function_name:
            focus = CodeLocationFocus(
                file_path=file_path,
                function_name=function_name,
                context_type="function"
            )
        elif class_name:
            focus = CodeLocationFocus(
                file_path=file_path,
                class_name=class_name,
                context_type="class"
            )
        elif line_number:
            focus = CodeLocationFocus(
                file_path=file_path,
                line_range=(line_number, line_number),
                context_type="line_range"
            )
        else:
            focus = CodeLocationFocus(
                file_path=file_path,
                context_type="file"
            )
        
        conversation.set_focus(focus)
        logger.info(f"Navigated to {focus} in conversation {conversation_id}")
        return True
    
    def get_current_focus(self, conversation_id: str) -> Optional[CodeLocationFocus]:
        """Get the current focus location for a conversation."""
        if conversation_id not in self.conversations:
            return None
        
        return self.conversations[conversation_id].current_focus
    
    def get_focus_history(self, conversation_id: str) -> List[CodeLocationFocus]:
        """Get the focus history for a conversation."""
        if conversation_id not in self.conversations:
            return []
        
        return self.conversations[conversation_id].focus_history
    
    def navigate_back(self, conversation_id: str) -> bool:
        """Navigate back to the previous focus location."""
        if conversation_id not in self.conversations:
            return False
        
        conversation = self.conversations[conversation_id]
        
        if not conversation.focus_history:
            return False
        
        # Get the previous focus and set it as current
        previous_focus = conversation.focus_history.pop()
        conversation.current_focus = previous_focus
        
        logger.info(f"Navigated back to {previous_focus} in conversation {conversation_id}")
        return True
    
    def suggest_related_code(self, conversation_id: str, limit: int = 5) -> List[str]:
        """
        Suggest related code locations based on current focus and conversation history.
        
        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested code locations
        """
        if conversation_id not in self.conversations:
            return []
        
        conversation = self.conversations[conversation_id]
        suggestions = []
        
        # Get suggestions based on current focus
        if conversation.current_focus:
            # Search for related code using current focus as context
            search_query = ""
            if conversation.current_focus.function_name:
                search_query = conversation.current_focus.function_name
            elif conversation.current_focus.class_name:
                search_query = conversation.current_focus.class_name
            else:
                # Use file name as search context
                import os
                search_query = os.path.basename(conversation.current_focus.file_path)
            
            if search_query:
                try:
                    search_results = self.vector_store.search_code(
                        search_query,
                        limit=limit * 2  # Get more results to filter
                    )
                    
                    # Filter out current focus and add suggestions
                    for result in search_results:
                        location = f"{result.chunk.file_path}:{result.chunk.start_line}"
                        current_location = f"{conversation.current_focus.file_path}"
                        
                        # Skip if it's the same file and we're in file context
                        if (conversation.current_focus.context_type == "file" and 
                            result.chunk.file_path == conversation.current_focus.file_path):
                            continue
                        
                        # Skip if it's the exact same location
                        if (result.chunk.file_path == conversation.current_focus.file_path and
                            conversation.current_focus.line_range and
                            result.chunk.start_line >= conversation.current_focus.line_range[0] and
                            result.chunk.end_line <= conversation.current_focus.line_range[1]):
                            continue
                        
                        suggestions.append(location)
                        
                        if len(suggestions) >= limit:
                            break
                            
                except Exception as e:
                    logger.error(f"Error getting code suggestions: {e}")
        
        return suggestions
    
    def get_conversation_context_summary(self, conversation_id: str) -> Optional[str]:
        """Get a detailed summary of the conversation context including focus and history."""
        if conversation_id not in self.conversations:
            return None
        
        conversation = self.conversations[conversation_id]
        
        summary_parts = [
            f"Conversation Context Summary",
            f"=" * 30,
            f"Codebase: {conversation.codebase_context.codebase_path}",
            f"Session Duration: {datetime.now() - conversation.session_start}",
            f"Questions Asked: {len(conversation.previous_questions)}",
            ""
        ]
        
        # Current focus
        if conversation.current_focus:
            summary_parts.extend([
                "Current Focus:",
                f"  {conversation.current_focus}",
                ""
            ])
        
        # Focus history
        if conversation.focus_history:
            summary_parts.append("Recent Focus History:")
            for i, focus in enumerate(conversation.focus_history[-5:], 1):
                summary_parts.append(f"  {i}. {focus}")
            summary_parts.append("")
        
        # Recent questions with types
        if conversation.previous_questions:
            summary_parts.append("Recent Questions:")
            for qa in conversation.previous_questions[-3:]:
                summary_parts.append(f"  Q ({qa.question_type.value}): {qa.question}")
                summary_parts.append(f"  Confidence: {qa.confidence:.2f}")
                if qa.code_references:
                    summary_parts.append(f"  References: {', '.join(qa.code_references[:2])}")
                summary_parts.append("")
        
        # Contextual keywords
        keywords = conversation.get_contextual_keywords()
        if keywords:
            summary_parts.extend([
                f"Active Keywords: {', '.join(keywords[:5])}",
                ""
            ])
        
        return "\n".join(summary_parts)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Q&A engine statistics."""
        total_questions = sum(
            len(conv.previous_questions) for conv in self.conversations.values()
        )
        
        avg_confidence = 0.0
        if total_questions > 0:
            total_confidence = sum(
                qa.confidence 
                for conv in self.conversations.values()
                for qa in conv.previous_questions
            )
            avg_confidence = total_confidence / total_questions
        
        question_types = {}
        for conv in self.conversations.values():
            for qa in conv.previous_questions:
                qt = qa.question_type.value
                question_types[qt] = question_types.get(qt, 0) + 1
        
        # Focus statistics
        focus_types = {}
        total_focus_changes = 0
        for conv in self.conversations.values():
            total_focus_changes += len(conv.focus_history)
            if conv.current_focus:
                ft = conv.current_focus.context_type
                focus_types[ft] = focus_types.get(ft, 0) + 1
        
        return {
            "active_conversations": len(self.conversations),
            "total_questions": total_questions,
            "average_confidence": avg_confidence,
            "question_types": question_types,
            "focus_types": focus_types,
            "total_focus_changes": total_focus_changes,
            "vector_store_stats": self.vector_store.get_statistics()
        }


def create_qa_engine(
    vector_store_manager: VectorStoreManager,
    llm_service: LLMService,
    max_context_chunks: int = 5
) -> QAEngine:
    """
    Create a Q&A engine with default configuration.
    
    Args:
        vector_store_manager: Vector store manager for code retrieval
        llm_service: LLM service for answer generation
        max_context_chunks: Maximum context chunks to retrieve
        
    Returns:
        Configured QAEngine instance
    """
    return QAEngine(
        vector_store_manager=vector_store_manager,
        llm_service=llm_service,
        max_context_chunks=max_context_chunks
    )