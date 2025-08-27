#!/usr/bin/env python3
"""
Development server for Stock Agent
Takes advantage of Robyn's development mode features
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
from stock_agent.web import create_web_app


def main():
    """Run the development server with hot reloading and dev features"""

    # Load development environment variables
    env_path = project_root / '.dev.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️  Warning: {env_path} not found, using system environment")

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
        )
    except KeyboardInterrupt:
        print("\n👋 Development server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
