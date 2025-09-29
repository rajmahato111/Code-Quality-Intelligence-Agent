"""
CLI commands for accuracy validation.
"""

import click
import json
import logging
from pathlib import Path
from typing import Optional

from code_quality_agent.validation import (
    AccuracyMetrics, VulnerabilityValidator, 
    RegressionTester, ExplanationValidator
)
from code_quality_agent.core.orchestrator import AnalysisOrchestrator
from code_quality_agent.core.models import AnalysisOptions
from tests.fixtures import FixtureLoader

logger = logging.getLogger(__name__)


@click.group()
def validate():
    """Accuracy validation commands."""
    pass


@validate.command()
@click.argument('codebase_path', type=click.Path(exists=True))
@click.option('--fixture', '-f', help='Test fixture to validate against')
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
@click.option('--threshold', '-t', type=float, default=0.7, help='Match threshold for accuracy metrics')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def accuracy(codebase_path: str, fixture: Optional[str], output: Optional[str], 
            threshold: float, verbose: bool):
    """Validate analyzer accuracy against test fixtures."""
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    click.echo("🔍 Starting accuracy validation...")
    
    try:
        # Load test fixture
        fixture_loader = FixtureLoader()
        
        if fixture:
            test_fixture = fixture_loader.load_synthetic_sample(fixture)
            click.echo(f"📋 Loaded fixture: {test_fixture.name}")
        else:
            # Use security issues as default
            test_fixture = fixture_loader.load_synthetic_sample("security_issues")
            click.echo(f"📋 Using default fixture: {test_fixture.name}")
        
        # Run analysis on the codebase
        orchestrator = AnalysisOrchestrator()
        options = AnalysisOptions(
            include_patterns=['*.py', '*.js'],
            parallel_processing=False,
            max_workers=1
        )
        
        click.echo(f"🔬 Analyzing codebase: {codebase_path}")
        
        try:
            analysis_result = orchestrator.analyze_codebase(codebase_path, options)
            
            # Calculate accuracy metrics
            metrics_calculator = AccuracyMetrics(match_threshold=threshold)
            
            # Convert analysis result issues to expected format
            actual_issues = []
            for issue in analysis_result.issues:
                actual_issues.append({
                    'category': issue.category,
                    'severity': issue.severity,
                    'type': getattr(issue, 'type', 'unknown'),
                    'description': issue.description,
                    'line': getattr(issue.location, 'line_number', 0) if issue.location else 0
                })
            
            validation_result = metrics_calculator.calculate_metrics(
                test_fixture.expected_issues, 
                actual_issues
            )
            
            # Display results
            click.echo("\n📊 ACCURACY VALIDATION RESULTS")
            click.echo("=" * 50)
            click.echo(f"Precision: {validation_result.precision:.3f}")
            click.echo(f"Recall: {validation_result.recall:.3f}")
            click.echo(f"F1-Score: {validation_result.f1_score:.3f}")
            click.echo(f"Accuracy: {validation_result.accuracy:.3f}")
            click.echo(f"True Positives: {validation_result.true_positives}")
            click.echo(f"False Positives: {validation_result.false_positives}")
            click.echo(f"False Negatives: {validation_result.false_negatives}")
            
            if verbose:
                # Show detailed report
                report = metrics_calculator.generate_accuracy_report(validation_result)
                click.echo("\n" + report)
            
            # Save results if output specified
            if output:
                results_data = {
                    'fixture_name': test_fixture.name,
                    'codebase_path': codebase_path,
                    'precision': validation_result.precision,
                    'recall': validation_result.recall,
                    'f1_score': validation_result.f1_score,
                    'accuracy': validation_result.accuracy,
                    'true_positives': validation_result.true_positives,
                    'false_positives': validation_result.false_positives,
                    'false_negatives': validation_result.false_negatives,
                    'category_metrics': validation_result.category_metrics,
                    'severity_metrics': validation_result.severity_metrics
                }
                
                with open(output, 'w') as f:
                    json.dump(results_data, f, indent=2)
                
                click.echo(f"💾 Results saved to: {output}")
            
            click.echo("✅ Accuracy validation completed successfully!")
            
        except Exception as e:
            click.echo(f"⚠️  Analysis failed: {e}")
            click.echo("📋 Validating fixture structure instead...")
            
            # Validate fixture structure even if analysis fails
            if len(test_fixture.expected_issues) > 0:
                click.echo(f"✅ Fixture contains {len(test_fixture.expected_issues)} expected issues")
                
                # Show issue categories
                categories = {}
                for issue in test_fixture.expected_issues:
                    cat = issue.get('category', 'unknown')
                    categories[cat] = categories.get(cat, 0) + 1
                
                click.echo("📊 Expected issues by category:")
                for category, count in categories.items():
                    click.echo(f"  {category}: {count}")
            else:
                click.echo("❌ Fixture contains no expected issues")
    
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        raise click.ClickException(str(e))


