# Authentication System Documentation

## Overview
The Stock Agent uses a secure, session-based authentication system with bcrypt password hashing and admin-controlled user creation. No public registration is allowed - all users must be created by administrators.

## Architecture

### Core Components
1. **AuthService** (`src/stock_agent/auth/auth_service.py`)
2. **User Model** (`src/stock_agent/auth/models.py`)
3. **Admin CLI** (`src/stock_agent/cli/admin.py`)
4. **Web Authentication** (`src/stock_agent/web/web_app.py`)

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```

### User Favorites Table
```sql
CREATE TABLE user_favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    company_name TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, ticker)
);
```

## Authentication Flow

### 1. User Creation (Admin Only)
```bash
# Create new user via CLI
stock-admin create-user username email@example.com

# User will be prompted for secure password input
# Password must be at least 8 characters
```

### 2. Login Process
1. User submits credentials via JSON POST to `/login`
2. Server validates username/password against database
3. If valid, creates session token using `secrets.token_urlsafe(32)`
4. Session stored in memory with 24-hour expiration
5. Token returned as HttpOnly cookie

### 3. Session Management
```python
# Session structure
sessions = {
    'token': {
        'user_id': int,
        'username': str,
        'created_at': datetime,
        'expires_at': datetime  # 24 hours from creation
    }
}
```

### 4. Authentication Middleware
Two authentication methods supported:

#### Cookie-based (Web)
```python
def get_current_user(request: Request) -> Optional[User]:
    cookie_header = request.headers.get('cookie')
    # Parse session_token from cookies
    # Validate against in-memory sessions
```

#### Bearer Token (API)
```python
def get_user_from_bearer_token(request: Request) -> Optional[User]:
    auth_header = request.headers.get('authorization')
    # Extract token from "Bearer <token>" format
    # Validate against in-memory sessions
```

## Security Features

### Password Security
- **bcrypt hashing**: Industry-standard password hashing
- **Automatic salting**: Each password gets unique salt
- **Minimum length**: 8 character requirement
- **Secure input**: CLI uses `getpass` to hide password entry

### Session Security
- **Cryptographically secure tokens**: Using `secrets.token_urlsafe(32)`
- **HttpOnly cookies**: Prevents XSS access to session tokens
- **24-hour expiration**: Automatic session timeout
- **Memory storage**: Sessions don't persist across server restarts

### Access Control
- **Admin-only registration**: No public user creation
- **Route protection**: All sensitive routes require authentication
- **Session validation**: Every request validates session expiration

## Admin CLI Commands

### User Management
```bash
# Create user
stock-admin create-user <username> <email>

# List all users
stock-admin list-users

# Activate/deactivate users
stock-admin activate-user <username>
stock-admin deactivate-user <username>

# Reset password
stock-admin reset-password <username>
```

### CLI Features
- **Secure password input**: Uses `getpass` module
- **Input validation**: Checks email format, username uniqueness
- **Error handling**: Clear error messages for all failure cases
- **User feedback**: Success/failure indicators with emojis

## Web Routes

### Authentication Routes
- `GET /login` - Login form
- `POST /login` - Process login (JSON)
- `POST /logout` - Clear session and redirect

### Protected Routes
All routes require authentication:
- `GET /` - Dashboard (redirects to login if not authenticated)
- `GET /stocks` - Stock search page
- `GET /report` - Stock reports
- `GET /api/*` - All API endpoints

## API Authentication

### Firebase Endpoints
Protected endpoints for Firebase integration:
- `GET /api/vapid-public-key` - VAPID key for push notifications
- `GET /api/firebase-config` - Firebase configuration

### Stock API Endpoints
- `GET /api/search-stocks?q=<query>` - Search stocks
- `GET /api/favorites` - Get user favorites
- `POST /api/favorites` - Add favorite
- `DELETE /api/favorites` - Remove favorite
- `GET /api/dashboard-favorites` - Favorites with price data
- `GET /api/major-indexes` - Market index data

## Error Handling

### Login Errors
- Invalid credentials → "Invalid credentials" message
- JSON parsing error → "Invalid request format" message
- Missing fields → Form validation errors

### Session Errors
- Expired session → Automatic redirect to login
- Invalid token → 401 Unauthorized response
- Missing authentication → 401 Unauthorized response

## Security Best Practices Implemented

1. **No plaintext passwords**: All passwords hashed with bcrypt
2. **Secure session tokens**: Cryptographically random tokens
3. **Session expiration**: Automatic 24-hour timeout
4. **Input validation**: Server-side validation for all inputs
5. **SQL injection prevention**: Parameterized queries only
6. **XSS protection**: Template escaping enabled
7. **CSRF protection**: Session tokens validate user identity
8. **Admin-only registration**: Prevents unauthorized account creation

## Configuration

### Database Location
Default: `users.db` in current directory
Custom: `--db-path /path/to/database.db`

### Session Duration
Currently hardcoded to 24 hours. Can be modified in `AuthService.create_session()`:
```python
'expires_at': datetime.now() + timedelta(hours=24)
```

## Troubleshooting

### Common Issues
1. **"Password must be at least 8 characters"** - Increase password length
2. **"Username or email already exists"** - Use unique credentials
3. **"Invalid credentials"** - Check username/password combination
4. **Session expired** - Login again (24-hour limit)

### Database Issues
- **Database locked** - Ensure no other processes accessing database
- **Permission denied** - Check file permissions on database file
- **Table doesn't exist** - Database auto-initializes on first run

## Testing

### Manual Testing
```bash
# Create test user
stock-admin create-user testuser test@example.com

# Start server
stock_agent

# Test login at http://localhost:8080
```

### Session Testing
- Login and verify dashboard access
- Wait for session expiration (or modify timeout)
- Verify automatic redirect to login
- Test API endpoints with/without authentication
