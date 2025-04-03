#!/bin/sh
set -e

echo "Content of /usr/share/nginx/html:"
ls -la /usr/share/nginx/html/

# If no index.html exists, create a simple one
if [ ! -f /usr/share/nginx/html/index.html ]; then
  echo "Creating fallback index.html..."
  echo "<html><head><title>Event Platform</title></head><body><h1>Event Platform</h1><p>Welcome to the Event Platform!</p></body></html>" > /usr/share/nginx/html/index.html
fi

echo "Starting nginx..."
exec nginx -g 'daemon off;' 