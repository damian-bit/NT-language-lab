FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
# Usar --no-cache-dir para reducir tamaño de imagen
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY app/ ./app/
COPY scripts/ ./scripts/

# Copiar datos y base de datos persistente (necesario para HF Spaces)
COPY data/ ./data/
COPY chroma_db/ ./chroma_db/

# Hugging Face Spaces usa el puerto 7860; en local usamos 8501 por defecto
ENV PORT=8501
EXPOSE 7860

# Variables de entorno por defecto (llama.cpp en el host)
ENV LLM_BASE_URL=http://host.docker.internal:8080
ENV LLM_MODEL="Phi-3 Mini Instruct"
ENV CHROMA_DB_PATH=/app/chroma_db
ENV PYTHONPATH=/app
ENV DISABLE_LLM=1

# PORT=7860 lo inyecta Hugging Face; en local queda 8501
CMD ["sh", "-c", "streamlit run app/main.py --server.port=${PORT} --server.address=0.0.0.0"]
