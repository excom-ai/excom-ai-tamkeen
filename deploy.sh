#!/bin/bash

# ExCom AI Tamkeen - GCP Cloud Run Deployment Script
# Similar to ../mcp-tamkeen/deploy.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="singular-dev"
REGION="me-central1"
SERVICE_NAME="excom-ai-tamkeen"
REPOSITORY="excom-ai-tamkeen"
IMAGE_NAME="app"
IMAGE_TAG="latest"

# Build arguments for React frontend
REACT_APP_AZURE_CLIENT_ID="3f8e0863-88f4-4dde-b4cf-44728ce39ba7"
REACT_APP_AZURE_TENANT_ID="961673de-7f0e-40ff-af04-bf8853e979f2"
REACT_APP_REDIRECT_URI="https://excom-ai-tamkeen-150270395888.me-central1.run.app"
#REACT_APP_REDIRECT_URI=http://localhost:3000

# Full image path
FULL_IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "${BLUE}🚀 ExCom AI Tamkeen - GCP Deployment${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if gcloud is authenticated
echo -e "${YELLOW}🔐 Checking gcloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Not authenticated with gcloud. Please run 'gcloud auth login'${NC}"
    exit 1
fi

# Set the project
echo -e "${YELLOW}🎯 Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project $PROJECT_ID

# Check if Artifact Registry repository exists
echo -e "${YELLOW}📦 Checking Artifact Registry repository...${NC}"
if ! gcloud artifacts repositories describe $REPOSITORY --location=$REGION --format="value(name)" &>/dev/null; then
    echo -e "${YELLOW}📦 Creating Artifact Registry repository...${NC}"
    gcloud artifacts repositories create $REPOSITORY \
        --repository-format=docker \
        --location=$REGION \
        --description="ExCom AI Tamkeen container images"
fi

# Configure Docker for Artifact Registry
echo -e "${YELLOW}🔧 Configuring Docker for Artifact Registry...${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Build the Docker image with build arguments (force AMD64 for Cloud Run)
echo -e "${YELLOW}🏗️  Building Docker image for AMD64...${NC}"
docker build \
    --platform linux/amd64 \
    --build-arg REACT_APP_AZURE_CLIENT_ID=$REACT_APP_AZURE_CLIENT_ID \
    --build-arg REACT_APP_AZURE_TENANT_ID=$REACT_APP_AZURE_TENANT_ID \
    --build-arg REACT_APP_REDIRECT_URI=$REACT_APP_REDIRECT_URI \
    -t $FULL_IMAGE_PATH .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Push the image to Artifact Registry
echo -e "${YELLOW}📤 Pushing image to Artifact Registry...${NC}"
docker push $FULL_IMAGE_PATH

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker push failed${NC}"
    exit 1
fi

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image=$FULL_IMAGE_PATH \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --port=8000 \
    --memory=512Mi \
    --timeout=300 \
    --max-instances=10 \
    --concurrency=80

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Cloud Run deployment failed${NC}"
    exit 1
fi

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}📊 Monitor logs: gcloud run services logs read ${SERVICE_NAME} --region=${REGION}${NC}"

# Optional: Open the service in browser (uncomment if desired)
# echo -e "${BLUE}🌐 Opening service in browser...${NC}"
# open $SERVICE_URL

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}🎉 Deployment Complete!${NC}"