# Stock Agent Development Setup Guide

## Overview

This guide covers how to set up and run the Stock Agent project in development mode, taking advantage of Robyn's hot reloading and development features.

## Prerequisites

- Python 3.12+
- Git
- A modern web browser (for testing)
- Optional: UV package manager (recommended)

## Initial Setup

### 1. Clone and Navigate to Project

```bash
git clone <repository-url>
cd stock-agent
```

### 2. Set Up Python Environment

#### Using UV (Recommended)
```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

#### Using Standard Python
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .
```

### 3. Environment Configuration

The project uses `.dev.env` for development configuration. Key variables:

```bash
# API Configuration
POLYGON_API_KEY=your_polygon_api_key

# Firebase Configuration  
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_PROJECT_ID=your_project_id
# ... other Firebase configs

# Development Server Settings
DEV_HOST=127.0.0.1         # Development host
DEV_PORT=8080               # Development port
DEV_GENERATE_SUMMARY=false  # Skip market summary for faster startup

# Production Settings (when using main.py)
HOST=0.0.0.0
PORT=8080
GENERATE_MARKET_SUMMARY=true
```

## Running the Application

### Option 1: Development Server (Recommended)

Use the dedicated development server with hot reloading:

```bash
python dev_server.py
```

**Features:**
- ✅ Hot reloading (changes automatically restart server)
- ✅ Debug mode enabled
- ✅ Faster startup (skips market summary by default)
- ✅ Development-optimized configuration
- ✅ Better error messages and logging

**Output:**
```
✅ Loaded environment variables from .dev.env
⏩ Skipping market summary generation (set DEV_GENERATE_SUMMARY=true to enable)
🚀 Creating web application...

🔥 Starting development server...

   URL: http://127.0.0.1:8080

   Features enabled:
   ✅ Hot reloading
   ✅ Debug mode
   ✅ Static file serving
   ✅ Service worker authentication
```

### Option 2: Using UV Scripts

```bash
# Run development server
uv run python dev_server.py

# Run production server
uv run stock_agent
```

### Option 3: Direct Module Execution

```bash
# Development mode
python -m stock_agent.main

# Or using the installed script
stock_agent
```

### Option 4: Using Robyn CLI Directly

If you want to use Robyn's CLI directly:

```bash
# This approach requires creating a separate app.py file
python -c "
from src.stock_agent.web import create_web_app
app = create_web_app()
" --dev
```

## Development Workflow

### 1. Start Development Server

```bash
python dev_server.py
```

### 2. Access the Application

- **Main Dashboard**: http://127.0.0.1:8080/
- **Login**: http://127.0.0.1:8080/login
- **Stock Search**: http://127.0.0.1:8080/stocks
- **API Endpoints**: http://127.0.0.1:8080/api/*

### 3. Development Features

#### Hot Reloading
- Save any Python file
- Server automatically restarts
- Browser page refreshes (you may need to manually refresh)

#### Static File Changes
- JavaScript/CSS files are served dynamically
- Changes to templates are reflected immediately

#### Service Worker Development
- Service worker file: `src/stock_agent/static/firebase-messaging-sw.js`
- Authentication utility: `src/stock_agent/static/js/auth-utils.js`
- Changes require browser refresh and service worker re-registration

## Development Configuration Options

### Environment Variables

Add these to `.dev.env` to customize development behavior:

```bash
# Server Configuration
DEV_HOST=127.0.0.1          # Bind to localhost only
DEV_PORT=3000               # Use different port

# Feature Flags
DEV_GENERATE_SUMMARY=true   # Generate market summary on startup
DEBUG=true                  # Enable debug mode
LOG_LEVEL=DEBUG             # Set logging level

# Database
DATABASE_URL=sqlite:///dev_users.db  # Use different database for dev
```

### Performance Options

```bash
# Skip time-consuming operations for faster startup
DEV_GENERATE_SUMMARY=false
DEV_SKIP_MARKET_DATA=true
DEV_MOCK_APIS=true
```

## Testing Service Worker Authentication

### 1. Login and Check Console

After logging in, check browser console for:
```
Service worker registered successfully
Session token sent to service worker
```

### 2. Test API Endpoints

In browser console:
```javascript
// Test authenticated endpoints
fetch('/api/firebase-config').then(r => r.json()).then(console.log);
fetch('/api/vapid-public-key').then(r => r.json()).then(console.log);
```

### 3. Verify Token Persistence

- Close and reopen browser
- Should remain authenticated
- Check Application > IndexedDB > StockAgentAuth

## Common Development Tasks

### Adding New Routes

1. Edit `src/stock_agent/web/web_app.py`
2. Add your route handler
3. Save file - server auto-restarts
4. Test at http://127.0.0.1:8080/your-route

### Updating Templates

1. Edit files in `src/stock_agent/templates/`
2. Changes are reflected immediately
3. Refresh browser to see updates

### Modifying Static Files

1. Edit files in `src/stock_agent/static/`
2. Files are served dynamically
3. For service worker changes, unregister and re-register

### Database Changes

Development uses SQLite database `users.db`. To reset:

```bash
rm users.db
# Restart server - will recreate database
```

## Troubleshooting

### Server Won't Start

**Check Python Path:**
```bash
# Ensure you're in the right directory
pwd  # should end with /stock-agent

# Check Python can import the module
python -c "from src.stock_agent.web import create_web_app; print('✅ Import successful')"
```

**Check Dependencies:**
```bash
# Reinstall dependencies
pip install -e .

# Or with uv
uv sync
```

### Hot Reloading Not Working

- Robyn's dev mode should handle this automatically
- Try stopping (Ctrl+C) and restarting the server
- Check file permissions on your project directory

### Port Already in Use

```bash
# Change port in .dev.env
DEV_PORT=3000

# Or kill process using port 8080
lsof -ti:8080 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :8080   # Windows - then kill PID
```

### Service Worker Issues

```bash
# Clear browser data
# In Chrome: F12 > Application > Storage > Clear site data

# Check service worker status
# F12 > Application > Service Workers
```

### Authentication Issues

```bash
# Check if session token exists
# F12 > Application > Cookies > look for 'session_token'

# Check IndexedDB storage
# F12 > Application > IndexedDB > StockAgentAuth
```

## Production vs Development

| Feature | Development (`dev_server.py`) | Production (`stock_agent`) |
|---------|------------------------------|---------------------------|
| Hot Reloading | ✅ Enabled | ❌ Disabled |
| Host | 127.0.0.1 (localhost) | 0.0.0.0 (all interfaces) |
| Market Summary | ⏩ Skipped by default | ✅ Generated |
| Error Details | 🔍 Verbose | 🔒 Minimal |
| Performance | 🚀 Fast startup | 🏭 Optimized for load |

## Next Steps

1. **Test Authentication**: Login and verify service worker authentication
2. **Test API Endpoints**: Ensure all protected routes work
3. **Test Notifications**: Set up Firebase push notifications
4. **Add Features**: Use hot reloading to rapidly develop new features
5. **Debug Issues**: Use development mode's enhanced error reporting

## Getting Help

- Check the console for error messages
- Review `AUTHENTICATION_TEST.md` for service worker testing
- Check browser Developer Tools for network/console errors
- Verify all environment variables are set in `.dev.env`
