"""
Tests for test fixtures and data validation.
Ensures that test fixtures are properly structured and loadable.
"""

import pytest
import json
from pathlib import Path
from tests.fixtures.fixture_loader import (
    FixtureLoader, 
    load_security_samples,
    load_performance_samples,
    load_multi_language_scenario
)

class TestFixtureLoader:
    """Test the fixture loader functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = FixtureLoader()
    
    def test_load_synthetic_security_sample(self):
        """Test loading synthetic security sample."""
        fixture = self.loader.load_synthetic_sample("security_issues")
        
        assert fixture.name == "security_issues"
        assert fixture.language == "python"
        assert len(fixture.content) > 0
        assert len(fixture.expected_issues) > 0
        
        # Verify expected issues structure
        for issue in fixture.expected_issues:
            assert "category" in issue
            assert "severity" in issue
            assert "type" in issue
            assert "description" in issue
            assert issue["category"] == "security"
    
    def test_load_synthetic_performance_sample(self):
        """Test loading synthetic performance sample."""
        fixture = self.loader.load_synthetic_sample("performance_issues")
        
        assert fixture.name == "performance_issues"
        assert fixture.language == "python"
        assert len(fixture.content) > 0
        assert len(fixture.expected_issues) > 0
        
        # Verify expected issues structure
        for issue in fixture.expected_issues:
            assert "category" in issue
            assert "severity" in issue
            assert "type" in issue
            assert "description" in issue
            assert issue["category"] == "performance"
    
    def test_load_javascript_sample(self):
        """Test loading JavaScript sample."""
        fixture = self.loader.load_synthetic_sample("javascript_issues")
        
        assert fixture.name == "javascript_issues"
        assert fixture.language == "javascript"
        assert len(fixture.content) > 0
        assert "function" in fixture.content  # Should contain JS code
    
    def test_load_real_world_sample(self):
        """Test loading real-world sample."""
        fixture = self.loader.load_real_world_sample("flask_app")
        
        assert fixture.name == "flask_app"
        assert fixture.language == "python"
        assert len(fixture.content) > 0
        assert "Flask" in fixture.content  # Should contain Flask code
    
    def test_load_multi_language_scenario(self):
        """Test loading multi-language analysis scenario."""
        scenario = self.loader.load_analysis_scenario("multi_language_project")
        
        assert scenario.name == "multi_language_project"
        assert len(scenario.files) > 0
        
        # Should contain both Python and JavaScript files
        languages = {file_info["language"] for file_info in scenario.files}
        assert "python" in languages
        assert "javascript" in languages
        
        # Verify file structure
        file_paths = {file_info["path"] for file_info in scenario.files}
        assert any("backend" in path for path in file_paths)
        assert any("frontend" in path for path in file_paths)
    
    def test_list_synthetic_samples(self):
        """Test listing synthetic samples."""
        samples = self.loader.list_synthetic_samples()
        
        assert len(samples) > 0
        assert "security_issues" in samples
        assert "performance_issues" in samples
        assert "complexity_issues" in samples
        assert "duplication_issues" in samples
        assert "documentation_issues" in samples
        assert "testing_issues" in samples
    
    def test_list_analysis_scenarios(self):
        """Test listing analysis scenarios."""
        scenarios = self.loader.list_analysis_scenarios()
        
        assert len(scenarios) > 0
        assert "multi_language_project" in scenarios
    
    def test_get_samples_by_category(self):
        """Test getting samples by category."""
        security_samples = self.loader.get_samples_by_category("security")
        performance_samples = self.loader.get_samples_by_category("performance")
        
        assert len(security_samples) > 0
        assert len(performance_samples) > 0
        
        # Verify categories
        for sample in security_samples:
            assert "security" in sample.name.lower()
        
        for sample in performance_samples:
            assert "performance" in sample.name.lower()

class TestFixtureContent:
    """Test the content and structure of fixtures."""
    
    def test_security_issues_content(self):
        """Test that security issues fixture contains expected vulnerabilities."""
        loader = FixtureLoader()
        fixture = loader.load_synthetic_sample("security_issues")
        
        content = fixture.content
        
        # Should contain various security issues
        assert "hardcoded" in content.lower()
        assert "sql" in content.lower() or "injection" in content.lower()
        assert "pickle" in content.lower()
        assert "subprocess" in content.lower()
        assert "eval" in content.lower()
    
    def test_performance_issues_content(self):
        """Test that performance issues fixture contains expected problems."""
        loader = FixtureLoader()
        fixture = loader.load_synthetic_sample("performance_issues")
        
        content = fixture.content
        
        # Should contain various performance issues
        assert "for" in content  # Should have loops
        assert "+=" in content   # String concatenation
        assert "range" in content  # Inefficient operations
    
    def test_complexity_issues_content(self):
        """Test that complexity issues fixture contains high complexity code."""
        loader = FixtureLoader()
        fixture = loader.load_synthetic_sample("complexity_issues")
        
        content = fixture.content
        
        # Should contain nested conditions and complex logic
        nested_if_count = content.count("if ")
        assert nested_if_count > 10  # Should have many conditional statements
        
        # Should have deeply nested structures
        assert "if" in content and "else" in content
    
    def test_duplication_issues_content(self):
        """Test that duplication issues fixture contains duplicated code."""
        loader = FixtureLoader()
        fixture = loader.load_synthetic_sample("duplication_issues")
        
        content = fixture.content
        
        # Should contain similar function definitions
        function_count = content.count("def ")
        assert function_count > 5  # Should have multiple functions
        
        # Should have repeated patterns
        assert "validate" in content.lower()  # Common validation patterns
    
    def test_documentation_issues_content(self):
        """Test that documentation issues fixture contains doc problems."""
        loader = FixtureLoader()
        fixture = loader.load_synthetic_sample("documentation_issues")
        
        content = fixture.content
        
        # Should have functions with missing or poor documentation
        function_lines = [line for line in content.split('\n') if line.strip().startswith('def ')]
        assert len(function_lines) > 5  # Should have multiple functions
        
        # Should have some docstrings and some missing
        assert '"""' in content  # Some docstrings present
    
    def test_testing_issues_content(self):
        """Test that testing issues fixture contains testing problems."""
        loader = FixtureLoader()
        fixture = loader.load_synthetic_sample("testing_issues")
        
        content = fixture.content
        
        # Should contain test-related code
        assert "unittest" in content or "test" in content.lower()
        assert "assert" in content  # Should have assertions
        assert "def test" in content  # Should have test methods

