# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend dependency manifests
COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps

# Copy frontend source code and build production bundle
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Application Runner
FROM python:3.10-slim AS runner
WORKDIR /app

# Configure Python environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend:/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend application, scripts, and ML artifacts
COPY backend/ ./backend/
COPY scripts/ ./scripts/
COPY scripts/synthetic_dataset.json ./scripts/synthetic_dataset.json

# Build verification step to guarantee synthetic dataset exists in runner stage
RUN test -f /app/scripts/synthetic_dataset.json && echo "Verified /app/scripts/synthetic_dataset.json exists in image"

# Copy built production frontend assets from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose default application port
EXPOSE 10000

# Launch FastAPI web application with uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
