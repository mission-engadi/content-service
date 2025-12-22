# Content Service Deployment Guide

Complete guide for deploying the Content Service to production environments.

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Docker Deployment](#docker-deployment)
6. [Manual Deployment](#manual-deployment)
7. [Cloud Deployment](#cloud-deployment)
8. [Security Configuration](#security-configuration)
9. [Monitoring & Logging](#monitoring--logging)
10. [Backup & Recovery](#backup--recovery)
11. [Scaling](#scaling)
12. [Troubleshooting](#troubleshooting)

## Deployment Options

### Option 1: Docker (Recommended)
- Containerized deployment
- Easy scaling
- Consistent environments
- Good for cloud platforms

### Option 2: Manual
- Direct server installation
- More control
- Traditional deployment
- Good for dedicated servers

### Option 3: Cloud Platforms
- Platform-as-a-Service
- Managed infrastructure
- Auto-scaling
- Examples: AWS, GCP, Azure, Heroku

## Pre-Deployment Checklist

### Before Deployment

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] Secret keys generated
- [ ] CORS origins configured
- [ ] File upload limits set
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] SSL/TLS certificates ready
- [ ] Documentation updated

### Security Checklist

- [ ] Change default secret keys
- [ ] Use strong passwords
- [ ] Enable HTTPS
- [ ] Configure firewall
- [ ] Set up authentication
- [ ] Review CORS settings
- [ ] Enable rate limiting (if available)
- [ ] Configure security headers

### Performance Checklist

- [ ] Database indexes optimized
- [ ] Connection pooling configured
- [ ] Caching enabled (Redis)
- [ ] File upload limits appropriate
- [ ] Worker processes configured
- [ ] Load balancer set up (if needed)

## Environment Configuration

### Production .env File

```bash
# Application
SERVICE_NAME=content_service
SERVICE_PORT=8002
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database (Use managed database in production)
DATABASE_URL=postgresql+asyncpg://user:password@db-host:5432/content_db

# Security (GENERATE NEW KEYS!)
SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (Set to your frontend domains)
ENABLE_CORS=true
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# Storage
UPLOAD_DIR=/var/www/content_service/uploads
BASE_URL=https://api.yourdomain.com
MAX_UPLOAD_SIZE=104857600

# Redis (Optional, for caching)
REDIS_URL=redis://redis-host:6379/0

# Monitoring (Optional)
SENTRY_DSN=https://your-sentry-dsn
```

### Generate Secret Keys

```bash
# Generate secret keys
openssl rand -hex 32
```

## Database Setup

### PostgreSQL Installation

**Ubuntu/Debian:**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Production Database Configuration:**
```sql
-- Create database
CREATE DATABASE content_db;

-- Create user with password
CREATE USER content_user WITH ENCRYPTED PASSWORD 'strong_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE content_db TO content_user;

-- Connect to database
\c content_db

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO content_user;
```

### Database Migrations

```bash
# Run migrations
alembic upgrade head

# Verify migrations
alembic current
alembic history
```

### Database Backup

```bash
# Create backup
pg_dump -U content_user content_db > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U content_user content_db < backup_20241222.sql
```

## Docker Deployment

### Dockerfile (Production-Ready)

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/api/v1/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### docker-compose.yml (Production)

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: content_db
      POSTGRES_USER: content_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    restart: always
    networks:
      - app-network

  app:
    build: .
    ports:
      - "8002:8002"
    environment:
      DATABASE_URL: postgresql+asyncpg://content_user:${DB_PASSWORD}@db:5432/content_db
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - db
      - redis
    restart: always
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: always
    networks:
      - app-network

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
```

### Deploy with Docker

```bash
# Build image
docker build -t content-service:latest .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f app

# Run migrations
docker-compose exec app alembic upgrade head

# Stop services
docker-compose down
```

## Manual Deployment

### Server Setup (Ubuntu 22.04)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install Nginx
sudo apt install nginx

# Install Redis (optional)
sudo apt install redis-server
```

### Application Setup

```bash
# Create application directory
sudo mkdir -p /var/www/content_service
cd /var/www/content_service

# Clone repository
git clone <repository-url> .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
nano .env  # Configure production settings

# Create uploads directory
mkdir -p uploads

# Set permissions
sudo chown -R www-data:www-data /var/www/content_service
```

### Systemd Service

Create `/etc/systemd/system/content-service.service`:

```ini
[Unit]
Description=Content Service
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/content_service
Environment="PATH=/var/www/content_service/venv/bin"
ExecStart=/var/www/content_service/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8002 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable content-service
sudo systemctl start content-service
sudo systemctl status content-service
```

### Nginx Configuration

Create `/etc/nginx/sites-available/content-service`:

```nginx
upstream content_service {
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/your_cert.crt;
    ssl_certificate_key /etc/ssl/private/your_key.key;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Logging
    access_log /var/log/nginx/content_service_access.log;
    error_log /var/log/nginx/content_service_error.log;

    # Proxy settings
    location / {
        proxy_pass http://content_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Upload size limit
    client_max_body_size 100M;

    # Static files (uploads)
    location /uploads/ {
        alias /var/www/content_service/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/content-service /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Cloud Deployment

### AWS Elastic Beanstalk

1. Install EB CLI:
```bash
pip install awsebcli
```

2. Initialize EB:
```bash
eb init -p python-3.11 content-service --region us-east-1
```

3. Create environment:
```bash
eb create production-env
```

4. Deploy:
```bash
eb deploy
```

### Google Cloud Run

1. Build and push image:
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/content-service
```

2. Deploy:
```bash
gcloud run deploy content-service \
  --image gcr.io/PROJECT_ID/content-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Heroku

1. Create Heroku app:
```bash
heroku create content-service-prod
```

2. Add PostgreSQL:
```bash
heroku addons:create heroku-postgresql:standard-0
```

3. Set environment variables:
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set JWT_SECRET_KEY=your-jwt-secret
```

4. Deploy:
```bash
git push heroku main
heroku run alembic upgrade head
```

## Security Configuration

### SSL/TLS

**Let's Encrypt (Free SSL):**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Firewall

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

### Security Headers

Add to Nginx configuration:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
```

## Monitoring & Logging

### Application Logging

Configure in `app/core/config.py`:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/content_service/app.log'),
        logging.StreamHandler()
    ]
)
```

### Log Rotation

Create `/etc/logrotate.d/content-service`:

```
/var/log/content_service/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload content-service > /dev/null
    endscript
}
```

### Health Monitoring

Set up monitoring endpoints:

```bash
# Check health
curl https://api.yourdomain.com/api/v1/health

# Monitor with cron
*/5 * * * * curl -f https://api.yourdomain.com/api/v1/health || echo "Service down" | mail -s "Alert" admin@example.com
```

## Backup & Recovery

### Automated Database Backup

Create `/usr/local/bin/backup-content-db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/content_service"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U content_user content_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /var/www/content_service/uploads

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup-content-db.sh
```

### Disaster Recovery

```bash
# Restore database
gunzip < backup.sql.gz | psql -U content_user content_db

# Restore uploads
tar -xzf uploads_backup.tar.gz -C /
```

## Scaling

### Horizontal Scaling

Add more application servers behind load balancer:

```nginx
upstream content_service {
    least_conn;
    server 10.0.1.10:8002;
    server 10.0.1.11:8002;
    server 10.0.1.12:8002;
}
```

### Vertical Scaling

Increase workers in systemd service:

```ini
ExecStart=/var/www/content_service/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8002 --workers 8
```

### Database Scaling

- Enable connection pooling
- Add read replicas
- Use managed database service

## Troubleshooting

### Service Not Starting

```bash
# Check service status
sudo systemctl status content-service

# View logs
sudo journalctl -u content-service -f

# Check configuration
cd /var/www/content_service
source venv/bin/activate
python -c "from app.core.config import settings; print(settings)"
```

### Database Connection Issues

```bash
# Test database connection
psql -U content_user -d content_db -h localhost

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### Performance Issues

```bash
# Check resource usage
top
htop

# Check database queries
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Enable query logging
# Edit /etc/postgresql/15/main/postgresql.conf
log_statement = 'all'
```

### File Upload Issues

```bash
# Check disk space
df -h

# Check permissions
ls -la /var/www/content_service/uploads

# Fix permissions
sudo chown -R www-data:www-data /var/www/content_service/uploads
sudo chmod -R 755 /var/www/content_service/uploads
```

---

## Deployment Checklist

Before going live:

- [ ] SSL certificate installed and valid
- [ ] All environment variables set
- [ ] Database migrations applied
- [ ] Backups configured and tested
- [ ] Monitoring alerts set up
- [ ] Firewall rules configured
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Rollback plan prepared
- [ ] Team notified of deployment

---

**Last Updated:** December 22, 2024
**Document Version:** 1.0

For support, contact the development team or refer to the troubleshooting section.
