# backend/app/clients/rustfs_client.py
import logging
import boto3
from botocore.client import Config

logger = logging.getLogger("RustFS_Client")

def get_rustfs_client():
    logger.info("RustFS (MinIO/S3) istemcisi başlatılıyor...")
    # S3 uyumlu RustFS sunucumuzun ayarları
    s3_client = boto3.client(
        's3',
        endpoint_url='http://localhost:9000',
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin',
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )
    return s3_client