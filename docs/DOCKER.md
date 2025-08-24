# Docker Deployment Guide

## Overview

This guide covers deploying Stock Agent using Docker for production environments. The Docker setup is optimized for:

- **Small image size**: Multi-stage build with Python slim base
- **Security**: Non-root user execution
- **Persistence**: Database and logs mounted as volumes
- **Performance**: Optimized Python bytecode compilation
- **Monitoring**: Built-in health checks

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys and configuration
nano .env
```

### 2. Build and Run with Docker Compose (Recommended)

```bash
# Build and start the service
docker-compose up --build -d

# View logs
docker-compose logs -f

# Access the application
open http://localhost:8080
```

### 3. Manual Docker Build and Run

```bash
# Build the image
docker build -t stock-agent .

# Run the container
docker run -d \
  --name stock-agent \
  -p 8080:8080 \
  -v stock_agent_data:/app/data \
  -v stock_agent_logs:/app/logs \
  --env-file .env \
  stock-agent
```

## Configuration

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Required API Keys
POLYGON_API_KEY=your_polygon_api_key
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_VAPID_PUBLIC_KEY=your_vapid_key

# Server Configuration
HOST=0.0.0.0
PORT=8080
GENERATE_MARKET_SUMMARY=true

# Database (inside container)
DATABASE_PATH=/app/data/users.db
DATA_DIR=/app/data
```

### Firebase Credentials

Place your Firebase service account JSON file as `firebase_creds.json` in the project root. It will be copied into the container during build.

## Docker Compose (Recommended)

### Basic Usage

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f stock-agent

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up --build -d

# Remove everything including volumes
docker-compose down -v
```

### Customization

Edit `docker-compose.yml` to customize:

```yaml
services:
  stock-agent:
    ports:
      - "3000:8080"  # Use different host port
    environment:
      - PORT=8080
      - LOG_LEVEL=DEBUG  # Enable debug logging
    deploy:
      resources:
        limits:
          memory: 1G  # Increase memory limit
```

## Manual Docker Commands

### Building the Image

```bash
# Build with default tag
docker build -t stock-agent .

# Build with custom tag
docker build -t stock-agent:v1.0.0 .

# Build with build arguments
docker build --build-arg PYTHON_VERSION=3.12 -t stock-agent .
```

### Running Containers

#### Basic Run

```bash
docker run -d \
  --name stock-agent \
  -p 8080:8080 \
  --env-file .env \
  stock-agent
```

#### Production Run with Volumes

```bash
docker run -d \
  --name stock-agent \
  --restart unless-stopped \
  -p 8080:8080 \
  -v stock_agent_data:/app/data \
  -v stock_agent_logs:/app/logs \
  --env-file .env \
  --memory=512m \
  --cpus=1.0 \
  stock-agent
```

#### Development Run with File Mounting

```bash
docker run -d \
  --name stock-agent-dev \
  -p 8080:8080 \
  -v $(pwd)/firebase_creds.json:/app/firebase_creds.json:ro \
  -v $(pwd)/.env:/app/.env:ro \
  -v stock_agent_data:/app/data \
  stock-agent
```

## Volume Management

### Understanding Volumes

The container uses two main volumes:

- **`/app/data`**: Database and application data
- **`/app/logs`**: Application logs

### Volume Commands

```bash
# List volumes
docker volume ls | grep stock_agent

# Inspect volume
docker volume inspect stock_agent_data

# Backup database
docker run --rm \
  -v stock_agent_data:/data \
  -v $(pwd):/backup \
  alpine:latest \
  tar czf /backup/stock_agent_backup.tar.gz -C /data .

# Restore database
docker run --rm \
  -v stock_agent_data:/data \
  -v $(pwd):/backup \
  alpine:latest \
  tar xzf /backup/stock_agent_backup.tar.gz -C /data

