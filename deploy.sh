#!/bin/bash

# Deployment script for Excom AI to Google Cloud Run
# Usage: ./deploy.sh [project-id] [region]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID=${1:-"your-gcp-project-id"}
REGION=${2:-"us-central1"}
SERVICE_NAME="excom-ai"

echo -e "${GREEN}🚀 Deploying Excom AI to Google Cloud Run${NC}"
echo -e "${YELLOW}Project: $PROJECT_ID${NC}"
echo -e "${YELLOW}Region: $REGION${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set the project
echo -e "${GREEN}1. Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${GREEN}2. Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Create secrets if they don't exist
echo -e "${GREEN}3. Setting up secrets in Secret Manager...${NC}"
echo -e "${YELLOW}Please ensure you have created the following secrets in Secret Manager:${NC}"
echo "  - anthropic-api-key"
echo "  - jira-api-token"
echo "  - jira-email"
echo "  - jira-server"
echo "  - freshservice-domain"
echo "  - freshservice-api-key"
echo ""
read -p "Have you created all secrets? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Please create the secrets first using:${NC}"
    echo "echo -n 'YOUR_SECRET_VALUE' | gcloud secrets create SECRET_NAME --data-file=-"
    exit 1
fi

# Get Azure AD configuration
echo -e "${GREEN}4. Azure AD Configuration${NC}"
read -p "Enter your Azure Client ID: " AZURE_CLIENT_ID
read -p "Enter your Azure Tenant ID: " AZURE_TENANT_ID

# Build and deploy using Cloud Build
echo -e "${GREEN}5. Building and deploying with Cloud Build...${NC}"

# Get the Cloud Run service URL (if it exists)
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)' 2>/dev/null || echo "")

if [ -z "$SERVICE_URL" ]; then
    # First deployment - use placeholder URL
    echo -e "${YELLOW}First deployment detected. Using placeholder URL.${NC}"
    REDIRECT_URI="https://$SERVICE_NAME-PROJECTHASH-$REGION.run.app"
else
    # Subsequent deployment - use actual URL
    echo -e "${GREEN}Using existing service URL: $SERVICE_URL${NC}"
    REDIRECT_URI=$SERVICE_URL
fi

# Submit the build
gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions=_AZURE_CLIENT_ID="$AZURE_CLIENT_ID",_AZURE_TENANT_ID="$AZURE_TENANT_ID",_REDIRECT_URI="$REDIRECT_URI",_REGION="$REGION"

# Get the actual service URL after deployment
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
echo "2. If this was your first deployment, redeploy with the correct URL:"
echo "   ./deploy.sh $PROJECT_ID $REGION"
echo ""
echo -e "${GREEN}🎉 Your application is now live at: $SERVICE_URL${NC}"