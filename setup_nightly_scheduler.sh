#!/bin/bash
# Setup Cloud Scheduler to run nightly NHL data ingestion at 2am PST

set -e

PROJECT_ID="fantasy-snipe-ai"
REGION="us-central1"
JOB_NAME="nhl-nightly-ingestion"
SCHEDULER_NAME="nhl-nightly-scheduler"

echo "=========================================="
echo "Setting up Nightly NHL Data Ingestion"
echo "=========================================="

# Step 1: Create/Update the Cloud Run Job
echo ""
echo "Creating Cloud Run Job..."
gcloud run jobs create $JOB_NAME \
  --image gcr.io/$PROJECT_ID/nhl-data-ingestion:latest \
  --region $REGION \
  --memory 4Gi \
  --cpu 2 \
  --max-retries 1 \
  --task-timeout 7200s \
  --set-env-vars DATABASE_URL="postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require" \
  --project $PROJECT_ID \
  2>&1 || echo "Job exists, updating..." && \
gcloud run jobs update $JOB_NAME \
  --image gcr.io/$PROJECT_ID/nhl-data-ingestion:latest \
  --region $REGION \
  --memory 4Gi \
  --cpu 2 \
  --max-retries 1 \
  --task-timeout 7200s \
  --set-env-vars DATABASE_URL="postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require" \
  --project $PROJECT_ID

echo "✅ Cloud Run Job configured"

# Step 2: Create Cloud Scheduler Job
# Schedule: 2am PST = 10am UTC (PST is UTC-8)
echo ""
echo "Creating Cloud Scheduler..."

# Delete existing scheduler if it exists
gcloud scheduler jobs delete $SCHEDULER_NAME \
  --location $REGION \
  --project $PROJECT_ID \
  --quiet 2>/dev/null || echo "No existing scheduler to delete"

# Create new scheduler
gcloud scheduler jobs create http $SCHEDULER_NAME \
  --location $REGION \
  --schedule "0 10 * * *" \
  --time-zone "America/Los_Angeles" \
  --uri "https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run" \
  --http-method POST \
  --oauth-service-account-email $PROJECT_ID@appspot.gserviceaccount.com \
  --project $PROJECT_ID

echo "✅ Cloud Scheduler configured"

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📅 Schedule: Every night at 2:00 AM PST"
echo "🔄 Pipeline Order:"
echo "   1. Teams"
echo "   2. Players" 
echo "   3. Games/Schedule"
echo "   4. Play-by-Play Events"
echo "   5. Player Game Stats"
echo "   6. Shift Charts"
echo ""
echo "Manual execution:"
echo "  gcloud run jobs execute $JOB_NAME --region $REGION"
echo ""
echo "View logs:"
echo "  gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME\" --limit 50"
echo ""


