#!/bin/bash

# Ensure log directory exists
mkdir -p /var/log/postgresql
chown postgres:postgres /var/log/postgresql

# 1. Initialize PostgreSQL Data Dir if empty
if [ ! -s /var/lib/postgresql/15/main/PG_VERSION ]; then
    mkdir -p /var/lib/postgresql/15/main
    chown -R postgres:postgres /var/lib/postgresql/15/main
    su - postgres -c "/usr/lib/postgresql/15/bin/initdb -D /var/lib/postgresql/15/main"
fi

# 2. Start PostgreSQL to setup DB
echo "Starting PostgreSQL for initialization..."
su - postgres -c "/usr/lib/postgresql/15/bin/pg_ctl -D /var/lib/postgresql/15/main -l /var/log/postgresql/initialization.log start"

# Wait for PG
until pg_isready -h localhost -p 5432; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

# Create user/db and run migrations if needed
su - postgres -c "psql --command \"CREATE USER rag_user WITH SUPERUSER PASSWORD 'rag_password';\" || true"
su - postgres -c "createdb -O rag_user financial_rag || true"
su - postgres -c "psql -d financial_rag --command \"CREATE EXTENSION IF NOT EXISTS vector;\""
su - postgres -c "psql -d financial_rag -f /app/backend/database/migrations.sql"

# Stop temporary PG
su - postgres -c "/usr/lib/postgresql/15/bin/pg_ctl -D /var/lib/postgresql/15/main stop"

# 3. Start Ollama and Pull Models
echo "Starting Ollama to pull models..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama
until curl -s http://localhost:11434/api/tags > /dev/null; do
  echo "Waiting for Ollama..."
  sleep 5
done

echo "Pulling phi4:14b..."
ollama pull phi4:14b
echo "Pulling nomic-embed-text..."
ollama pull nomic-embed-text

# Kill temporary Ollama
kill $OLLAMA_PID

# 4. Hand over to Supervisor
echo "Initialization complete. Starting Supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
