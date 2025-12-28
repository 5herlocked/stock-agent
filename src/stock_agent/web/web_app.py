import os
import pathlib
from typing import Optional

from robyn import Robyn, Request, Response, serve_file
from robyn.templating import JinjaTemplate

from ..auth import AuthService, User
from ..auth.firebase_auth_service import FirebaseAuthService
from ..polygon.stock_service import StockService
from ..notification_service import NotificationService

def create_web_app() -> Robyn:
    """Create and configure the web application"""
    src_path = pathlib.Path(__file__).parent.parent.resolve()

    app = Robyn(__file__)
    jinja_template = JinjaTemplate(os.path.join(src_path, "templates"))

    # Initialize services
    auth_service = AuthService()
    firebase_auth_service = FirebaseAuthService(auth_service)
    stock_service = StockService()
    
    # Initialize notification service (will reuse existing Firebase app)
    notification_service = None
    try:
        notification_service = NotificationService()
    except Exception as e:
        print(f"Warning: NotificationService not available: {e}")

    def get_current_user(request: Request) -> Optional[User]:
        """Get current user from Firebase ID token"""
        # Try Authorization header first (for API calls)
        auth_header = request.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            id_token = auth_header[7:]  # Remove 'Bearer ' prefix
            return firebase_auth_service.get_user_from_firebase_token(id_token)
        
        # Try cookie for web requests
        cookie_header = request.headers.get('cookie')
        if cookie_header:
            cookies = {}
            for cookie in cookie_header.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value
            
            firebase_token = cookies.get('firebase_token')
            if firebase_token:
                return firebase_auth_service.get_user_from_firebase_token(firebase_token)
        
        return None

    def require_auth(func):
        """Decorator to require Firebase authentication"""
        def wrapper(request: Request):
            user = get_current_user(request)
            if not user:
                # For API requests, return 401
                if request.url.path.startswith('/api/'):
                    return Response(
                        status_code=401,
                        description='{"error": "Authentication required"}',
                        headers={"Content-Type": "application/json"}
                    )
                # For web requests, redirect to login
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
        # Serve the Firebase messaging service worker
        return serve_file(os.path.join(src_path, "static", "js", "firebase-messaging-sw.js"))

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
            # Parse JSON body for Firebase ID token
            if isinstance(request.body, bytes):
                body_str = request.body.decode('utf-8')
            else:
                body_str = request.body

            data = json.loads(body_str)
            firebase_token = data.get('firebase_token', '')
            
            if not firebase_token:
                return Response(
                    status_code=400,
                    description='{"error": "Firebase token required"}',
                    headers={"Content-Type": "application/json"}
                )
            
            # Verify Firebase token and get/create user
            user = firebase_auth_service.get_user_from_firebase_token(firebase_token)
            
            if user:
                return Response(
                    status_code=200,
                    description='{"success": true}',
                    headers={
                        "Content-Type": "application/json",
                        "Set-Cookie": f'firebase_token={firebase_token}; Path=/; HttpOnly; SameSite=Strict'
                    }
                )
            else:
                return Response(
                    status_code=401,
                    description='{"error": "Invalid Firebase token"}',
                    headers={"Content-Type": "application/json"}
                )
                
        except (json.JSONDecodeError, AttributeError) as e:
            return Response(
                status_code=400,
                description='{"error": "Invalid request format"}',
                headers={"Content-Type": "application/json"}
            )

    @app.post("/logout")
    async def logout(request: Request):
        return Response(
            status_code=302,
            description="",
            headers={
                "Location": "/login",
                "Set-Cookie": "firebase_token=; Path=/; HttpOnly; Max-Age=0"
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

    @app.get('/portfolio')
    async def portfolio_page(request: Request):
        """Render portfolio page"""
        # For Firebase auth, we'll let the frontend handle authentication
        # The template will check Firebase auth state and redirect if needed
        context = {
            "framework": "Robyn",
            "templating_engine": "Jinja2",
            "user": None  # Firebase auth will handle user info
        }
        template = jinja_template.render_template("portfolio.html", **context)
        return template

    # API routes - require Firebase authentication
    @app.get('/api/vapid-public-key')
    def get_vapid_public_key(request: Request):
        user = get_current_user(request)
        if not user:
            return Response(
                status_code=401,
                description='{"error": "Authentication required"}',
                headers={"Content-Type": "application/json"}
            )
        return {'vapidPublicKey': os.getenv('FIREBASE_VAPID_PUBLIC_KEY')}

    @app.get('/api/firebase-config')
    async def get_firebase_config(request: Request):
        user = get_current_user(request)
        if not user:
            return Response(
                status_code=401,
                description='{"error": "Authentication required"}',
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
        user = get_current_user(request)
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
        user = get_current_user(request)
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
        user = get_current_user(request)
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
            if "rate limit" in str(e).lower():
                error_message = "🐎 Whoa there, cowboy! Slow down on those stock searches. Our data provider needs a breather!"
            else:
                error_message = "Search failed. Please try again."
            template = jinja_template.render_template("fragments/error.html", message=error_message)
            return template

    @app.get('/api/favorites')
    async def get_favorites(request: Request):
        user = get_current_user(request)
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
        user = get_current_user(request)
        if not user:
            template = jinja_template.render_template("fragments/error.html", message="Please sign in to add favorites")
            return template

        try:
            # Use query parameters - only ticker needed, get company name from Polygon
            ticker = request.query_params.get('ticker', '').upper()

            if not ticker:
                template = jinja_template.render_template("fragments/error.html", message="Ticker required")
                return template

            # Get company name from Polygon API by searching for the ticker
            try:
                search_results = stock_service.search_stocks(ticker)
                company_name = ''
                # Find exact ticker match in search results
                for result in search_results:
                    if result.get('ticker', '').upper() == ticker:
                        company_name = result.get('company_name', '')
                        break
            except:
                company_name = ''

            success = auth_service.add_favorite(user.id, ticker, company_name)
            if success:
                # Return updated favorites list for HTMX
                favorites = auth_service.get_user_favorites(user.id)
                template = jinja_template.render_template("fragments/favorites_list.html", favorites=favorites)
                return template
            else:
                template = jinja_template.render_template("fragments/error.html", message="Already in favorites or failed to add")
                return template

        except Exception as e:
            template = jinja_template.render_template("fragments/error.html", message="Invalid request")
            return template

    @app.delete('/api/favorites')
    async def remove_favorite(request: Request):
        user = get_current_user(request)
        if not user:
            template = jinja_template.render_template("fragments/error.html", message="Please sign in to remove favorites")
            return template

        try:
            # Use query parameters instead of JSON body
            ticker = request.query_params.get('ticker', '').upper()

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

        except Exception as e:
            template = jinja_template.render_template("fragments/error.html", message="Invalid request")
            return template

    @app.get('/api/dashboard-favorites')
    async def get_dashboard_favorites(request: Request):
        user = get_current_user(request)
        if not user:
            return jinja_template.render_template("fragments/error.html", message="Unauthorized")

        try:
            favorites = auth_service.get_user_favorites(user.id)
            if not favorites:
                return jinja_template.render_template("fragments/dashboard_favorites.html", favorites=[])

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

            return jinja_template.render_template("fragments/dashboard_favorites.html", favorites=favorites_data)
        except Exception as e:
            if "rate limit" in str(e).lower():
                error_message = "📊 Easy there, speed racer! Your portfolio is popular, but our data feed needs a coffee break. Try again in a moment!"
            else:
                error_message = "Failed to load dashboard data. Please try again."
            return jinja_template.render_template("fragments/error.html", message=error_message)

    @app.get('/api/major-indexes')
    async def get_major_indexes(request: Request):
        user = get_current_user(request)
        if not user:
            return jinja_template.render_template("fragments/error.html", message="Unauthorized")

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

            return jinja_template.render_template("fragments/major_indexes.html", indexes=indexes_data)
        except Exception as e:
            if "rate limit" in str(e).lower():
                error_message = "📈 Hold your horses! The market indexes are taking a quick power nap. Even Wall Street needs a breather sometimes!"
            else:
                error_message = "Failed to load index data. Please try again."
            return jinja_template.render_template("fragments/error.html", message=error_message)

    @app.post('/api/notifications/subscribe')
    async def subscribe_to_notifications(request: Request):
        """Subscribe device token to stock_update topic"""
        user = get_current_user(request)

        if not user:
            return Response(
                status_code=401,
                description='{"error": "Authentication required"}',
                headers={"Content-Type": "application/json"}
            )

        if not notification_service:
            return Response(
                status_code=500,
                description='{"error": "Notification service not available"}',
                headers={"Content-Type": "application/json"}
            )

        try:
            import json
            
            # Parse JSON body for device token
            if isinstance(request.body, bytes):
                body_str = request.body.decode('utf-8')
            else:
                body_str = request.body

            data = json.loads(body_str)
            device_token = data.get('token', '')

            if not device_token:
                return Response(
                    status_code=400,
                    description='{"error": "Device token required"}',
                    headers={"Content-Type": "application/json"}
                )
            
            # Subscribe token to stock_update topic using NotificationService
            success = notification_service.subscribe_to_topic(device_token, 'stock_update')
            
            if success:
                # Save device token to database
                token_saved = auth_service.save_device_token(user.id, device_token)
                if not token_saved:
                    print(f"Warning: Failed to save device token to database for user {user.id}")
                
                return Response(
                    status_code=200,
                    description='{"success": true, "message": "Successfully subscribed to stock updates"}',
                    headers={"Content-Type": "application/json"}
                )
            else:
                print(f"Failed to subscribe to topic")
                return Response(
                    status_code=400,
                    description='{"error": "Failed to subscribe to topic"}',
                    headers={"Content-Type": "application/json"}
                )
                
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Invalid request format: {e}")
            return Response(
                status_code=400,
                description='{"error": "Invalid request format"}',
                headers={"Content-Type": "application/json"}
            )

    @app.post('/api/trades')
    async def add_trade_endpoint(request: Request):
        """Add a new trade from form submission"""
        import json
        from datetime import date

        user = get_current_user(request)
        if not user:
            return Response(
                status_code=401,
                description='{"error": "Authentication required"}',
                headers={"Content-Type": "application/json"}
            )

        try:
            # Parse form data
            if isinstance(request.body, bytes):
                body_str = request.body.decode('utf-8')
            else:
                body_str = request.body

            # Parse URL-encoded form data
            from urllib.parse import parse_qs
            form_data = parse_qs(body_str)

            ticker = form_data.get('ticker', [''])[0].upper()
            action = form_data.get('action', [''])[0].upper()
            quantity = int(form_data.get('quantity', ['0'])[0])
            price = float(form_data.get('price', ['0'])[0])
            trade_date = form_data.get('trade_date', [str(date.today())])[0]
            notes = form_data.get('notes', [''])[0] or None
            whatsapp_rec_id = form_data.get('whatsapp_recommendation_id', [''])[0]
            whatsapp_recommendation_id = int(whatsapp_rec_id) if whatsapp_rec_id else None

            # Validate
            if not ticker or action not in ['BUY', 'SELL'] or quantity <= 0 or price <= 0:
                return jinja_template.render_template("fragments/error.html",
                    message="Invalid trade data. Please check all fields.")

            # Add trade
            trade_id = auth_service.add_trade(
                user_id=user.id,
                ticker=ticker,
                action=action,
                quantity=quantity,
                price=price,
                trade_date=trade_date,
                notes=notes,
                whatsapp_recommendation_id=whatsapp_recommendation_id
            )

            if not trade_id:
                return jinja_template.render_template("fragments/error.html",
                    message="Failed to add trade")

            # If linked to WhatsApp recommendation, mark as accepted
            if whatsapp_recommendation_id:
                auth_service.update_whatsapp_recommendation_status(whatsapp_recommendation_id, 'accepted')

            # Return updated trades list
            trades = auth_service.get_user_trades(user.id)
            return jinja_template.render_template("fragments/trades_list.html", trades=trades)

        except Exception as e:
            print(f"Error adding trade: {e}")
            return jinja_template.render_template("fragments/error.html",
                message="Failed to add trade. Please try again.")

    @app.get('/api/trades')
    async def get_trades_endpoint(request: Request):
        """Get user's trades"""
        user = get_current_user(request)
        if not user:
            return jinja_template.render_template("fragments/error.html", message="Unauthorized")

        try:
            trades = auth_service.get_user_trades(user.id)
            return jinja_template.render_template("fragments/trades_list.html", trades=trades)
        except Exception as e:
            print(f"Error getting trades: {e}")
            return jinja_template.render_template("fragments/error.html", message="Failed to load trades")

    @app.delete('/api/trades')
    async def delete_trade_endpoint(request: Request):
        """Delete a trade"""
        user = get_current_user(request)
        if not user:
            return jinja_template.render_template("fragments/error.html", message="Unauthorized")

        try:
            trade_id = int(request.query_params.get('trade_id', '0'))
            if trade_id <= 0:
                return jinja_template.render_template("fragments/error.html", message="Invalid trade ID")

            success = auth_service.delete_trade(user.id, trade_id)
            if not success:
                return jinja_template.render_template("fragments/error.html", message="Failed to delete trade")

            # Return updated trades list
            trades = auth_service.get_user_trades(user.id)
            return jinja_template.render_template("fragments/trades_list.html", trades=trades)

        except Exception as e:
            print(f"Error deleting trade: {e}")
            return jinja_template.render_template("fragments/error.html", message="Failed to delete trade")

    @app.get('/api/portfolio/positions')
    async def get_portfolio_positions_endpoint(request: Request):
        """Get portfolio positions with current prices and P&L"""
        user = get_current_user(request)
        if not user:
            return jinja_template.render_template("fragments/error.html", message="Unauthorized")

        try:
            positions = auth_service.get_user_positions(user.id)

            if not positions:
                return jinja_template.render_template("fragments/portfolio_positions.html", positions=[])

            # Get current prices
            tickers = [p['ticker'] for p in positions]
            stock_data = stock_service.get_stock_data(tickers)

            prices = {s.ticker: s.price for s in stock_data}

            # Calculate P&L
            for position in positions:
                ticker = position['ticker']
                current_price = prices.get(ticker, 0)

                position['current_price'] = current_price
                position['market_value'] = current_price * position['total_quantity']
                position['pnl'] = (current_price - position['avg_cost']) * position['total_quantity']
                position['pnl_percent'] = ((current_price - position['avg_cost']) / position['avg_cost'] * 100) if position['avg_cost'] > 0 else 0

            return jinja_template.render_template("fragments/portfolio_positions.html", positions=positions)

        except Exception as e:
            print(f"Error loading positions: {e}")
            return jinja_template.render_template("fragments/error.html", message="Failed to load positions")

    @app.get('/api/portfolio/summary')
    async def get_portfolio_summary_endpoint(request: Request):
        """Get portfolio summary metrics"""
        user = get_current_user(request)
        if not user:
            return jinja_template.render_template("fragments/error.html", message="Unauthorized")

        try:
            positions = auth_service.get_user_positions(user.id)
            trades = auth_service.get_user_trades(user.id)

            if not positions:
                return jinja_template.render_template("fragments/portfolio_summary.html",
                    total_value=0, total_cost=0, total_pnl=0, total_pnl_percent=0,
                    position_count=0, trade_count=len(trades))

            # Get current prices
            tickers = [p['ticker'] for p in positions]
            stock_data = stock_service.get_stock_data(tickers)
            prices = {s.ticker: s.price for s in stock_data}

            # Calculate totals
            total_value = 0
            total_cost = 0

            for position in positions:
                current_price = prices.get(position['ticker'], 0)
                total_value += current_price * position['total_quantity']
                total_cost += position['total_cost_basis']

            total_pnl = total_value - total_cost
            total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0

            return jinja_template.render_template("fragments/portfolio_summary.html",
                total_value=total_value,
                total_cost=total_cost,
                total_pnl=total_pnl,
                total_pnl_percent=total_pnl_percent,
                position_count=len(positions),
                trade_count=len(trades))

        except Exception as e:
            print(f"Error loading summary: {e}")
            return jinja_template.render_template("fragments/error.html", message="Failed to load summary")

    @app.get('/api/dashboard-portfolio')
    async def get_dashboard_portfolio_endpoint(request: Request):
        """Get compact portfolio data for dashboard"""
        user = get_current_user(request)
        if not user:
            return jinja_template.render_template("fragments/error.html", message="Unauthorized")

        try:
            positions = auth_service.get_user_positions(user.id)

            if not positions:
                return jinja_template.render_template("fragments/dashboard_portfolio.html",
                    total_value=0, total_pnl=0, total_pnl_percent=0, top_positions=[])

            # Get current prices
            tickers = [p['ticker'] for p in positions]
            stock_data = stock_service.get_stock_data(tickers)
            prices = {s.ticker: s.price for s in stock_data}

            # Calculate P&L for each position
            total_value = 0
            total_cost = 0

            for position in positions:
                current_price = prices.get(position['ticker'], 0)
                position['current_price'] = current_price
                position['market_value'] = current_price * position['total_quantity']
                position['pnl'] = (current_price - position['avg_cost']) * position['total_quantity']
                position['pnl_percent'] = ((current_price - position['avg_cost']) / position['avg_cost'] * 100) if position['avg_cost'] > 0 else 0

                total_value += position['market_value']
                total_cost += position['total_cost_basis']

            total_pnl = total_value - total_cost
            total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0

            # Sort by market value
            positions.sort(key=lambda x: x['market_value'], reverse=True)

            return jinja_template.render_template("fragments/dashboard_portfolio.html",
                total_value=total_value,
                total_pnl=total_pnl,
                total_pnl_percent=total_pnl_percent,
                top_positions=positions[:3])

        except Exception as e:
            print(f"Error loading dashboard portfolio: {e}")
            return jinja_template.render_template("fragments/error.html", message="Failed to load portfolio")

    @app.get('/api/header')
    async def get_header_fragment(request: Request):
        """Get the header fragment"""
        current_page = request.query_params.get('page', '')
        show_notifications = request.query_params.get('notifications', 'false') == 'true'
        show_refresh = request.query_params.get('refresh', 'false') == 'true'

        # Determine title based on page
        page_titles = {
            'dashboard': 'Stock Dashboard',
            'stocks': 'Stock Search & Favorites',
            'portfolio': 'Portfolio'
        }
        page_title = page_titles.get(current_page, 'Stock Agent')

        return jinja_template.render_template("fragments/header.html",
            page_title=page_title,
            current_page=current_page,
            show_notifications=show_notifications,
            show_refresh=show_refresh)

    @app.get('/api/trade-form')
    async def get_trade_form_endpoint(request: Request):
        """Get the trade form fragment"""
        from datetime import date

        user = get_current_user(request)
        if not user:
            return jinja_template.render_template("fragments/error.html", message="Unauthorized")

        try:
            return jinja_template.render_template("fragments/trade_form.html",
                ticker='',
                recommendation_id=None,
                today=str(date.today()))
        except Exception as e:
            print(f"Error loading trade form: {e}")
            return jinja_template.render_template("fragments/error.html", message="Failed to load form")

    @app.post('/api/whatsapp/recommendations/:id/accept')
    async def accept_whatsapp_recommendation_endpoint(request: Request):
        """Accept a WhatsApp recommendation and return trade form"""
        from datetime import date

        user = get_current_user(request)
        if not user:
            return jinja_template.render_template("fragments/error.html", message="Unauthorized")

        try:
            rec_id = int(request.path_params.get('id', '0'))
            if rec_id <= 0:
                return jinja_template.render_template("fragments/error.html", message="Invalid recommendation ID")

            # Get recommendation details
            recommendations = auth_service.get_whatsapp_recommendations(limit=1000)
            recommendation = next((r for r in recommendations if r['id'] == rec_id), None)

            if not recommendation:
                return jinja_template.render_template("fragments/error.html", message="Recommendation not found")

            # Return trade form pre-filled with ticker
            return jinja_template.render_template("fragments/trade_form.html",
                ticker=recommendation['ticker'],
                recommendation_id=rec_id,
                today=str(date.today()))

        except Exception as e:
            print(f"Error accepting recommendation: {e}")
            return jinja_template.render_template("fragments/error.html", message="Failed to accept recommendation")

    @app.post('/api/whatsapp/recommendations/:id/reject')
    async def reject_whatsapp_recommendation_endpoint(request: Request):
        """Reject a WhatsApp recommendation"""
        user = get_current_user(request)
        if not user:
            return jinja_template.render_template("fragments/error.html", message="Unauthorized")

        try:
            rec_id = int(request.path_params.get('id', '0'))
            if rec_id <= 0:
                return jinja_template.render_template("fragments/error.html", message="Invalid recommendation ID")

            # Update status
            success = auth_service.update_whatsapp_recommendation_status(rec_id, 'rejected')

            if not success:
                return jinja_template.render_template("fragments/error.html", message="Failed to reject recommendation")

            # Return updated recommendations list
            recommendations = auth_service.get_whatsapp_recommendations(limit=50)
            return jinja_template.render_template("fragments/whatsapp_recommendations.html",
                recommendations=recommendations)

        except Exception as e:
            print(f"Error rejecting recommendation: {e}")
            return jinja_template.render_template("fragments/error.html", message="Failed to reject recommendation")

    @app.post('/api/whatsapp/message')
    async def receive_whatsapp_message(request: Request):
        """Receive WhatsApp messages and extract stock recommendations"""
        import json

        try:
            # Parse JSON body
            if isinstance(request.body, bytes):
                body_str = request.body.decode('utf-8')
            else:
                body_str = request.body

            data = json.loads(body_str)
            tickers = data.get('tickers', [])
            from_sender = data.get('from', '')
            chat_name = data.get('chatName', '')
            message = data.get('message', '')
            timestamp = data.get('timestamp', '')

            if not tickers or not from_sender:
                return Response(
                    status_code=400,
                    description='{"error": "Missing required fields"}',
                    headers={"Content-Type": "application/json"}
                )

            saved_count = 0
            # Process each ticker
            for ticker in tickers:
                try:
                    # Get stock data from Polygon API
                    stock_data = stock_service.get_stock_data([ticker])

                    if stock_data:
                        stock = stock_data[0]
                        success = auth_service.save_whatsapp_recommendation(
                            ticker=ticker,
                            company_name=stock.company_name,
                            price=stock.price,
                            change_percent=stock.change_percent,
                            from_sender=from_sender,
                            chat_name=chat_name,
                            original_message=message,
                            received_at=timestamp
                        )
                        if success:
                            saved_count += 1
                            print(f"Saved WhatsApp recommendation: {ticker} from {from_sender}")
                    else:
                        # Save without stock data if API fails
                        success = auth_service.save_whatsapp_recommendation(
                            ticker=ticker,
                            company_name=None,
                            price=None,
                            change_percent=None,
                            from_sender=from_sender,
                            chat_name=chat_name,
                            original_message=message,
                            received_at=timestamp
                        )
                        if success:
                            saved_count += 1

                except Exception as e:
                    print(f"Error processing ticker {ticker}: {e}")
                    continue

            return Response(
                status_code=200,
                description=json.dumps({"success": True, "saved": saved_count, "total": len(tickers)}),
                headers={"Content-Type": "application/json"}
            )

        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Invalid WhatsApp message format: {e}")
            return Response(
                status_code=400,
                description='{"error": "Invalid request format"}',
                headers={"Content-Type": "application/json"}
            )

    @app.get('/api/whatsapp/recommendations')
    async def get_whatsapp_recommendations_fragment(request: Request):
        """Get recent WhatsApp recommendations as HTML fragment"""
        user = get_current_user(request)
        if not user:
            return jinja_template.render_template("fragments/error.html", message="Unauthorized")

        try:
            limit = int(request.query_params.get('limit', '20'))
            recommendations = auth_service.get_whatsapp_recommendations(limit)

            return jinja_template.render_template("fragments/whatsapp_recommendations.html", recommendations=recommendations)
        except Exception as e:
            print(f"Error getting WhatsApp recommendations: {e}")
            return jinja_template.render_template("fragments/error.html", message="Failed to load WhatsApp recommendations")

    return app