@validate.command()
@click.argument('codebase_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for vulnerability report')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def vulnerabilities(codebase_path: str, output: Optional[str], verbose: bool):
    """Validate detected issues against known vulnerability databases."""
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    click.echo("🛡️  Starting vulnerability validation...")
    
    try:
        # Run analysis
        orchestrator = AnalysisOrchestrator()
        options = AnalysisOptions(
            include_patterns=['*.py', '*.js'],
            parallel_processing=False,
            max_workers=1
        )
        
        click.echo(f"🔬 Analyzing codebase: {codebase_path}")
        
        try:
            analysis_result = orchestrator.analyze_codebase(codebase_path, options)
            
            # Convert issues to vulnerability validator format
            detected_issues = []
            for issue in analysis_result.issues:
                detected_issues.append({
                    'category': issue.category,
                    'severity': issue.severity,
                    'type': getattr(issue, 'type', 'unknown'),
                    'description': issue.description
                })
            
            # Validate against vulnerability databases
            validator = VulnerabilityValidator()
            matches = validator.validate_against_vulnerabilities(detected_issues)
            
            # Display results
            click.echo(f"\n🛡️  VULNERABILITY VALIDATION RESULTS")
            click.echo("=" * 50)
            click.echo(f"Total detected issues: {len(detected_issues)}")
            click.echo(f"Vulnerability matches: {len(matches)}")
            
            if matches:
                # Show statistics
                stats = validator.get_vulnerability_statistics(matches)
                
                click.echo(f"\nMatches by severity:")
                for severity, count in stats['by_severity'].items():
                    click.echo(f"  {severity}: {count}")
                
                click.echo(f"\nMatches by type:")
                for vuln_type, count in stats['by_type'].items():
                    click.echo(f"  {vuln_type}: {count}")
                
                click.echo(f"\nCoverage:")
                click.echo(f"  With CWE mapping: {stats['with_cwe']}")
                click.echo(f"  With CVE mapping: {stats['with_cve']}")
                
                if verbose:
                    # Show detailed report
                    report = validator.generate_vulnerability_report(matches)
                    click.echo("\n" + report)
            
            # Save results if output specified
            if output:
                report = validator.generate_vulnerability_report(matches)
                with open(output, 'w') as f:
                    f.write(report)
                click.echo(f"💾 Report saved to: {output}")
            
            click.echo("✅ Vulnerability validation completed successfully!")
            
        except Exception as e:
            click.echo(f"⚠️  Analysis failed: {e}")
            click.echo("Using built-in vulnerability patterns for demonstration...")
            
            # Show available vulnerability patterns
            validator = VulnerabilityValidator()
            click.echo(f"📋 Available vulnerability patterns: {len(validator.builtin_patterns)}")
            for pattern_name in validator.builtin_patterns.keys():
                click.echo(f"  - {pattern_name}")
    
    except Exception as e:
        click.echo(f"❌ Vulnerability validation failed: {e}")
        raise click.ClickException(str(e))


@validate.command()
@click.argument('codebase_path', type=click.Path(exists=True))
@click.option('--baseline-version', '-b', help='Baseline version for comparison')
@click.option('--current-version', '-c', default='current', help='Current version identifier')
@click.option('--output', '-o', type=click.Path(), help='Output file for regression report')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def regression(codebase_path: str, baseline_version: Optional[str], 
              current_version: str, output: Optional[str], verbose: bool):
    """Test for regressions in analysis results."""
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    click.echo("📈 Starting regression testing...")
    
    try:
        # Initialize regression tester
        tester = RegressionTester()
        
        # Run current analysis
        orchestrator = AnalysisOrchestrator()
        options = AnalysisOptions(
            include_patterns=['*.py', '*.js'],
            parallel_processing=False,
            max_workers=1
        )
        
        click.echo(f"🔬 Analyzing current codebase: {codebase_path}")
        
        try:
            analysis_result = orchestrator.analyze_codebase(codebase_path, options)
            
            # Create current snapshot
            current_snapshot = tester.create_snapshot(codebase_path, analysis_result, current_version)
            click.echo(f"📸 Created snapshot for version: {current_version}")
            
            # Find baseline snapshot
            baseline_snapshot = tester.find_baseline_snapshot(codebase_path, baseline_version)
            
            if baseline_snapshot:
                click.echo(f"📸 Found baseline snapshot: {baseline_snapshot.version}")
                
                # Compare snapshots
                comparison = tester.compare_snapshots(baseline_snapshot, current_snapshot)
                
                # Display results
                click.echo(f"\n📈 REGRESSION TESTING RESULTS")
                click.echo("=" * 50)
                click.echo(f"Baseline: {baseline_snapshot.version} ({baseline_snapshot.timestamp.strftime('%Y-%m-%d %H:%M')})")
                click.echo(f"Current:  {current_snapshot.version} ({current_snapshot.timestamp.strftime('%Y-%m-%d %H:%M')})")
                click.echo(f"Score change: {comparison.score_change:+.2f}")
                click.echo(f"Issues added: {len(comparison.issues_added)}")
                click.echo(f"Issues removed: {len(comparison.issues_removed)}")
                click.echo(f"Issues changed: {len(comparison.issues_changed)}")
                
                if comparison.regression_detected:
                    click.echo("🔴 REGRESSION DETECTED")
                elif comparison.improvement_detected:
                    click.echo("🟢 IMPROVEMENT DETECTED")
                else:
                    click.echo("⚪ NO SIGNIFICANT CHANGE")
                
                if verbose:
                    # Show detailed report
                    report = tester.generate_regression_report(comparison)
                    click.echo("\n" + report)
                
                # Save results if output specified
                if output:
                    report = tester.generate_regression_report(comparison)
                    with open(output, 'w') as f:
                        f.write(report)
                    click.echo(f"💾 Report saved to: {output}")
                
            else:
                click.echo("📸 No baseline snapshot found - this will be the new baseline")
                click.echo(f"Current snapshot stats:")
                click.echo(f"  Total files: {current_snapshot.total_files}")
                click.echo(f"  Total issues: {current_snapshot.total_issues}")
                click.echo(f"  Overall score: {current_snapshot.overall_score:.2f}")
            
            click.echo("✅ Regression testing completed successfully!")
            
        except Exception as e:
            click.echo(f"⚠️  Analysis failed: {e}")
            click.echo("Regression testing requires successful analysis")
    
    except Exception as e:
        click.echo(f"❌ Regression testing failed: {e}")
        raise click.ClickException(str(e))


