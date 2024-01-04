#!/bin/bash
COLOR='\033[0;36m' # Cyan
NC='\033[0m' # No Color
# Variables
PROJECT_ID=$(gcloud config get-value project 2> /dev/null)
PROJECT_NAME=$(gcloud projects describe $PROJECT_ID --format="value(name)")
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID | grep projectNumber | sed "s/.* '//;s/'//g")
SERVICE_ACCOUNT=$PROJECT_NUMBER-compute@developer.gserviceaccount.com
IMAGE_NAME="shrinkify"
TAG="latest" # e.g., "latest"


enable_apis() {
  echo -e "${COLOR}Enabling APIs...${NC}"
  gcloud services enable storage-component.googleapis.com
  gcloud services enable artifactregistry.googleapis.com \
    run.googleapis.com \
    iamcredentials.googleapis.com \
    cloudbuild.googleapis.com \
    cloudfunctions.googleapis.com \
    aiplatform.googleapis.com \
    pubsub.googleapis.com \
    eventarc.googleapis.com \
    bigquery.googleapis.com \
    compute.googleapis.com
}

zip_cf_source() {
    echo -e "${COLOR}Zipping cloud function source...${NC}"
    zip -j setup/shrinkify_cf.zip cloud_function/main.py cloud_function/requirements.txt
}

create_image() {
    echo "Enabling container deployment..."
    gcloud auth configure-docker
    echo -e "${COLOR}Creating Image...${NC}"
    docker build -t ${IMAGE_NAME} ../
    docker tag ${IMAGE_NAME} gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${TAG}
    docker push gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${TAG}
    echo "Image pushed to GCP Container Registry successfully."
}

run_tf() {
    cd setup
    terraform init
    echo -e "${COLOR}Creating Infra...${NC}"
    terraform apply -var "project_id=$PROJECT_ID" -var "project_number=$PROJECT_NUMBER" -auto-approve
    echo -e "${COLOR}Infra Created!${NC}"
}

deploy_all() {
    enable_apis
    zip_cf_source
    create_image
    run_tf
}

for i in "$@"; do
    "$i"
    exitcode=$?
    if [ $exitcode -ne 0 ]; then
        echo "Breaking script as command '$i' failed"
        exit $exitcode
    fi
done