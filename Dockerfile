# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Run the FastAPI backend and serve frontend static assets
FROM python:3.11-slim
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY src/ ./src/

# Copy the built frontend static files from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist/

# Expose the service port
EXPOSE 8000

# Set environment variable so Python can find 'app' inside 'src'
ENV PYTHONPATH=/app/src

# Create database volume directory
RUN mkdir -p /app/data

# Run the FastAPI web application
CMD ["uvicorn", "app.web_main:app", "--host", "0.0.0.0", "--port", "8000"]
