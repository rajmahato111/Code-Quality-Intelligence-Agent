"""Tests for vector store and RAG functionality."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from code_quality_agent.rag import (
    CodeChunk, SearchResult, CodeChunker, VectorStoreManager,
    MockVectorStore, create_vector_store_manager, CHROMADB_AVAILABLE
)
from code_quality_agent.core.models import (
    ParsedFile, Function, Class, Import, AnalysisResult, QualityMetrics
)


class TestCodeChunk:
    """Test cases for CodeChunk data class."""
    
    def test_code_chunk_creation(self):
        """Test CodeChunk creation and serialization."""
        chunk = CodeChunk(
            id="test-chunk-1",
            content="def test_function():\n    return True",
            chunk_type="function",
            file_path="test.py",
            start_line=10,
            end_line=12,
            metadata={"function_name": "test_function", "language": "python"}
        )
        
        assert chunk.id == "test-chunk-1"
        assert chunk.chunk_type == "function"
        assert chunk.file_path == "test.py"
        assert chunk.metadata["function_name"] == "test_function"
        
        # Test serialization
        chunk_dict = chunk.to_dict()
        assert isinstance(chunk_dict, dict)
        assert chunk_dict["id"] == "test-chunk-1"
        assert chunk_dict["content"] == "def test_function():\n    return True"
        
        # Test deserialization
        reconstructed = CodeChunk.from_dict(chunk_dict)
        assert reconstructed.id == chunk.id
        assert reconstructed.content == chunk.content
        assert reconstructed.metadata == chunk.metadata


class TestCodeChunker:
    """Test cases for CodeChunker."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = CodeChunker(max_chunk_size=500, overlap_size=50)
        
        # Create test parsed file
        self.test_function = Function(
            name="test_function",
            line_start=10,
            line_end=15,
            parameters=["param1", "param2"],
            return_type="bool",
            docstring="Test function docstring",
            complexity=3,
            is_async=False,
            is_method=False
        )
        
        self.test_class = Class(
            name="TestClass",
            line_start=20,
            line_end=35,
            methods=[
                Function(
                    name="method1",
                    line_start=22,
                    line_end=25,
                    parameters=["self"],
                    is_method=True,
                    class_name="TestClass"
                )
            ],
            docstring="Test class docstring"
        )
        
        self.test_import = Import(
            module="os",
            names=["path"],
            is_from_import=True,
            line_number=1
        )
        
        self.parsed_file = ParsedFile(
            path="test_file.py",
            language="python",
            content="""import os
from pathlib import Path

# Module level comment
MODULE_CONSTANT = "test"

def helper_function():
    '''Helper function'''
    return "helper"

def test_function(param1, param2):
    '''Test function docstring'''
    if param1:
        return param2
    return False

# Another module comment
ANOTHER_CONSTANT = 42

class TestClass:
    '''Test class docstring'''
    
    def method1(self):
        '''Method docstring'''
        return "method1"
    
    def method2(self):
        return "method2"

# Final module code
if __name__ == "__main__":
    print("Running tests")""",
            functions=[
                Function(name="helper_function", line_start=7, line_end=9),
                Function(name="test_function", line_start=11, line_end=15, 
                        parameters=["param1", "param2"], docstring="Test function docstring"),
            ],
            classes=[
                Class(name="TestClass", line_start=20, line_end=28,
                     methods=[
                         Function(name="method1", line_start=23, line_end=25, is_method=True),
                         Function(name="method2", line_start=27, line_end=28, is_method=True)
                     ],
                     docstring="Test class docstring")
            ],
            imports=[
                Import(module="os", line_number=1),
                Import(module="pathlib", names=["Path"], is_from_import=True, line_number=2)
            ]
        )
    
    def test_chunk_parsed_file(self):
        """Test chunking a complete parsed file."""
        chunks = self.chunker.chunk_parsed_file(self.parsed_file)
        
        assert len(chunks) > 0
        
        # Should have function chunks
        function_chunks = [c for c in chunks if c.chunk_type == "function"]
        assert len(function_chunks) == 2  # helper_function and test_function
        
        # Should have class chunk
        class_chunks = [c for c in chunks if c.chunk_type == "class"]
        assert len(class_chunks) == 1
        
        # Should have module chunks
        module_chunks = [c for c in chunks if c.chunk_type == "module"]
        assert len(module_chunks) > 0
        
        # Verify function chunk content
        test_func_chunk = next((c for c in function_chunks if "test_function" in c.content), None)
        assert test_func_chunk is not None
        assert "def test_function(param1, param2):" in test_func_chunk.content
        assert test_func_chunk.metadata["function_name"] == "test_function"
        assert test_func_chunk.metadata["parameters"] == ["param1", "param2"]
    
    def test_function_chunk_creation(self):
        """Test creation of function chunks."""
        chunk = self.chunker._create_function_chunk(self.parsed_file, self.parsed_file.functions[1])
        
        assert chunk is not None
        assert chunk.chunk_type == "function"
        assert chunk.file_path == "test_file.py"
        assert "def test_function" in chunk.content
        assert chunk.metadata["function_name"] == "test_function"
        assert chunk.metadata["language"] == "python"
        assert "context_content" in chunk.metadata
    
    def test_class_chunk_creation(self):
        """Test creation of class chunks."""
        chunk = self.chunker._create_class_chunk(self.parsed_file, self.parsed_file.classes[0])
        
        assert chunk is not None
        assert chunk.chunk_type == "class"
        assert chunk.file_path == "test_file.py"
        assert "class TestClass:" in chunk.content
        assert chunk.metadata["class_name"] == "TestClass"
        assert chunk.metadata["method_count"] == 2
        assert "method1" in chunk.metadata["method_names"]
        assert "method2" in chunk.metadata["method_names"]
    
    def test_module_chunks_creation(self):
        """Test creation of module-level chunks."""
        chunks = self.chunker._create_module_chunks(self.parsed_file)
        
        assert len(chunks) > 0
        
        # Should contain module-level constants and imports
        module_content = '\n'.join(chunk.content for chunk in chunks)
        assert "MODULE_CONSTANT" in module_content or "ANOTHER_CONSTANT" in module_content
    
    def test_chunk_id_generation(self):
        """Test unique chunk ID generation."""
        id1 = self.chunker._generate_chunk_id("file1.py", "function", "func1", 10)
        id2 = self.chunker._generate_chunk_id("file1.py", "function", "func1", 10)
        id3 = self.chunker._generate_chunk_id("file1.py", "function", "func2", 10)
        
        # Same parameters should generate same ID
        assert id1 == id2
        
        # Different parameters should generate different IDs
        assert id1 != id3
        
        # IDs should be valid MD5 hashes
        assert len(id1) == 32
        assert all(c in '0123456789abcdef' for c in id1)


