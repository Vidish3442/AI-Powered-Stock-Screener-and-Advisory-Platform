"""
Test cases for backend API endpoints
Tests authentication, portfolio, alerts, and screener endpoints
"""

import requests
import json

API_URL = "http://127.0.0.1:8001"

def test_authentication():
    """Test authentication endpoints."""
    print("\n1. Testing login with valid credentials...")
    response = requests.post(f"{API_URL}/auth/login", json={
        "email": "vk@example.com",
        "password": "vkqwerty12345"
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"Login successful")
        print(f"Token: {token[:20]}...")
        return token
    else:
        print(f"Login failed: {response.status_code}")
        return None

def test_portfolio_endpoints(token):
    """Test portfolio endpoints."""
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Get portfolios
    print("\n1. Testing GET /portfolio/...")
    response = requests.get(f"{API_URL}/portfolio/", headers=headers)
    
    if response.status_code == 200:
        portfolios = response.json()
        print(f"Retrieved {len(portfolios)} portfolios")
        for p in portfolios:
            print(f"      - {p['name']}: {p['total_holdings']} holdings")
        return portfolios[0]['portfolio_id'] if portfolios else None
    else:
        print(f"Failed: {response.status_code}")
        return None
    
    # Test 2: Get portfolio summary
    print("\n2. Testing GET /portfolio/summary...")
    response = requests.get(f"{API_URL}/portfolio/summary", headers=headers)
    
    if response.status_code == 200:
        summary = response.json()
        print(f"Summary retrieved")
        print(f"Total Portfolios: {summary.get('total_portfolios', 0)}")
        print(f"Total Holdings: {summary.get('total_holdings', 0)}")
        print(f"Total Invested: ${summary.get('total_invested', 0):,.2f}")
    else:
        print(f"Failed: {response.status_code}")

def test_alert_endpoints(token):
    """Test alert endpoints."""
    print("\n" + "=" * 60)
    print("TESTING ALERT ENDPOINTS")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Get alerts
    print("\n1. Testing GET /alerts/...")
    response = requests.get(f"{API_URL}/alerts/", headers=headers)
    
    if response.status_code == 200:
        alerts = response.json()
        print(f"Retrieved {len(alerts)} alerts")
        for a in alerts:
            print(f"      - {a['symbol']}: {a['metric']} {a['operator']} {a['threshold']}")
    else:
        print(f"Failed: {response.status_code}")
    
    # Test 2: Get alert summary
    print("\n2. Testing GET /alerts/summary...")
    response = requests.get(f"{API_URL}/alerts/summary", headers=headers)
    
    if response.status_code == 200:
        summary = response.json()
        print(f"Summary retrieved")
        print(f"Total Alerts: {summary.get('total_alerts', 0)}")
        print(f"Active Alerts: {summary.get('active_alerts', 0)}")
        print(f"Total Triggers: {summary.get('total_triggers', 0)}")
    else:
        print(f"Failed: {response.status_code}")
    
    # Test 3: Get alert events
    print("\n3. Testing GET /alerts/events...")
    response = requests.get(f"{API_URL}/alerts/events", headers=headers)
    
    if response.status_code == 200:
        events = response.json()
        print(f"Retrieved {len(events)} alert events")
        for e in events[:3]:  # Show first 3
            print(f"      - {e['symbol']}: {e['metric']} triggered at {e['triggered_value']}")
    else:
        print(f"Failed: {response.status_code}")
    
    # Test 4: Search stock
    print("\n4. Testing GET /alerts/stocks/search...")
    response = requests.get(f"{API_URL}/alerts/stocks/search", 
                          params={"symbol": "AAPL"},
                          headers=headers)
    
    if response.status_code == 200:
        stock = response.json()
        print(f"Stock found: {stock['symbol']} - {stock['company_name']}")
    else:
        print(f"Failed: {response.status_code}")

def test_screener_endpoint(token):
    """Test stock screener endpoint."""
    print("\n" + "=" * 60)
    print("TESTING STOCK SCREENER ENDPOINT")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Simple query
    print("\n1. Testing simple query: 'PE ratio > 15'...")
    response = requests.post(f"{API_URL}/ai/screener",
                           params={"query": "PE ratio > 15"},
                           headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        print(f"Query successful")
        print(f"Found {len(results)} stocks")
        if results:
            print(f"Sample: {results[0]['symbol']} - PE: {results[0].get('pe_ratio', 'N/A')}")
    else:
        print(f"Failed: {response.status_code}")
        try:
            error = response.json()
            print(f"Error: {error.get('detail', 'Unknown error')}")
        except:
            pass
    
    # Test 2: Another simple query
    print("\n2. Testing query with multiple conditions...")
    response = requests.post(f"{API_URL}/ai/screener",
                           params={"query": "PE ratio greater than 10 and dividend yield above 2"},
                           headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        print(f"Query successful")
        print(f"Found {len(results)} stocks")
        if results:
            print(f"Sample: {results[0]['symbol']} - PE: {results[0].get('pe_ratio', 'N/A')}")
    else:
        print(f"Failed: {response.status_code}")
        try:
            error = response.json()
            print(f"Error: {error.get('detail', 'Unknown error')}")
        except:
            print(f"Response: {response.text}")

def run_all_tests():
    """Run all API tests."""
    print("BACKEND API ENDPOINT TESTS")
    
    try:
        token = test_authentication()        
        if not token:
            print("\nAuthentication failed. Cannot proceed with other tests.")
            return False        
        test_portfolio_endpoints(token)
        test_alert_endpoints(token)
        test_screener_endpoint(token)
        return True
        
    except requests.exceptions.ConnectionError:
        print("\ncannot connect")
        return False
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
