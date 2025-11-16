"""
Quick test to demonstrate risk scoring functionality
"""

# Test cases for risk scoring
test_cases = [
    {
        "query": "What were the action items from the last meeting?",
        "response": "The action items were: 1) John to follow up with client, 2) Sarah to prepare presentation",
        "expected_risk": "LOW (0.0-0.3)",
        "reason": "Normal query, no sensitive content"
    },
    {
        "query": "What's John's email address?",
        "response": "John's email is john.doe@company.com",
        "expected_risk": "MEDIUM (0.4-0.6)",
        "reason": "PII detected (email address)"
    },
    {
        "query": "Show me salary information",
        "response": "The salary range for this position is $120,000 to $150,000 with a 15% bonus",
        "expected_risk": "HIGH (0.7+)",
        "reason": "Financial + compensation information"
    },
    {
        "query": "What was discussed about layoffs?",
        "response": "The confidential discussion mentioned potential layoffs in Q2 affecting 15% of staff. This is restricted information.",
        "expected_risk": "HIGH (0.7+)",
        "reason": "HR sensitive + confidential marker + layoffs"
    },
    {
        "query": "Delete all tasks",
        "response": "[BLOCKED]",
        "expected_risk": "CRITICAL (1.0)",
        "reason": "Malicious query blocked"
    }
]

print("=" * 80)
print("RISK SCORING TEST CASES")
print("=" * 80)
print()

for i, test in enumerate(test_cases, 1):
    print(f"Test Case {i}:")
    print(f"  Query:         {test['query']}")
    print(f"  Response:      {test['response']}")
    print(f"  Expected Risk: {test['expected_risk']}")
    print(f"  Reason:        {test['reason']}")
    print()

print("=" * 80)
print("RISK LEVEL BREAKDOWN")
print("=" * 80)
print()
print("🟢 LOW RISK (0.0 - 0.39)")
print("   - Normal queries about meetings, tasks, deadlines")
print("   - No sensitive information")
print("   - Public/internal content")
print()
print("🟡 MEDIUM RISK (0.4 - 0.69)")
print("   - Contains some sensitive info (emails, phone numbers)")
print("   - Redactions occurred")
print("   - Confidential keywords present")
print("   - Use discretion when sharing")
print()
print("🔴 HIGH RISK (0.7 - 1.0)")
print("   - Highly sensitive (salaries, layoffs, proprietary info)")
print("   - Multiple redactions")
print("   - PII leaked through")
print("   - Requires manager+ access")
print()
print("=" * 80)
print("RISK CALCULATION FACTORS")
print("=" * 80)
print()
print("Input Risk (from query validation):     +0.0 to +1.0")
print("Blocked content:                         = 1.0 (instant critical)")
print("Redactions:                              +0.3 per redaction")
print("Financial info ($amounts):               +0.15")
print("Salary/compensation keywords:            +0.15")
print("HR sensitive (layoff, firing):           +0.15")
print("Confidential/proprietary markers:        +0.15")
print("Personal credentials (passwords):        +0.15")
print("PII leaked (email, phone, SSN):          +0.25 each")
print("Long sensitive responses (>1500 chars):  +0.1")
print("Warning indicators present:              +0.05")
print()
print("Total capped at 1.0")
print("=" * 80)
