# Quick Start & Running Instructions

## 🚀 Fast Start (30 seconds)

### Local Development (without Docker)

```bash
# 1. Clone project
cd /home/sayrex/Рабочий\ стол/derrebit_project

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env if needed (default values work for local dev)

# 5. Setup database
python manage.py migrate
python manage.py createsuperuser

# 6. Start services (open 3 terminals)

# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A config worker --loglevel=info

# Terminal 3: Celery Beat
celery -A config beat --loglevel=info
```

Visit:
- 🌐 **API**: http://localhost:8000/api/prices/
- 🔐 **Admin**: http://localhost:8000/admin/

---

## 🐳 Docker Start (10 seconds)

```bash
# 1. Navigate to project
cd /home/sayrex/Рабочий\ стол/derrebit_project

# 2. Create .env file (optional - uses defaults)
cp .env.example .env

# 3. Start everything
docker-compose up -d

# 4. Verify services are running
docker-compose ps

# Output should show:
# NAME              STATUS
# deribit_web       running
# deribit_postgres  running
# deribit_redis     running
# deribit_celery_worker running
# deribit_celery_beat running
```

Visit:
- 🌐 **API**: http://localhost:8000/api/prices/
- 🔐 **Admin**: http://localhost:8000/admin/

---

## 📚 Testing the API

### Option 1: Using curl

```bash
# Get latest BTC price
curl -X GET "http://localhost:8000/api/prices/latest/?ticker=btc_usd"

# Get all ETH prices
curl -X GET "http://localhost:8000/api/prices/all/?ticker=eth_usd&page=1&per_page=10"

# Get prices in date range
curl -X GET "http://localhost:8000/api/prices/range/?ticker=btc_usd&start_date=2024-01-18T00:00:00&end_date=2024-01-19T23:59:59"
```

### Option 2: Using Python

```bash
# Run examples
python examples.py
```

### Option 3: Using HTTPie (recommended)

```bash
pip install httpie

# Get latest price
http http://localhost:8000/api/prices/latest/ ticker=btc_usd

# Get all prices
http http://localhost:8000/api/prices/all/ ticker=eth_usd page=1 per_page=10
```

---

## ⚙️ Configuration

### Environment Variables

Edit `.env` file to configure:

```ini
# Security
SECRET_KEY=your-secret-key-here
DEBUG=True/False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=deribit_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Message Broker (Redis)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# External API
DERIBIT_BASE_URL=https://www.deribit.com/api/v2
DERIBIT_TIMEOUT=10
```

---

## 🧪 Running Tests

```bash
# All tests
pytest

# Specific test file
pytest apps/prices/tests.py

# Specific test class
pytest apps/prices/tests.py::PriceServiceTestCase

# Specific test method
pytest apps/prices/tests.py::PriceServiceTestCase::test_save_price

# With coverage
pytest --cov=apps

# Verbose output
pytest -v

# Docker: Run tests inside container
docker-compose exec web pytest
```

---

## 📊 Admin Dashboard

Access Django Admin at: http://localhost:8000/admin/

**Features**:
- View all stored prices
- Filter by ticker and date
- Add/delete price records (superuser only)
- View historical data

---

## 🔍 Monitoring & Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat

# Last 100 lines
docker-compose logs --tail=100

# Without timestamp
docker-compose logs --no-log-prefix
```

### Check Service Status

```bash
# All services
docker-compose ps

# Specific service
docker-compose ps web

# Resource usage
docker stats
```

### Django Shell

```bash
# Access Django shell
python manage.py shell

# Or with Docker
docker-compose exec web python manage.py shell

# Example commands:
from apps.prices.models import Price
from apps.prices.services import PriceService

# Get latest BTC price
latest = Price.objects.filter(ticker='btc_usd').order_by('-timestamp').first()
print(latest.price)

# Use service
service = PriceService()
prices = service.get_all_prices('btc_usd')
print(prices.count())
```

---

## 🛑 Stopping & Cleanup

### Docker

```bash
# Stop all services (keep data)
docker-compose down

# Stop and remove all data
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### Local Development

```bash
# Stop Django server
# Press Ctrl+C in terminal

# Stop Celery worker
# Press Ctrl+C in terminal

# Stop Celery beat
# Press Ctrl+C in terminal

# Deactivate virtual environment
deactivate
```

