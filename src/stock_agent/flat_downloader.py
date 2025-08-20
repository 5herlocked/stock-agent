import os
from typing import List, Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class FlatFileDownloader:
    """
    A class to handle downloading and listing Polygon.io flat files from S3
    """

    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        endpoint_url: str = 'https://files.polygon.io',
        bucket_name: str = 'flatfiles'
    ):
        """
        Initialize S3 client with configurable credentials and settings

        Args:
            access_key (Optional[str]): AWS access key ID
            secret_key (Optional[str]): AWS secret access key
            endpoint_url (str): Custom S3 endpoint URL
            bucket_name (str): S3 bucket name for flat files
        """
        # Use provided credentials or environment variables
        self.access_key = access_key or os.getenv('POLYGON_FLAT_ACCESS_KEY_ID')
        self.secret_key = secret_key or os.getenv('POLYGON_FLAT_SECRET_ACCESS_KEY')
        self.endpoint_url = endpoint_url
        self.bucket_name = bucket_name

        # Validate credentials
        if not (self.access_key and self.secret_key):
            raise ValueError("AWS credentials must be provided via arguments or environment variables")

        # Create S3 client
        session = boto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )
        self.s3_client = session.client(
            's3',
            endpoint_url=self.endpoint_url,
            config=Config(signature_version='s3v4')
        )

    def list_files(
        self,
        prefix: str = 'us_stocks_sip',
        max_items: Optional[int] = None
    ) -> List[str]:
        """
        List files in the specified S3 prefix

        Args:
            prefix (str): S3 prefix to list files under
            max_items (Optional[int]): Maximum number of items to return

        Returns:
            List[str]: List of file keys matching the prefix
        """
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            file_keys = []
            for page in pages:
                for obj in page.get('Contents', []):
                    file_keys.append(obj['Key'])
                    if max_items and len(file_keys) >= max_items:
                        return file_keys[:max_items]

            return file_keys

        except ClientError as e:
            print(f"Error listing files: {e}")
            return []

    def download_file(
        self,
        object_key: str,
        local_path: Optional[str] = None
    ) -> str:
        """
        Download a specific file from S3

        Args:
            object_key (str): Full S3 object key to download
            local_path (Optional[str]): Custom local file path.
                                        If None, uses filename from object key

        Returns:
            str: Path to the downloaded file
        """
        try:
            # If no local path provided, use the filename from object key
            if local_path is None:
                local_path = os.path.join('.', object_key.split('/')[-1])

            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path) or '.', exist_ok=True)

            # Download file
            self.s3_client.download_file(
                self.bucket_name,
                object_key,
                local_path
            )

            return local_path

        except ClientError as e:
            print(f"Error downloading file {object_key}: {e}")
            raise

def main():
    """
    Example usage of FlatFileDownloader
    """
    try:
        downloader = FlatFileDownloader()

        # List files
        files = downloader.list_files(max_items=10)
        print("Available files:", files)

        # Download first file
        if files:
            downloaded_file = downloader.download_file(files[0])
            print(f"Downloaded: {downloaded_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
