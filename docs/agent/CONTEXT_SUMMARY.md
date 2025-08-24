# Stock Agent - Context Summary for AI Agents

## Project Identity
**Stock Agent** is a secure, real-time stock market tracking and notification system built with Python. It provides authenticated users with personalized dashboards, stock favorites management, and push notifications for market movements.

## Key Characteristics

### Architecture Philosophy
- **Security-first**: Admin-controlled user creation, bcrypt authentication, session-based security
- **Simplicity**: SQLite database, server-side rendering, minimal dependencies
- **Responsiveness**: Mobile-optimized UI with real-time updates
- **Modularity**: Clean separation between auth, web, stock data, and CLI components

### Technology Choices
- **Robyn Framework**: Async Python web framework for performance
- **SQLite**: Single-file database for simplicity and portability
- **Jinja2 Templates**: Server-side rendering with progressive enhancement
- **Vanilla JavaScript**: No frontend frameworks, direct DOM manipulation
- **bcrypt**: Industry-standard password hashing with automatic salting

## Core Functionality

### User Management
- **Admin-only registration**: No public signup, CLI-based user creation
- **Secure authentication**: bcrypt + salt, 24-hour session tokens
- **Session management**: In-memory storage with automatic expiration
- **Dual auth support**: Cookie-based (web) and Bearer token (API)

### Stock Features
- **Personal favorites**: Per-user stock watchlists with persistent storage
- **Real-time dashboard**: Auto-refreshing price data every 30 seconds
- **Stock search**: Query-based discovery via Polygon.io API
- **Major indexes**: DJI, SPX, IXIC, SWTSX with realistic price simulation
- **Mobile responsive**: Touch-friendly interface optimized for phones

### Data Strategy
- **Real market data**: Live stock prices via Polygon.io API
- **API key required**: Application requires POLYGON_API_KEY to function
- **No fallback data**: System depends on external Polygon API
- **Firebase integration**: Push notification infrastructure (requires configuration)

## File Structure Context

### Core Application (`src/stock_agent/`)
```
main.py                 # Entry point, starts Robyn server
auth/
  ├── auth_service.py   # User auth, sessions, favorites CRUD
  ├── models.py         # User, StockFavorite, StockData models
  └── __init__.py
web/
  ├── web_app.py        # All routes, middleware, template rendering
  └── __init__.py
polygon/
  ├── stock_service.py  # Stock data, search, price generation
  ├── polygon_worker.py # Polygon API integration
  └── __init__.py
cli/
  ├── admin.py          # User management CLI commands
  └── __init__.py
templates/
  ├── dashboard.html    # Main page: favorites + indexes
  ├── stocks.html       # Search and favorites management
  ├── login.html        # Authentication form
  ├── report.html       # Stock reports page
  └── index.html        # Firebase notifications setup
```

### Key Configuration
- **pyproject.toml**: Dependencies, scripts, build config
- **users.db**: SQLite database (auto-created)
- **.env**: Environment variables (Firebase, Polygon API keys)

## Development Patterns

### Authentication Pattern
```python
# Every protected route uses this pattern:
user = get_current_user(request) or get_user_from_bearer_token(request)
if not user:
    return redirect_to_login() or {'error': 'Unauthorized'}, 401
```

### Database Pattern
```python
# All database operations use parameterized queries:
with sqlite3.connect(self.db_path) as conn:
    cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
```

### API Response Pattern
```python
# Consistent error handling:
try:
    # Business logic
    return {'success': True, 'data': result}
except Exception as e:
    return {'error': 'Description'}, 500
```

### Template Context Pattern
```python
# Standard context for all templates:
context = {
    "framework": "Robyn",
    "templating_engine": "Jinja2", 
    "user": user,
    # Page-specific data
}
```

## Critical Implementation Details

### Session Management
- **Storage**: In-memory dictionary (lost on restart)
- **Token generation**: `secrets.token_urlsafe(32)`
- **Expiration**: 24 hours from creation
- **Cleanup**: Manual cleanup of expired sessions

### Stock Data Integration
- **Polygon API**: Real-time market data from Polygon.io
- **Live prices**: Current stock prices and trading volumes
- **Market data**: Real market capitalization and price changes
- **API dependency**: Requires valid POLYGON_API_KEY environment variable

### Security Measures
- **Password requirements**: Minimum 8 characters
- **SQL injection prevention**: Parameterized queries throughout
- **XSS protection**: Jinja2 auto-escaping enabled
- **Session security**: HttpOnly cookies, secure token generation

## Common Operations

### Adding New Stock Data
Stock data comes directly from Polygon.io API. All publicly traded stocks are automatically available through the search functionality - no manual addition needed.

### Adding New Routes
1. Add route function in `web/web_app.py`
2. Include authentication check
3. Return template or JSON response
4. Add navigation links in templates if needed

### Database Schema Changes
1. Modify `_init_db()` in `auth/auth_service.py`
2. Delete existing `users.db` file
3. Restart application to recreate schema
4. Recreate admin users

### CLI Command Addition
1. Add command function in `cli/admin.py`
2. Add parser in `main()` function
3. Add command handling in main logic
4. Update help text and examples

## Integration Points

### External Services
- **Polygon.io**: Stock market data API (required)
- **Firebase**: Push notifications (optional)
- **Docker**: Self-hosted containerized deployment

### Environment Dependencies
- **POLYGON_API_KEY**: Required for stock data (application won't function without it)
- **FIREBASE_***: Enables push notifications (optional)

## Performance Characteristics
- **Startup time**: ~1-2 seconds (database init, service setup)
- **Response time**: <100ms for most routes (SQLite queries)
- **Memory usage**: Minimal (sessions + application state)
- **Concurrency**: Robyn async framework handles multiple requests
- **Database**: Single SQLite file, no connection pooling needed

## Deployment Readiness
- **Development**: Ready to run with `stock_agent` command
- **Production**: Needs HTTPS, proper logging, monitoring
- **Scaling**: Single-instance design, would need Redis for multi-instance
- **Monitoring**: Basic error handling, no metrics/logging framework

## AI Agent Guidance

### When Modifying Code
1. **Always check authentication** on new routes
2. **Use parameterized queries** for database operations
3. **Follow existing patterns** for consistency
4. **Test both web and API interfaces** for changes
5. **Update documentation** for significant changes

### When Debugging Issues
1. **Check session expiration** for auth problems
2. **Verify database schema** for data issues
3. **Check environment variables** for service failures
4. **Look at browser network tab** for API issues
5. **Use CLI tools** for user management problems

### When Adding Features
1. **Consider mobile experience** first
2. **Add both web and API interfaces** when applicable
3. **Include proper error handling** and user feedback
4. **Follow security patterns** established in codebase
5. **Test with and without external API keys**

This context should provide sufficient understanding for an AI agent to effectively work with the Stock Agent codebase, understanding its architecture, patterns, and development practices.