class TestExpectedResults:
    """Test the expected results structure and validity."""
    
    def test_security_expected_results_structure(self):
        """Test security expected results structure."""
        loader = FixtureLoader()
        fixture = loader.load_synthetic_sample("security_issues")
        
        assert len(fixture.expected_issues) > 0
        assert fixture.expected_metrics is not None
        
        # Verify issue structure
        for issue in fixture.expected_issues:
            required_fields = ["category", "severity", "type", "description"]
            for field in required_fields:
                assert field in issue, f"Missing field: {field}"
            
            # Verify severity levels
            assert issue["severity"] in ["low", "medium", "high", "critical"]
            assert issue["category"] == "security"
        
        # Verify metrics structure
        metrics = fixture.expected_metrics
        assert "security_score" in metrics
        assert "total_security_issues" in metrics
        assert isinstance(metrics["security_score"], (int, float))
        assert isinstance(metrics["total_security_issues"], int)
    
    def test_performance_expected_results_structure(self):
        """Test performance expected results structure."""
        loader = FixtureLoader()
        fixture = loader.load_synthetic_sample("performance_issues")
        
        assert len(fixture.expected_issues) > 0
        assert fixture.expected_metrics is not None
        
        # Verify issue structure
        for issue in fixture.expected_issues:
            required_fields = ["category", "severity", "type", "description"]
            for field in required_fields:
                assert field in issue, f"Missing field: {field}"
            
            assert issue["category"] == "performance"
        
        # Verify metrics structure
        metrics = fixture.expected_metrics
        assert "performance_score" in metrics
        assert "total_performance_issues" in metrics

class TestConvenienceFunctions:
    """Test convenience functions for loading fixtures."""
    
    def test_load_security_samples(self):
        """Test loading security samples via convenience function."""
        samples = load_security_samples()
        
        assert len(samples) > 0
        for sample in samples:
            assert "security" in sample.name.lower()
    
    def test_load_performance_samples(self):
        """Test loading performance samples via convenience function."""
        samples = load_performance_samples()
        
        assert len(samples) > 0
        for sample in samples:
            assert "performance" in sample.name.lower()
    
    def test_load_multi_language_scenario(self):
        """Test loading multi-language scenario via convenience function."""
        scenario = load_multi_language_scenario()
        
        assert scenario.name == "multi_language_project"
        assert len(scenario.files) > 0
        
        # Should have multiple languages
        languages = {file_info["language"] for file_info in scenario.files}
        assert len(languages) > 1

class TestFixtureValidation:
    """Test validation of fixture data integrity."""
    
    def test_all_synthetic_samples_loadable(self):
        """Test that all synthetic samples can be loaded without errors."""
        loader = FixtureLoader()
        samples = loader.list_synthetic_samples()
        
        for sample_name in samples:
            try:
                fixture = loader.load_synthetic_sample(sample_name)
                assert fixture.name == sample_name
                assert len(fixture.content) > 0
            except Exception as e:
                pytest.fail(f"Failed to load synthetic sample '{sample_name}': {e}")
    
    def test_all_real_world_samples_loadable(self):
        """Test that all real-world samples can be loaded without errors."""
        loader = FixtureLoader()
        samples = loader.list_real_world_samples()
        
        for sample_name in samples:
            try:
                fixture = loader.load_real_world_sample(sample_name)
                assert fixture.name == sample_name
                assert len(fixture.content) > 0
            except Exception as e:
                pytest.fail(f"Failed to load real-world sample '{sample_name}': {e}")
    
    def test_all_scenarios_loadable(self):
        """Test that all analysis scenarios can be loaded without errors."""
        loader = FixtureLoader()
        scenarios = loader.list_analysis_scenarios()
        
        for scenario_name in scenarios:
            try:
                scenario = loader.load_analysis_scenario(scenario_name)
                assert scenario.name == scenario_name
                assert len(scenario.files) > 0
            except Exception as e:
                pytest.fail(f"Failed to load analysis scenario '{scenario_name}': {e}")
    
    def test_expected_results_json_valid(self):
        """Test that all expected results JSON files are valid."""
        loader = FixtureLoader()
        expected_dir = loader.expected_dir
        
        for json_file in expected_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Basic structure validation
                if "expected_issues" in data:
                    assert isinstance(data["expected_issues"], list)
                
                if "expected_metrics" in data:
                    assert isinstance(data["expected_metrics"], dict)
                    
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {json_file}: {e}")
            except Exception as e:
                pytest.fail(f"Error loading {json_file}: {e}")