# FluxScan Deployment Guide

## Table of Contents
1. [Deployment Options](#deployment-options)
2. [Local Development](#local-development)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Configuration Management](#configuration-management)
7. [Security Considerations](#security-considerations)
8. [Monitoring & Maintenance](#monitoring--maintenance)

## Deployment Options

### Comparison Matrix

| Option | Complexity | Cost | Scalability | Best For |
|--------|------------|------|-------------|----------|
| Local Development | Low | Free | None | Development/Testing |
| VPS Deployment | Medium | Low | Limited | Small teams |
| Docker | Medium | Variable | Good | Consistent deployments |
| Cloud (AWS/GCP/Azure) | High | Variable | Excellent | Production/Enterprise |
| Kubernetes | High | High | Excellent | Large scale operations |

## Local Development

### Prerequisites
```bash
# System requirements
- Python 3.8+
- 2GB RAM minimum
- 1GB disk space
```

### Setup Steps

1. **Clone Repository**
```bash
git clone https://github.com/yourusername/fluxscan.git
cd fluxscan
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Initialize Database**
```bash
python init_db.py
```

6. **Run Application**
```bash
python app.py
```

## Production Deployment

### Using Gunicorn (Linux)

1. **Install Production Dependencies**
```bash
pip install gunicorn gevent
```

2. **Create Gunicorn Configuration**
```python
# gunicorn_config.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
```

3. **Create Systemd Service**
```ini
# /etc/systemd/system/fluxscan.service
[Unit]
Description=FluxScan Trading Scanner
After=network.target

[Service]
User=fluxscan
Group=fluxscan
WorkingDirectory=/opt/fluxscan
Environment="PATH=/opt/fluxscan/venv/bin"
ExecStart=/opt/fluxscan/venv/bin/gunicorn \
    --config gunicorn_config.py \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

4. **Enable and Start Service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable fluxscan
sudo systemctl start fluxscan
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/fluxscan
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /opt/fluxscan/static;
        expires 30d;
    }
}
```

### SSL Configuration

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

## Docker Deployment

### Dockerfile

```dockerfile
# Multi-stage build
FROM python:3.9-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Production image
FROM python:3.9-slim

# Copy TA-Lib from builder
COPY --from=builder /usr/lib/libta_lib* /usr/lib/
COPY --from=builder /usr/include/ta-lib /usr/include/ta-lib

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 fluxscan && \
    chown -R fluxscan:fluxscan /app

USER fluxscan

# Expose port
EXPOSE 5001

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--worker-class", "eventlet", "-w", "1", "app:app"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  fluxscan:
    build: .
    container_name: fluxscan
    ports:
      - "5001:5001"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://fluxscan:password@postgres:5432/fluxscan
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:14-alpine
    container_name: fluxscan-db
    environment:
      - POSTGRES_DB=fluxscan
      - POSTGRES_USER=fluxscan
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: fluxscan-cache
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: fluxscan-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - fluxscan
    restart: unless-stopped

volumes:
  postgres_data:
```

### Deployment Commands

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f fluxscan

# Stop services
docker-compose down

# Backup database
docker-compose exec postgres pg_dump -U fluxscan fluxscan > backup.sql

# Restore database
docker-compose exec -T postgres psql -U fluxscan fluxscan < backup.sql
```

## Cloud Deployment

### AWS Deployment

#### Using Elastic Beanstalk

1. **Install EB CLI**
```bash
pip install awsebcli
```

2. **Initialize EB**
```bash
eb init -p python-3.9 fluxscan
```

3. **Create Environment**
```bash
eb create fluxscan-prod
```

4. **Configuration (.ebextensions/python.config)**
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app.py
  aws:elasticbeanstalk:application:environment:
    FLASK_ENV: production
    DATABASE_URL: your-rds-url
```

#### Using EC2

```bash
# Launch EC2 instance (Ubuntu 22.04)
# SSH into instance

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3-pip python3-venv nginx postgresql-client

# Clone and setup application
git clone https://github.com/yourusername/fluxscan.git
cd fluxscan
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure and run
# Follow production deployment steps above
```

### Google Cloud Platform

#### Using App Engine

**app.yaml:**
```yaml
runtime: python39
entrypoint: gunicorn -b :$PORT app:app

env_variables:
  FLASK_ENV: production
  DATABASE_URL: your-cloud-sql-url

automatic_scaling:
  target_cpu_utilization: 0.65
  min_instances: 1
  max_instances: 10
```

**Deploy:**
```bash
gcloud app deploy
```

### Azure Deployment

#### Using App Service

```bash
# Create resource group
az group create --name fluxscan-rg --location eastus

# Create app service plan
az appservice plan create \
    --name fluxscan-plan \
    --resource-group fluxscan-rg \
    --sku B1 \
    --is-linux

# Create web app
az webapp create \
    --resource-group fluxscan-rg \
    --plan fluxscan-plan \
    --name fluxscan \
    --runtime "PYTHON|3.9"

# Deploy code
az webapp deployment source config \
    --name fluxscan \
    --resource-group fluxscan-rg \
    --repo-url https://github.com/yourusername/fluxscan \
    --branch main \
    --manual-integration
```

## Configuration Management

### Environment Variables

```bash
# .env.production
FLASK_ENV=production
SECRET_KEY=generate-strong-secret-key
DATABASE_URL=postgresql://user:pass@localhost/fluxscan
REDIS_URL=redis://localhost:6379/0
OPENALGO_API_KEY=your-production-key
OPENALGO_HOST=https://api.openalgo.com

# Security
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# Performance
MAX_CONCURRENT_SCANS=20
CACHE_DEFAULT_TIMEOUT=600
```

### Database Migration

```bash
# PostgreSQL setup
sudo -u postgres psql

CREATE DATABASE fluxscan;
CREATE USER fluxscan WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE fluxscan TO fluxscan;
```

### Production Settings

```python
# config_production.py
import os

class ProductionConfig:
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }

    # Cache
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/fluxscan.log'
```

## Security Considerations

### Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use HTTPS in production
- [ ] Enable CORS restrictions
- [ ] Implement rate limiting
- [ ] Set secure headers
- [ ] Regular security updates
- [ ] Database backups
- [ ] Monitor access logs
- [ ] Implement API authentication
- [ ] Sanitize user inputs

### Security Headers

```python
# security.py
from flask import Flask
from flask_talisman import Talisman

def init_security(app: Flask):
    Talisman(app,
        force_https=True,
        strict_transport_security=True,
        content_security_policy={
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' cdn.jsdelivr.net",
            'style-src': "'self' 'unsafe-inline' cdn.jsdelivr.net"
        }
    )
```

### Firewall Rules

```bash
# UFW configuration
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Monitoring & Maintenance

### Health Monitoring

```python
# healthcheck.py
import psutil
import requests

def check_health():
    checks = {
        'database': check_database(),
        'cache': check_cache(),
        'disk_space': psutil.disk_usage('/').percent < 90,
        'memory': psutil.virtual_memory().percent < 90,
        'openalgo': check_openalgo_connection()
    }
    return all(checks.values()), checks
```

### Logging Configuration

```python
# logging_config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/fluxscan.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'default'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console']
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

# Database backup
pg_dump $DATABASE_URL > backups/db_$(date +%Y%m%d_%H%M%S).sql

# Application backup
tar -czf backups/app_$(date +%Y%m%d_%H%M%S).tar.gz \
    --exclude=venv \
    --exclude=__pycache__ \
    --exclude=logs \
    /opt/fluxscan

# Upload to S3 (optional)
aws s3 cp backups/ s3://your-backup-bucket/ --recursive

# Clean old backups (keep 30 days)
find backups/ -type f -mtime +30 -delete
```

### Monitoring Stack

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  node-exporter:
    image: prom/node-exporter
    ports:
      - "9100:9100"
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
```bash
# Find process using port
lsof -i :5001
# Kill process
kill -9 <PID>
```

2. **Database Connection Error**
```bash
# Test connection
psql -h localhost -U fluxscan -d fluxscan
```

3. **Permission Denied**
```bash
# Fix permissions
sudo chown -R $USER:$USER /opt/fluxscan
```

4. **Memory Issues**
```bash
# Increase swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Performance Optimization

### Application Level
- Use production WSGI server (Gunicorn)
- Enable response compression
- Implement query optimization
- Use connection pooling

### Database Level
- Add appropriate indexes
- Regular VACUUM and ANALYZE
- Query optimization
- Read replicas for scaling

### Caching Strategy
- Redis for session storage
- Cache API responses
- Static file caching
- CDN for assets