class TestMockVectorStore:
    """Test cases for MockVectorStore."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_store = MockVectorStore()
        
        self.test_chunks = [
            CodeChunk(
                id="chunk1",
                content="def function1(): return True",
                chunk_type="function",
                file_path="file1.py",
                start_line=1,
                end_line=1,
                metadata={"function_name": "function1"}
            ),
            CodeChunk(
                id="chunk2",
                content="class TestClass: pass",
                chunk_type="class",
                file_path="file2.py",
                start_line=1,
                end_line=1,
                metadata={"class_name": "TestClass"}
            )
        ]
    
    def test_add_chunks(self):
        """Test adding chunks to mock store."""
        self.mock_store.add_chunks(self.test_chunks)
        
        assert len(self.mock_store.chunks) == 2
        assert "chunk1" in self.mock_store.chunks
        assert "chunk2" in self.mock_store.chunks
        assert len(self.mock_store.embeddings) == 2
    
    def test_search_similar(self):
        """Test similarity search in mock store."""
        self.mock_store.add_chunks(self.test_chunks)
        
        results = self.mock_store.search_similar("function", limit=5)
        
        assert len(results) <= 2
        assert all(isinstance(result, SearchResult) for result in results)
        assert all(0 <= result.similarity_score <= 1 for result in results)
        
        # Results should be sorted by similarity
        if len(results) > 1:
            assert results[0].similarity_score >= results[1].similarity_score
    
    def test_collection_info(self):
        """Test getting collection information."""
        self.mock_store.add_chunks(self.test_chunks)
        
        info = self.mock_store.get_collection_info()
        
        assert info["total_chunks"] == 2
        assert "function" in info["chunk_types"]
        assert "class" in info["chunk_types"]
        assert "file1.py" in info["files"]
        assert "file2.py" in info["files"]
    
    def test_delete_collection(self):
        """Test clearing the mock store."""
        self.mock_store.add_chunks(self.test_chunks)
        assert len(self.mock_store.chunks) == 2
        
        self.mock_store.delete_collection()
        
        assert len(self.mock_store.chunks) == 0
        assert len(self.mock_store.embeddings) == 0


class TestVectorStoreManager:
    """Test cases for VectorStoreManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use mock store for testing
        self.manager = VectorStoreManager(use_chromadb=False)
        
        # Create test analysis result
        self.parsed_file = ParsedFile(
            path="test.py",
            language="python",
            content="""def test_function():
    '''Test function'''
    return True

class TestClass:
    '''Test class'''
    def method(self):
        return "test"
""",
            functions=[
                Function(name="test_function", line_start=1, line_end=3, 
                        docstring="Test function")
            ],
            classes=[
                Class(name="TestClass", line_start=5, line_end=8,
                     docstring="Test class",
                     methods=[Function(name="method", line_start=7, line_end=8, is_method=True)])
            ]
        )
        
        self.analysis_result = AnalysisResult(
            analysis_id="test-analysis",
            codebase_path="/test/path",
            parsed_files=[self.parsed_file],
            issues=[],
            metrics=QualityMetrics()
        )
    
    def test_initialization(self):
        """Test VectorStoreManager initialization."""
        assert self.manager.store_type == "mock"
        assert self.manager.chunker is not None
        assert self.manager.vector_store is not None
    
    def test_index_analysis_result(self):
        """Test indexing an analysis result."""
        chunk_count = self.manager.index_analysis_result(self.analysis_result)
        
        assert chunk_count > 0
        
        # Verify chunks were created and stored
        stats = self.manager.get_statistics()
        assert stats["total_chunks"] == chunk_count
        assert "function" in stats["chunk_types"]
        assert "class" in stats["chunk_types"]
    
    def test_search_code(self):
        """Test searching for code chunks."""
        # Index the analysis result first
        self.manager.index_analysis_result(self.analysis_result)
        
        # Search for function-related code
        results = self.manager.search_code("function test", limit=5)
        
        assert len(results) > 0
        assert all(isinstance(result, SearchResult) for result in results)
        
        # Search with type filter
        function_results = self.manager.search_code(
            "test", 
            limit=5, 
            chunk_types=["function"]
        )
        
        assert all(result.chunk.chunk_type == "function" for result in function_results)
    
    def test_clear_index(self):
        """Test clearing the vector store index."""
        # Index some data
        self.manager.index_analysis_result(self.analysis_result)
        stats_before = self.manager.get_statistics()
        assert stats_before["total_chunks"] > 0
        
        # Clear the index
        self.manager.clear_index()
        
        # Verify it's empty
        stats_after = self.manager.get_statistics()
        assert stats_after["total_chunks"] == 0
    
    def test_get_statistics(self):
        """Test getting vector store statistics."""
        stats = self.manager.get_statistics()
        
        assert "store_type" in stats
        assert "chromadb_available" in stats
        assert "total_chunks" in stats
        assert stats["store_type"] == "mock"
        
        # After indexing
        self.manager.index_analysis_result(self.analysis_result)
        stats_after = self.manager.get_statistics()
        
        assert stats_after["total_chunks"] > 0
        assert "chunk_types" in stats_after
        assert "files" in stats_after


