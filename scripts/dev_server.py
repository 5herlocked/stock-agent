#!/usr/bin/env python3
"""
Development server for Stock Agent
Takes advantage of Robyn's development mode features
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
from stock_agent.web import create_web_app
from stock_agent.polygon import StockService


def main():
    """Run the development server with hot reloading and dev features"""

    # Load development environment variables
    env_path = project_root / '.dev.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️  Warning: {env_path} not found, using system environment")

    # Optional: Generate market summary (skip for faster dev startup)
    generate_summary = os.getenv('DEV_GENERATE_SUMMARY', 'false').lower() == 'true'

    if generate_summary:
        print("📊 Generating market summary...")
        try:
            stock_service = StockService()
            stock_service.generate_market_summary()
            print("✅ Market summary generated")
        except Exception as e:
            print(f"⚠️  Warning: Failed to generate market summary: {e}")
    else:
        print("⏩ Skipping market summary generation (set DEV_GENERATE_SUMMARY=true to enable)")

    # Create web application
    print("🚀 Creating web application...")
    app = create_web_app()

    # Development server configuration
    host = os.getenv('DEV_HOST', '127.0.0.1')
    port = int(os.getenv('DEV_PORT', '8080'))

    print(f"""
🔥 Starting development server...

   URL: http://{host}:{port}

   Features enabled:
   ✅ Hot reloading
   ✅ Debug mode
   ✅ Static file serving
   ✅ Service worker authentication

   Environment:
   📁 Project root: {project_root}
   🔧 Config file: {env_path}

   Press Ctrl+C to stop the server
   """)

    try:
        # Start server in development mode
        app.start(
            host=host,
            port=port,
            dev=True  # This enables Robyn's development mode with hot reloading
        )
    except KeyboardInterrupt:
        print("\n👋 Development server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
