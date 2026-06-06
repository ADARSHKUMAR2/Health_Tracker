import os
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from dotenv import load_dotenv

# Initialize dotenv safely
load_dotenv()

# Static file paths are fine globally
LOCAL_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "health_data.db"
OBJECT_NAME = "health_data.db"

def get_s3_client():
    """Initializes the S3 client using environment variables."""
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )

def download_db_from_s3():
    """Pulls the latest database version from AWS on server startup."""
    # 🔗 Moved inside the function so it reads dynamically on call
    bucket_name = os.getenv("AWS_BUCKET_NAME")
    
    print(f"☁️ Attempting to pull database from S3 bucket: {bucket_name}...")
    
    if not bucket_name:
        raise ValueError("❌ AWS_BUCKET_NAME is missing! Ensure your .env file contains this key.")

    s3 = get_s3_client()
    LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        s3.download_file(bucket_name, OBJECT_NAME, str(LOCAL_DB_PATH))
        print("✅ Fresh database synchronized locally.")
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("ℹ️ No existing database found in S3 bucket. Starting with a clean canvas.")
        else:
            print(f"❌ Critical S3 download error: {e}")
            raise e

def upload_db_to_s3():
    """Pushes the updated local database back up to AWS after an ingestion run."""
    # 🔗 Moved inside the function so it reads dynamically on call
    bucket_name = os.getenv("AWS_BUCKET_NAME")
    
    if not bucket_name:
        raise ValueError("❌ AWS_BUCKET_NAME is missing! Ensure your .env file contains this key.")
        
    if not LOCAL_DB_PATH.exists():
        print("❌ Cannot upload: Local database file does not exist.")
        return
        
    s3 = get_s3_client()
    try:
        print(f"☁️ Syncing updates to AWS S3 bucket: {bucket_name}...")
        s3.upload_file(str(LOCAL_DB_PATH), bucket_name, OBJECT_NAME)
        print("🚀 Cloud synchronization complete. Your data is safely backed up!")
    except ClientError as e:
        print(f"❌ Critical S3 upload failure: {e}")