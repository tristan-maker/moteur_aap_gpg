FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# Installation de Node.js et npm requis pour le MCP H Company (npx)
RUN apt-get update && apt-get install -y \
    curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
