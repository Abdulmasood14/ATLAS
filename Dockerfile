# --- STAGE 1: Build Frontend ---
FROM node:18-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
# Set production environment
ENV NODE_ENV=production
RUN npm run build

# --- STAGE 2: Build Backend & Final Image ---
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    procps \
    supervisor \
    postgresql \
    postgresql-contrib \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -L https://ollama.com/install.sh | sh

WORKDIR /app

# Setup PostgreSQL
USER postgres
RUN /etc/init.d/postgresql start && \
    psql --command "CREATE USER rag_user WITH SUPERUSER PASSWORD 'rag_password';" && \
    createdb -O rag_user financial_rag && \
    psql -d financial_rag --command "CREATE EXTENSION IF NOT EXISTS vector;"
USER root

# Install Backend Dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Add supervisor for process management
RUN pip install supervisor

# Copy App Content
COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/node_modules ./frontend/node_modules
COPY --from=frontend-builder /app/frontend/package.json ./frontend/package.json

# Copy Configuration Files
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Environment Variables
ENV DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/financial_rag
ENV OLLAMA_BASE_URL=http://localhost:11434
ENV PORT=7860

# Next.js Public URL (Hugging Face default port is 7860)
EXPOSE 7860

CMD ["/app/start.sh"]
