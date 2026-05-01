#!/bin/sh
set -e

# Environment defaults
# export LISTEN_PORT="${LISTEN_PORT:-80}"
# export BACKEND_HOST="${BACKEND_HOST:-http://mpcautofill-backend:8000}"
# export BACKEND_TIMEOUT="${BACKEND_TIMEOUT:-600}"
# export BACKEND_PUBLIC_URL="${BACKEND_PUBLIC_URL:-http://localhost:8000}"
# export IMAGE_BUCKET_URL="${IMAGE_BUCKET_URL:-''}"
# export IMAGE_WORKER_URL="${IMAGE_WORKER_URL:-''}"

# Configure Nextjs: Add environment variables
echo "Configuring Nextjs ..."
# Todo: Use templates to fill in .env.local?
npm ci
npm install -g npx
npx next build
cp -a out/. /usr/share/nginx/html/

# Configure Nginx: Remove default, add custom nginx.conf
echo "Configuring Nginx ..."
# envsubst '$LISTEN_PORT,$BACKEND_HOST,$BACKEND_TIMEOUT' < /docker/nginx.conf.template  > /etc/nginx/conf.d/nginx.conf
# Todo: Use templates to fill in envs

# Start Nginx in the foreground
exec nginx -g 'daemon off;'
