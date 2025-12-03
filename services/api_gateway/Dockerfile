FROM python:3.11-slim

WORKDIR /app

# Dependencias necesarias para psycopg2, asyncpg, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código del API Gateway
COPY . .

# Copiar entrypoint.sh y dar permisos
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copiar la carpeta database si existe
COPY database /app/database

# Exponer puerto
EXPOSE 8000

# Comando de arranque
CMD ["bash", "-c", "/usr/local/bin/entrypoint.sh ${PORT}"]
