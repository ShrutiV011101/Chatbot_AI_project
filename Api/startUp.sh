#!/bin/bash

# Check and install Playwright system dependencies and browsers if missing
echo "Checking Playwright dependencies and browsers..."

if [ ! -d "/root/.cache/ms-playwright" ]; then
    echo "Installing Playwright system dependencies..."
    playwright install-deps
    echo "Installing Playwright browsers..."
    playwright install
else
    echo "Playwright dependencies and browsers already installed."
fi

echo "Running Alembic migrations..."
# python -m alembic upgrade head

# echo "Installing spacy model..."
# python -m spacy download en_core_web_sm


# Start the Gunicorn server
echo "Starting Gunicorn server..."
gunicorn main:app \
    --workers 12 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --forwarded-allow-ips=* \
    --log-level debug \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -