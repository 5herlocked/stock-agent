from dotenv import load_dotenv
from .web import create_web_app

def main():
    load_dotenv(dotenv_path='.dev.env')
    
    app = create_web_app()
    app.start(host='127.0.0.1', port=8080)

if __name__ == "__main__":
    main()
