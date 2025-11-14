#!/bin/bash

# MinIO Initialization Script
# This script automatically creates the required bucket when MinIO starts

set -e

# Start MinIO in the background
echo "🚀 Starting MinIO server..."
minio server /minio_data --console-address :9001 &

# Store the MinIO process ID
MINIO_PID=$!

# Wait for MinIO to be ready
echo "⏳ Waiting for MinIO to be ready..."
MAX_RETRIES=30
RETRIES=0

while [ $RETRIES -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
        echo "✅ MinIO is ready!"
        break
    fi
    RETRIES=$((RETRIES + 1))
    echo "⏳ Waiting... ($RETRIES/$MAX_RETRIES)"
    sleep 1
done

if [ $RETRIES -eq $MAX_RETRIES ]; then
    echo "❌ MinIO failed to start after $MAX_RETRIES attempts"
    exit 1
fi

# Install mc (MinIO client)
echo "📦 Installing MinIO client..."
wget -q https://dl.min.io/client/mc/release/linux-amd64/mc -O /usr/local/bin/mc
chmod +x /usr/local/bin/mc

# Configure MinIO client alias
echo "⚙️ Configuring MinIO client..."
/usr/local/bin/mc alias set myminio http://localhost:9000 minioadmin minioadmin --api S3v4 > /dev/null 2>&1 || true

# Create bucket if it doesn't exist
echo "📦 Creating bucket 'poi-images'..."
if /usr/local/bin/mc ls myminio/poi-images > /dev/null 2>&1; then
    echo "✅ Bucket 'poi-images' already exists"
else
    /usr/local/bin/mc mb myminio/poi-images
    echo "✅ Bucket 'poi-images' created successfully"
fi

# Wait for the MinIO process
echo "✅ MinIO initialization complete!"
wait $MINIO_PID
