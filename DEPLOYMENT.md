# Production Deployment Guide

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- Domain name (for SSL)
- SSL certificate (Let's Encrypt recommended)

## Architecture Overview

```
                                    ┌─────────────────┐
                                    │  Load Balancer  │
                                    │   (Nginx/HAProxy)
                                    └────────┬────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                   ┌────▼───┐          ┌────▼───┐          ┌────▼───┐
                   │ Django │          │ Django │          │ Django │
                   │ (8000) │          │ (8001) │          │ (8002) │
                   └────┬───┘          └────┬───┘          └────┬───┘
                        │                    │                    │
                        └────────────────────┼────────────────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   PostgreSQL    │
                                    │   (Master)      │
                                    └────────┬────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                   ┌────▼──────┐        ┌────▼──────┐        ┌────▼──────┐
                   │ PostgreSQL │        │ PostgreSQL │        │ PostgreSQL │
                   │  (Replica) │        │  (Replica) │        │  (Replica) │
                   └────────────┘        └────────────┘        └────────────┘

                                    ┌─────────────────┐
                                    │     Redis       │
                                    │   (Cluster)     │
                                    └────────┬────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
                   │  Celery  │          │  Celery  │          │  Celery  │
                   │ (Worker) │          │ (Worker) │          │ (Worker) │
                   └──────────┘          └──────────┘          └──────────┘
```

## Step 1: Server Setup

### 1.1 System Updates

```bash
ssh ubuntu@your-server-ip
sudo apt update
sudo apt upgrade -y
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev
```

### 1.2 Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 1.3 Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Step 2: Clone and Setup Project

```bash
# Clone project
git clone https://your-repo-url.git /opt/deribit
cd /opt/deribit

# Create production .env
cp .env.example .env
```

### 2.1 Edit Production .env

```bash
sudo nano /opt/deribit/.env
```

Set these values:

```ini
# Security
SECRET_KEY=your-long-random-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL RDS or managed service recommended)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=deribit_db
DB_USER=deribit_user
DB_PASSWORD=your-strong-password
DB_HOST=your-rds-endpoint.amazonaws.com
DB_PORT=5432

# Redis
CELERY_BROKER_URL=redis://your-redis-endpoint:6379/0
CELERY_RESULT_BACKEND=redis://your-redis-endpoint:6379/0

# Deribit
DERIBIT_BASE_URL=https://www.deribit.com/api/v2
DERIBIT_TIMEOUT=10
```

## Step 3: Database Setup

### Option A: AWS RDS (Recommended for Production)

```bash
# Create RDS PostgreSQL instance via AWS Console or CLI
aws rds create-db-instance \
  --db-instance-identifier deribit-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username deribit_user \
  --master-user-password 'your-strong-password' \
  --allocated-storage 20 \
  --backup-retention-period 7
```

### Option B: Docker (Development)

```bash
docker run -d \
  --name postgres \
  -e POSTGRES_DB=deribit_db \
  -e POSTGRES_USER=deribit_user \
  -e POSTGRES_PASSWORD=password \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15-alpine
```

## Step 4: Redis Setup

### Option A: AWS ElastiCache (Recommended)

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id deribit-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0
```

### Option B: Docker

```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine
```

## Step 5: Docker Compose Deployment

```bash
cd /opt/deribit

# Build images
docker-compose build

# Start services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput
```

## Step 6: Nginx Configuration

### 6.1 Install Nginx

```bash
sudo apt install -y nginx
```

### 6.2 Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/deribit
```

Add:

```nginx
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    client_max_body_size 75M;

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /app/staticfiles/;
    }
}
```

### 6.3 Enable and Start Nginx

```bash
sudo ln -s /etc/nginx/sites-available/deribit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 7: SSL Certificate (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx

sudo certbot certonly --nginx \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email your-email@example.com
```

Update Nginx config to use SSL:

```bash
sudo nano /etc/nginx/sites-available/deribit
```

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # ... rest of config
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

## Step 8: Monitoring and Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

### Monitor Resources

```bash
# Docker stats
docker stats

# Check disk usage
df -h

# Check processes
top
```

### Setup Log Rotation

```bash
sudo nano /etc/logrotate.d/deribit
```

Add:

```
/var/log/deribit/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
```

## Step 9: Automated Backups

```bash
# Create backup script
cat > /opt/deribit/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/deribit"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec -T postgres pg_dump -U deribit_user deribit_db > \
    "$BACKUP_DIR/db_$DATE.sql"

# Compress
gzip "$BACKUP_DIR/db_$DATE.sql"

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_$DATE.sql.gz"
EOF

chmod +x /opt/deribit/backup.sh

# Schedule daily backups
sudo crontab -e
# Add: 0 2 * * * /opt/deribit/backup.sh
```

## Step 10: Health Checks

Create a monitoring script:

```bash
#!/bin/bash
# /opt/deribit/health_check.sh

API_URL="https://yourdomain.com/api/prices/latest/?ticker=btc_usd"

response=$(curl -s -w "%{http_code}" "$API_URL")
http_code="${response: -3}"

if [ "$http_code" != "200" ]; then
    # Send alert email
    echo "API health check failed: HTTP $http_code" | \
        mail -s "Alert: Deribit API Down" admin@example.com
fi
```

Add to crontab:

```bash
*/5 * * * * /opt/deribit/health_check.sh
```

## Troubleshooting

### Docker Container Won't Start

```bash
docker-compose logs web
docker-compose ps

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Issues

```bash
# Test connection
docker-compose exec web python manage.py dbshell

# Check environment variables
docker-compose config
```

### Celery Tasks Not Running

```bash
# Check worker status
docker-compose logs celery_worker

# Restart worker
docker-compose restart celery_worker

# Check beat schedule
docker-compose exec celery_beat celery -A config inspect scheduled
```

## Performance Tuning

### Database Connection Pool

```python
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,
        'ATOMIC_REQUESTS': False,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=read_committed'
        }
    }
}
```

### Gunicorn Workers

```bash
# Optimal workers = (2 * CPU cores) + 1
gunicorn config.wsgi:application --workers 9 --threads 2
```

## Maintenance

### Regular Tasks

- [ ] Check disk space weekly
- [ ] Monitor error logs daily
- [ ] Review Celery task failures
- [ ] Backup database daily
- [ ] Update SSL certificates (90-day renewal)
- [ ] Review security logs
- [ ] Update dependencies monthly

### Django Maintenance

```bash
# Clear old sessions
docker-compose exec web python manage.py clearsessions

# Update database statistics
docker-compose exec web python manage.py clearsessions

# Analyze migrations
docker-compose exec web python manage.py showmigrations
```

## Scaling to Production Load

1. **Database**: Use connection pooling (PgBouncer)
2. **Caching**: Implement Redis caching layer
3. **Workers**: Scale Celery workers horizontally
4. **Load Balancer**: Use HAProxy or AWS ALB
5. **CDN**: Use CloudFront for static files
6. **Monitoring**: Implement APM (DataDog, New Relic)
7. **Alerting**: Setup PagerDuty integration

## Security Checklist

- [ ] Change all default passwords
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Setup rate limiting
- [ ] Enable CORS only for trusted domains
- [ ] Implement API authentication (if needed)
- [ ] Setup audit logging
- [ ] Enable database encryption
- [ ] Regular security updates
- [ ] Monitor for suspicious activity
