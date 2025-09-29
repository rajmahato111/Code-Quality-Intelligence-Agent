#!/bin/bash
# CI/CD Quality Gate Script
# This script runs code quality analysis and fails the build if critical issues are found

set -e  # Exit on any error

echo "🔍 Starting Code Quality Analysis..."
echo "=================================="

# Configuration
CODEBASE_PATH="${1:-src/}"
MIN_SEVERITY="${2:-high}"
MAX_ISSUES="${3:-5}"
OUTPUT_FORMAT="${4:-json}"
REPORT_FILE="quality_report.json"

echo "📋 Configuration:"
echo "  - Codebase Path: $CODEBASE_PATH"
echo "  - Minimum Severity: $MIN_SEVERITY"
echo "  - Max Allowed Issues: $MAX_ISSUES"
echo "  - Output Format: $OUTPUT_FORMAT"
echo ""

# Run code quality analysis
echo "🚀 Running Code Quality Analysis..."
python3 -m code_quality_agent.cli.main analyze "$CODEBASE_PATH" \
    --output-format "$OUTPUT_FORMAT" \
    --output-file "$REPORT_FILE" \
    --min-severity "$MIN_SEVERITY" \
    --no-cache

# Check if analysis succeeded
if [ $? -ne 0 ]; then
    echo "❌ Code quality analysis failed!"
    exit 1
fi

echo "✅ Analysis completed successfully"

# Parse results from JSON report
if [ "$OUTPUT_FORMAT" = "json" ]; then
    echo ""
    echo "📊 Parsing Results..."
    
    # Extract metrics using jq (if available) or python
    if command -v jq &> /dev/null; then
        TOTAL_ISSUES=$(jq '.summary.total_issues' "$REPORT_FILE")
        HIGH_ISSUES=$(jq '.summary.issues_by_severity.high // 0' "$REPORT_FILE")
        CRITICAL_ISSUES=$(jq '.summary.issues_by_severity.critical // 0' "$REPORT_FILE")
        QUALITY_SCORE=$(jq '.summary.quality_score' "$REPORT_FILE")
    else
        # Fallback to python parsing
        TOTAL_ISSUES=$(python3 -c "import json; data=json.load(open('$REPORT_FILE')); print(data['summary']['total_issues'])")
        HIGH_ISSUES=$(python3 -c "import json; data=json.load(open('$REPORT_FILE')); print(data['summary']['issues_by_severity'].get('high', 0))")
        CRITICAL_ISSUES=$(python3 -c "import json; data=json.load(open('$REPORT_FILE')); print(data['summary']['issues_by_severity'].get('critical', 0))")
        QUALITY_SCORE=$(python3 -c "import json; data=json.load(open('$REPORT_FILE')); print(data['summary']['quality_score'])")
    fi
    
    echo "📈 Quality Metrics:"
    echo "  - Total Issues: $TOTAL_ISSUES"
    echo "  - High Severity Issues: $HIGH_ISSUES"
    echo "  - Critical Issues: $CRITICAL_ISSUES"
    echo "  - Quality Score: $QUALITY_SCORE/100"
    echo ""
    
    # Quality Gate Checks
    echo "🚪 Quality Gate Checks:"
    
    # Check 1: Critical Issues
    if [ "$CRITICAL_ISSUES" -gt 0 ]; then
        echo "❌ FAIL: Found $CRITICAL_ISSUES critical issues (max allowed: 0)"
        echo "🚨 Build FAILED due to critical security/quality issues!"
        exit 1
    else
        echo "✅ PASS: No critical issues found"
    fi
    
    # Check 2: High Severity Issues
    if [ "$HIGH_ISSUES" -gt "$MAX_ISSUES" ]; then
        echo "❌ FAIL: Found $HIGH_ISSUES high severity issues (max allowed: $MAX_ISSUES)"
        echo "🚨 Build FAILED due to too many high severity issues!"
        exit 1
    else
        echo "✅ PASS: High severity issues within acceptable limit ($HIGH_ISSUES/$MAX_ISSUES)"
    fi
    
    # Check 3: Quality Score
    MIN_QUALITY_SCORE=70
    if [ "$QUALITY_SCORE" -lt "$MIN_QUALITY_SCORE" ]; then
        echo "⚠️  WARN: Quality score is low ($QUALITY_SCORE < $MIN_QUALITY_SCORE)"
        echo "📝 Consider improving code quality before release"
        # Note: This is a warning, not a failure
    else
        echo "✅ PASS: Quality score meets minimum threshold ($QUALITY_SCORE >= $MIN_QUALITY_SCORE)"
    fi
    
    echo ""
    echo "🎉 All quality gates passed! Build can proceed."
    echo "📄 Full report saved to: $REPORT_FILE"
    
else
    echo "⚠️  JSON output not available for automated quality gate checks"
    echo "📄 Check the console output above for quality issues"
fi

echo ""
echo "✅ Quality gate check completed successfully!"
exit 0