# Project Architecture & Design Patterns

## Overview

This document explains the architectural decisions, design patterns, and technical choices made in the Deribit Price Tracker project.

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Design Patterns](#design-patterns)
3. [Code Organization](#code-organization)
4. [Data Flow](#data-flow)
5. [Error Handling](#error-handling)
6. [Testing Strategy](#testing-strategy)
7. [Scalability Considerations](#scalability-considerations)

---

## High-Level Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      External: Deribit API                      │
│                   (https://www.deribit.com/api/v2)              │
└────────────────────────────┬────────────────────────────────────┘
                             │ (aiohttp async requests)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Application Layer                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐    ┌──────────────────┐                    │
│  │   REST API      │    │  Celery Tasks    │                    │
│  │   (DRF Views)   │    │  (Async Fetch)   │                    │
│  └────────┬────────┘    └────────┬─────────┘                    │
│           │                      │                               │
│  ┌────────▼──────────────────────▼──────────────┐               │
│  │         Service Layer (Business Logic)       │               │
│  │  - PriceService                             │               │
│  │  - DeribitAPIClient                         │               │
│  └────────┬──────────────────────────────────────┘              │
│           │                                                      │
│  ┌────────▼──────────────────────────────────────┐              │
│  │      Django ORM / Models                      │              │
│  │  - Price model with validation               │              │
│  │  - QuerySet optimization                     │              │
│  └────────┬──────────────────────────────────────┘              │
└───────────┼──────────────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────────────┐
│                    Data & Message Layer                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐        ┌───────────────────┐              │
│  │   PostgreSQL     │        │      Redis        │              │
│  │   (Persistence)  │        │  (Message Broker) │              │
│  │                  │        │  (Caching)        │              │
│  └──────────────────┘        └───────────────────┘              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Request Flow

#### GET Request Flow (Client → API → Database)

```
1. HTTP GET /api/prices/latest/?ticker=btc_usd
   │
2. → URL Router (config/urls.py)
   │
3. → API View (views.py - LatestPriceAPIView)
   │
4. → Serializer Validation (serializers.py)
   │
5. → Service Layer (services.py - PriceService)
   │
6. → Django ORM Query
   │
7. → PostgreSQL Database
   │
8. ← Query Result
   │
9. ← Serialized Response (PriceSerializer)
   │
10. ← JSON Response (200 OK)
```

#### Background Task Flow (Scheduler → Worker → Database)

```
1. Celery Beat triggers at interval (1 minute)
   │
2. → Celery Task (tasks.py - fetch_deribit_prices)
   │
3. → Service Layer (services.py - PriceService)
   │
4. → DeribitAPIClient (aiohttp async request)
   │
5. → External API (Deribit)
   │
6. ← API Response
   │
7. → Data Validation & Transformation
   │
8. → Django ORM Save
   │
9. → PostgreSQL Database
   │
10. ← Task Result (stored in Redis)
```

---

## Design Patterns

### 1. Service Layer Pattern

**Purpose**: Separate business logic from web framework

**Implementation**:

```python
# ❌ ANTI-PATTERN: Business logic in views
class PriceView(APIView):
    def get(self, request):
        prices = Price.objects.filter(ticker='btc_usd')
        for price in prices:
            price.price = price.price * 1.1  # Business logic!
        return Response(...)

# ✅ PATTERN: Business logic in service
class PriceService:
    def get_adjusted_prices(self, ticker):
        prices = self.get_all_prices(ticker)
        return [p * 1.1 for p in prices]

class PriceView(APIView):
    def __init__(self):
        self.service = PriceService()
    
    def get(self, request):
        prices = self.service.get_adjusted_prices(ticker)
        return Response(...)
```

**Benefits**:
- Reusable business logic
- Testable without Django/views
- Decoupled from web framework
- Easier to refactor

### 2. Dependency Injection

**Purpose**: Provide dependencies through constructor, not globals

**Implementation**:

```python
# ❌ ANTI-PATTERN: Global dependencies
DERIBIT_CLIENT = DeribitAPIClient()

class PriceService:
    def fetch_prices(self):
        result = DERIBIT_CLIENT.get_index_prices()  # Global!
        return result

# ✅ PATTERN: Injected dependencies
class PriceService:
    def __init__(self, deribit_client=None):
        self.deribit_client = deribit_client or DeribitAPIClient()
    
    def fetch_prices(self):
        result = self.deribit_client.get_index_prices()
        return result

# Easy to test with mock
service = PriceService(deribit_client=MockDeribitClient())
```

**Benefits**:
- Easy to mock for testing
- No side effects
- Clear dependencies
- Flexible configuration

### 3. Async/Await Pattern

**Purpose**: Non-blocking I/O for external API calls

**Implementation**:

```python
class DeribitAPIClient:
    async def get_index_price(self, ticker: str) -> Optional[Dict]:
        """Async HTTP request without blocking."""
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint) as response:
                return await response.json()

# Usage in Celery task
@shared_task
def fetch_prices():
    service = PriceService()
    result = asyncio.run(service.fetch_and_save_latest_prices())
    return result
```

**Benefits**:
- Handles network delays efficiently
- No thread overhead
- Better resource utilization
- Cleaner code than callbacks

### 4. Repository Pattern (Django ORM)

**Purpose**: Encapsulate data access logic

**Implementation**:

```python
class PriceRepository:
    """All database queries here."""
    
    @staticmethod
    def get_all_prices(ticker: str):
        return Price.objects.filter(ticker=ticker)
    
    @staticmethod
    def get_latest_price(ticker: str):
        return Price.objects.filter(ticker=ticker).first()
    
    @staticmethod
    def save_price(ticker: str, price: Decimal, timestamp: int):
        return Price.objects.create(
            ticker=ticker,
            price=price,
            timestamp=timestamp
        )
```

**Benefits**:
- Centralized query logic
- Easy to optimize queries
- Single place to add caching
- Better testing (can mock repository)

### 5. Value Object Pattern

**Purpose**: Immutable data objects with validation

**Implementation**:

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class PriceData:
    ticker: str
    price: Decimal
    timestamp: int
    
    def __post_init__(self):
        if not isinstance(self.price, Decimal):
            object.__setattr__(self, 'price', Decimal(str(self.price)))
        if self.price < 0:
            raise ValueError("Price cannot be negative")

# Usage
price = PriceData(
    ticker='btc_usd',
    price=Decimal('42850.50'),
    timestamp=1705689600
)
```

**Benefits**:
- Type safety
- Automatic validation
- Immutability prevents bugs
- Clear data contracts

---

## Code Organization

### Directory Structure with Responsibilities

```
derrebit_project/
│
├── config/                          # Project configuration
│   ├── settings.py                 # Django settings (DB, Celery, etc.)
│   ├── celery.py                   # Celery app configuration
│   ├── urls.py                     # URL routing
│   ├── wsgi.py                     # WSGI entry point
│   └── production.py               # Production overrides
│
├── apps/prices/                    # Main application
│   ├── models.py                   # Data models
│   │   └── Price                   # ORM model with validation
│   │
│   ├── services.py                 # Business logic
│   │   ├── DeribitAPIClient        # External API calls (aiohttp)
│   │   └── PriceService            # Core business logic
│   │
│   ├── views.py                    # REST API endpoints
│   │   ├── BaseTickerAPIView       # Common validation logic
│   │   ├── AllPricesAPIView        # GET /api/prices/all/
│   │   ├── LatestPriceAPIView      # GET /api/prices/latest/
│   │   └── PricesByDateRangeAPIView # GET /api/prices/range/
│   │
│   ├── serializers.py              # Data validation & serialization
│   │   ├── PriceSerializer         # Model serialization
│   │   ├── TickerFilterSerializer  # Input validation
│   │   └── DateRangeFilterSerializer # Advanced validation
│   │
│   ├── tasks.py                    # Celery background tasks
│   │   ├── fetch_deribit_prices    # Main price fetching task
│   │   └── cleanup_old_prices      # Data maintenance
│   │
│   ├── urls.py                     # App URL routing
│   ├── admin.py                    # Django Admin configuration
│   ├── apps.py                     # App initialization
│   ├── signals.py                  # Django signals (future use)
│   │
│   └── tests.py                    # Unit tests
│       ├── PriceModelTestCase      # Model tests
│       ├── PriceServiceTestCase    # Service tests
│       └── PriceAPITestCase        # API integration tests
│
├── manage.py                       # Django CLI
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Test configuration
├── .env.example                    # Environment template
│
├── Docker setup
│   ├── Dockerfile                  # Container definition
│   └── docker-compose.yml          # Multi-container setup
│
└── Documentation
    ├── README.md                   # Main documentation
    ├── API_EXAMPLES.md             # API usage examples
    ├── DERIBIT_INTEGRATION.md      # External API details
    ├── DEPLOYMENT.md               # Production deployment
    └── ARCHITECTURE.md             # This file
```

### Separation of Concerns

| Layer | Responsibility | Examples |
|-------|-----------------|----------|
| **Models** | Data structure & validation | Price model with fields and validators |
| **Serializers** | Request/response transformation | Validate input, format output |
| **Views** | HTTP handling | Parse requests, call services, return responses |
| **Services** | Business logic | Price retrieval, API integration, data transformation |
| **Tasks** | Background jobs | Schedule execution, handle retries |
| **URLs** | Routing | Map URLs to views |

---

## Data Flow

### Complete Price Fetch Cycle (1 minute)

```
Time: 00:00

1. Celery Beat scheduler fires
   └─> Sends task to Redis queue

2. Celery Worker picks up task
   └─> Executes fetch_deribit_prices()

3. fetch_deribit_prices() task
   └─> Creates PriceService instance
   └─> Calls fetch_and_save_latest_prices()

4. PriceService.fetch_and_save_latest_prices()
   └─> Calls DeribitAPIClient.get_index_prices()
       ├─> Async HTTP GET btc_usd
       └─> Async HTTP GET eth_usd (parallel)

5. DeribitAPIClient responses
   ├─> btc_usd: {"index_price": 42850.50, ...}
   └─> eth_usd: {"index_price": 2345.75, ...}

6. PriceService validates and saves
   ├─> save_price('btc_usd', 42850.50, timestamp)
   │   └─> Creates Price object
   │   └─> Saves to PostgreSQL
   │   └─> Returns saved Price instance
   │
   └─> save_price('eth_usd', 2345.75, timestamp)
       └─> Creates Price object
       └─> Saves to PostgreSQL
       └─> Returns saved Price instance

7. Task completes
   └─> Stores result in Redis
   └─> Logs success

Time: 01:00
   (Cycle repeats)
```

### API Response Cycle

```
Client Request: GET /api/prices/latest/?ticker=btc_usd

1. HTTP Request → Django URL Router
   └─> Matches to views.LatestPriceAPIView

2. LatestPriceAPIView.get()
   ├─> Validate ticker parameter
   │   └─> TickerFilterSerializer validates input
   ├─> Create PriceService instance
   ├─> Call service.get_latest_price('btc_usd')

3. PriceService.get_latest_price()
   └─> Executes QuerySet:
       Price.objects.filter(ticker='btc_usd')
                    .order_by('-timestamp')
                    .first()
   └─> Uses database index: idx_ticker_timestamp

4. Database Query Execution
   ├─> PostgreSQL receives query
   ├─> Uses index to find btc_usd prices
   ├─> Orders by timestamp descending
   ├─> Returns first result
   └─> ~5-15ms execution time

5. Result Serialization
   └─> PriceSerializer.to_representation()
   ├─> Converts Price instance to dict
   ├─> Formats decimal as string
   └─> Returns JSON-compatible data

6. HTTP Response
   ├─> Status: 200 OK
   ├─> Body: {
   │     "id": 1234,
   │     "ticker": "btc_usd",
   │     "price": "42850.50",
   │     "timestamp": 1705689600,
   │     "created_at": "2024-01-19T12:00:00Z"
   │   }
   └─> Content-Type: application/json

Client receives response
   └─> Parses JSON
   └─> Uses data
```

---

## Error Handling

### Multi-Level Error Strategy

#### 1. Validation Layer (Serializers)

```python
# Input validation before business logic
class TickerFilterSerializer(serializers.Serializer):
    ticker = serializers.ChoiceField(
        choices=PriceTickerChoices.choices,
        required=True
    )

# View catches validation errors
try:
    serializer = TickerFilterSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid ticker', 'details': serializer.errors},
            status=400
        )
except ValidationError as e:
    return Response({'error': str(e)}, status=400)
```

#### 2. Service Layer (Business Logic)

```python
# Service validates and handles errors
def save_price(self, ticker: str, price: Decimal, timestamp: int):
    if ticker not in dict(PriceTickerChoices.choices):
        raise ValueError(f"Invalid ticker: {ticker}")
    
    try:
        price_obj = Price.objects.create(...)
        logger.info(f"Saved price: {ticker}")
        return price_obj
    except IntegrityError as e:
        logger.error(f"Database error: {e}")
        raise
```

#### 3. Task Layer (Celery)

```python
@shared_task(bind=True, max_retries=3)
def fetch_deribit_prices(self):
    try:
        service = PriceService()
        result = asyncio.run(service.fetch_and_save_latest_prices())
        return {'status': 'success', ...}
    except Exception as exc:
        logger.error(f"Task error: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

#### 4. External API Layer (aiohttp)

```python
async def get_index_price(self, ticker: str) -> Optional[Dict]:
    try:
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API error: {response.status}")
                    return None
    except asyncio.TimeoutError:
        logger.error(f"Timeout for {ticker}")
        return None
    except aiohttp.ClientError as e:
        logger.error(f"Network error: {e}")
        return None
```

### Error Response Examples

```
Validation Error (400):
{
  "error": "Invalid ticker parameter",
  "details": {
    "ticker": ["\"xyz\" is not a valid choice"]
  }
}

Not Found (404):
{
  "error": "No price records found for btc_usd",
  "ticker": "btc_usd"
}

Server Error (500):
{
  "error": "Internal server error",
  "details": "Contact support"
}
```

---

## Testing Strategy

### Test Pyramid

```
        ▲
       ╱│╲                    (1-5 tests)
      ╱ │ ╲       Integration Tests
     ╱  │  ╲       (API, DB interactions)
    ╱───┼───╲
   ╱    │    ╲                (10-20 tests)
  ╱  Unit     ╲       Unit Tests
 ╱   Tests     ╲      (Services, Models)
╱──────────────╲
    (50+ tests)
```

### Unit Tests (Service Layer)

```python
class PriceServiceTestCase(TestCase):
    def test_save_price(self):
        service = PriceService()
        price = service.save_price(
            ticker='btc_usd',
            price=Decimal('50000.00'),
            timestamp=1234567890
        )
        self.assertEqual(price.price, Decimal('50000.00'))
    
    def test_invalid_ticker(self):
        service = PriceService()
        with self.assertRaises(ValueError):
            service.save_price(
                ticker='invalid',
                price=Decimal('1000.00'),
                timestamp=1234567890
            )
```

### Integration Tests (API Layer)

```python
class PriceAPITestCase(TestCase):
    def test_latest_price_endpoint(self):
        Price.objects.create(
            ticker='btc_usd',
            price=Decimal('42850.50'),
            timestamp=1705689600
        )
        response = self.client.get('/api/prices/latest/?ticker=btc_usd')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['price'], '42850.50')
```

### Mock Testing (External Dependencies)

```python
@patch('apps.prices.services.aiohttp.ClientSession')
async def test_api_client_timeout(mock_session):
    # Setup mock to raise timeout
    mock_session.return_value.__aenter__.side_effect = asyncio.TimeoutError()
    
    client = DeribitAPIClient()
    result = await client.get_index_price('btc_usd')
    
    self.assertIsNone(result)  # Should return None on timeout
```

---

## Scalability Considerations

### Horizontal Scaling

#### Current (Single Instance)

```
Client → Django Instance → PostgreSQL
                        ↓
                       Redis
                        ↓
                    Celery Worker
```

#### Scaled (Multiple Instances)

```
        → Django Instance 1 ↘
Client → Django Instance 2 → PostgreSQL (Master)
        → Django Instance 3 ↗  ↓
                         PostgreSQL (Replicas)
                        
        Redis Cluster (distributed cache)
                        ↓
        Celery Workers (multiple, distributed)
```

### Database Optimization

```python
# Current: Single database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'localhost',
    }
}

# Scaled: Master-slave replication
DATABASES = {
    'default': {  # Write operations
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'postgres-master',
    },
    'replica': {  # Read operations (GET endpoints)
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'postgres-replica-1',
        'OPTIONS': {'connect_timeout': 10}
    }
}

# Use replica for read queries
class PriceService:
    def get_all_prices(self, ticker):
        return Price.objects.using('replica').filter(ticker=ticker)
```

### Caching Strategy

```python
# Redis caching for frequent queries
from django.views.decorators.cache import cache_page

class LatestPriceAPIView(APIView):
    @cache_page(60)  # Cache for 60 seconds
    def get(self, request):
        ticker = request.query_params.get('ticker')
        latest = PriceService().get_latest_price(ticker)
        serializer = PriceSerializer(latest)
        return Response(serializer.data)
```

### Task Optimization

```python
# Batch insert instead of individual saves
class PriceService:
    def save_prices_batch(self, prices_data):
        """Bulk insert for better performance."""
        price_objects = [
            Price(ticker=ticker, price=price, timestamp=ts)
            for ticker, (price, ts) in prices_data.items()
        ]
        Price.objects.bulk_create(price_objects, batch_size=100)
```

### Monitoring & Metrics

```python
# Track important metrics
from django.core.cache import cache

def record_price_fetch(ticker, success):
    cache.incr(f'price_fetch_attempts:{ticker}')
    if success:
        cache.incr(f'price_fetch_success:{ticker}')

# Monitor in admin dashboard
def get_fetch_success_rate(ticker):
    attempts = cache.get(f'price_fetch_attempts:{ticker}', 0)
    successes = cache.get(f'price_fetch_success:{ticker}', 0)
    if attempts == 0:
        return 100
    return (successes / attempts) * 100
```

---

## Best Practices Implemented

✅ **Separation of Concerns**: Clear boundaries between models, services, views
✅ **DRY (Don't Repeat Yourself)**: Reusable service methods
✅ **SOLID Principles**: Single responsibility, open/closed principle
✅ **Type Hints**: Full Python type annotations
✅ **Error Handling**: Multi-level validation and error handling
✅ **Async Operations**: Non-blocking I/O for external calls
✅ **Testing**: Unit and integration tests with good coverage
✅ **Documentation**: Comprehensive comments and docstrings
✅ **Logging**: Structured logging for debugging
✅ **Security**: Input validation, no SQL injection, safe serialization

---

## Future Improvements

1. **Caching Layer**: Implement Redis caching for frequent queries
2. **API Authentication**: Add JWT or OAuth2 authentication
3. **Rate Limiting**: Implement API rate limiting per client
4. **GraphQL API**: Alternative to REST API
5. **WebSocket Support**: Real-time price updates
6. **Database Partitioning**: Partition Price table by date
7. **Event Sourcing**: Store all events for audit trail
8. **Command Query Separation**: CQRS pattern for complex scenarios
9. **Monitoring Dashboard**: Grafana/Prometheus integration
10. **Load Testing**: Simulate high-traffic scenarios

