import os
import pathlib
from typing import Optional

from robyn import Robyn, Request, Response, serve_file
from robyn.templating import JinjaTemplate

from ..auth import AuthService, User
from ..auth.firebase_auth_service import FirebaseAuthService
from ..polygon.stock_service import StockService

def create_web_app() -> Robyn:
    """Create and configure the web application"""
    src_path = pathlib.Path(__file__).parent.parent.resolve()

    app = Robyn(__file__)
    jinja_template = JinjaTemplate(os.path.join(src_path, "templates"))

    # Initialize services
    auth_service = AuthService()
    firebase_auth_service = FirebaseAuthService(auth_service)
    stock_service = StockService()

    def get_current_user(request: Request) -> Optional[User]:
        """Get current user from session cookie"""
        # Parse cookies from Cookie header
        cookie_header = request.headers.get('cookie')
        session_token = None

        if cookie_header:
            # Parse cookies manually since Robyn doesn't have request.cookies
            cookies = {}
            for cookie in cookie_header.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value
            session_token = cookies.get('session_token')

        if session_token:
            return auth_service.get_user_from_session(session_token)
        return None

    def get_user_from_firebase_token(request: Request) -> Optional[User]:
        """Get user from Firebase ID token in Authorization header"""
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            id_token = auth_header[7:]  # Remove 'Bearer ' prefix
            return firebase_auth_service.get_user_from_firebase_token(id_token)
        return None

    def get_user_from_bearer_token(request: Request) -> Optional[User]:
        """Get user from Bearer token in Authorization header (legacy support)"""
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            session_token = auth_header[7:]  # Remove 'Bearer ' prefix
            return auth_service.get_user_from_session(session_token)
        return None

    def require_auth(func):
        """Decorator to require authentication"""
        def wrapper(request: Request):
            user = get_current_user(request)
            if not user:
                response = Response(
                    status_code=302,
                    description="",
                    headers={"Location": "/login"}
                )
                return response
            return func(request, user)
        return wrapper

    # Static files
    @app.get("/firebase-messaging-sw.js")
    async def firebase_service_worker(request: Request):
        # Serve the new Firebase auth service worker
        return serve_file(os.path.join(src_path, "static", "js", "firebase-auth-sw.js"))
    
    @app.get("/firebase-auth-sw.js")
    async def firebase_auth_service_worker(request: Request):
        return serve_file(os.path.join(src_path, "static", "js", "firebase-auth-sw.js"))

    @app.get("/static/js/:filename")
    async def serve_js_files(request: Request):
        filename = request.path_params.get("filename")
        if not filename or ".." in filename:
            return Response(status_code=404, description="Not Found", headers={})

        file_path = os.path.join(src_path, "static", "js", filename)
        if os.path.exists(file_path) and filename.endswith('.js'):
            return serve_file(file_path)
        else:
            return Response(status_code=404, description="Not Found", headers={})

    # Authentication routes
    @app.get("/login")
    async def login_page(request: Request):
        user = get_current_user(request)
        if user:
            return Response(
                status_code=302,
                description="",
                headers={"Location": "/"}
            )

        template = jinja_template.render_template("login.html")
        return template

    @app.post("/login")
    async def login_submit(request: Request):
        import json

        try:
            # Parse JSON body
            if isinstance(request.body, bytes):
                body_str = request.body.decode('utf-8')
            else:
                body_str = request.body

            data = json.loads(body_str)
            username = data.get('username', '')
            password = data.get('password', '')
        except (json.JSONDecodeError, AttributeError) as e:
            template = jinja_template.render_template("login.html", error="Invalid request format")
            return template

        user = auth_service.authenticate_user(username, password)

        if user:
            session_token = auth_service.create_session(user)
            return Response(
                status_code=302,
                description="",
                headers={
                    "Location": "/",
                    "Set-Cookie": f'session_token={session_token}; Path=/; HttpOnly'
                }
            )
        else:
            template = jinja_template.render_template("login.html", error="Invalid credentials")
            return template


    @app.post("/logout")
    async def logout(request: Request):
        # Parse cookies from Cookie header
        cookie_header = request.headers.get('cookie')
        session_token = None

        if cookie_header:
            cookies = {}
            for cookie in cookie_header.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value
            session_token = cookies.get('session_token')

        if session_token:
            auth_service.logout(session_token)

        return Response(
            status_code=302,
            description="",
            headers={
                "Location": "/login",
                "Set-Cookie": "session_token=; Path=/; HttpOnly; Max-Age=0"
            }
        )

    # Protected routes
    @app.get("/")
    async def index(request: Request):
        # For Firebase auth, we'll let the frontend handle authentication
        # The template will check Firebase auth state and redirect if needed
        context = {
            "framework": "Robyn",
            "templating_engine": "Jinja2",
            "user": None  # Firebase auth will handle user info
        }
        template = jinja_template.render_template("dashboard.html", **context)
        return template

    @app.get("/notifications")
    async def notifications_page(request: Request):
        # Let Firebase auth handle authentication on the frontend
        context = {
            "framework": "Robyn",
            "templating_engine": "Jinja2",
            "user": None  # Firebase auth will handle user info
        }
        template = jinja_template.render_template("index.html", **context)
        return template

    @app.get('/report')
    async def todays_report(request: Request):
        user = get_current_user(request)
        if not user:
            return Response(
                status_code=302,
                description="",
                headers={"Location": "/login"}
            )

        context = {
            "framework": "Robyn",
            "templating_engine": "Jinja2",
            "user": user
        }
        template = jinja_template.render_template("report.html", **context)
        return template

    # API routes - require Firebase authentication
    @app.get('/api/vapid-public-key')
    def get_vapid_public_key(request: Request):
        # Check for Firebase ID token first, fallback to legacy session token
        user = get_user_from_firebase_token(request) or get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            return Response(
                status_code=401,
                description="Unauthorized - Valid Firebase ID token required",
                headers={"Content-Type": "application/json"}
            )
        return {'vapidPublicKey': os.getenv('FIREBASE_VAPID_PUBLIC_KEY')}

    @app.get('/api/firebase-config')
    async def get_firebase_config(request: Request):
        # Check for Firebase ID token first, fallback to legacy session token
        user = get_user_from_firebase_token(request) or get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            return Response(
                status_code=401,
                description="Unauthorized - Valid Firebase ID token required",
                headers={"Content-Type": "application/json"}
            )

        config = {
            "apiKey": os.environ.get("FIREBASE_API_KEY"),
            "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
            "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
            "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.environ.get("FIREBASE_APP_ID")
        }
        return config

    @app.get('/api/firebase-config-public')
    async def get_firebase_config_public(request: Request):
        """Public endpoint for Firebase config - no authentication required"""
        config = {
            "apiKey": os.environ.get("FIREBASE_API_KEY"),
            "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
            "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
            "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.environ.get("FIREBASE_APP_ID")
        }
        return config

    @app.get('/api/auth/status')
    async def get_auth_status(request: Request):
        """HTMX-friendly endpoint to check authentication status"""
        user = get_user_from_firebase_token(request)
        if user:
            return {
                'authenticated': True,
                'user': {
                    'email': user.email,
                    'username': user.username
                }
            }
        else:
            return {'authenticated': False}

    @app.get('/api/auth/user-info')
    async def get_user_info(request: Request):
        """Get current user info for HTMX updates"""
        user = get_user_from_firebase_token(request)
        if not user:
            return Response(
                status_code=401,
                description="Unauthorized",
                headers={"Content-Type": "text/html"}
            )
        
        template = jinja_template.render_template("fragments/user_info.html", user=user)
        return template

    # Stock search and favorites routes
    @app.get('/stocks')
    async def stocks_page(request: Request):
        # Let Firebase auth handle authentication on the frontend
        context = {
            "framework": "Robyn",
            "templating_engine": "Jinja2",
            "user": None  # Firebase auth will handle user info
        }
        template = jinja_template.render_template("stocks.html", **context)
        return template

    @app.get('/api/search-stocks')
    async def search_stocks(request: Request):
        user = get_user_from_firebase_token(request) or get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            template = jinja_template.render_template("fragments/error.html", message="Please sign in to search stocks")
            return template

        query = request.query_params.get('q', '')
        if not query:
            template = jinja_template.render_template("fragments/error.html", message="Please enter a search term")
            return template

        try:
            results = stock_service.search_stocks(query)
            
            # Get user favorites to show correct button state
            favorites = auth_service.get_user_favorites(user.id)
            user_favorites = {fav.ticker for fav in favorites}
            
            template = jinja_template.render_template(
                "fragments/search_results.html", 
                results=results,
                user_favorites=user_favorites
            )
            return template
        except Exception as e:
            template = jinja_template.render_template("fragments/error.html", message="Search failed. Please try again.")
            return template

    @app.get('/api/favorites')
    async def get_favorites(request: Request):
        user = get_user_from_firebase_token(request) or get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            template = jinja_template.render_template("fragments/error.html", message="Please sign in to view favorites")
            return template

        try:
            favorites = auth_service.get_user_favorites(user.id)
            template = jinja_template.render_template("fragments/favorites_list.html", favorites=favorites)
            return template
        except Exception as e:
            template = jinja_template.render_template("fragments/error.html", message="Failed to load favorites")
            return template

    @app.post('/api/favorites')
    async def add_favorite(request: Request):
        user = get_user_from_firebase_token(request) or get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            template = jinja_template.render_template("fragments/error.html", message="Please sign in to add favorites")
            return template

        try:
            import json
            if isinstance(request.body, bytes):
                body_str = request.body.decode('utf-8')
            else:
                body_str = request.body

            data = json.loads(body_str)
            ticker = data.get('ticker', '').upper()
            company_name = data.get('company_name', '')

            if not ticker:
                template = jinja_template.render_template("fragments/error.html", message="Ticker required")
                return template

            success = auth_service.add_favorite(user.id, ticker, company_name)
            if success:
                # Return updated favorites list for HTMX
                favorites = auth_service.get_user_favorites(user.id)
                template = jinja_template.render_template("fragments/favorites_list.html", favorites=favorites)
                return template
            else:
                template = jinja_template.render_template("fragments/error.html", message="Already in favorites or failed to add")
                return template

        except (json.JSONDecodeError, Exception) as e:
            template = jinja_template.render_template("fragments/error.html", message="Invalid request")
            return template

    @app.delete('/api/favorites')
    async def remove_favorite(request: Request):
        user = get_user_from_firebase_token(request) or get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            template = jinja_template.render_template("fragments/error.html", message="Please sign in to remove favorites")
            return template

        try:
            import json
            if isinstance(request.body, bytes):
                body_str = request.body.decode('utf-8')
            else:
                body_str = request.body

            data = json.loads(body_str)
            ticker = data.get('ticker', '').upper()

            if not ticker:
                template = jinja_template.render_template("fragments/error.html", message="Ticker required")
                return template

            success = auth_service.remove_favorite(user.id, ticker)
            if success:
                # Return updated favorites list for HTMX
                favorites = auth_service.get_user_favorites(user.id)
                template = jinja_template.render_template("fragments/favorites_list.html", favorites=favorites)
                return template
            else:
                template = jinja_template.render_template("fragments/error.html", message="Not in favorites or failed to remove")
                return template

        except (json.JSONDecodeError, Exception) as e:
            template = jinja_template.render_template("fragments/error.html", message="Invalid request")
            return template

    @app.get('/api/dashboard-favorites')
    async def get_dashboard_favorites(request: Request):
        user = get_user_from_firebase_token(request) or get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            return {'error': 'Unauthorized'}, 401

        try:
            favorites = auth_service.get_user_favorites(user.id)
            if not favorites:
                return {'favorites': []}

            # Get stock data for favorites
            tickers = [fav.ticker for fav in favorites]
            stock_data = stock_service.get_stock_data(tickers)

            # Convert to dict format
            favorites_data = []
            for stock in stock_data:
                favorites_data.append({
                    'ticker': stock.ticker,
                    'company_name': stock.company_name,
                    'price': stock.price,
                    'change': stock.change,
                    'change_percent': stock.change_percent,
                    'volume': stock.volume,
                    'market_cap': stock.market_cap
                })

            return {'favorites': favorites_data}
        except Exception as e:
            return {'error': 'Failed to load dashboard data'}, 500

    @app.get('/api/major-indexes')
    async def get_major_indexes(request: Request):
        user = get_user_from_firebase_token(request) or get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            return {'error': 'Unauthorized'}, 401

        try:
            indexes = stock_service.get_major_indexes()

            indexes_data = []
            for stock in indexes:
                indexes_data.append({
                    'ticker': stock.ticker,
                    'company_name': stock.company_name,
                    'price': stock.price,
                    'change': stock.change,
                    'change_percent': stock.change_percent,
                    'volume': stock.volume,
                    'market_cap': stock.market_cap
                })

            return {'indexes': indexes_data}
        except Exception as e:
            return {'error': 'Failed to load index data'}, 500

    return app
