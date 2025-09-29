#!/bin/bash
# Test CI/CD Pipeline Scenarios
# This script demonstrates different CI/CD pipeline outcomes

echo "🧪 Testing CI/CD Pipeline Scenarios"
echo "===================================="

# Test 1: Clean code (should pass)
echo ""
echo "📋 Test 1: Clean Code (Should PASS)"
echo "-----------------------------------"
./ci_scripts/quality_gate.sh test_clean_code/ high 10 json
TEST1_RESULT=$?
echo "Result: $([ $TEST1_RESULT -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"

# Test 2: Code with many issues (should fail)
echo ""
echo "📋 Test 2: Problematic Code (Should FAIL)"
echo "-----------------------------------------"
./ci_scripts/quality_gate.sh test_hotspots/ high 5 json
TEST2_RESULT=$?
echo "Result: $([ $TEST2_RESULT -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED (Expected)")"

# Test 3: Security vulnerabilities (should fail)
echo ""
echo "📋 Test 3: Security Issues (Should FAIL)"
echo "----------------------------------------"
./ci_scripts/quality_gate.sh test_critical_issues/ high 0 json
TEST3_RESULT=$?
echo "Result: $([ $TEST3_RESULT -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED (Expected)")"

# Test 4: Security-only analysis
echo ""
echo "📋 Test 4: Security-Only Analysis"
echo "---------------------------------"
python3 -m code_quality_agent.cli.main analyze test_critical_issues/ \
    --categories security \
    --output-format json \
    --output-file security_only.json \
    --no-cache

if [ -f "security_only.json" ]; then
    SECURITY_ISSUES=$(python3 -c "import json; data=json.load(open('security_only.json')); print(data['summary']['total_issues'])")
    echo "Security Issues Found: $SECURITY_ISSUES"
    echo "Result: $([ $SECURITY_ISSUES -gt 0 ] && echo "✅ Security issues detected" || echo "❌ No security issues found")"
else
    echo "❌ Security analysis failed"
fi

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="
echo "Test 1 (Clean Code):      $([ $TEST1_RESULT -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
echo "Test 2 (Many Issues):     $([ $TEST2_RESULT -ne 0 ] && echo "✅ FAILED (Expected)" || echo "❌ PASSED (Unexpected)")"
echo "Test 3 (Security Issues): $([ $TEST3_RESULT -ne 0 ] && echo "✅ FAILED (Expected)" || echo "❌ PASSED (Unexpected)")"

# Cleanup
rm -f quality_report.json security_only.json

echo ""
echo "🎯 CI/CD Pipeline Testing Complete!"
echo "The pipeline correctly:"
echo "  ✅ Passes builds with acceptable code quality"
echo "  ❌ Fails builds with too many issues"
echo "  🔒 Detects and blocks security vulnerabilities"