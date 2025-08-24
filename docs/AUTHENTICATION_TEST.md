# Service Worker Authentication Testing Guide

## Overview

This document describes how to test the enhanced service worker authentication system that allows background notifications to access protected APIs using cached session tokens.

## What Was Implemented

### 1. Enhanced Service Worker (`firebase-messaging-sw.js`)
- **IndexedDB Token Storage**: Persistent storage for session tokens across browser restarts
- **Authentication Headers**: Automatic Bearer token inclusion in API requests
- **Token Validation**: Periodic validation and expiration handling
- **Message Handling**: Communication with main thread for token updates

### 2. Authentication Utility (`auth-utils.js`)
- **Token Management**: Extraction from cookies and localStorage persistence
- **Service Worker Integration**: Automatic token synchronization
- **Validation**: API-based token validation
- **Error Handling**: Automatic cleanup of expired tokens

### 3. Updated Web Pages
- **Login Page**: Automatic service worker setup after successful login
- **Dashboard**: Automatic authentication initialization
- **API Endpoints**: Proper Response objects for unauthorized access

## Testing Steps

### 1. Initial Setup Test

1. **Clear Browser Data**
   ```
   - Open Developer Tools (F12)
   - Go to Application/Storage tab
   - Clear all data (cookies, localStorage, IndexedDB)
   - Unregister any existing service workers
   ```

2. **Login Test**
   ```
   - Navigate to /login
   - Enter valid credentials
   - Check Console for:
     * "Service worker registered successfully"
     * "Session token sent to service worker"
   - Verify redirect to dashboard
   ```

### 2. Service Worker Registration Verification

1. **Check Service Worker Status**
   ```
   Developer Tools > Application > Service Workers
   - Verify firebase-messaging-sw.js is registered and active
   - Status should show "activated and is running"
   ```

2. **Check IndexedDB Storage**
   ```
   Developer Tools > Application > IndexedDB
   - Look for "StockAgentAuth" database
   - Should contain "auth" object store
   - Should have "session_token" entry with your token
   ```

### 3. API Authentication Test

1. **Test Authenticated API Calls**
   ```javascript
   // In browser console, test service worker API access
   fetch('/api/vapid-public-key').then(r => r.json()).then(console.log);
   fetch('/api/firebase-config').then(r => r.json()).then(console.log);
   ```

2. **Expected Results**
   - Should return valid Firebase configuration
   - Should NOT return 401 Unauthorized errors
   - Check Network tab for proper Authorization headers

### 4. Token Persistence Test

1. **Browser Restart Test**
   ```
   - Close browser completely
   - Reopen and navigate to dashboard
   - Check Console for:
     * "Service worker activated"
     * No authentication errors
   - Dashboard should load normally
   ```

2. **Service Worker Restart Test**
   ```
   Developer Tools > Application > Service Workers
   - Click "Unregister" next to firebase-messaging-sw.js
   - Refresh the page
   - Service worker should re-register and authenticate automatically
   ```

### 5. Token Expiration Test

1. **Manual Token Invalidation**
   ```
   Developer Tools > Application > IndexedDB > StockAgentAuth > auth
   - Modify the session_token value to something invalid
   - Refresh the page
   - Should redirect to login page
   ```

2. **Cookie Expiration**
   ```
   Developer Tools > Application > Cookies
   - Delete the session_token cookie
   - Keep localStorage token intact
   - Refresh page - should still work (using stored token)
   - Clear localStorage - should redirect to login
   ```

## Expected Console Messages

### Successful Setup
```
Service worker registered successfully
Session token sent to service worker
Service worker activated
Firebase messaging initialized successfully
```

### Authentication Errors
```
Service worker requires authentication: Session token expired or invalid
No session token available for authentication
Failed to fetch Firebase configuration: 401
```

### Token Management
```
Session token sent to service worker
Updated service worker with new session token
Service worker session token cleared
```

## Troubleshooting

### Service Worker Not Registering
- Check browser supports service workers
- Verify HTTPS connection (required for service workers)
- Check for JavaScript errors in console

### Authentication Failing
- Verify session token exists in cookies or localStorage
- Check API endpoints return proper Response objects (not tuples)
- Ensure Bearer token format is correct

### Token Not Persisting
- Check IndexedDB permissions
- Verify localStorage is enabled
- Check for browser privacy modes that block storage

### Background Notifications Not Working
- Verify Firebase configuration is loaded
- Check notification permissions
- Test with browser's background sync

## API Endpoint Verification

### Before Fix (Incorrect Response)
```python
return {'error': 'Unauthorized'}, 401  # Wrong format
```

### After Fix (Correct Response)
```python
return Response(
    status_code=401,
    description="Unauthorized - Valid session token required",
    headers={"Content-Type": "application/json"}
)
```

## Files Modified

1. `src/stock_agent/static/firebase-messaging-sw.js` - Enhanced with authentication
2. `src/stock_agent/static/js/auth-utils.js` - New authentication utility
3. `src/stock_agent/templates/login.html` - Integrated auth utility
4. `src/stock_agent/templates/dashboard.html` - Integrated auth utility  
5. `src/stock_agent/web/web_app.py` - Fixed API responses and added static file serving

## Security Considerations

- Session tokens are stored in IndexedDB (persistent but domain-restricted)
- Tokens are validated periodically and cleared on expiration
- Service worker only sends tokens over HTTPS
- No sensitive data is logged in production

## Next Steps

1. Test with actual Firebase push notifications
2. Implement token refresh mechanism if needed
3. Add notification permission handling
4. Test cross-tab session synchronization