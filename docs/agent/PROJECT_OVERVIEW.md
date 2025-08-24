# Stock Agent - Project Overview

## Project Description
Stock Agent is a real-time stock market notification and tracking system built with Python. It provides users with a secure, personalized dashboard to track favorite stocks, view major market indexes, and receive push notifications about market movements.

## Core Features
- **User Authentication**: Secure bcrypt-based authentication with session management
- **Stock Favorites**: Personal stock watchlists with persistent storage
- **Real-time Dashboard**: Live market data with auto-refresh functionality
- **Stock Search**: Search and discover stocks to add to favorites
- **Push Notifications**: Firebase Cloud Messaging integration for market alerts
- **Admin Management**: CLI tools for user administration
- **Mobile Responsive**: Optimized for mobile and desktop usage

## Technology Stack

### Backend
- **Framework**: Robyn (Python async web framework)
- **Database**: SQLite with manual schema management
- **Authentication**: bcrypt for password hashing, session-based auth
- **Stock Data**: Polygon.io API integration with mock data fallback
- **Notifications**: Firebase Admin SDK for push notifications
- **Deployment**: Docker containerization for self-hosting

### Frontend
- **Templates**: Jinja2 templating engine
- **Styling**: Vanilla CSS with responsive design
- **JavaScript**: Vanilla JS with fetch API for AJAX calls
- **Real-time Updates**: Auto-refresh with 30-second intervals

### Dependencies
```toml
dependencies = [
    "numpy",           # Data processing
    "pandas",          # Data analysis and manipulation
    "python-dotenv",   # Environment variable management
    "firebase-admin",  # Firebase push notifications
    "jinja2",          # HTML templating
    "robyn",           # Web framework
    "bcrypt",          # Password hashing
    "polygon-api-client", # Stock market data API
]
```

## Project Structure
```
stock-agent/
├── src/stock_agent/
│   ├── auth/                 # Authentication system
│   │   ├── auth_service.py   # User auth and session management
│   │   ├── models.py         # User and stock data models
│   │   └── __init__.py
│   ├── cli/                  # Command line tools
│   │   ├── admin.py          # User administration CLI
│   │   └── __init__.py
│   ├── polygon/              # Stock data services
│   │   ├── stock_service.py  # Stock data and search functionality
│   │   ├── polygon_worker.py # Polygon API integration
│   │   └── __init__.py
│   ├── web/                  # Web application
│   │   ├── web_app.py        # Main web app with all routes
│   │   └── __init__.py
│   ├── templates/            # HTML templates
│   │   ├── dashboard.html    # Main dashboard (home page)
│   │   ├── stocks.html       # Stock search and favorites
│   │   ├── login.html        # User login form
│   │   ├── report.html       # Stock reports page
│   │   └── index.html        # Firebase notifications page
│   ├── notification_service.py # Firebase messaging
│   └── main.py               # Application entry point
├── docs/                     # Documentation
├── pyproject.toml           # Project configuration
└── README.md                # Project readme
```

## Key Design Decisions

### Authentication Architecture
- **No public registration**: Users must be created by administrators via CLI
- **Session-based auth**: 24-hour session tokens stored in memory
- **Dual auth support**: Cookie-based (web) and Bearer token (API) authentication
- **Secure password storage**: bcrypt with automatic salting

### Database Design
- **SQLite for simplicity**: Single-file database, no external dependencies
- **Two main tables**: `users` and `user_favorites`
- **Foreign key constraints**: Proper relational integrity
- **Unique constraints**: Prevent duplicate favorites per user

### Stock Data Strategy
- **Polygon.io integration**: Real market data when API key available
- **Mock data fallback**: Realistic simulation for development/testing
- **Major indexes**: DJI, SPX, IXIC, SWTSX with realistic base prices
- **Volatility simulation**: Random price movements within realistic ranges

### Frontend Architecture
- **Server-side rendering**: Jinja2 templates for initial page load
- **Progressive enhancement**: JavaScript for dynamic functionality
- **Mobile-first design**: Responsive CSS grid layouts
- **Real-time updates**: Auto-refresh without page reload

## Security Considerations
- **Password requirements**: Minimum 8 characters
- **Session expiration**: 24-hour automatic timeout
- **CSRF protection**: Session tokens prevent unauthorized requests
- **Input validation**: Server-side validation for all user inputs
- **SQL injection prevention**: Parameterized queries throughout
- **XSS protection**: Template escaping enabled by default

## Development Workflow
1. **Install dependencies**: `pip install -e .`
2. **Create admin user**: `stock-admin create-user username email`
3. **Start server**: `stock_agent` (runs on port 8080)
4. **Access application**: Navigate to `http://localhost:8080`

## Environment Configuration
Required environment variables:
```env
# Firebase Configuration (optional)
FIREBASE_CREDS_PATH=./firebase-credentials.json
FIREBASE_API_KEY=your-api-key
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_VAPID_PUBLIC_KEY=your-vapid-key

# Polygon API (optional)
POLYGON_API_KEY=your-polygon-key
```

## Current Status
- ✅ **Authentication system**: Complete with admin CLI
- ✅ **Stock favorites**: Full CRUD functionality
- ✅ **Dashboard**: Real-time updates with major indexes
- ✅ **Stock search**: Mock data with realistic companies
- ✅ **Mobile responsive**: Optimized for phone usage
- ⚠️ **Push notifications**: Firebase integration present but needs configuration
- ⚠️ **Real stock data**: Polygon integration present but needs API key

## Future Enhancements
- Real-time WebSocket connections for live price updates
- Advanced charting and technical analysis
- Portfolio tracking with profit/loss calculations
- Email notifications as backup to push notifications
- Stock alerts based on price thresholds
- Historical data analysis and trends