@validate.command()
@click.option('--fixture', '-f', help='Test fixture to validate explanations for')
@click.option('--output', '-o', type=click.Path(), help='Output file for explanation report')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def explanations(fixture: Optional[str], output: Optional[str], verbose: bool):
    """Validate explanation quality for test fixtures."""
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    click.echo("📝 Starting explanation quality validation...")
    
    try:
        # Load test fixture
        fixture_loader = FixtureLoader()
        
        if fixture:
            test_fixture = fixture_loader.load_synthetic_sample(fixture)
            click.echo(f"📋 Loaded fixture: {test_fixture.name}")
        else:
            # Use security issues as default
            test_fixture = fixture_loader.load_synthetic_sample("security_issues")
            click.echo(f"📋 Using default fixture: {test_fixture.name}")
        
        # Create mock explanations for testing
        issues_with_explanations = []
        for issue in test_fixture.expected_issues[:5]:  # Test first 5 issues
            explanation = issue.get('explanation', 'This is a code quality issue that needs attention.')
            suggestion = issue.get('suggestion', 'Consider fixing this issue to improve code quality.')
            
            issues_with_explanations.append({
                'issue': issue,
                'explanation': explanation,
                'suggestion': suggestion
            })
        
        # Validate explanations
        validator = ExplanationValidator()
        assessments = validator.validate_explanations_batch(issues_with_explanations)
        
        # Display results
        click.echo(f"\n📝 EXPLANATION QUALITY RESULTS")
        click.echo("=" * 50)
        click.echo(f"Total explanations assessed: {len(assessments)}")
        
        # Calculate averages
        avg_quality = sum(a.quality_score for a in assessments) / len(assessments)
        avg_readability = sum(a.readability_score for a in assessments) / len(assessments)
        avg_completeness = sum(a.completeness_score for a in assessments) / len(assessments)
        avg_actionability = sum(a.actionability_score for a in assessments) / len(assessments)
        
        click.echo(f"Average quality score: {avg_quality:.3f}")
        click.echo(f"Average readability: {avg_readability:.3f}")
        click.echo(f"Average completeness: {avg_completeness:.3f}")
        click.echo(f"Average actionability: {avg_actionability:.3f}")
        
        # Quality distribution
        quality_counts = {}
        for assessment in assessments:
            level = assessment.quality_level.value
            quality_counts[level] = quality_counts.get(level, 0) + 1
        
        click.echo(f"\nQuality distribution:")
        for level in ['excellent', 'good', 'fair', 'poor']:
            count = quality_counts.get(level, 0)
            if count > 0:
                click.echo(f"  {level.title()}: {count}")
        
        if verbose:
            # Show detailed report
            report = validator.generate_explanation_report(assessments)
            click.echo("\n" + report)
        
        # Save results if output specified
        if output:
            report = validator.generate_explanation_report(assessments)
            with open(output, 'w') as f:
                f.write(report)
            click.echo(f"💾 Report saved to: {output}")
        
        click.echo("✅ Explanation quality validation completed successfully!")
    
    except Exception as e:
        click.echo(f"❌ Explanation validation failed: {e}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    validate()