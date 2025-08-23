import os
import pathlib
from typing import Optional

from robyn import Robyn, Request, Response, serve_file
from robyn.templating import JinjaTemplate

from ..auth import AuthService, User
from ..polygon.stock_service import StockService

def create_web_app() -> Robyn:
    """Create and configure the web application"""
    src_path = pathlib.Path(__file__).parent.parent.resolve()

    app = Robyn(__file__)
    jinja_template = JinjaTemplate(os.path.join(src_path, "templates"))

    # Initialize services
    auth_service = AuthService()
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

    def get_user_from_bearer_token(request: Request) -> Optional[User]:
        """Get user from Bearer token in Authorization header"""
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
        return serve_file(os.path.join(src_path, "static", "firebase-messaging-sw.js"))

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
        template = jinja_template.render_template("dashboard.html", **context)
        return template
    
    @app.get("/notifications")
    async def notifications_page(request: Request):
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

    # API routes - require session token authentication
    @app.get('/api/vapid-public-key')
    def get_vapid_public_key(request: Request):
        # Check for user session (cookie or Bearer token)
        user = get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            return {'error': 'Unauthorized - Valid session token required'}, 401
        return {'vapidPublicKey': os.getenv('FIREBASE_VAPID_PUBLIC_KEY')}

    @app.get('/api/firebase-config')
    async def get_firebase_config(request: Request):
        # Check for user session (cookie or Bearer token)
        user = get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            return {'error': 'Unauthorized - Valid session token required'}, 401

        config = {
            "apiKey": os.environ.get("FIREBASE_API_KEY"),
            "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
            "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
            "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.environ.get("FIREBASE_APP_ID")
        }
        return config
    
    # Stock search and favorites routes
    @app.get('/stocks')
    async def stocks_page(request: Request):
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
        template = jinja_template.render_template("stocks.html", **context)
        return template
    
    @app.get('/api/search-stocks')
    async def search_stocks(request: Request):
        user = get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            return {'error': 'Unauthorized'}, 401
        
        query = request.query_params.get('q', '')
        if not query:
            return {'error': 'Query parameter required'}, 400
        
        try:
            results = stock_service.search_stocks(query)
            return {'results': results}
        except Exception as e:
            return {'error': 'Search failed'}, 500
    
    @app.get('/api/favorites')
    async def get_favorites(request: Request):
        user = get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            return {'error': 'Unauthorized'}, 401
        
        try:
            favorites = auth_service.get_user_favorites(user.id)
            favorites_data = []
            for fav in favorites:
                favorites_data.append({
                    'ticker': fav.ticker,
                    'company_name': fav.company_name,
                    'added_at': fav.added_at.isoformat() if fav.added_at else None
                })
            return {'favorites': favorites_data}
        except Exception as e:
            return {'error': 'Failed to load favorites'}, 500
    
    @app.post('/api/favorites')
    async def add_favorite(request: Request):
        user = get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            return {'error': 'Unauthorized'}, 401
        
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
                return {'error': 'Ticker required'}, 400
            
            success = auth_service.add_favorite(user.id, ticker, company_name)
            if success:
                return {'success': True, 'message': 'Added to favorites'}
            else:
                return {'error': 'Already in favorites or failed to add'}, 400
                
        except (json.JSONDecodeError, Exception) as e:
            return {'error': 'Invalid request'}, 400
    
    @app.delete('/api/favorites')
    async def remove_favorite(request: Request):
        user = get_current_user(request) or get_user_from_bearer_token(request)
        if not user:
            return {'error': 'Unauthorized'}, 401
        
        try:
            import json
            if isinstance(request.body, bytes):
                body_str = request.body.decode('utf-8')
            else:
                body_str = request.body
            
            data = json.loads(body_str)
            ticker = data.get('ticker', '').upper()
            
            if not ticker:
                return {'error': 'Ticker required'}, 400
            
            success = auth_service.remove_favorite(user.id, ticker)
            if success:
                return {'success': True, 'message': 'Removed from favorites'}
            else:
                return {'error': 'Not in favorites or failed to remove'}, 400
                
        except (json.JSONDecodeError, Exception) as e:
            return {'error': 'Invalid request'}, 400
    
    @app.get('/api/dashboard-favorites')
    async def get_dashboard_favorites(request: Request):
        user = get_current_user(request) or get_user_from_bearer_token(request)
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
        user = get_current_user(request) or get_user_from_bearer_token(request)
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
