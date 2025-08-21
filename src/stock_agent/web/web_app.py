import os
import pathlib
from typing import Optional

from robyn import Robyn, Request, Response, serve_file
from robyn.templating import JinjaTemplate

from ..auth import AuthService, User
from ..stock_math import StockService

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

    def require_auth(func):
        """Decorator to require authentication"""
        def wrapper(request: Request):
            user = get_current_user(request)
            if not user:
                response = Response()
                response.status_code = 302
                response.headers['Location'] = '/login'
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
        form_data = request.form_data
        username = form_data.get('username', '')
        password = form_data.get('password', '')

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
        cookie_header = request.headers.get('cookie', '')
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
    
    # API routes
    @app.get('/api/vapid-public-key')
    def get_vapid_public_key(request: Request):
        user = get_current_user(request)
        if not user:
            return {'error': 'Unauthorized'}, 401
        return {'vapidPublicKey': os.getenv('FIREBASE_VAPID_PUBLIC_KEY')}
    
    @app.get('/api/firebase-config')
    async def get_firebase_config(request: Request):
        user = get_current_user(request)
        if not user:
            return {'error': 'Unauthorized'}, 401
        
        config = {
            "apiKey": os.environ.get("FIREBASE_API_KEY"),
            "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
            "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
            "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.environ.get("FIREBASE_APP_ID")
        }
        return config
    
    return app
