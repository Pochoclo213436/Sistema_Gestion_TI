FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema (para psycopg2, asyncpg, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY services/reportes_service/requirements.txt .
RUN pip install --no-cache-dir -r services/reportes_service/requirements.txt

# Copiar todo el código del servicio
COPY services/reportes_service .

# Entrypoint (si aplica)
COPY services/reportes_service/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000

CMD ["bash", "-c", "/usr/local/bin/entrypoint.sh ${PORT}"]
