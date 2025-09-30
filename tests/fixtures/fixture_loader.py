"""
Test fixture loader for the Code Quality Intelligence Agent.
Provides utilities to load test data, expected results, and analysis scenarios.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class TestFixture:
    """Represents a test fixture with code and expected results."""
    name: str
    file_path: str
    content: str
    language: str
    expected_issues: List[Dict[str, Any]]
    expected_metrics: Dict[str, Any]
    description: str = ""

@dataclass
class AnalysisScenario:
    """Represents a complete analysis scenario with multiple files."""
    name: str
    description: str
    files: List[Dict[str, str]]  # List of {path, content, language}
    expected_results: Dict[str, Any]

class FixtureLoader:
    """Load and manage test fixtures for code quality analysis testing."""
    
    def __init__(self, fixtures_dir: Optional[str] = None):
        """Initialize fixture loader."""
        if fixtures_dir is None:
            fixtures_dir = Path(__file__).parent
        self.fixtures_dir = Path(fixtures_dir)
        self.synthetic_dir = self.fixtures_dir / "synthetic_samples"
        self.real_world_dir = self.fixtures_dir / "real_world_samples"
        self.scenarios_dir = self.fixtures_dir / "analysis_scenarios"
        self.expected_dir = self.fixtures_dir / "expected_results"
    
    def load_synthetic_sample(self, sample_name: str) -> TestFixture:
        """Load a synthetic code sample with known issues."""
        sample_file = self.synthetic_dir / f"{sample_name}.py"
        if not sample_file.exists():
            # Try JavaScript extension
            sample_file = self.synthetic_dir / f"{sample_name}.js"
        
        if not sample_file.exists():
            raise FileNotFoundError(f"Synthetic sample not found: {sample_name}")
        
        content = sample_file.read_text()
        language = self._detect_language(sample_file)
        
        # Load expected results if available
        expected_file = self.expected_dir / f"{sample_name}_expected.json"
        expected_issues = []
        expected_metrics = {}
        
        if expected_file.exists():
            expected_data = json.loads(expected_file.read_text())
            expected_issues = expected_data.get("expected_issues", [])
            expected_metrics = expected_data.get("expected_metrics", {})
        
        return TestFixture(
            name=sample_name,
            file_path=str(sample_file),
            content=content,
            language=language,
            expected_issues=expected_issues,
            expected_metrics=expected_metrics,
            description=f"Synthetic sample: {sample_name}"
        )
    
    def load_real_world_sample(self, sample_name: str) -> TestFixture:
        """Load a real-world code sample."""
        sample_files = list(self.real_world_dir.glob(f"{sample_name}.*"))
        if not sample_files:
            raise FileNotFoundError(f"Real-world sample not found: {sample_name}")
        
        sample_file = sample_files[0]
        content = sample_file.read_text()
        language = self._detect_language(sample_file)
        
        # Load expected results if available
        expected_file = self.expected_dir / f"{sample_name}_expected.json"
        expected_issues = []
        expected_metrics = {}
        
        if expected_file.exists():
            expected_data = json.loads(expected_file.read_text())
            expected_issues = expected_data.get("expected_issues", [])
            expected_metrics = expected_data.get("expected_metrics", {})
        
        return TestFixture(
            name=sample_name,
            file_path=str(sample_file),
            content=content,
            language=language,
            expected_issues=expected_issues,
            expected_metrics=expected_metrics,
            description=f"Real-world sample: {sample_name}"
        )
    
    def load_analysis_scenario(self, scenario_name: str) -> AnalysisScenario:
        """Load a complete analysis scenario with multiple files."""
        scenario_dir = self.scenarios_dir / scenario_name
        if not scenario_dir.exists():
            raise FileNotFoundError(f"Analysis scenario not found: {scenario_name}")
        
        # Read scenario description
        readme_file = scenario_dir / "README.md"
        description = ""
        if readme_file.exists():
            description = readme_file.read_text()
        
        # Collect all code files in the scenario
        files = []
        for file_path in scenario_dir.rglob("*"):
            if file_path.is_file() and file_path.name != "README.md":
                relative_path = file_path.relative_to(scenario_dir)
                content = file_path.read_text()
                language = self._detect_language(file_path)
                
                files.append({
                    "path": str(relative_path),
                    "content": content,
                    "language": language,
                    "full_path": str(file_path)
                })
        
        # Load expected results if available
        expected_file = self.expected_dir / f"{scenario_name}_scenario_expected.json"
        expected_results = {}
        if expected_file.exists():
            expected_results = json.loads(expected_file.read_text())
        
        return AnalysisScenario(
            name=scenario_name,
            description=description,
            files=files,
            expected_results=expected_results
        )
    
    def list_synthetic_samples(self) -> List[str]:
        """List all available synthetic samples."""
        samples = []
        for file_path in self.synthetic_dir.glob("*.py"):
            samples.append(file_path.stem)
        for file_path in self.synthetic_dir.glob("*.js"):
            samples.append(file_path.stem)
        return sorted(samples)
    
    def list_real_world_samples(self) -> List[str]:
        """List all available real-world samples."""
        samples = []
        for file_path in self.real_world_dir.iterdir():
            if file_path.is_file():
                samples.append(file_path.stem)
        return sorted(samples)
    
    def list_analysis_scenarios(self) -> List[str]:
        """List all available analysis scenarios."""
        scenarios = []
        for dir_path in self.scenarios_dir.iterdir():
            if dir_path.is_dir():
                scenarios.append(dir_path.name)
        return sorted(scenarios)
    
    def get_samples_by_category(self, category: str) -> List[TestFixture]:
        """Get all samples that test a specific category of issues."""
        samples = []
        
        # Load synthetic samples
        for sample_name in self.list_synthetic_samples():
            if category.lower() in sample_name.lower():
                try:
                    fixture = self.load_synthetic_sample(sample_name)
                    samples.append(fixture)
                except FileNotFoundError:
                    continue
        
        # Load real-world samples
        for sample_name in self.list_real_world_samples():
            try:
                fixture = self.load_real_world_sample(sample_name)
                # Check if expected issues contain the category
                for issue in fixture.expected_issues:
                    if issue.get("category", "").lower() == category.lower():
                        samples.append(fixture)
                        break
            except FileNotFoundError:
                continue
        
        return samples
    
    def create_temporary_project(self, scenario: AnalysisScenario, temp_dir: Path) -> Path:
        """Create a temporary project directory from an analysis scenario."""
        project_dir = temp_dir / scenario.name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        for file_info in scenario.files:
            file_path = project_dir / file_info["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file_info["content"])
        
        return project_dir
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        extension = file_path.suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql'
        }
        
        return language_map.get(extension, 'unknown')

# Convenience functions for easy access
def load_security_samples() -> List[TestFixture]:
    """Load all security-related test samples."""
    loader = FixtureLoader()
    return loader.get_samples_by_category("security")

def load_performance_samples() -> List[TestFixture]:
    """Load all performance-related test samples."""
    loader = FixtureLoader()
    return loader.get_samples_by_category("performance")

def load_complexity_samples() -> List[TestFixture]:
    """Load all complexity-related test samples."""
    loader = FixtureLoader()
    return loader.get_samples_by_category("complexity")

def load_duplication_samples() -> List[TestFixture]:
    """Load all duplication-related test samples."""
    loader = FixtureLoader()
    return loader.get_samples_by_category("duplication")

def load_documentation_samples() -> List[TestFixture]:
    """Load all documentation-related test samples."""
    loader = FixtureLoader()
    return loader.get_samples_by_category("documentation")

def load_testing_samples() -> List[TestFixture]:
    """Load all testing-related test samples."""
    loader = FixtureLoader()
    return loader.get_samples_by_category("testing")

def load_multi_language_scenario() -> AnalysisScenario:
    """Load the multi-language analysis scenario."""
    loader = FixtureLoader()
    return loader.load_analysis_scenario("multi_language_project")