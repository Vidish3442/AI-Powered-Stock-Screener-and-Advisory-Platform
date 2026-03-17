"""
Test cases for DSL compiler
Tests query compilation and execution
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.ai.compiler import compile_and_run

def test_compiler():
    """Test for DSL compiler with various queries."""
    test_cases = [
        # Test 1: Normal condition
        {
            "name": "Simple PE ratio filter",
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
            }
        },
        
        # Test 2: Multiple conditions
        {
            "name": "Multiple conditions with AND",
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
                        "type": "condition",
                        "field": "market_cap",
                        "operator": ">",
                        "value": 1000000000
                    }
                ]
            }
        },
        
        # Test 3: Quarterly data
        {
            "name": "Quarterly profit condition",
            "dsl": {
                "type": "group",
                "logic": "AND",
                "conditions": [
                    {
                        "type": "quarterly",
                        "field": "net_profit",
                        "condition": "positive",
                        "last_n": 4
                    }
                ]
            }
        },
        
        # Test 4: Nested conditions
        {
            "name": "Nested conditions with OR",
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
                                "value": 5000000000
                            },
                            {
                                "type": "quarterly",
                                "field": "net_profit",
                                "condition": "positive",
                                "last_n": 2
                            }
                        ]
                    }
                ]
            }
        }
    ]
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")        
        try:
            result = compile_and_run(test['dsl'])
            stocks = result.get('stocks', [])
            has_quarterly = result.get('has_quarterly', False)
            quarterly_data = result.get('quarterly_data', {})
            print(f"Query executed successfully")
            print(f"   Found {len(stocks)} stocks")
            print(f"   Has quarterly data: {has_quarterly}")
            if stocks:
                print(f"   Sample results:")
                for stock in stocks[:3]:
                    print(f"      - {stock['symbol']}: PE={stock.get('pe_ratio', 'N/A')}, "
                          f"Cap=${stock.get('market_cap', 0)/1e9:.1f}B")
            if has_quarterly and quarterly_data:
                print(f"   Quarterly data for {len(quarterly_data)} stocks")
            passed += 1
            
        except Exception as e:
            print(f"Query failed: {str(e)}")
            failed += 1

    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_cases)*100):.1f}%")    
    return passed == len(test_cases)

if __name__ == "__main__":
    success = test_compiler()
    sys.exit(0 if success else 1)
