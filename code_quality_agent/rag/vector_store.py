"""Vector store implementation using ChromaDB for RAG system."""

import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import json

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None

from ..core.models import ParsedFile, Issue, AnalysisResult, Function, Class


logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    """Represents a chunk of code for embedding and retrieval."""
    id: str
    content: str
    chunk_type: str  # 'function', 'class', 'module', 'documentation'
    file_path: str
    start_line: int
    end_line: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeChunk':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SearchResult:
    """Result from vector similarity search."""
    chunk: CodeChunk
    similarity_score: float
    distance: float


class CodeChunker:
    """Handles chunking of code into meaningful segments for embedding."""
    
    def __init__(self, max_chunk_size: int = 1000, overlap_size: int = 100):
        """
        Initialize code chunker.
        
        Args:
            max_chunk_size: Maximum size of code chunks in characters
            overlap_size: Overlap between adjacent chunks in characters
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
    
    def chunk_parsed_file(self, parsed_file: ParsedFile) -> List[CodeChunk]:
        """
        Chunk a parsed file into meaningful segments.
        
        Args:
            parsed_file: Parsed file to chunk
            
        Returns:
            List of code chunks
        """
        chunks = []
        
        # Chunk functions
        for func in parsed_file.functions:
            chunk = self._create_function_chunk(parsed_file, func)
            if chunk:
                chunks.append(chunk)
        
        # Chunk classes
        for cls in parsed_file.classes:
            chunk = self._create_class_chunk(parsed_file, cls)
            if chunk:
                chunks.append(chunk)
        
        # Chunk module-level code
        module_chunks = self._create_module_chunks(parsed_file)
        chunks.extend(module_chunks)
        
        return chunks
    
    def _create_function_chunk(self, parsed_file: ParsedFile, function: Function) -> Optional[CodeChunk]:
        """Create a chunk for a function."""
        try:
            lines = parsed_file.content.splitlines()
            start_idx = max(0, function.line_start - 1)
            end_idx = min(len(lines), function.line_end)
            
            content = '\n'.join(lines[start_idx:end_idx])
            
            # Add some context around the function
            context_start = max(0, start_idx - 2)
            context_end = min(len(lines), end_idx + 2)
            context_content = '\n'.join(lines[context_start:context_end])
            
            chunk_id = self._generate_chunk_id(parsed_file.path, 'function', function.name, function.line_start)
            
            return CodeChunk(
                id=chunk_id,
                content=content,
                chunk_type='function',
                file_path=parsed_file.path,
                start_line=function.line_start,
                end_line=function.line_end,
                metadata={
                    'function_name': function.name,
                    'parameters': function.parameters,
                    'return_type': function.return_type,
                    'docstring': function.docstring,
                    'complexity': function.complexity,
                    'is_async': function.is_async,
                    'is_method': function.is_method,
                    'class_name': function.class_name,
                    'decorators': function.decorators,
                    'language': parsed_file.language,
                    'context_content': context_content
                }
            )
        except Exception as e:
            logger.warning(f"Failed to create function chunk for {function.name}: {e}")
            return None
    
    def _create_class_chunk(self, parsed_file: ParsedFile, cls: Class) -> Optional[CodeChunk]:
        """Create a chunk for a class."""
        try:
            lines = parsed_file.content.splitlines()
            start_idx = max(0, cls.line_start - 1)
            end_idx = min(len(lines), cls.line_end)
            
            content = '\n'.join(lines[start_idx:end_idx])
            
            # For large classes, create a summary chunk with class definition and method signatures
            if len(content) > self.max_chunk_size:
                content = self._create_class_summary(parsed_file, cls)
            
            chunk_id = self._generate_chunk_id(parsed_file.path, 'class', cls.name, cls.line_start)
            
            return CodeChunk(
                id=chunk_id,
                content=content,
                chunk_type='class',
                file_path=parsed_file.path,
                start_line=cls.line_start,
                end_line=cls.line_end,
                metadata={
                    'class_name': cls.name,
                    'base_classes': cls.base_classes,
                    'docstring': cls.docstring,
                    'decorators': cls.decorators,
                    'method_count': len(cls.methods),
                    'method_names': [m.name for m in cls.methods],
                    'language': parsed_file.language
                }
            )
        except Exception as e:
            logger.warning(f"Failed to create class chunk for {cls.name}: {e}")
            return None
    
    def _create_class_summary(self, parsed_file: ParsedFile, cls: Class) -> str:
        """Create a summary of a large class."""
        lines = parsed_file.content.splitlines()
        summary_lines = []
        
        # Add class definition
        class_start = max(0, cls.line_start - 1)
        class_def_end = min(class_start + 10, len(lines))  # First 10 lines of class
        summary_lines.extend(lines[class_start:class_def_end])
        
        # Add method signatures
        summary_lines.append("\n# Method signatures:")
        for method in cls.methods:
            method_start = max(0, method.line_start - 1)
            if method_start < len(lines):
                method_line = lines[method_start].strip()
                summary_lines.append(f"# {method_line}")
        
        return '\n'.join(summary_lines)
    
    def _create_module_chunks(self, parsed_file: ParsedFile) -> List[CodeChunk]:
        """Create chunks for module-level code."""
        chunks = []
        lines = parsed_file.content.splitlines()
        
        # Find module-level code (not inside functions or classes)
        occupied_lines = set()
        
        # Mark lines occupied by functions and classes
        for func in parsed_file.functions:
            for line_num in range(func.line_start, func.line_end + 1):
                occupied_lines.add(line_num)
        
        for cls in parsed_file.classes:
            for line_num in range(cls.line_start, cls.line_end + 1):
                occupied_lines.add(line_num)
        
        # Find continuous blocks of module-level code
        current_block = []
        current_start = None
        
        for i, line in enumerate(lines, 1):
            if i not in occupied_lines and line.strip():
                if current_start is None:
                    current_start = i
                current_block.append(line)
            else:
                if current_block and len('\n'.join(current_block)) > 50:  # Minimum chunk size
                    chunk = self._create_module_chunk(
                        parsed_file, current_block, current_start, i - 1
                    )
                    if chunk:
                        chunks.append(chunk)
                current_block = []
                current_start = None
        
        # Handle remaining block
        if current_block and len('\n'.join(current_block)) > 50:
            chunk = self._create_module_chunk(
                parsed_file, current_block, current_start, len(lines)
            )
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _create_module_chunk(
        self, 
        parsed_file: ParsedFile, 
        lines: List[str], 
        start_line: int, 
        end_line: int
    ) -> Optional[CodeChunk]:
        """Create a module-level code chunk."""
        try:
            content = '\n'.join(lines)
            chunk_id = self._generate_chunk_id(parsed_file.path, 'module', 'module_code', start_line)
            
            return CodeChunk(
                id=chunk_id,
                content=content,
                chunk_type='module',
                file_path=parsed_file.path,
                start_line=start_line,
                end_line=end_line,
                metadata={
                    'language': parsed_file.language,
                    'imports': [imp.module for imp in parsed_file.imports],
                    'line_count': len(lines)
                }
            )
        except Exception as e:
            logger.warning(f"Failed to create module chunk: {e}")
            return None
    
    def _generate_chunk_id(self, file_path: str, chunk_type: str, name: str, line_start: int) -> str:
        """Generate a unique ID for a code chunk."""
        content = f"{file_path}:{chunk_type}:{name}:{line_start}"
        return hashlib.md5(content.encode()).hexdigest()


class MockVectorStore:
    """Mock vector store for when ChromaDB is not available."""
    
    def __init__(self, *args, **kwargs):
        self.chunks = {}
        self.embeddings = {}
        logger.warning("Using mock vector store - ChromaDB not available")
    
    def add_chunks(self, chunks: List[CodeChunk]) -> None:
        """Add chunks to mock store."""
        for chunk in chunks:
            self.chunks[chunk.id] = chunk
            # Mock embedding as simple hash
            self.embeddings[chunk.id] = hash(chunk.content) % 1000
    
    def search_similar(
        self, 
        query: str, 
        limit: int = 10,
        chunk_types: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Mock similarity search with filtering."""
        query_hash = hash(query) % 1000
        results = []
        
        for chunk_id, chunk in self.chunks.items():
            # Apply filters
            if chunk_types and chunk.chunk_type not in chunk_types:
                continue
            if file_paths and chunk.file_path not in file_paths:
                continue
            
            embedding = self.embeddings[chunk_id]
            distance = abs(embedding - query_hash)
            similarity = max(0, 1 - distance / 1000)
            
            results.append(SearchResult(
                chunk=chunk,
                similarity_score=similarity,
                distance=distance
            ))
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:limit]
    
    def delete_collection(self) -> None:
        """Clear mock store."""
        self.chunks.clear()
        self.embeddings.clear()
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get mock collection info."""
        return {
            'total_chunks': len(self.chunks),
            'chunk_types': list(set(chunk.chunk_type for chunk in self.chunks.values())),
            'files': list(set(chunk.file_path for chunk in self.chunks.values()))
        }


class ChromaVectorStore:
    """ChromaDB-based vector store for code embeddings."""
    
    def __init__(
        self, 
        collection_name: str = "code_quality_chunks",
        persist_directory: Optional[str] = None,
        embedding_function: Optional[str] = "sentence-transformers"
    ):
        """
        Initialize ChromaDB vector store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the database
            embedding_function: Embedding function to use
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is required but not installed")
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        if persist_directory:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self.client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False)
            )
        
        # Set up embedding function
        if embedding_function == "sentence-transformers":
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        else:
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_fn
            )
            logger.info(f"Loaded existing ChromaDB collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_fn
            )
            logger.info(f"Created new ChromaDB collection: {collection_name}")
    
    def add_chunks(self, chunks: List[CodeChunk]) -> None:
        """
        Add code chunks to the vector store.
        
        Args:
            chunks: List of code chunks to add
        """
        if not chunks:
            return
        
        try:
            # Prepare data for ChromaDB
            ids = [chunk.id for chunk in chunks]
            documents = [chunk.content for chunk in chunks]
            
            # Sanitize metadata for ChromaDB (only supports str, int, float, bool - no None)
            metadatas = []
            for chunk in chunks:
                sanitized_metadata = {}
                for key, value in chunk.metadata.items():
                    if value is None:
                        # Skip None values as ChromaDB doesn't handle them well
                        continue
                    elif isinstance(value, (str, int, float, bool)):
                        sanitized_metadata[key] = value
                    elif isinstance(value, list):
                        # Convert lists to comma-separated strings
                        sanitized_metadata[key] = ','.join(str(v) for v in value) if value else ''
                    else:
                        # Convert other types to strings
                        sanitized_metadata[key] = str(value)
                
                # Add chunk-specific metadata (ensure no None values)
                sanitized_metadata.update({
                    'chunk_type': chunk.chunk_type,
                    'file_path': chunk.file_path,
                    'start_line': chunk.start_line,
                    'end_line': chunk.end_line
                })
                
                metadatas.append(sanitized_metadata)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks to vector store")
            
        except Exception as e:
            logger.error(f"Failed to add chunks to vector store: {e}")
            raise
    
    def search_similar(
        self, 
        query: str, 
        limit: int = 10,
        chunk_types: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Search for similar code chunks.
        
        Args:
            query: Search query
            limit: Maximum number of results
            chunk_types: Filter by chunk types
            file_paths: Filter by file paths
            
        Returns:
            List of search results
        """
        try:
            # Build where clause for filtering
            where_clause = {}
            if chunk_types:
                where_clause["chunk_type"] = {"$in": chunk_types}
            if file_paths:
                where_clause["file_path"] = {"$in": file_paths}
            
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            # Convert to SearchResult objects
            search_results = []
            if results['ids'] and results['ids'][0]:
                for i, chunk_id in enumerate(results['ids'][0]):
                    document = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    
                    # Reconstruct CodeChunk
                    chunk = CodeChunk(
                        id=chunk_id,
                        content=document,
                        chunk_type=metadata.get('chunk_type', 'unknown'),
                        file_path=metadata.get('file_path', ''),
                        start_line=metadata.get('start_line', 0),
                        end_line=metadata.get('end_line', 0),
                        metadata=metadata
                    )
                    
                    # Convert distance to similarity score (0-1, higher is more similar)
                    similarity_score = max(0, 1 - distance)
                    
                    search_results.append(SearchResult(
                        chunk=chunk,
                        similarity_score=similarity_score,
                        distance=distance
                    ))
            
            logger.debug(f"Found {len(search_results)} similar chunks for query")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search vector store: {e}")
            return []
    
    def delete_collection(self) -> None:
        """Delete the entire collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection: {e}")
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            count = self.collection.count()
            
            # Get sample of metadata to understand chunk types and files
            sample_results = self.collection.get(limit=100)
            
            chunk_types = set()
            files = set()
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    if 'chunk_type' in metadata:
                        chunk_types.add(metadata['chunk_type'])
                    if 'file_path' in metadata:
                        files.add(metadata['file_path'])
            
            return {
                'total_chunks': count,
                'chunk_types': list(chunk_types),
                'files': list(files),
                'collection_name': self.collection_name,
                'persist_directory': self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {'error': str(e)}


class VectorStoreManager:
    """High-level manager for vector store operations."""
    
    def __init__(
        self, 
        use_chromadb: bool = True,
        collection_name: str = "code_quality_chunks",
        persist_directory: Optional[str] = None,
        max_chunk_size: int = 1000
    ):
        """
        Initialize vector store manager.
        
        Args:
            use_chromadb: Whether to use ChromaDB (falls back to mock if unavailable)
            collection_name: Name of the collection
            persist_directory: Directory for persistent storage
            max_chunk_size: Maximum size of code chunks
        """
        self.chunker = CodeChunker(max_chunk_size=max_chunk_size)
        
        # Initialize vector store
        if use_chromadb and CHROMADB_AVAILABLE:
            try:
                self.vector_store = ChromaVectorStore(
                    collection_name=collection_name,
                    persist_directory=persist_directory
                )
                self.store_type = "chromadb"
            except Exception as e:
                logger.warning(f"Failed to initialize ChromaDB, using mock store: {e}")
                self.vector_store = MockVectorStore()
                self.store_type = "mock"
        else:
            self.vector_store = MockVectorStore()
            self.store_type = "mock"
        
        logger.info(f"Initialized vector store manager with {self.store_type} backend")
    
    def index_analysis_result(self, analysis_result: AnalysisResult) -> int:
        """
        Index an analysis result in the vector store.
        
        Args:
            analysis_result: Analysis result to index
            
        Returns:
            Number of chunks created
        """
        all_chunks = []
        
        # Process each parsed file
        for parsed_file in analysis_result.parsed_files:
            try:
                chunks = self.chunker.chunk_parsed_file(parsed_file)
                all_chunks.extend(chunks)
                logger.debug(f"Created {len(chunks)} chunks for {parsed_file.path}")
            except Exception as e:
                logger.warning(f"Failed to chunk file {parsed_file.path}: {e}")
        
        # Add chunks to vector store
        if all_chunks:
            self.vector_store.add_chunks(all_chunks)
        
        logger.info(f"Indexed {len(all_chunks)} code chunks from {len(analysis_result.parsed_files)} files")
        return len(all_chunks)
    
    def search_code(
        self, 
        query: str, 
        limit: int = 10,
        chunk_types: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Search for relevant code chunks.
        
        Args:
            query: Search query
            limit: Maximum number of results
            chunk_types: Filter by chunk types ('function', 'class', 'module')
            file_paths: Filter by specific file paths
            
        Returns:
            List of search results
        """
        return self.vector_store.search_similar(
            query=query,
            limit=limit,
            chunk_types=chunk_types,
            file_paths=file_paths
        )
    
    def clear_index(self) -> None:
        """Clear the entire vector store index."""
        self.vector_store.delete_collection()
        logger.info("Cleared vector store index")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        stats = self.vector_store.get_collection_info()
        stats['store_type'] = self.store_type
        stats['chromadb_available'] = CHROMADB_AVAILABLE
        return stats


def create_vector_store_manager(
    persist_directory: Optional[str] = None,
    collection_name: str = "code_quality_chunks"
) -> VectorStoreManager:
    """
    Create a vector store manager with default configuration.
    
    Args:
        persist_directory: Directory for persistent storage
        collection_name: Name of the collection
        
    Returns:
        Configured VectorStoreManager instance
    """
    return VectorStoreManager(
        use_chromadb=True,
        collection_name=collection_name,
        persist_directory=persist_directory
    )