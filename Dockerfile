# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with legacy peer deps for React 19 compatibility
RUN npm install --legacy-peer-deps

# Accept build arguments for Azure AD configuration
ARG REACT_APP_AZURE_CLIENT_ID
ARG REACT_APP_AZURE_TENANT_ID
ARG REACT_APP_REDIRECT_URI

# Set environment variables for the React build
ENV REACT_APP_AZURE_CLIENT_ID=${REACT_APP_AZURE_CLIENT_ID}
ENV REACT_APP_AZURE_TENANT_ID=${REACT_APP_AZURE_TENANT_ID}
ENV REACT_APP_REDIRECT_URI=${REACT_APP_REDIRECT_URI}

# Copy source code
COPY public/ ./public/
COPY src/ ./src/

# Build the React app with the environment variables
RUN npm run build

# Stage 2: Python backend with React static files
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy React build from frontend stage
COPY --from=frontend-build /app/build ./static

# Expose port (Cloud Run will set PORT environment variable)
EXPOSE 8000

# Run the application - use PORT environment variable if set, otherwise 8000
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}