import os
import boto3
from typing import Optional

def upload_directory_to_s3(directory_path: str, bucket_name: str, prefix: Optional[str] = "") -> None:
    """
    Recursively uploads all files in 'directory_path' to the specified S3 bucket.
    
    Args:
        directory_path: Local directory path to upload
        bucket_name: Target S3 bucket name
        prefix: Optional S3 key prefix (folder path)
    
    Raises:
        FileNotFoundError: If directory_path doesn't exist
        boto3.exceptions.S3UploadFailedError: If S3 upload fails
    """
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
        
    s3_client = boto3.client("s3")
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, directory_path)
            s3_key = os.path.join(prefix, relative_path).replace("\\", "/")
            
            print(f"Uploading {local_path} to s3://{bucket_name}/{s3_key}")
            try:
                s3_client.upload_file(local_path, bucket_name, s3_key)
            except Exception as e:
                print(f"Failed to upload {local_path}: {str(e)}")

# Example usage:
if __name__ == "__main__":
    SOURCE_DIRECTORY = "/home/sagemaker-user/project/openai_bedrock_test/crewai_FM_and_portkey"
    # SOURCE_DIRECTORY = "D:/PhotonUser/Downloads/crewai-creditreport"
    TARGET_BUCKET = "aws-agent-poc-0033"
    S3_PREFIX = "crewai_and_portkey"
    # S3_PREFIX = "crewai-creditreport"
    
    upload_directory_to_s3(SOURCE_DIRECTORY, TARGET_BUCKET, S3_PREFIX)