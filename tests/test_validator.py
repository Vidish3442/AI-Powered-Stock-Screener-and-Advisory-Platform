"""
Test cases for DSL validator
Tests both valid and invalid query structures
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.ai.validator import validate_dsl
def test_validator():
    """Test for DSL validator with correct and incorrect queries."""
    print("=" * 60)
    print("TESTING DSL VALIDATOR")
    print("=" * 60)
    test_cases = [
        # correct case 1: Simple PE ratio condition
        {
            "name": "Simple PE ratio condition",
            "dsl": {
                "type": "group",
                "logic": "AND",
                "conditions": [
                    {
                        "type": "condition",
                        "field": "pe_ratio",
                        "operator": ">",
                        "value": 15
                    }
                ]
            },
            "should_pass": True
        },
        
        # correct case 2: Complex nested query
        {
            "name": "Nested conditions with quarterly data",
            "dsl": {
                "type": "group",
                "logic": "AND",
                "conditions": [
                    {
                        "type": "condition",
                        "field": "pe_ratio",
                        "operator": ">",
                        "value": 10
                    },
                    {
                        "type": "group",
                        "logic": "OR",
                        "conditions": [
                            {
                                "type": "condition",
                                "field": "market_cap",
                                "operator": ">",
                                "value": 1000000000
                            },
                            {
                                "type": "quarterly",
                                "field": "net_profit",
                                "condition": "positive",
                                "last_n": 4
                            }
                        ]
                    }
                ]
            },
            "should_pass": True
        },
        
        # incorrect case 1: Missing required field
        {
            "name": "Missing 'field' in condition",
            "dsl": {
                "type": "group",
                "logic": "AND",
                "conditions": [
                    {
                        "type": "condition",
                        "operator": ">",
                        "value": 15
                    }
                ]
            },
            "should_pass": False,
            "expected_error": "Missing 'field'"
        },
        
        # incorrect case 2: Invalid operator
        {
            "name": "Invalid operator '!='",
            "dsl": {
                "type": "group",
                "logic": "AND",
                "conditions": [
                    {
                        "type": "condition",
                        "field": "pe_ratio",
                        "operator": "!=",
                        "value": 15
                    }
                ]
            },
            "should_pass": False,
            "expected_error": "Invalid operator"
        },
        
        # incorrect case 3: Invalid field name
        {
            "name": "Invalid field 'invalid_field'",
            "dsl": {
                "type": "group",
                "logic": "AND",
                "conditions": [
                    {
                        "type": "condition",
                        "field": "invalid_field",
                        "operator": ">",
                        "value": 100
                    }
                ]
            },
            "should_pass": False,
            "expected_error": "Invalid field"
        },
        
        # incorrect case 4: Missing value
        {
            "name": "Missing 'value' in condition",
            "dsl": {
                "type": "group",
                "logic": "AND",
                "conditions": [
                    {
                        "type": "condition",
                        "field": "pe_ratio",
                        "operator": ">"
                    }
                ]
            },
            "should_pass": False,
            "expected_error": "Missing 'value'"
        }
    ]
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'-' * 60}")
        print(f"Test {i}: {test['name']}")
        print(f"{'-' * 60}")
        
        try:
            validate_dsl(test['dsl'])
            if test['should_pass']:
                print(f"Pass: Validation succeeded as expected")
                passed += 1
            else:
                print(f"Fail: Expected to fail but passed")
                failed += 1
                    
        except Exception as e:
            if not test['should_pass']:
                print(f"Pass: Validation failed as expected")
                print(f"Error: {str(e)}")
                passed += 1
            else:
                print(f"Fail: Expected to pass but failed")
                print(f"Error: {str(e)}")
                failed += 1
    
    print(f"Summary:")
    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_cases)*100):.1f}%")    
    return passed == len(test_cases)
if __name__ == "__main__":
    success = test_validator()
    sys.exit(0 if success else 1)
