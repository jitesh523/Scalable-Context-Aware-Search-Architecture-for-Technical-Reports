terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.51.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# VPC Network
resource "google_compute_network" "vpc_network" {
  name                    = "rag-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "rag-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc_network.id
}

# Serverless VPC Access Connector
resource "google_vpc_access_connector" "connector" {
  name          = "rag-connector"
  region        = var.region
  network       = google_compute_network.vpc_network.name
  ip_cidr_range = "10.8.0.0/28"
  min_throughput = 200
  max_throughput = 1000
}

# Cloud SQL Instance (PostgreSQL + pgvector)
resource "google_sql_database_instance" "instance" {
  name             = "rag-db-instance"
  region           = var.region
  database_version = "POSTGRES_15"

  settings {
    tier = "db-custom-2-7680"
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc_network.id
    }
    
    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }
  }
  
  deletion_protection = false # For demo purposes
}

resource "google_sql_database" "database" {
  name     = "rag_system"
  instance = google_sql_database_instance.instance.name
}

resource "google_sql_user" "users" {
  name     = "rag-service-sa"
  instance = google_sql_database_instance.instance.name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}

# Cloud Run Service
resource "google_cloud_run_service" "default" {
  name     = "rag-service"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/rag-service:latest"
        
        env {
          name = "DB_HOST"
          value = google_sql_database_instance.instance.private_ip_address
        }
        
        # Secrets from Secret Manager
        env {
          name = "OPENAI_API_KEY"
          value_from {
            secret_key_ref {
              name = "openai-api-key"
              key  = "latest"
            }
          }
        }
      }
      service_account_name = google_service_account.rag_sa.email
    }

    metadata {
      annotations = {
        "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.connector.name
        "run.googleapis.com/vpc-access-egress"    = "private-ranges-only"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Service Account
resource "google_service_account" "rag_sa" {
  account_id   = "rag-service-sa"
  display_name = "RAG Service Account"
}

# IAM Roles
resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.rag_sa.email}"
}

resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.rag_sa.email}"
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
}

variable "region" {
  description = "GCP Region"
  default     = "us-central1"
}
