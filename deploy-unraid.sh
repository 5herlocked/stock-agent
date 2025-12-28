#!/bin/bash
#
# Stock Agent Deployment Script for Unraid
# Usage: ./deploy-unraid.sh [option]
# Options: 1 (nginx), 2 (swag-direct), 3 (caddy)
#

set -e

echo "========================================="
echo "  Stock Agent - Unraid Deployment"
echo "========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Unraid (optional)
if [ ! -d "/mnt/user/appdata" ]; then
    echo -e "${YELLOW}Warning: /mnt/user/appdata not found. Are you running on Unraid?${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get deployment option
if [ -z "$1" ]; then
    echo "Select deployment option:"
    echo "1) NGINX Web Server (Recommended)"
    echo "2) SWAG Direct (Simplest)"
    echo "3) Caddy Server (Advanced)"
    echo ""
    read -p "Enter option (1-3): " OPTION
else
    OPTION=$1
fi

# Get domain name
read -p "Enter your subdomain (e.g., stocks.yourdomain.com): " DOMAIN

# Get Polygon API Key
read -sp "Enter your Polygon.io API Key: " POLYGON_API_KEY
echo ""

# Get Firebase credentials path (optional)
read -p "Enter path to Firebase credentials JSON (optional, press Enter to skip): " FIREBASE_CREDS_PATH

case $OPTION in
    1)
        echo -e "\n${GREEN}Deploying to NGINX...${NC}"
        DEST_DIR="/mnt/user/appdata/stock-agent"

        # Create directory structure
        mkdir -p "$DEST_DIR"
        mkdir -p "$DEST_DIR/data"

        # Create docker-compose.yml for stock-agent
        cat > $DEST_DIR/docker-compose.yml << 'EOF'
version: '3.8'

services:
  stock-agent:
    image: python:3.12-slim
    container_name: stock-agent
    restart: unless-stopped
    working_dir: /app
    command: >
      sh -c "pip install -e . &&
             stock_agent"
    environment:
      - POLYGON_API_KEY=${POLYGON_API_KEY}
      - FLASK_ENV=production
    volumes:
      - /path/to/stock-agent:/app
      - ./data:/app/data
      - ./firebase-creds.json:/app/firebase-creds.json:ro
    networks:
      - proxynet
    expose:
      - "8080"

networks:
  proxynet:
    external: true
EOF

        echo -e "${GREEN}Docker Compose configuration created${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Update docker-compose.yml:"
        echo "   - Replace /path/to/stock-agent with actual path"
        echo ""
        echo "2. Copy Firebase credentials (if provided):"
        if [ -n "$FIREBASE_CREDS_PATH" ] && [ -f "$FIREBASE_CREDS_PATH" ]; then
            cp "$FIREBASE_CREDS_PATH" "$DEST_DIR/firebase-creds.json"
            echo "   ✓ Firebase credentials copied"
        else
            echo "   cp your-firebase-creds.json $DEST_DIR/firebase-creds.json"
        fi
        echo ""
        echo "3. Create SWAG proxy config at:"
        echo "   /mnt/user/appdata/swag/nginx/proxy-confs/stock-agent.subdomain.conf"
        echo ""
        echo "4. Add this configuration:"
        echo "---"
        cat << 'PROXY_CONF'
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;

    server_name DOMAIN;

    include /config/nginx/ssl.conf;

    client_max_body_size 0;

    location / {
        include /config/nginx/proxy.conf;
        include /config/nginx/resolver.conf;
        set $upstream_app stock-agent;
        set $upstream_port 8080;
        set $upstream_proto http;
        proxy_pass $upstream_proto://$upstream_app:$upstream_port;
    }
}
PROXY_CONF
        echo "---"
        echo ""
        echo "5. Replace 'DOMAIN' with: $DOMAIN"
        echo "6. Create .env file:"
        echo "   cat > $DEST_DIR/.env << 'ENVEOF'"
        echo "POLYGON_API_KEY=$POLYGON_API_KEY"
        echo "ENVEOF"
        echo ""
        echo "7. Start application:"
        echo "   cd $DEST_DIR && docker-compose up -d"
        echo ""
        echo "8. Restart SWAG:"
        echo "   docker restart swag"
        ;;

    2)
        echo -e "\n${GREEN}Deploying directly with SWAG...${NC}"
        DEST_DIR="/mnt/user/appdata/stock-agent"

        if [ ! -d "/mnt/user/appdata/swag" ]; then
            echo -e "${RED}Error: SWAG appdata directory not found!${NC}"
            echo "Please install SWAG first."
            exit 1
        fi

        # Create directory structure
        mkdir -p "$DEST_DIR"
        mkdir -p "$DEST_DIR/data"

        # Create docker-compose.yml
        cat > $DEST_DIR/docker-compose.yml << 'EOF'
version: '3.8'

services:
  stock-agent:
    image: python:3.12-slim
    container_name: stock-agent
    restart: unless-stopped
    working_dir: /app
    command: >
      sh -c "pip install -e . &&
             stock_agent"
    environment:
      - POLYGON_API_KEY=${POLYGON_API_KEY}
      - FLASK_ENV=production
    volumes:
      - /path/to/stock-agent:/app
      - ./data:/app/data
      - ./firebase-creds.json:/app/firebase-creds.json:ro
    networks:
      - proxynet
    expose:
      - "8080"

