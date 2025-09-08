#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Variables
export GCP_PROJECT_ID=$(gcloud config get-value project)
export GCP_REGION="us-central1"
export CLOUD_RUN_JOB_NAME="populate-bigquery-job"
export DOCKER_IMAGE_NAME="nhl-api"
export JOB_YAML_FILE="/tmp/job.yaml"

# Check for --skip-build flag
SKIP_BUILD=false
if [[ "$1" == "--skip-build" ]]; then
  SKIP_BUILD=true
fi

# 1. Submit the build to Google Cloud Build (optional)
if [ "$SKIP_BUILD" = false ]; then
  echo "Submitting the build to Google Cloud Build..."
  gcloud builds submit --config cloudbuild.yaml --project $GCP_PROJECT_ID
else
  echo "Skipping the build process."
fi

# 2. Create the Cloud Run Job YAML definition
echo "Creating Cloud Run Job YAML file..."
cat > $JOB_YAML_FILE <<EOF
apiVersion: run.googleapis.com/v1
kind: Job
metadata:
  name: $CLOUD_RUN_JOB_NAME
spec:
  template:
    spec:
      template:
        spec:
          maxRetries: 3
          serviceAccountName: cloud-run-job-sa@fantasy-snipe-ai.iam.gserviceaccount.com
          containers:
          - image: gcr.io/$GCP_PROJECT_ID/$DOCKER_IMAGE_NAME
            command:
            - "python"
            args:
            - "scripts/populate_bigquery.py"
            env:
            - name: GCP_PROJECT_ID
              value: "$GCP_PROJECT_ID"
            - name: BIGQUERY_DATASET_ID
              value: "nhl_data"
            - name: BIGQUERY_TABLE_ID
              value: "player_game_logs"
            - name: INSTANCE_CONNECTION_NAME
              value: "fantasy-snipe-ai:northamerica-northeast1:nhl-api-db-montreal"
EOF

# 3. Create or update the Cloud Run Job
echo "Creating or updating the Cloud Run Job..."
gcloud run jobs replace $JOB_YAML_FILE --region $GCP_REGION --project $GCP_PROJECT_ID

# 4. Run the Cloud Run Job
echo "Running the Cloud Run Job..."
gcloud run jobs execute $CLOUD_RUN_JOB_NAME --region $GCP_REGION --wait --project $GCP_PROJECT_ID

echo "Cloud Run Job execution finished."

# 5. Clean up the temporary YAML file
rm $JOB_YAML_FILE
