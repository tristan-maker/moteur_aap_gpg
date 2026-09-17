#!/bin/bash
set -e

echo "🔑 Configuration des identifiants Vertex AI pour Google Cloud Shell..."

# Configuration automatique à partir du projet GCP actif dans Cloud Shell
export GOOGLE_GENAI_USE_ENTERPRISE="TRUE"
export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "gravir-pour-grandir-prod")
export GOOGLE_CLOUD_LOCATION="europe-west9"

echo "✔ Projet GCP ciblé : $GOOGLE_CLOUD_PROJECT ($GOOGLE_CLOUD_LOCATION)"

# Authentification Application Default Credentials (ADC) si nécessaire
if [ ! -f "$HOME/.config/gcloud/application_default_credentials.json" ]; then
    echo "⚠️ Génération des identifiants ADC..."
    gcloud auth application-default login --no-launch-browser
fi

echo "🚀 Lancement du benchmark d'évaluation ADK..."
adk eval . eval_data.evalset.json --config_file_path=eval_config.json
