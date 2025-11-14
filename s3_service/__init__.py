"""
MinIO S3 Service Package
Local module for MinIO operations - DO NOT shadow the PyPI minio package
"""

# This package intentionally does NOT re-export PyPI minio classes
# to avoid import confusion. Use minio.minio_service for MinIO operations.
