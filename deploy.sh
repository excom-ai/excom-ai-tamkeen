#!/bin/bash

# Exit on any error
set -e

# Configuration
DOCKER_HUB_USERNAME="larnholt"
IMAGE_NAME="excom-ai-tamkeen"
TAG="latest"
GCP_PROJECT_ID="singular-dev"
GCP_REGION="me-central1"
GCP_SERVICE_NAME="excom-ai-tamkeen"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting deployment process...${NC}"

# Build Docker image for Linux AMD64 (same as GCP Cloud Run)
echo -e "${YELLOW}Building Docker image for Linux AMD64...${NC}"
docker buildx build --platform linux/amd64 -t ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${TAG} .

# Tag the image
echo -e "${YELLOW}Tagging image...${NC}"
docker tag ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${TAG} ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${TAG}

# Login to Docker Hub
echo -e "${YELLOW}Logging in to Docker Hub...${NC}"
echo -e "${YELLOW}Please enter your Docker Hub credentials:${NC}"
docker login

# Push to Docker Hub
echo -e "${YELLOW}Pushing image to Docker Hub...${NC}"
docker push ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${TAG}

# Deploy to Cloud Run from Docker Hub
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy ${GCP_SERVICE_NAME} \
  --image docker.io/${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${TAG} \
  --platform managed \
  --region ${GCP_REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 100 \
  --port 8000 \
  --project ${GCP_PROJECT_ID}

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}Service URL: https://${GCP_SERVICE_NAME}-${GCP_PROJECT_ID}-${GCP_REGION}.a.run.app${NC}"