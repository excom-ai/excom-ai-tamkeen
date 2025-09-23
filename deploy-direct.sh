#!/bin/bash

# Direct deployment script for Excom AI to Google Cloud Run
# Uses gcloud to push local Docker image directly to Artifact Registry
# Usage: ./deploy-direct.sh [project-id] [region]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parameters
PROJECT_ID=${1:-"singular-dev"}
REGION=${2:-"us-central1"}
SERVICE_NAME="excom-ai"
LOCAL_IMAGE="excom-ai:latest"
REMOTE_IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/${SERVICE_NAME}:latest"

echo -e "${GREEN}🚀 Direct deployment of Excom AI to Google Cloud Run${NC}"
echo -e "${YELLOW}Project: $PROJECT_ID${NC}"
echo -e "${YELLOW}Region: $REGION${NC}"
echo ""

# Set the GCP project
echo -e "${GREEN}1. Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Configure Docker to use gcloud for Artifact Registry
echo -e "${GREEN}2. Configuring Docker authentication...${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Tag the local image for Artifact Registry
echo -e "${GREEN}3. Tagging image for Artifact Registry...${NC}"
docker tag ${LOCAL_IMAGE} ${REMOTE_IMAGE}

# Push to Artifact Registry
echo -e "${GREEN}4. Pushing to Artifact Registry...${NC}"
docker push ${REMOTE_IMAGE}

# Deploy to Cloud Run
echo -e "${GREEN}5. Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image ${REMOTE_IMAGE} \
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
echo -e "${GREEN}6. Getting service information...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}Service URL: $SERVICE_URL${NC}"
echo ""
echo -e "${YELLOW}⚠️  Important next steps:${NC}"
echo "1. Update your Azure AD app registration:"
echo "   - Add redirect URI: $SERVICE_URL"
echo ""
echo -e "${GREEN}🎉 Your application is now live at: $SERVICE_URL${NC}"