# Remove volumes (destructive)
docker-compose down -v
```

## Image Optimization

### Multi-stage Build Benefits

The Dockerfile uses multi-stage build for optimization:

```dockerfile
FROM python:3.12-slim as builder  # Build dependencies
FROM python:3.12-slim as runtime  # Minimal runtime
```

**Benefits:**
- **Smaller image**: ~200MB vs ~800MB+ without multi-stage
- **Faster startup**: Pre-compiled bytecode
- **Better security**: No build tools in final image

### Build Size Comparison

```bash
# Check image size
docker images stock-agent

# Compare with single-stage build
docker build -f Dockerfile.single-stage -t stock-agent:single .
docker images | grep stock-agent
```

## Health Checks and Monitoring

### Built-in Health Check

The container includes a health check:

```bash
# Check container health
docker ps
docker inspect stock-agent | grep -A 10 Health
```

### Custom Health Checks

```bash
# Manual health check
docker exec stock-agent curl -f http://localhost:8080/ || echo "Unhealthy"

# View health check logs
docker inspect stock-agent | jq '.[0].State.Health.Log'
```

### Monitoring with Docker Stats

```bash
# Real-time stats
docker stats stock-agent

# One-time stats
docker stats --no-stream stock-agent
```

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check container logs
docker logs stock-agent

# Check if port is available
netstat -tlnp | grep 8080
lsof -i :8080

# Check environment variables
docker exec stock-agent env | grep -E "(FIREBASE|POLYGON)"
```

#### Permission Issues

```bash
# Check file ownership in volume
docker exec stock-agent ls -la /app/data/

# Fix volume permissions (if needed)
docker exec --user root stock-agent chown -R stockagent:stockagent /app/data
```

#### Database Issues

```bash
# Check database file
docker exec stock-agent ls -la /app/data/users.db

# Access database directly
docker exec -it stock-agent sqlite3 /app/data/users.db ".tables"

# Check database logs
docker exec stock-agent tail -f /app/logs/app.log
```

### Debugging Commands

```bash
# Interactive shell in running container
docker exec -it stock-agent /bin/bash

# Run container in debug mode
docker run -it --rm \
  --env-file .env \
  -v stock_agent_data:/app/data \
  stock-agent /bin/bash

# Check Python import
docker exec stock-agent python -c "from stock_agent.web import create_web_app; print('OK')"
```

## Production Deployment

### Security Considerations

```bash
# Run with read-only root filesystem
docker run -d \
  --name stock-agent \
  --read-only \
  --tmpfs /tmp \
  -v stock_agent_data:/app/data \
  stock-agent

# Use secrets for sensitive data
docker swarm init
echo "your_api_key" | docker secret create polygon_api_key -
docker service create \
  --name stock-agent \
  --secret polygon_api_key \
  stock-agent
```

### Resource Limits

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 128M
```

### Logging Configuration

```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## Scaling and Load Balancing

### Multiple Instances

```yaml
# docker-compose.yml
services:
  stock-agent:
    scale: 3  # Run 3 instances
    ports:
      - "8080-8082:8080"  # Map to different ports
```

### With Nginx Load Balancer

```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - stock-agent

  stock-agent:
    scale: 2
    expose:
      - "8080"
```

## Maintenance

### Updates and Rollbacks

```bash
# Update to new version
docker pull stock-agent:latest
docker-compose up -d

# Rollback to previous version
docker tag stock-agent:latest stock-agent:rollback
docker pull stock-agent:previous
docker-compose up -d

# Clean up old images
docker image prune -f
```

### Database Maintenance

```bash
# Vacuum database
docker exec stock-agent sqlite3 /app/data/users.db "VACUUM;"

# Check database integrity
docker exec stock-agent sqlite3 /app/data/users.db "PRAGMA integrity_check;"
```

## Performance Tips

1. **Use volume mounts** for database persistence
2. **Set resource limits** to prevent memory issues
3. **Enable health checks** for automatic restarts
4. **Use multi-stage builds** for smaller images
5. **Run as non-root user** for security
6. **Use proper logging drivers** for log management

## Getting Help

- Check container logs: `docker logs stock-agent`
- Inspect container: `docker inspect stock-agent`
- Interactive debugging: `docker exec -it stock-agent /bin/bash`
- Health status: `docker ps` (look for "healthy" status)