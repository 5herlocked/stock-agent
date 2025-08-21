import os
from dotenv import load_dotenv
from .flat_downloader import FlatFileDownloader

from robyn import Robyn, Request, serve_file

from robyn.templating import JinjaTemplate
import pathlib
from .notification_service import NotificationService

current_file_path = pathlib.Path(__file__).parent.resolve()
JINJA_TEMPLATE = JinjaTemplate(os.path.join(current_file_path, "templates"))

app = Robyn(__file__)
# app.serve_directory("/static", os.path.join(current_file_path, "static"))

context = {
    "framework": "Robyn",
    "templating_engine": "Jinja2"
}

@app.get("/firebase-messaging-sw.js")
async def firebase_service_worker(request: Request):
    return serve_file(os.path.join(current_file_path, "static", "firebase-messaging-sw.js"))

@app.get("/")
async def index(request: Request):
   template = JINJA_TEMPLATE.render_template("index.html", **context)
   return template

@app.get('/api/vapid-public-key')
def get_vapid_public_key():
    return {'vapidPublicKey': os.getenv('FIREBASE_VAPID_PUBLIC_KEY')}

@app.get('/api/firebase-config')
async def get_firebase_config():
    config = {
        "apiKey": os.environ.get("FIREBASE_API_KEY"),
        "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
        "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.environ.get("FIREBASE_APP_ID")
    }
    return config

@app.get('/report')
async def todays_report(request: Request):
    template = JINJA_TEMPLATE.render_template("report.html", **context)
    return template


def main():
    # Load environment variables
    load_dotenv(dotenv_path='.dev.env')

    # # Create downloader using environment configuration
    # downloader = FlatFileDownloader()

    # # List files
    # files = downloader.list_files(prefix='us_stocks_sip', max_items=10)
    # print("Available files:", files)

    # # Download a file
    # if files:
    #     downloaded_file = downloader.download_file(files[0])
    #     print(f"Downloaded: {downloaded_file}")

    app.start(host='127.0.0.1', port=8080)

if __name__ == "__main__":
    main()
