"""RAG (Retrieval-Augmented Generation) module for code quality intelligence."""

from .vector_store import (
    CodeChunk,
    SearchResult,
    CodeChunker,
    VectorStoreManager,
    ChromaVectorStore,
    MockVectorStore,
    create_vector_store_manager,
    CHROMADB_AVAILABLE
)

from .qa_engine import (
    QAEngine,
    QuestionType,
    QAPair,
    CodebaseContext,
    ConversationContext,
    QuestionClassifier,
    create_qa_engine
)

__all__ = [
    # Vector store classes
    "CodeChunk",
    "SearchResult",
    "CodeChunker",
    "VectorStoreManager",
    "ChromaVectorStore",
    "MockVectorStore",
    
    # Q&A engine classes
    "QAEngine",
    "QuestionType",
    "QAPair",
    "CodebaseContext",
    "ConversationContext",
    "QuestionClassifier",
    
    # Factory functions
    "create_vector_store_manager",
    "create_qa_engine",
    
    # Constants
    "CHROMADB_AVAILABLE"
]