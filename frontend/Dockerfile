FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema (streamlit + libs comunes)
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Render asigna el valor de $PORT automáticamente
CMD ["bash", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT}"]