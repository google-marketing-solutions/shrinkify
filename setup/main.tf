#############################################
# Vars
#############################################

variable "project_id" {
  type = string
}

variable "project_number" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "location" {
  type    = string
  default = "US"
}

variable "service_name" {
  type    = string
  default = "shrinkify"
}

variable "dataset_id" {
  type = string
  default = "shrinkify_output"
}

variable "table_id" {
  type = string
  default = "results_*"
}

locals {
  service_account = "${var.project_number}-compute@developer.gserviceaccount.com"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

#############################################
# IAM
#############################################

resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${local.service_account}"
}

resource "google_project_iam_member" "bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${local.service_account}"
}

resource "google_project_iam_member" "run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${local.service_account}"
}

resource "google_project_iam_member" "function_viewer" {
  project = var.project_id
  role    = "roles/cloudfunctions.viewer"
  member  = "serviceAccount:${local.service_account}"
}

resource "google_project_iam_member" "service_account_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${local.service_account}"
}

resource "google_project_iam_member" "eventarc_event_receiver" {
  project = var.project_id
  role    = "roles/eventarc.eventReceiver"
  member  = "serviceAccount:${local.service_account}"
}

resource "google_project_iam_member" "service_account_token_creator" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${local.service_account}"
}

resource "google_project_iam_member" "eventarc_admin" {
  project = var.project_id
  role    = "roles/eventarc.admin"
  member  = "serviceAccount:${local.service_account}"
}

resource "google_project_iam_member" "pubsub_service_account_token_creator" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:service-${var.project_number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

#############################################
# Cloud Run
#############################################

data "google_container_registry_image" "shrinkify_image" {
  name = "gcr.io/${var.project_id}/${var.service_name}:latest"
}

resource "google_cloud_run_service" "shrinkify_service" {
  name     = "${var.service_name}-service"
  location = var.region
  template {
    spec {
      containers {
        image = data.google_container_registry_image.shrinkify_image.name
        env {
          name = "PROJECT_NAME"
          value = var.project_id
        }
        env {
          name = "PROJECT_NUMBER"
          value = var.project_number
        }
      }
    }
  }
  traffic {
    percent         = 100
    latest_revision = true
  }
}
data "google_iam_policy" "public_access" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}
resource "google_cloud_run_service_iam_policy" "public_access" {
  location    = google_cloud_run_service.shrinkify_service.location
  project     = google_cloud_run_service.shrinkify_service.project
  service     = google_cloud_run_service.shrinkify_service.name
  policy_data = data.google_iam_policy.public_access.policy_data
}

#############################################
# Cloud Function 
#############################################

# Create GCS Bucket and upload zipped CF code

resource "google_storage_bucket" "cf_zip_bucket" {
  name          = "${var.project_id}-shrinkify"
  location      = "US"
  project       = var.project_id
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_object" "source" {
  name   = "shrinkify_cf.zip"
  source = "shrinkify_cf.zip"
  bucket = google_storage_bucket.cf_zip_bucket.name
}

# Deploy Cloud Function 

resource "google_cloudfunctions2_function" "function" {
  depends_on = [
    google_project_iam_member.bigquery_admin,
    google_project_iam_member.eventarc_admin,
    google_project_iam_member.eventarc_event_receiver,
    google_project_iam_member.function_viewer,
    google_project_iam_member.pubsub_service_account_token_creator,
    google_project_iam_member.run_invoker,
    google_project_iam_member.service_account_token_creator,
    google_project_iam_member.service_account_user,
    google_project_iam_member.storage_admin,
  ]
  name = "shrinkify_cf"
  location = var.region
  project = var.project_id
  build_config {
    runtime     = "python310"
    entry_point = "cloud_agent" # Set the entry point in the code
    source {
      storage_source {
        bucket = google_storage_bucket.cf_zip_bucket.name
        object = google_storage_bucket_object.source.name
      }
    }
  }
  service_config {
    max_instance_count  = 1
    available_memory    = "512M"
    timeout_seconds     = 540
    service_account_email = local.service_account
  }
  event_trigger {
    trigger_region = var.region
    event_type = "google.cloud.audit.log.v1.written"
    retry_policy = "RETRY_POLICY_DO_NOT_RETRY"
    service_account_email = local.service_account
    event_filters {
      attribute = "serviceName"
      value = "bigquery.googleapis.com"
    }
    event_filters {
      attribute = "methodName"
      value = "google.cloud.bigquery.v2.JobService.InsertJob"
    }
    event_filters {
      attribute = "resourceName"
      value = "/projects/${var.project_id}/datasets/${var.dataset_id}/tables/${var.table_id}"
      operator = "match-path-pattern" # This allows path patterns to be used in the value field
    }
  }
}