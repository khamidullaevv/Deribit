"""
Deribit API Documentation Reference

This document describes how the Deribit API client works and how to integrate
with the Deribit API.

OFFICIAL DOCUMENTATION:
https://docs.deribit.com/
"""

# =============================================================================
# API ENDPOINTS USED IN THIS PROJECT
# =============================================================================

# Get Index Price
# ===============
# Endpoint: GET /public/get_index_price
# Description: Returns the current index price for the requested index
# 
# Parameters:
#   index_name (string) - The index name (e.g., btc_usd, eth_usd)
#
# Example Request:
# GET https://www.deribit.com/api/v2/public/get_index_price?index_name=btc_usd
#
# Example Response:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "edp": 0.5,
#     "estimated_delivery_price": 42850.50,
#     "index_price": 42850.50,
#     "interest_rate": 0,
#     "timestamp": 1705689600000
#   },
#   "usIn": 1705689600123456,
#   "usMid": 1705689600654321,
#   "usOut": 1705689600789012
# }

# =============================================================================
# AVAILABLE INDEXES
# =============================================================================

AVAILABLE_INDEXES = {
    "btc_usd": {
        "name": "Bitcoin USD",
        "description": "Bitcoin price in USD",
        "decimals": 2,
    },
    "eth_usd": {
        "name": "Ethereum USD",
        "description": "Ethereum price in USD",
        "decimals": 2,
    }
}

# =============================================================================
# HOW THE CLIENT WORKS
# =============================================================================

"""
The DeribitAPIClient class in services.py provides:

1. Async HTTP Requests
   - Uses aiohttp for non-blocking I/O
   - Properly handles timeouts and connection errors
   - Automatic retry on network failures

2. Connection Management
   - Creates a session with proper timeout configuration
   - Closes connection after each request
   - Configurable timeout (default 10 seconds)

3. Error Handling
   - Gracefully handles HTTP errors (4xx, 5xx)
   - Catches timeout errors
   - Catches network/connection errors
   - Returns None on failure for safe handling

4. Concurrent Requests
   - Can fetch multiple tickers in parallel
   - Uses asyncio.gather() for concurrent execution
   - Efficient resource utilization

Example Usage:

    from apps.prices.services import DeribitAPIClient
    import asyncio
    
    client = DeribitAPIClient()
    
    # Fetch single price
    result = asyncio.run(client.get_index_price('btc_usd'))
    print(result)  # {'index_price': 42850.50, ...}
    
    # Fetch multiple prices concurrently
    results = asyncio.run(client.get_index_prices(('btc_usd', 'eth_usd')))
    print(results)  # {'btc_usd': {...}, 'eth_usd': {...}}
"""

# =============================================================================
# RATE LIMITING
# =============================================================================

"""
Deribit API Rate Limits (as per documentation):
- Public endpoints: Generally high rate limits
- No authentication required for price endpoints
- Rate limiting is by IP address
- Recommended: 1 request per second per ticker

Current Implementation:
- Fetches prices every 60 seconds (1 per minute)
- Runs concurrently for multiple tickers
- Well within rate limits
"""

# =============================================================================
# EXTENDING THE CLIENT
# =============================================================================

"""
To add new endpoints, extend DeribitAPIClient:

class DeribitAPIClient:
    async def get_ticker_info(self, ticker: str) -> Optional[Dict]:
        '''Get detailed ticker information.'''
        endpoint = f"{self.base_url}/public/ticker"
        params = {'instrument_name': f"{ticker.replace('_', '-').upper()}"}
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('result')
        return None

    async def get_market_data(self, ticker: str) -> Optional[Dict]:
        '''Get market data for ticker.'''
        # Similar implementation...
        pass
"""

# =============================================================================
# HANDLING RESPONSE FORMATS
# =============================================================================

"""
Deribit API uses JSON-RPC 2.0 format:

{
  "jsonrpc": "2.0",
  "result": {
    "index_price": 42850.50,
    ...
  },
  "usIn": ...,
  "usMid": ...,
  "usOut": ...,
  "id": null
}

Our client extracts the 'result' field automatically.
"""

# =============================================================================
# MONITORING AND DEBUGGING
# =============================================================================

"""
Enable detailed logging:

import logging
logging.basicConfig(level=logging.DEBUG)

This will show:
- Request URLs being made
- Response status codes
- Timeout errors
- Connection errors
- Response parsing
"""

# =============================================================================
# REFERENCES
# =============================================================================

"""
- Deribit API Docs: https://docs.deribit.com/
- Index Prices: https://docs.deribit.com/#public-get_index_price
- Rate Limiting: https://docs.deribit.com/#rate-limiting
- Error Codes: https://docs.deribit.com/#error-codes
"""
