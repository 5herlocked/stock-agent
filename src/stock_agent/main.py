import os
from dotenv import load_dotenv
from stock_agent.flat_downloader import FlatFileDownloader

def main():
    # Load environment variables
    load_dotenv(dotenv_path='.dev.env')

    # Create downloader using environment configuration
    downloader = FlatFileDownloader()

    # List files
    files = downloader.list_files(prefix='us_stocks_sip', max_items=10)
    print("Available files:", files)

    # Download a file
    if files:
        downloaded_file = downloader.download_file(files[0])
        print(f"Downloaded: {downloaded_file}")

if __name__ == "__main__":
    main()
