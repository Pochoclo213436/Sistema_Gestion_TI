#!/bin/bash
echo "Esperando a que la base de datos esté disponible..."
/usr/local/bin/python /app/init_db.py
echo "Iniciando la aplicación..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
