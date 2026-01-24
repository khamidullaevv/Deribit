# API Examples - cURL Commands

## 1. Get All Prices for Bitcoin (BTC/USD)

```bash
curl -X GET "http://localhost:8000/api/prices/all/?ticker=btc_usd"
```

With pagination:

```bash
curl -X GET "http://localhost:8000/api/prices/all/?ticker=btc_usd&page=1&per_page=50"
```

## 2. Get Latest Price for Ethereum (ETH/USD)

```bash
curl -X GET "http://localhost:8000/api/prices/latest/?ticker=eth_usd"
```

## 3. Get Prices Within Date Range

```bash
curl -X GET "http://localhost:8000/api/prices/range/?ticker=btc_usd&start_date=2024-01-18T00:00:00&end_date=2024-01-19T23:59:59"
```

With pagination:

```bash
curl -X GET "http://localhost:8000/api/prices/range/?ticker=btc_usd&start_date=2024-01-18T00:00:00&end_date=2024-01-19T23:59:59&page=1&per_page=100"
```

## 4. Error Cases

### Invalid ticker

```bash
curl -X GET "http://localhost:8000/api/prices/all/?ticker=invalid"
```

Response: 400 Bad Request

### Missing required parameter

```bash
curl -X GET "http://localhost:8000/api/prices/all/"
```

Response: 400 Bad Request

### Non-existent ticker (empty result)

```bash
curl -X GET "http://localhost:8000/api/prices/latest/?ticker=xrp_usd"
```

Response: 404 Not Found

## 5. Using HTTPie (better formatting)

If you prefer HTTPie over curl:

```bash
# Install
pip install httpie

# Get latest price
http http://localhost:8000/api/prices/latest/ ticker=btc_usd

# Get all prices
http http://localhost:8000/api/prices/all/ ticker=eth_usd page=1 per_page=10

# Get price range
http http://localhost:8000/api/prices/range/ \
    ticker=btc_usd \
    start_date="2024-01-18T00:00:00" \
    end_date="2024-01-19T23:59:59"
```

## 6. Using Python requests library

```python
import requests

BASE_URL = "http://localhost:8000/api/prices"

# Get latest BTC price
response = requests.get(
    f"{BASE_URL}/latest/",
    params={"ticker": "btc_usd"}
)
print(response.json())

# Get all ETH prices
response = requests.get(
    f"{BASE_URL}/all/",
    params={
        "ticker": "eth_usd",
        "page": 1,
        "per_page": 100
    }
)
print(response.json())

# Get prices in date range
from datetime import datetime, timedelta
now = datetime.now()
start = (now - timedelta(days=1)).isoformat()
end = now.isoformat()

response = requests.get(
    f"{BASE_URL}/range/",
    params={
        "ticker": "btc_usd",
        "start_date": start,
        "end_date": end
    }
)
print(response.json())
```

## 7. Piping results to jq for formatting

```bash
# Pretty print JSON
curl -s "http://localhost:8000/api/prices/latest/?ticker=btc_usd" | jq '.'

# Extract specific fields
curl -s "http://localhost:8000/api/prices/latest/?ticker=btc_usd" | jq '.price'

# Get all prices and count
curl -s "http://localhost:8000/api/prices/all/?ticker=btc_usd" | jq '.count'

# Extract prices from results
curl -s "http://localhost:8000/api/prices/all/?ticker=btc_usd" | jq '.results[].price'
```

## Response Format Examples

### Successful Response (200 OK)

```json
{
  "id": 1234,
  "ticker": "btc_usd",
  "ticker_display": "Bitcoin USD",
  "price": "42850.50",
  "timestamp": 1705689600,
  "created_at": "2024-01-19T12:00:00Z"
}
```

### List Response (200 OK)

```json
{
  "count": 1440,
  "ticker": "btc_usd",
  "page": 1,
  "per_page": 100,
  "results": [
    {
      "id": 1440,
      "ticker": "btc_usd",
      "ticker_display": "Bitcoin USD",
      "price": "42850.50",
      "timestamp": 1705689600,
      "created_at": "2024-01-19T12:00:00Z"
    }
  ]
}
```

### Error Response (400 Bad Request)

```json
{
  "error": "Invalid ticker parameter",
  "details": {
    "ticker": ["\"invalid\" is not a valid choice. Choices are: btc_usd, eth_usd"]
  }
}
```

### Not Found Response (404 Not Found)

```json
{
  "error": "No price records found for xrp_usd",
  "ticker": "xrp_usd"
}
```
