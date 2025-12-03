#!/bin/bash

echo "Ejecutando migraciones..."
python init_db.py

echo "Iniciando API Gateway..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}