class TestChromaDBIntegration:
    """Test cases for ChromaDB integration (if available)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not available")
    def test_chromadb_vector_store_creation(self):
        """Test creating ChromaDB vector store."""
        from code_quality_agent.rag.vector_store import ChromaVectorStore
        
        store = ChromaVectorStore(
            collection_name="test_collection",
            persist_directory=str(self.temp_dir)
        )
        
        assert store.collection_name == "test_collection"
        assert store.persist_directory == str(self.temp_dir)
        assert store.collection is not None
    
    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not available")
    def test_chromadb_add_and_search(self):
        """Test adding chunks and searching with ChromaDB."""
        from code_quality_agent.rag.vector_store import ChromaVectorStore
        
        store = ChromaVectorStore(
            collection_name="test_search",
            persist_directory=str(self.temp_dir)
        )
        
        # Create test chunks
        chunks = [
            CodeChunk(
                id="test1",
                content="def calculate_sum(a, b): return a + b",
                chunk_type="function",
                file_path="math.py",
                start_line=1,
                end_line=1,
                metadata={"function_name": "calculate_sum", "language": "python"}
            ),
            CodeChunk(
                id="test2",
                content="class Calculator: def add(self, x, y): return x + y",
                chunk_type="class",
                file_path="calc.py",
                start_line=1,
                end_line=1,
                metadata={"class_name": "Calculator", "language": "python"}
            )
        ]
        
        # Add chunks
        store.add_chunks(chunks)
        
        # Search for similar content
        results = store.search_similar("addition function", limit=5)
        
        assert len(results) > 0
        assert all(isinstance(result, SearchResult) for result in results)
        assert all(0 <= result.similarity_score <= 1 for result in results)
        
        # Test filtering by chunk type
        function_results = store.search_similar(
            "calculate", 
            limit=5, 
            chunk_types=["function"]
        )
        
        assert all(result.chunk.chunk_type == "function" for result in function_results)
    
    def test_vector_store_manager_with_chromadb(self):
        """Test VectorStoreManager with ChromaDB backend."""
        manager = VectorStoreManager(
            use_chromadb=True,
            persist_directory=str(self.temp_dir),
            collection_name="test_manager"
        )
        
        # Should use ChromaDB if available, otherwise fall back to mock
        expected_type = "chromadb" if CHROMADB_AVAILABLE else "mock"
        assert manager.store_type == expected_type


class TestFactoryFunction:
    """Test cases for factory functions."""
    
    def test_create_vector_store_manager(self):
        """Test factory function for creating vector store manager."""
        manager = create_vector_store_manager(
            collection_name="test_factory"
        )
        
        assert isinstance(manager, VectorStoreManager)
        assert manager.chunker is not None
        assert manager.vector_store is not None
    
    def test_create_with_persist_directory(self):
        """Test factory function with persistent directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = create_vector_store_manager(
                persist_directory=temp_dir,
                collection_name="test_persist"
            )
            
            assert isinstance(manager, VectorStoreManager)
            
            # If ChromaDB is available, should use persistent storage
            if CHROMADB_AVAILABLE:
                assert manager.store_type == "chromadb"


