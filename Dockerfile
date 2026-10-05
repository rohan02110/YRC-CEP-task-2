# Stage 1: Build and Obfuscate Frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Runtime
FROM python:3.12-slim AS runner

# Create non-root user
RUN groupadd -g 10001 ctfgroup && \
    useradd -u 10001 -g ctfgroup -s /sbin/nologin -d /app appuser

WORKDIR /app

# Install dependencies
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir fastapi uvicorn pydantic pyyaml

# Copy backend application and assets
COPY backend/app/ ./backend/app/
COPY config/ ./config/
COPY tools/ ./tools/
COPY public_artifacts/ ./public_artifacts/

# Copy built frontend assets from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Setup data directory for SQLite with appropriate permissions
RUN mkdir -p /data && chown -R appuser:ctfgroup /data /app

ENV PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/data/chakravyuha.db \
    PUBLIC_ARTIFACTS_PATH=/app/public_artifacts \
    PHRASES_FILE=/app/tools/phrases_sanskrit.txt \
    FRONTEND_DIST_PATH=/app/frontend/dist

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/robots.txt')" || exit 1

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
