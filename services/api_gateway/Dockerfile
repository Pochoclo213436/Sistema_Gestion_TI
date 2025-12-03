FROM python:3.11-slim

WORKDIR /app

# Dependencias necesarias para psycopg2, asyncpg, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY database /app/database
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000

CMD ["bash", "-c", "/usr/local/bin/entrypoint.sh ${PORT}"]