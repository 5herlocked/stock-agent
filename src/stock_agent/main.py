import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

from .web import create_web_app

def main():
    """Run the Stock Agent server"""

    # Parse command-line arguments (allow unknown args for Robyn CLI)
    parser = argparse.ArgumentParser(description='Stock Agent Server')
    parser.add_argument('--env',
                       choices=['dev', 'prod'],
                       default='dev',
                       help='Environment to run (dev or prod). Default: dev')
    args, unknown_args = parser.parse_known_args()

    # Pass unknown args back to sys.argv for Robyn to process
    sys.argv = [sys.argv[0]] + unknown_args

    # Load environment variables based on --env flag
    if args.env == 'dev':
        env_file = '.dev.env'
    else:
        env_file = '.prod.env'

    # Try to load the specified env file, fallback to .env
    if os.path.exists(env_file):
        load_dotenv(dotenv_path=env_file)
        print(f"Loaded environment from {env_file}")
    elif os.path.exists('.env'):
        load_dotenv(dotenv_path='.env')
        print(f"Loaded environment from .env (fallback)")
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
