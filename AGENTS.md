# Stock Agent Guidelines

## Project Overview
Stock Agent is a secure, real-time stock market tracking and notification system built with Python. For comprehensive project documentation, see `docs/agent/PROJECT_OVERVIEW.md`.

## Common Commands

### Development
- `pip install -e .` - Install project in development mode
- `stock_agent` - Start the development server (runs on port 8080)
- **Note**: No CLI user creation - users auto-created via Firebase authentication

### Testing & Verification
- **ALWAYS** test authentication flows after auth changes
- **ALWAYS** verify API endpoints work with curl after modifications
- Test mobile responsiveness for UI changes

### Database Operations
- Delete `users.db` file to reset database (recreates schema automatically)
- Use `sqlite3 users.db "SELECT * FROM users;"` to inspect user data

## Key Files & Directories

### Core Application
- `src/stock_agent/main.py` - Application entry point
- `src/stock_agent/web/web_app.py` - Main web application with all routes
- `src/stock_agent/auth/auth_service.py` - Authentication system and database schema
- `src/stock_agent/polygon/stock_service.py` - Stock data and Polygon API integration

### Templates & Frontend
- `src/stock_agent/templates/` - Jinja2 HTML templates
- `src/stock_agent/static/` - CSS and JavaScript assets
- **IMPORTANT**: Use HTMX attributes for dynamic interactions

### Documentation
- `docs/agent/AUTHENTICATION_SYSTEM.md` - Authentication architecture and security
- `docs/agent/API_REFERENCE.md` - Complete API endpoint documentation
- `docs/agent/DEVELOPMENT_GUIDE.md` - Development setup and workflows
- `docs/agent/CONTEXT_SUMMARY.md` - Quick reference for agents

## Code Style & Conventions

### Python Code
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Add docstrings for public functions and classes
- Use parameterized queries for all database operations (SQL injection prevention)

### Authentication
- **ALWAYS** use `get_current_user(request)` for route authentication (Firebase-only)
- **NEVER** bypass authentication checks on protected routes
- **Firebase-only authentication**: All auth handled by Firebase ID tokens
- Users auto-created in local database when first authenticated via Firebase
- No local password authentication - Firebase handles all auth flows

### Database Schema
- Users table: id, username, email, firebase_uid, created_at, is_active
- User favorites table: id, user_id, ticker, company_name, added_at
- **IMPORTANT**: Firebase users auto-created in local DB when first authenticated
- **IMPORTANT**: No password storage - Firebase handles all authentication
- **IMPORTANT**: Update schema in `auth_service.py` for any database changes

### API Endpoints
- Use `/api/` prefix for all API routes
- Return JSON with `{"success": true, "data": {...}}` for success
- Return JSON with `{"error": "description"}` for errors
- **ALWAYS** include authentication middleware for protected endpoints
- **ONLY** Firebase ID tokens accepted for authentication

## Environment Setup

### Required Environment Variables
- `POLYGON_API_KEY` - **REQUIRED** for stock data (get from Polygon.io)

### Firebase Authentication (Required)
- `FIREBASE_CREDS_PATH` - **REQUIRED** Path to Firebase credentials JSON file
- `FIREBASE_SERVICE_ACCOUNT_JSON` - **REQUIRED** Firebase service account JSON string (alternative to file)
- `FIREBASE_API_KEY` - **REQUIRED** Firebase API key for client-side auth
- `FIREBASE_PROJECT_ID` - **REQUIRED** Firebase project ID
- `FIREBASE_VAPID_PUBLIC_KEY` - VAPID key for web push notifications (optional)

### Development Prerequisites
- Python 3.12+
- Polygon.io API account and key
- SQLite (included with Python)

## Git Workflow

### Commit Messages
- Follow conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- **ALWAYS** include co-author: `Co-authored-by: Ona <no-reply@ona.com>`
- Include bullet points for major changes in commit body

### Before Committing
- **ALWAYS** run `git status` and `git diff` to review changes
- Only stage files relevant to the current task
- Test changes locally before committing

## Security Considerations

### Implemented Security
- **Firebase-only authentication**: All auth handled by Firebase ID tokens
- Firebase Admin SDK for secure server-side token verification
- Auto-user provisioning from verified Firebase tokens
- SQL injection prevention through parameterized queries
- XSS protection via Jinja2 template escaping
- HttpOnly cookies for Firebase token storage

