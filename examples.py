"""
Development utilities and examples.
"""

# API Examples using Python requests library
# Save this as examples.py and run with: python examples.py

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/prices"

def print_response(title, response):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))

def test_all_prices():
    """Test getting all prices for BTC."""
    response = requests.get(
        f"{BASE_URL}/all/",
        params={
            "ticker": "btc_usd",
            "page": 1,
            "per_page": 5
        }
    )
    print_response("GET /api/prices/all/?ticker=btc_usd", response)

def test_latest_price():
    """Test getting latest price."""
    response = requests.get(
        f"{BASE_URL}/latest/",
        params={"ticker": "eth_usd"}
    )
    print_response("GET /api/prices/latest/?ticker=eth_usd", response)

def test_price_range():
    """Test getting prices by date range."""
    now = datetime.now()
    start_date = (now - timedelta(days=1)).isoformat()
    end_date = now.isoformat()
    
    response = requests.get(
        f"{BASE_URL}/range/",
        params={
            "ticker": "btc_usd",
            "start_date": start_date,
            "end_date": end_date,
            "page": 1,
            "per_page": 10
        }
    )
    print_response(
        f"GET /api/prices/range/?ticker=btc_usd&start_date={start_date}&end_date={end_date}",
        response
    )

def test_invalid_ticker():
    """Test error handling with invalid ticker."""
    response = requests.get(
        f"{BASE_URL}/all/",
        params={"ticker": "invalid_ticker"}
    )
    print_response("GET /api/prices/all/?ticker=invalid_ticker (INVALID)", response)

def test_missing_ticker():
    """Test error handling with missing ticker."""
    response = requests.get(f"{BASE_URL}/all/")
    print_response("GET /api/prices/all/ (MISSING TICKER)", response)

if __name__ == "__main__":
    print("Testing Deribit Price Tracker API")
    print("Make sure the server is running on http://localhost:8000")
    
    try:
        test_all_prices()
        test_latest_price()
        test_price_range()
        test_invalid_ticker()
        test_missing_ticker()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to http://localhost:8000")
        print("Make sure Django development server is running:")
        print("  python manage.py runserver")
    except Exception as e:
        print(f"Error: {str(e)}")
