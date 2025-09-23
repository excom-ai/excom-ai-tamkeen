# 🚀 Google Cloud Run Deployment Guide

This guide explains how to deploy the Excom AI application as a single service to Google Cloud Run.

## Architecture

- **Single Container**: FastAPI backend serves both API and React frontend
- **Port**: 8000
- **Static Files**: React build served by FastAPI
- **No CORS Issues**: Everything on the same domain

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and configured
3. **Project created** in Google Cloud Console
4. **APIs enabled**: Cloud Run, Cloud Build, Secret Manager, Container Registry

## Setup Steps

### 1. Install Google Cloud SDK

```bash
# macOS
brew install google-cloud-sdk

# Or download from
https://cloud.google.com/sdk/docs/install
```

### 2. Authenticate and Set Project

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 3. Enable Required APIs

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 4. Create Secrets in Secret Manager

```bash
# Create each secret
echo -n 'your-anthropic-api-key' | gcloud secrets create anthropic-api-key --data-file=-
echo -n 'your-jira-token' | gcloud secrets create jira-api-token --data-file=-
echo -n 'your-jira-email' | gcloud secrets create jira-email --data-file=-
echo -n 'https://your.atlassian.net/' | gcloud secrets create jira-server --data-file=-
echo -n 'your.freshservice.com' | gcloud secrets create freshservice-domain --data-file=-
echo -n 'your-freshservice-key' | gcloud secrets create freshservice-api-key --data-file=-
```

### 5. Grant Cloud Run Access to Secrets

```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')

# Grant access to each secret
for SECRET in anthropic-api-key jira-api-token jira-email jira-server freshservice-domain freshservice-api-key; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

## Deployment

### Option 1: Using the Deploy Script (Recommended)

```bash
# Make the script executable
chmod +x deploy.sh

# Run the deployment
./deploy.sh YOUR_PROJECT_ID us-central1
```

The script will:
1. Set up your GCP project
2. Enable required APIs
3. Prompt for Azure AD configuration
4. Build and deploy the application
5. Output the service URL

### Option 2: Manual Deployment

```bash
# Set your variables
export PROJECT_ID="your-project-id"
export AZURE_CLIENT_ID="your-azure-client-id"
export AZURE_TENANT_ID="your-azure-tenant-id"

# Submit the build
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_AZURE_CLIENT_ID="$AZURE_CLIENT_ID",_AZURE_TENANT_ID="$AZURE_TENANT_ID",_REDIRECT_URI="https://excom-ai-$PROJECT_ID.run.app"

# Get the service URL
gcloud run services describe excom-ai --region=us-central1 --format='value(status.url)'
```

## Post-Deployment Configuration

### 1. Update Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to Azure Active Directory > App registrations
3. Select your app
4. Go to Authentication
5. Add your Cloud Run URL as a redirect URI:
   - Type: Single-page application
   - URI: `https://your-service-xxxxx-uc.a.run.app`

### 2. Redeploy with Correct URL (First Deployment Only)

After the first deployment, you'll get the actual Cloud Run URL. Update and redeploy:

```bash
# The deploy script handles this automatically on second run
./deploy.sh YOUR_PROJECT_ID us-central1
```

## Testing

1. **Visit your Cloud Run URL**: `https://excom-ai-xxxxx-uc.a.run.app`
2. **Sign in** with your Microsoft account
3. **Test the chat** functionality

## Monitoring

View logs and metrics:

```bash
# View logs
gcloud run services logs read excom-ai --region=us-central1

# View service details
gcloud run services describe excom-ai --region=us-central1

# Stream logs
gcloud alpha run services logs tail excom-ai --region=us-central1
```

## Updating the Application

To deploy updates:

```bash
# Just run the deploy script again
./deploy.sh YOUR_PROJECT_ID us-central1
```

## Custom Domain (Optional)

To use a custom domain:

```bash
gcloud run domain-mappings create --service=excom-ai --domain=your-domain.com --region=us-central1
```

Then update your DNS records as instructed by Cloud Run.

## Troubleshooting

### Authentication Issues
- Ensure Azure AD redirect URI matches Cloud Run URL exactly
- Check that Azure AD app is configured as "Single-page application"

### API Issues
- Check secrets are properly configured: `gcloud secrets list`
- View logs: `gcloud run services logs read excom-ai --region=us-central1`

### Build Failures
- Check Cloud Build logs: `gcloud builds list --limit=5`
- Ensure all files are present and not in `.gcloudignore`

## Cost Optimization

- **Set minimum instances to 0** for development (may have cold starts)
- **Use Cloud Scheduler** to warm up the instance periodically
- **Monitor usage** in Cloud Console

## Security Best Practices

1. **Never commit secrets** to git
2. **Use Secret Manager** for all sensitive data
3. **Enable Cloud Armor** for DDoS protection
4. **Set up Identity-Aware Proxy** for additional authentication layer
5. **Regular security audits** using Cloud Security Command Center

## Support

For issues or questions:
1. Check Cloud Run logs
2. Review Cloud Build history
3. Verify secret configurations
4. Ensure Azure AD settings are correct