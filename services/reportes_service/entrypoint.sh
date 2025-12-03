#!/bin/bash
set -e

PORT=${1:-8000}

echo "Starting service on port $PORT..."

exec uvicorn main:app --host 0.0.0.0 --port $PORT