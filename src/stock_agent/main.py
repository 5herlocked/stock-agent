import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from .web import create_web_app

def main():
    """Run the production Stock Agent server"""

    # Load environment variables (check multiple locations)
    env_files = ['.env', '.dev.env', '.prod.env']
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(dotenv_path=env_file)
            print(f"Loaded environment from {env_file}")
            break
    else:
        print("No environment file found, using system environment")

    # Create and start web application
    try:
        app = create_web_app()

        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', '8080'))

        print(f"Starting Stock Agent server on {host}:{port}")
        app.start(host=host, port=port)

    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
