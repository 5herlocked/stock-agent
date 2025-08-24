# Running Stock Agent

## Quick Start (Development Mode)

The fastest way to get started with development is using our dedicated development server:

```bash
# Clone and setup
git clone <repository-url>
cd stock-agent

# Install dependencies (with UV - recommended)
uv sync
source .venv/bin/activate

# Or with standard pip
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -e .

# Start development server with hot reloading
python dev_server.py
```

Visit http://127.0.0.1:8080 to access the application.

## Running Options

### 1. Development Server (Recommended for Development)

**Using Python directly:**
```bash
# Start development server with hot reloading
python scripts/dev_server.py
```

**Using convenient shell scripts:**
```bash
# Linux/Mac
./scripts/dev.sh

# Windows
scripts\dev.bat
```

**Features:**
- ✅ Hot reloading (automatic restart on file changes)
- ✅ Debug mode enabled
- ✅ Faster startup (skips market summary by default)
- ✅ Localhost binding (127.0.0.1:8080)
- ✅ Enhanced error messages and logging

### 2. Production Server

**Using the installed command:**
```bash
stock_agent
```

**Using Python module:**
```bash
python -m stock_agent.main
```

**Using UV:**
```bash
uv run stock_agent
```

**Features:**
- 🏭 Production optimized
- 🌐 Binds to all interfaces (0.0.0.0:8080)
- 📊 Generates market summary on startup
- 🔒 Minimal error disclosure

### 3. Custom Configuration

**With command-line options (shell scripts):**
```bash
# Custom port
./scripts/dev.sh --port 3000

# Custom host
./scripts/dev.sh --host 0.0.0.0

# Enable market summary generation
./scripts/dev.sh --summary

# Multiple options
./scripts/dev.sh --port 3000 --summary
```

**With environment variables:**
```bash
# Set in .dev.env or export directly
export DEV_HOST=0.0.0.0
export DEV_PORT=3000
export DEV_GENERATE_SUMMARY=true

python scripts/dev_server.py
```

## Environment Configuration

### Required Variables

Create a `.dev.env` file in the project root:

```bash
# API Configuration
POLYGON_API_KEY=your_polygon_api_key_here

# Firebase Configuration
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:abcdef123456
FIREBASE_VAPID_PUBLIC_KEY=your_vapid_public_key

# Development Server Settings
DEV_HOST=127.0.0.1
DEV_PORT=8080
DEV_GENERATE_SUMMARY=false

# Production Settings
HOST=0.0.0.0
PORT=8080
GENERATE_MARKET_SUMMARY=true
```

### Optional Variables

```bash
# Performance tuning
DEBUG=true
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=sqlite:///dev_users.db

# Feature flags
DEV_SKIP_MARKET_DATA=true
DEV_MOCK_APIS=true
```

## What Happens When You Run

### Development Server (`python scripts/dev_server.py`)

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

   Environment:
   📁 Project root: /path/to/stock-agent
   🔧 Config file: /path/to/stock-agent/.dev.env

   Press Ctrl+C to stop the server
```

### Production Server (`stock_agent`)

```
Loaded environment from .dev.env
Generating market summary...
Market summary generated successfully
Starting Stock Agent server on 0.0.0.0:8080
```

## Application URLs

Once running, access these URLs:

- **Dashboard**: http://127.0.0.1:8080/
- **Login**: http://127.0.0.1:8080/login  
- **Stock Search**: http://127.0.0.1:8080/stocks
- **Notifications**: http://127.0.0.1:8080/notifications
- **Reports**: http://127.0.0.1:8080/report

### API Endpoints

- **Firebase Config**: http://127.0.0.1:8080/api/firebase-config
- **VAPID Key**: http://127.0.0.1:8080/api/vapid-public-key
- **Search Stocks**: http://127.0.0.1:8080/api/search-stocks
- **Favorites**: http://127.0.0.1:8080/api/favorites
- **Dashboard Data**: http://127.0.0.1:8080/api/dashboard-favorites
- **Market Indexes**: http://127.0.0.1:8080/api/major-indexes

## Development Features

### Hot Reloading

Thanks to Robyn's `--dev` mode, the development server automatically restarts when you:

- Modify any Python file
- Change template files
- Update static assets

### Service Worker Development

The service worker authentication system is automatically initialized:

1. **Login** → Session token is cached for service worker use
2. **Browser restart** → Token persists via IndexedDB
3. **API calls** → Service worker uses cached token for authentication

### Static File Serving

Static assets are served dynamically during development:

- JavaScript: `/static/js/auth-utils.js`
- Service Worker: `/firebase-messaging-sw.js`
- Templates: Served via Jinja2

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Kill existing process
lsof -ti:8080 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :8080   # Windows - note PID, then: taskkill /PID <pid> /F

# Or use different port
./scripts/dev.sh --port 3000
```

**Module not found errors:**
```bash
# Ensure you're in the right directory
pwd  # should end with 'stock-agent'

# Reinstall in development mode
pip install -e .

# Or with UV
uv sync
```

**Virtual environment issues:**
```bash
# Recreate virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

**Service worker not working:**
- Clear browser data (F12 > Application > Storage > Clear site data)
- Check browser console for errors
- Ensure you're using HTTPS or localhost (service workers requirement)

### Logs and Debugging

**View detailed logs:**
```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG
python scripts/dev_server.py
```

**Check service worker logs:**
- Open browser Developer Tools (F12)
- Go to Console tab
- Look for service worker messages

**Check authentication:**
- F12 > Application > Cookies > look for `session_token`
- F12 > Application > IndexedDB > StockAgentAuth

## Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| **Command** | `python scripts/dev_server.py` | `stock_agent` |
| **Host** | 127.0.0.1 (localhost) | 0.0.0.0 (all interfaces) |
| **Port** | 8080 (configurable) | 8080 (configurable) |
| **Hot Reload** | ✅ Enabled | ❌ Disabled |
| **Market Summary** | ⏩ Skipped | ✅ Generated |
| **Error Details** | 🔍 Verbose | 🔒 Minimal |
| **Startup Time** | 🚀 Fast | 🐢 Slower (market data) |

## Performance Tips

### Faster Development Startup

```bash
# Skip market summary generation
export DEV_GENERATE_SUMMARY=false

# Use development database
export DATABASE_URL=sqlite:///dev_users.db
```

### Memory Usage

The application uses:
- SQLite database (lightweight)
- In-memory caching for stock data
- IndexedDB for client-side token storage

## Getting Help

1. **Check the logs** in your terminal for error messages
2. **Browser Developer Tools** (F12) for client-side issues
3. **Review configuration** in `.dev.env`
4. **Clear browser data** if authentication issues persist
5. **Restart the server** if hot reloading stops working

For service worker authentication specifically, see `AUTHENTICATION_TEST.md`.