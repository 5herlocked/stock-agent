# Development Guide

## Quick Start

### Prerequisites
- Python 3.12+
- Git

### Setup
```bash
# Clone repository
git clone <repository-url>
cd stock-agent

# Install in development mode
pip install -e .

# Create admin user
stock-admin create-user admin admin@example.com

# Start development server
stock_agent
```

Access at: http://localhost:8080

## Development Workflow

### 1. Code Organization
```
src/stock_agent/
├── auth/           # Authentication & user management
├── cli/            # Command line tools
├── polygon/        # Stock data services
├── web/            # Web application & routes
├── templates/      # HTML templates
└── main.py         # Application entry point
```

### 2. Making Changes

#### Backend Changes
- Modify Python files in `src/stock_agent/`
- Restart server to see changes: `Ctrl+C` then `stock_agent`
- No hot reload currently implemented

#### Frontend Changes
- Modify HTML templates in `src/stock_agent/templates/`
- CSS is embedded in templates
- JavaScript is embedded in templates
- Refresh browser to see changes

#### Database Changes
- Modify schema in `auth_service.py` `_init_db()` method
- Delete `users.db` to recreate with new schema
- Recreate admin user after schema changes

### 3. Testing Changes

#### Manual Testing
```bash
# Create test user
stock-admin create-user testuser test@example.com

# Test login flow
# 1. Go to http://localhost:8080
# 2. Should redirect to /login
# 3. Login with testuser credentials
# 4. Should see dashboard

# Test stock search
# 1. Go to /stocks
# 2. Search for "AAPL"
# 3. Add to favorites
# 4. Return to dashboard
# 5. Should see AAPL in favorites
```

#### API Testing
```bash
# Test API endpoints with curl
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password"}' \
  -c cookies.txt

curl -X GET "http://localhost:8080/api/search-stocks?q=AAPL" \
  -b cookies.txt
```

## Architecture Deep Dive

### Authentication Flow
1. **User Creation**: Admin CLI → SQLite database
2. **Login**: JSON POST → bcrypt verification → session token
3. **Session Management**: In-memory storage with 24h expiration
4. **Route Protection**: Middleware checks session on each request

### Stock Data Flow
1. **Search**: User query → mock database search → JSON response
2. **Favorites**: User selection → SQLite storage → dashboard display
3. **Price Data**: Mock generation with realistic volatility
4. **Real-time Updates**: JavaScript polling every 30 seconds

### Template Rendering
1. **Server-side**: Jinja2 templates with context data
2. **Client-side**: JavaScript for dynamic updates
3. **Responsive**: CSS Grid for mobile/desktop layouts

## Common Development Tasks

### Adding New Stock Data
```python
# In polygon/stock_service.py
mock_stocks = [
    {'ticker': 'NEWCO', 'company_name': 'New Company Inc.'},
    # Add new entries here
]

stock_prices = {
    'NEWCO': 150,  # Base price for realistic mock data
    # Add new prices here
}
```

### Adding New API Endpoints
```python
# In web/web_app.py
@app.get('/api/new-endpoint')
async def new_endpoint(request: Request):
    user = get_current_user(request) or get_user_from_bearer_token(request)
    if not user:
        return {'error': 'Unauthorized'}, 401
    
    # Your logic here
    return {'data': 'response'}
```

### Adding New Templates
1. Create HTML file in `src/stock_agent/templates/`
2. Add route in `web/web_app.py`
3. Use Jinja2 template rendering:
```python
@app.get('/new-page')
async def new_page(request: Request):
    user = get_current_user(request)
    if not user:
        return redirect_to_login()
    
    context = {"user": user, "data": "value"}
    template = jinja_template.render_template("new-page.html", **context)
    return template
```

### Adding Database Tables
```python
# In auth/auth_service.py _init_db() method
conn.execute("""
    CREATE TABLE IF NOT EXISTS new_table (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
""")
```

### Adding CLI Commands
```python
# In cli/admin.py
def new_command(auth_service: AuthService, param: str) -> bool:
    """New CLI command"""
    # Implementation here
    return True

# Add to parser
new_parser = subparsers.add_parser('new-command', help='Description')
new_parser.add_argument('param', help='Parameter description')

# Add to main() function
elif args.command == 'new-command':
    success = new_command(auth_service, args.param)
    sys.exit(0 if success else 1)
```

## Debugging

### Common Issues

#### "ModuleNotFoundError"
```bash
# Reinstall in development mode
pip install -e .
```

#### "Database is locked"
```bash
# Stop all running instances
pkill -f stock_agent
# Or restart terminal
```

#### "Port already in use"
```bash
# Find and kill process on port 8080
lsof -ti:8080 | xargs kill -9
```

#### Session/Login Issues
```bash
# Delete database and recreate user
rm users.db
stock-admin create-user admin admin@example.com
```

### Debug Logging
Add debug prints to troubleshoot:
```python
print(f"DEBUG: User: {user}")
print(f"DEBUG: Request headers: {request.headers}")
print(f"DEBUG: Form data: {form_data}")
```

### Database Inspection
```bash
# Install sqlite3 command line tool
sqlite3 users.db

# View tables
.tables

# View users
SELECT * FROM users;

# View favorites
SELECT * FROM user_favorites;
```

## Performance Considerations

### Current Limitations
- **In-memory sessions**: Lost on server restart
- **No caching**: Every request hits database
- **Polling updates**: 30-second intervals for real-time data
- **Single-threaded**: Robyn handles concurrency

### Optimization Opportunities
- **Redis sessions**: Persistent session storage
- **Database connection pooling**: Reduce connection overhead
- **WebSocket updates**: Real-time price streaming
- **Response caching**: Cache static/semi-static data
- **Database indexing**: Add indexes for common queries

## Security Considerations

### Current Security Features
- ✅ bcrypt password hashing
- ✅ Session token authentication
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS protection (template escaping)
- ✅ Admin-only user creation

### Security Improvements Needed
- ⚠️ HTTPS enforcement
- ⚠️ Rate limiting
- ⚠️ CSRF tokens
- ⚠️ Input sanitization
- ⚠️ Session storage encryption

## Deployment Considerations

### Environment Variables
```env
# Required for production
FIREBASE_CREDS_PATH=./firebase-credentials.json
FIREBASE_API_KEY=your-api-key
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_VAPID_PUBLIC_KEY=your-vapid-key

# Optional for real stock data
POLYGON_API_KEY=your-polygon-key
```

### Production Checklist
- [ ] Build Docker container
- [ ] Set up HTTPS/TLS
- [ ] Configure proper logging
- [ ] Set up monitoring/alerting
- [ ] Database backups (SQLite file)
- [ ] Error tracking
- [ ] Performance monitoring
- [ ] Security headers
- [ ] Rate limiting

## Contributing Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings for functions
- Keep functions focused and small

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature

- Detailed description of changes
- Include any breaking changes

Co-authored-by: Ona <no-reply@ona.com>"

# Push and create PR
git push origin feature/new-feature
```

### Testing
- Test all authentication flows
- Test API endpoints with curl
- Test mobile responsiveness
- Test error conditions
- Test with/without API keys

### Documentation
- Update relevant documentation files
- Add inline code comments for complex logic
- Update API reference for new endpoints
- Update development guide for new processes
