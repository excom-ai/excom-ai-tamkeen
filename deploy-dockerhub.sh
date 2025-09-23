#!/bin/bash

# Deployment script for Excom AI using DockerHub
# Usage: ./deploy-dockerhub.sh [dockerhub-username] [project-id] [region]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parameters
DOCKERHUB_USER=${1:-"your-dockerhub-username"}
PROJECT_ID=${2:-"singular-dev"}
REGION=${3:-"us-central1"}
SERVICE_NAME="excom-ai"
IMAGE_NAME="excom-ai"

echo -e "${GREEN}🚀 Deploying Excom AI via DockerHub to Google Cloud Run${NC}"
echo -e "${YELLOW}DockerHub User: $DOCKERHUB_USER${NC}"
echo -e "${YELLOW}Project: $PROJECT_ID${NC}"
echo -e "${YELLOW}Region: $REGION${NC}"
echo ""

# Tag the image for DockerHub
echo -e "${GREEN}1. Tagging image for DockerHub...${NC}"
docker tag ${IMAGE_NAME}:latest ${DOCKERHUB_USER}/${IMAGE_NAME}:latest
docker tag ${IMAGE_NAME}:latest ${DOCKERHUB_USER}/${IMAGE_NAME}:$(date +%Y%m%d-%H%M%S)

# Push to DockerHub
echo -e "${GREEN}2. Pushing to DockerHub...${NC}"
echo "Please make sure you're logged in to DockerHub (docker login)"
docker push ${DOCKERHUB_USER}/${IMAGE_NAME}:latest
docker push ${DOCKERHUB_USER}/${IMAGE_NAME}:$(date +%Y%m%d-%H%M%S)

# Set the GCP project
echo -e "${GREEN}3. Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Deploy to Cloud Run
echo -e "${GREEN}4. Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image docker.io/${DOCKERHUB_USER}/${IMAGE_NAME}:latest \
    --platform managed \
    --region $REGION \
    --port 8000 \
    --allow-unauthenticated \
    --min-instances 1 \
    --max-instances 100 \
    --memory 1Gi \
    --cpu 1 \
    --set-secrets ANTHROPIC_API_KEY=anthropic-api-key:latest \
    --set-secrets JIRA_API_TOKEN=jira-api-token:latest \
    --set-secrets JIRA_EMAIL=jira-email:latest \
    --set-secrets JIRA_SERVER=jira-server:latest \
    --set-secrets FRESHSERVICE_DOMAIN=freshservice-domain:latest \
    --set-secrets FRESHSERVICE_API_KEY=freshservice-api-key:latest \
    --set-env-vars "JIRA_JQL=PROJECT = \"DMD\" AND type = epic" \
    --set-env-vars "LANGCHAIN_TRACING_V2=false"

# Get the service URL
echo -e "${GREEN}5. Getting service information...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}Service URL: $SERVICE_URL${NC}"
echo ""
echo -e "${YELLOW}⚠️  Important next steps:${NC}"
echo "1. Update your Azure AD app registration:"
echo "   - Add redirect URI: $SERVICE_URL"
echo "2. Update the React app environment if needed"
echo ""
echo -e "${GREEN}🎉 Your application is now live at: $SERVICE_URL${NC}"