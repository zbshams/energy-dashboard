# Google Cloud Run Deployment Guide

Deploy your Energy Dashboard to Google Cloud Run (free tier - no costs).

## Prerequisites

1. **Google Cloud Account** - Create one at [console.cloud.google.com](https://console.cloud.google.com)
2. **GitHub Account** - Create a repository for this project
3. **gcloud CLI** - Install from [cloud.google.com/sdk](https://cloud.google.com/sdk)

## Step 1: Set Up GitHub Repository

```bash
# Initialize git in your project directory
cd ~/Claude\ Cowork/energy-dashboard
git init
git add .
git commit -m "Initial Energy Dashboard commit"

# Create a new repository on GitHub (https://github.com/new)
# Then push your code
git remote add origin https://github.com/YOUR_USERNAME/energy-dashboard.git
git branch -M main
git push -u origin main
```

## Step 2: Create Google Cloud Project

```bash
# Set your Google Cloud project ID
export PROJECT_ID="energy-dashboard-$(date +%s)"

# Create the project
gcloud projects create $PROJECT_ID

# Set it as your active project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

## Step 3: Deploy to Cloud Run

**Option A: Direct deployment (fastest)**

```bash
cd ~/Claude\ Cowork/energy-dashboard

gcloud run deploy energy-dashboard \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="API_KEY_ZUBE=YOUR_ZUBE_KEY,API_KEY_ASSISTANT=YOUR_ASSISTANT_KEY"
```

**Option B: Using Cloud Build (recommended for CI/CD)**

```bash
# Push code to GitHub first, then:
gcloud builds submit --config cloudbuild.yaml \
  https://github.com/YOUR_USERNAME/energy-dashboard.git
```

## Step 4: Configure Environment Variables

Once deployed, update the secrets:

```bash
gcloud run services update energy-dashboard \
  --update-env-vars=API_KEY_ZUBE=your-unique-zube-key \
  --region=us-central1
```

Or through the Cloud Console:
1. Go to Cloud Run → Services → energy-dashboard
2. Click "Edit & Deploy New Revision"
3. Add environment variables under "Runtime settings"
4. Click "Deploy"

## Step 5: Access Your Dashboard

After deployment, you'll get a URL like:
```
https://energy-dashboard-xxxxx.run.app
```

Visit this URL in your browser to access the upload form.

## Testing the Deployment

```bash
# Test health endpoint
curl https://energy-dashboard-xxxxx.run.app/health

# Test upload endpoint
curl -X POST https://energy-dashboard-xxxxx.run.app/upload \
  -H "X-API-Key: YOUR_ZUBE_KEY" \
  -F "file=@emporia-export.zip"
```

## Cost Estimate

**Cloud Run Free Tier Includes**:
- 2 million requests/month
- 360,000 GB-seconds compute/month
- 1 GB egress/month

For personal/assistant use, you'll **never exceed** the free tier.

## Monitoring

View logs:
```bash
gcloud run logs read energy-dashboard --limit 50 --region us-central1
```

## Troubleshooting

**Deployment fails**:
- Check logs: `gcloud builds log <BUILD_ID>`
- Verify Dockerfile is correct
- Ensure all files are committed to git

**Upload endpoint 500 error**:
- Check Cloud Run logs for Python errors
- Verify environment variables are set
- Test with curl from terminal first

**Network timeout**:
- Cloud Run has cold-start delay (~2-5 seconds)
- First request may be slow; subsequent requests are fast

## Next Steps

1. Share the Cloud Run URL with your assistant
2. Both of you use the same API key or add additional keys
3. Upload Emporia zips and view dashboards
4. Set up regular exports from your energy system

## Cleanup

If you want to remove everything:

```bash
gcloud run services delete energy-dashboard --region us-central1
gcloud projects delete $PROJECT_ID
```
