import logging
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config
from dotenv import load_dotenv

# Çevresel değişkenlerin (.env) güvenli bir şekilde yüklendiğini garantiye alıyoruz
load_dotenv()

from app.configs.config import settings

logger = logging.getLogger("RustFS_Client")


class RustFSClient:
    """
    RustFS (MinIO/S3 uyumlu) Nesne Depolama İstemcisi.
    Belgelerin ham (orijinal) dosyalarını doğrudan RustFS bucket'ına yüklemek,
    indirmek ve silmek için Lazy Singleton deseni ile kullanılır.
    """

    _s3_client = None

    @classmethod
    def get_client(cls):
        """Boto3 S3 client örneğini lazy singleton olarak döner."""
        if cls._s3_client is None:
            logger.info("RustFS (S3) istemcisi başlatılıyor...")
            cls._s3_client = boto3.client(
                "s3",
                endpoint_url=settings.RUSTFS_ENDPOINT,
                aws_access_key_id=settings.RUSTFS_ACCESS_KEY,
                aws_secret_access_key=settings.RUSTFS_SECRET_KEY,
                config=Config(signature_version='s3v4'),
                region_name="us-east-1"
            )
        return cls._s3_client

    # --- YENİ EKLENEN DİNAMİK KOVA KONTROL FONKSİYONU ---
    @classmethod
    def initialize_all_buckets(cls):
        """
        Sistem ayağa kalktığında config.py içindeki adında 'BUCKET' geçen
        tüm ayarları dinamik olarak tarar ve eksik kovaları otomatik oluşturur.
        """
        # settings içindeki tüm değişkenleri tara, adında BUCKET geçenlerin değerini al
        buckets_to_check = [
            value for key, value in settings.__dict__.items()
            if "BUCKET" in key and isinstance(value, str)
        ]

        s3 = cls.get_client()
        for bucket in buckets_to_check:
            try:
                s3.head_bucket(Bucket=bucket)
            except ClientError:
                try:
                    s3.create_bucket(Bucket=bucket)
                    logger.info(f"[RustFS Data Lake] Yeni kova oluşturuldu: {bucket}")
                except Exception as e:
                    logger.error(f"[RustFS Error] {bucket} oluşturulurken hata: {e}")

    # ----------------------------------------------------

    @classmethod
    def ensure_bucket_exists(cls, bucket_name: str = None) -> str:
        """Bucket mevcut değilse oluşturur."""
        target_bucket = bucket_name or settings.RUSTFS_BUCKET_NAME
        s3 = cls.get_client()
        try:
            s3.head_bucket(Bucket=target_bucket)
        except ClientError:
            try:
                s3.create_bucket(Bucket=target_bucket)
                logger.info(f"[RustFS] '{target_bucket}' adında yeni bucket oluşturuldu.")
            except Exception as e:
                logger.error(f"[RustFS Error] Bucket oluşturulurken hata: {e}")
        return target_bucket

    @classmethod
    def upload_file(cls, file_bytes: bytes, object_name: str, bucket_name: str = None) -> str:
        """
        Ham dosya baytlarını doğrudan RustFS S3 bucket'ına yükler.
        Yüklenen nesnenin S3 nesne adını/yolunu döner.
        """
        target_bucket = cls.ensure_bucket_exists(bucket_name)
        s3 = cls.get_client()
        try:
            s3.put_object(
                Bucket=target_bucket,
                Key=object_name,
                Body=file_bytes
            )
            s3_url = f"{settings.RUSTFS_ENDPOINT}/{target_bucket}/{object_name}"
            logger.info(f"[RustFS] Dosya başarıyla yüklendi: {s3_url}")
            return object_name
        except Exception as e:
            logger.error(f"[RustFS Error] Dosya yüklenirken hata: {e}")
            raise e

    @classmethod
    def delete_file(cls, object_name: str, bucket_name: str = None) -> bool:
        """
        Belirtilen nesneyi RustFS S3 bucket'ından siler.
        """
        target_bucket = bucket_name or settings.RUSTFS_BUCKET_NAME
        s3 = cls.get_client()
        try:
            s3.delete_object(
                Bucket=target_bucket,
                Key=object_name
            )
            logger.info(f"[RustFS] Nesne silindi: {target_bucket}/{object_name}")
            return True
        except Exception as e:
            logger.error(f"[RustFS Error] Nesne silinirken hata: {e}")
            return False