networks:
  proxynet:
    external: true
EOF

        echo -e "${GREEN}Docker Compose configuration created${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Update docker-compose.yml:"
        echo "   - Replace /path/to/stock-agent with actual path"
        echo ""
        echo "2. Copy Firebase credentials (if provided):"
        if [ -n "$FIREBASE_CREDS_PATH" ] && [ -f "$FIREBASE_CREDS_PATH" ]; then
            cp "$FIREBASE_CREDS_PATH" "$DEST_DIR/firebase-creds.json"
            echo "   ✓ Firebase credentials copied"
        else
            echo "   cp your-firebase-creds.json $DEST_DIR/firebase-creds.json"
        fi
        echo ""
        echo "3. Create SWAG site config at:"
        echo "   /mnt/user/appdata/swag/nginx/site-confs/stock-agent.conf"
        echo ""
        echo "4. Add this configuration:"
        echo "---"
        cat << 'SITE_CONF'
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;

    server_name DOMAIN;

    include /config/nginx/ssl.conf;

    client_max_body_size 0;

    location / {
        include /config/nginx/proxy.conf;
        include /config/nginx/resolver.conf;
        set $upstream_app stock-agent;
        set $upstream_port 8080;
        set $upstream_proto http;
        proxy_pass $upstream_proto://$upstream_app:$upstream_port;
    }
}
SITE_CONF
        echo "---"
        echo ""
        echo "5. Replace 'DOMAIN' with: $DOMAIN"
        echo "6. Create .env file:"
        echo "   cat > $DEST_DIR/.env << 'ENVEOF'"
        echo "POLYGON_API_KEY=$POLYGON_API_KEY"
        echo "ENVEOF"
        echo ""
        echo "7. Start application:"
        echo "   cd $DEST_DIR && docker-compose up -d"
        echo ""
        echo "8. Restart SWAG:"
        echo "   docker restart swag"
        ;;

    3)
        echo -e "\n${GREEN}Setting up Caddy deployment...${NC}"
        DEST_DIR="/mnt/user/appdata/stock-agent"

        # Create directory structure
        mkdir -p "$DEST_DIR"
        mkdir -p "$DEST_DIR/data"

        # Create Caddyfile
        cat > $DEST_DIR/Caddyfile << 'EOF'
DOMAIN {
    reverse_proxy stock-agent:8080

    # Security headers
    header X-Frame-Options SAMEORIGIN
    header X-Content-Type-Options nosniff
    header X-XSS-Protection "1; mode=block"

    # Enable compression
    encode gzip
}
EOF

        # Create docker-compose.yml with both Caddy and stock-agent
        cat > $DEST_DIR/docker-compose.yml << 'EOF'
version: '3.8'

services:
  caddy:
    image: caddy:alpine
    container_name: stock-agent-caddy
    restart: unless-stopped
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - proxynet
    expose:
      - "80"
      - "443"

  stock-agent:
    image: python:3.12-slim
    container_name: stock-agent
    restart: unless-stopped
    working_dir: /app
    command: >
      sh -c "pip install -e . &&
             stock_agent"
    environment:
      - POLYGON_API_KEY=${POLYGON_API_KEY}
      - FLASK_ENV=production
    volumes:
      - /path/to/stock-agent:/app
      - ./data:/app/data
      - ./firebase-creds.json:/app/firebase-creds.json:ro
    networks:
      - proxynet
    expose:
      - "8080"

volumes:
  caddy_data:
  caddy_config:

networks:
  proxynet:
    external: true
EOF

        echo -e "${GREEN}Files created in $DEST_DIR${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Update docker-compose.yml:"
        echo "   - Replace /path/to/stock-agent with actual path"
        echo ""
        echo "2. Update Caddyfile:"
        echo "   - Replace 'DOMAIN' with: $DOMAIN"
        echo ""
        echo "3. Copy Firebase credentials (if provided):"
        if [ -n "$FIREBASE_CREDS_PATH" ] && [ -f "$FIREBASE_CREDS_PATH" ]; then
            cp "$FIREBASE_CREDS_PATH" "$DEST_DIR/firebase-creds.json"
            echo "   ✓ Firebase credentials copied"
        else
            echo "   cp your-firebase-creds.json $DEST_DIR/firebase-creds.json"
        fi
        echo ""
        echo "4. Create .env file:"
        echo "   cat > $DEST_DIR/.env << 'ENVEOF'"
        echo "POLYGON_API_KEY=$POLYGON_API_KEY"
        echo "ENVEOF"
        echo ""
        echo "5. Start the containers:"
        echo "   cd $DEST_DIR && docker-compose up -d"
        echo ""
        echo "6. Test access: https://$DOMAIN"
        ;;

    *)
        echo -e "${RED}Invalid option!${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Deployment preparation complete!${NC}"
echo ""
echo "Additional reminders:"
echo "- Ensure DNS points to your server"
echo "- Verify Firebase credentials are copied"
echo "- Verify POLYGON_API_KEY is set"
echo "- Test access: https://$DOMAIN"
echo "- Check logs: docker logs stock-agent"
echo ""
echo -e "${YELLOW}Happy self-hosting!${NC}"
