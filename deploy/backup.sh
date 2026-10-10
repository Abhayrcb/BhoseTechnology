#!/usr/bin/env bash
# Nightly MongoDB backup. Optional S3 upload if S3_BUCKET is set (needs an EC2 IAM role with s3:PutObject).
# Cron (as the deploy user):  0 2 * * * cd /home/ubuntu/BhoseTechnology/deploy && ./backup.sh >> backup.log 2>&1
set -euo pipefail
cd "$(dirname "$0")"
set -a; . ./.env; set +a
mkdir -p backups
FILE="backups/mongo-$(date +%F).archive.gz"
docker compose exec -T mongo mongodump --username "${MONGO_USER:-bhose}" --password "$MONGO_PASSWORD" \
  --authenticationDatabase admin --db "${DB_NAME:-bhose_store}" --archive --gzip > "$FILE"
find backups -name 'mongo-*.archive.gz' -mtime +14 -delete
if [ -n "${S3_BUCKET:-}" ]; then aws s3 cp "$FILE" "s3://$S3_BUCKET/mongo/"; fi
echo "Backup saved: $FILE"
