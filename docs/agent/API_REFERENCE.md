# API Reference Documentation

## Overview
The Stock Agent API provides endpoints for user authentication, stock data retrieval, favorites management, and Firebase integration. All API endpoints require authentication via session tokens.

## Authentication
All API endpoints require authentication using one of two methods:

### Cookie-based Authentication (Web)
Session token automatically included in cookies after login.

### Bearer Token Authentication (API)
Include session token in Authorization header:
```
Authorization: Bearer <session_token>
```

## Base URL
```
http://localhost:8080
```

## Web Routes

### Authentication Routes

#### `GET /login`
Display login form.

**Response**: HTML login page

#### `POST /login`
Authenticate user with JSON credentials.

**Request Body**:
```json
{
    "username": "string",
    "password": "string"
}
```

**Success Response** (302):
- Redirects to `/` (dashboard)
- Sets `session_token` cookie

**Error Response** (200):
- Returns login form with error message

#### `POST /logout`
Clear user session and redirect to login.

**Response** (302):
- Redirects to `/login`
- Clears `session_token` cookie

### Application Routes

#### `GET /`
Main dashboard showing user favorites and major market indexes.

**Authentication**: Required
**Response**: HTML dashboard page

#### `GET /stocks`
Stock search and favorites management page.

**Authentication**: Required
**Response**: HTML stock search page

#### `GET /report`
Stock reports and analysis page.

**Authentication**: Required
**Response**: HTML reports page

#### `GET /notifications`
Firebase push notifications setup page.

**Authentication**: Required
**Response**: HTML notifications page

## API Endpoints

### Firebase Integration

#### `GET /api/vapid-public-key`
Get VAPID public key for Firebase push notifications.

**Authentication**: Required

**Response**:
```json
{
    "vapidPublicKey": "string"
}
```

**Error Response** (401):
```json
{
    "error": "Unauthorized - Valid session token required"
}
```

#### `GET /api/firebase-config`
Get Firebase configuration for client initialization.

**Authentication**: Required

**Response**:
```json
{
    "apiKey": "string",
    "authDomain": "string",
    "projectId": "string",
    "messagingSenderId": "string",
    "appId": "string"
}
```

### Stock Data Endpoints

#### `GET /api/search-stocks`
Search for stocks by ticker or company name.

**Authentication**: Required

**Query Parameters**:
- `q` (required): Search query string

**Example**: `/api/search-stocks?q=AAPL`

**Response**:
```json
{
    "results": [
        {
            "ticker": "AAPL",
            "company_name": "Apple Inc."
        }
    ]
}
```

**Error Responses**:
- 400: `{"error": "Query parameter required"}`
- 401: `{"error": "Unauthorized"}`
- 500: `{"error": "Search failed"}`

#### `GET /api/major-indexes`
Get current data for major market indexes.

**Authentication**: Required

**Response**:
```json
{
    "indexes": [
        {
            "ticker": "DJI",
            "company_name": "Dow Jones Industrial Average",
            "price": 34123.45,
            "change": 123.45,
            "change_percent": 0.36,
            "volume": 150000000,
            "market_cap": "N/A"
        },
        {
            "ticker": "SPX",
            "company_name": "S&P 500",
            "price": 4234.56,
            "change": -12.34,
            "change_percent": -0.29,
            "volume": 120000000,
            "market_cap": "N/A"
        }
    ]
}
```

### Favorites Management

#### `GET /api/favorites`
Get user's favorite stocks list.

**Authentication**: Required

**Response**:
```json
{
    "favorites": [
        {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "added_at": "2024-01-15T10:30:00"
        }
    ]
}
```

**Error Response** (500):
```json
{
    "error": "Failed to load favorites"
}
```

#### `POST /api/favorites`
Add stock to user's favorites.

**Authentication**: Required

**Request Body**:
```json
{
    "ticker": "AAPL",
    "company_name": "Apple Inc."
}
```

**Success Response**:
```json
{
    "success": true,
    "message": "Added to favorites"
}
```

**Error Responses**:
- 400: `{"error": "Ticker required"}`
- 400: `{"error": "Already in favorites or failed to add"}`
- 400: `{"error": "Invalid request"}`

#### `DELETE /api/favorites`
Remove stock from user's favorites.

**Authentication**: Required

**Request Body**:
```json
{
    "ticker": "AAPL"
}
```

**Success Response**:
```json
{
    "success": true,
    "message": "Removed from favorites"
}
```

**Error Responses**:
- 400: `{"error": "Ticker required"}`
- 400: `{"error": "Not in favorites or failed to remove"}`

#### `GET /api/dashboard-favorites`
Get user's favorites with current stock data.

**Authentication**: Required

**Response**:
```json
{
    "favorites": [
        {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "price": 175.23,
            "change": 2.45,
            "change_percent": 1.42,
            "volume": 45000000,
            "market_cap": "$2.8T"
        }
    ]
}
```

## Static Files

#### `GET /firebase-messaging-sw.js`
Firebase messaging service worker for push notifications.

**Response**: JavaScript service worker file

## Error Handling

### HTTP Status Codes
- `200` - Success
- `302` - Redirect (authentication flows)
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (authentication required)
- `500` - Internal Server Error

### Error Response Format
```json
{
    "error": "Error description"
}
```

### Common Error Scenarios

#### Authentication Errors
- Missing session token → 401 Unauthorized
- Expired session → 401 Unauthorized
- Invalid session token → 401 Unauthorized

#### Validation Errors
- Missing required fields → 400 Bad Request
- Invalid JSON format → 400 Bad Request
- Invalid ticker format → 400 Bad Request

#### Server Errors
- Database connection issues → 500 Internal Server Error
- External API failures → 500 Internal Server Error
- Service initialization errors → 500 Internal Server Error

## Rate Limiting
Currently no rate limiting implemented. Consider adding for production use.

## CORS
No CORS headers currently set. Same-origin policy applies.

## Data Models

### Stock Data Model
```json
{
    "ticker": "string",           // Stock ticker symbol
    "company_name": "string",     // Company name
    "price": "number",            // Current price
    "change": "number",           // Price change
    "change_percent": "number",   // Percentage change
    "volume": "number",           // Trading volume
    "market_cap": "string"        // Market capitalization
}
```

### User Favorite Model
```json
{
    "ticker": "string",           // Stock ticker symbol
    "company_name": "string",     // Company name
    "added_at": "string"          // ISO datetime string
}
```

## Testing Examples

### Using curl

#### Login
```bash
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo1234"}' \
  -c cookies.txt
```

#### Search Stocks
```bash
curl -X GET "http://localhost:8080/api/search-stocks?q=AAPL" \
  -b cookies.txt
```

#### Add Favorite
```bash
curl -X POST http://localhost:8080/api/favorites \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL","company_name":"Apple Inc."}' \
  -b cookies.txt
```

#### Get Dashboard Data
```bash
curl -X GET http://localhost:8080/api/dashboard-favorites \
  -b cookies.txt
```

### Using Bearer Token
```bash
# Get session token from login response, then:
curl -X GET http://localhost:8080/api/favorites \
  -H "Authorization: Bearer <session_token>"
```

## WebSocket Support
Currently not implemented. All real-time updates use HTTP polling with 30-second intervals.

## Pagination
Currently not implemented. All endpoints return complete datasets.

## Caching
No caching headers currently set. Consider adding for static resources and stable data.