---

## 🔧 Common Commands

### Database Operations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Clear sessions
python manage.py clearsessions

# Backup database
pg_dump deribit_db > backup.sql

# Restore database
psql deribit_db < backup.sql
```

### Celery Operations

```bash
# Inspect active tasks
celery -A config inspect active

# Inspect task stats
celery -A config inspect stats

# View registered tasks
celery -A config inspect registered

# Inspect scheduled tasks
celery -A config inspect scheduled

# Clear all tasks
celery -A config purge
```

### Django Commands

```bash
# Run development server with reload
python manage.py runserver

# Run on different port
python manage.py runserver 0.0.0.0:8001

# Create app
python manage.py startapp myapp

# Collect static files
python manage.py collectstatic

# Check project health
python manage.py check

# Show database schema
python manage.py sqlmigrate prices 0001_initial
```

---

## ⚠️ Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
python manage.py runserver 8001
```

### Database Connection Error

```bash
# Check if PostgreSQL is running
pg_isready

# Connect to database manually
psql -U postgres -d deribit_db

# Check credentials in .env
cat .env | grep DB_
```

### Redis Connection Error

```bash
# Check if Redis is running
redis-cli ping

# Monitor Redis commands
redis-cli monitor

# Clear Redis cache
redis-cli FLUSHALL
```

### Celery Tasks Not Running

```bash
# Check worker is running
docker-compose logs celery_worker

# Check beat scheduler
docker-compose logs celery_beat

# Check Redis connection
redis-cli ping

# Restart worker
docker-compose restart celery_worker
```

### API Returns 400 Bad Request

```bash
# Check query parameters
# Required: ?ticker=btc_usd or ?ticker=eth_usd

# Validate datetime format (ISO 8601)
# Correct: 2024-01-19T12:00:00
# Wrong: 2024-01-19 12:00:00

# View error details
curl -s "http://localhost:8000/api/prices/all/" | jq '.'
```

---

## 📝 API Quick Reference

### 1. All Prices

```bash
GET /api/prices/all/?ticker=btc_usd
```

**Parameters**:
- `ticker` (required): `btc_usd` or `eth_usd`
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 100, max: 1000)

**Response**: List of all prices with count

### 2. Latest Price

```bash
GET /api/prices/latest/?ticker=btc_usd
```

**Parameters**:
- `ticker` (required): `btc_usd` or `eth_usd`

**Response**: Single latest price record

### 3. Price Range

```bash
GET /api/prices/range/?ticker=btc_usd&start_date=2024-01-18T00:00:00&end_date=2024-01-19T23:59:59
```

**Parameters**:
- `ticker` (required): `btc_usd` or `eth_usd`
- `start_date` (required): ISO 8601 datetime
- `end_date` (required): ISO 8601 datetime
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 100)

**Response**: Prices within date range

---

## 🎯 What to Check First

After starting the project:

1. ✅ Can you access the API? `curl http://localhost:8000/api/prices/latest/?ticker=btc_usd`
2. ✅ Are prices being fetched? Check `/admin` → Prices
3. ✅ Is Celery working? `celery -A config inspect active`
4. ✅ Can you create superuser? `python manage.py createsuperuser`
5. ✅ Do tests pass? `pytest`

---

## 📚 Documentation Files

- **README.md** - Complete project overview
- **API_EXAMPLES.md** - API usage examples with curl/Python
- **DERIBIT_INTEGRATION.md** - Deribit API reference
- **ARCHITECTURE.md** - System design and patterns
- **DEPLOYMENT.md** - Production deployment guide
- **REQUIREMENTS.txt** - Python dependencies

---

## 🆘 Getting Help

### Check Logs

```bash
# Django logs
docker-compose logs web

# Celery worker logs
docker-compose logs celery_worker

# Application logs
docker-compose logs -f

# Search for errors
docker-compose logs | grep ERROR
```

### Run Diagnostics

```bash
# Check configuration
python manage.py check

# Test database connection
python manage.py dbshell

# Test Redis connection
redis-cli ping

# Test API
curl -v http://localhost:8000/api/prices/latest/?ticker=btc_usd
```

### Contact Support

Refer to code comments and docstrings for detailed explanations.

---

**Version**: 1.0.0  
**Last Updated**: January 19, 2024