### Critical Security Rules
- **NEVER** log or expose API keys or Firebase ID tokens
- **ALWAYS** validate user input before database operations
- **NEVER** commit sensitive credentials to version control
- **ALWAYS** verify Firebase ID tokens server-side using Firebase Admin SDK
- **NEVER** trust client-side Firebase auth state - always verify server-side
- Use HTTPS in production (not implemented in development)

## Architecture Notes

### Technology Stack
- **Backend**: Robyn (async Python web framework)
- **Database**: SQLite with manual schema management
- **Authentication**: Firebase Auth (ID tokens only)
- **Frontend**: Jinja2 templates + HTMX for dynamic interactions
- **Stock Data**: Polygon.io REST API
- **Notifications**: Firebase Cloud Messaging (optional)

### Key Design Decisions
- **Firebase-only authentication**: All authentication delegated to Firebase Auth
- Firebase users auto-created in local database for unified user management
- No local password storage or session management
- SQLite for development (consider PostgreSQL for production)
- HTMX for frontend interactivity (no complex JavaScript framework)
- User provisioning handled entirely by Firebase authentication flows

## Agent-Specific Instructions

### For Code Modifications
- **ALWAYS** read files before editing to understand context
- Follow existing code patterns and naming conventions
- **IMPORTANT**: Firebase-only authentication - no local auth supported
- Use `get_current_user()` for Firebase ID token authentication (handles both cookies and headers)
- **NEVER** implement local password authentication or session management
- **Note**: JavaScript files in `static/js/` still reference session tokens - these need updating for full Firebase integration
- Update related documentation when making significant changes
- Reference `docs/agent/` files for detailed technical information

### For New Features
- Check `docs/agent/API_REFERENCE.md` for existing endpoint patterns
- Follow authentication patterns from existing protected routes
- Update database schema in `auth_service.py` if needed
- Add appropriate error handling and validation

### Testing Approach
- **Note for AI Agents**: Focus on code modifications and documentation
- Human developers handle server execution and testing
- Provide curl commands for API testing when relevant
- Suggest manual testing steps for UI changes

### Firebase Authentication Testing
- Test with Firebase ID token: `curl -H "Authorization: Bearer <firebase_id_token>"`
- Verify Firebase users auto-created in local database
- Check Firebase Admin SDK initialization in server logs
- Test user creation flow: authenticate with Firebase, check local DB for user record

## Troubleshooting

### Common Issues
For detailed troubleshooting information, see `docs/agent/DEVELOPMENT_GUIDE.md`.

**Authentication Problems:**
- Verify Firebase ID token is valid and not expired
- Check Firebase Admin SDK initialization: look for "Firebase Admin SDK initialized successfully"
- Check Firebase environment variables are set correctly
- Verify user auto-creation: check if user appears in local database after Firebase auth
- Delete `users.db` to reset if corrupted
- Test Firebase token verification with `firebase_auth_service.verify_firebase_id_token()`

**Stock Data Issues:**
- **IMPORTANT**: Verify `POLYGON_API_KEY` environment variable is set
- Check API rate limits (5 requests per minute on free tier)
- Test with: `curl "https://api.polygon.io/v2/aggs/ticker/AAPL/prev?apikey=YOUR_KEY"`

**Database Problems:**
- Delete `users.db` file to reset database (auto-recreates schema)
- Check file permissions if SQLite errors occur

### Debug Commands
```bash
# Check users
sqlite3 users.db "SELECT * FROM users;"

# Check favorites
sqlite3 users.db "SELECT * FROM user_favorites;"

# Test API endpoints
curl -X GET "http://localhost:8080/api/search-stocks?q=AAPL" \
  -H "Authorization: Bearer <token>"
```

## Additional Documentation

For comprehensive technical details, see the `docs/agent/` directory:

- **Project Overview**: `docs/agent/PROJECT_OVERVIEW.md` - Complete system architecture
- **Authentication**: `docs/agent/AUTHENTICATION_SYSTEM.md` - Security implementation details  
- **API Reference**: `docs/agent/API_REFERENCE.md` - Complete endpoint documentation
- **Development**: `docs/agent/DEVELOPMENT_GUIDE.md` - Setup and workflow details
- **Context Summary**: `docs/agent/CONTEXT_SUMMARY.md` - Quick reference for agents