class TestEdgeCases:
    """Test cases for edge cases and error handling."""
    
    def test_empty_parsed_file(self):
        """Test chunking an empty parsed file."""
        chunker = CodeChunker()
        empty_file = ParsedFile(
            path="empty.py",
            language="python",
            content="",
            functions=[],
            classes=[],
            imports=[]
        )
        
        chunks = chunker.chunk_parsed_file(empty_file)
        assert isinstance(chunks, list)
        # May be empty or contain minimal module chunks
    
    def test_large_function_chunking(self):
        """Test chunking very large functions."""
        chunker = CodeChunker(max_chunk_size=100)  # Small chunk size
        
        large_content = "def large_function():\n" + "    # comment\n" * 50 + "    return True"
        
        large_function = Function(
            name="large_function",
            line_start=1,
            line_end=52
        )
        
        parsed_file = ParsedFile(
            path="large.py",
            language="python",
            content=large_content,
            functions=[large_function]
        )
        
        chunks = chunker.chunk_parsed_file(parsed_file)
        
        # Should still create chunks even for large functions
        assert len(chunks) > 0
        function_chunks = [c for c in chunks if c.chunk_type == "function"]
        assert len(function_chunks) > 0
    
    def test_invalid_line_numbers(self):
        """Test handling of invalid line numbers."""
        chunker = CodeChunker()
        
        # Function with invalid line numbers
        invalid_function = Function(
            name="invalid_function",
            line_start=100,  # Beyond file content
            line_end=105
        )
        
        parsed_file = ParsedFile(
            path="invalid.py",
            language="python",
            content="def valid_function():\n    return True",
            functions=[invalid_function]
        )
        
        # Should handle gracefully without crashing
        chunks = chunker.chunk_parsed_file(parsed_file)
        assert isinstance(chunks, list)


if __name__ == "__main__":
    pytest.main([__file__])