#!/bin/bash

# Setup script for Google Gemini AI
# Run this to enable Gemini API in your Google Cloud project

echo "🚀 Setting up Google Gemini AI for fantasy-snipe-ai..."
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo "📋 Setting project to fantasy-snipe-ai..."
gcloud config set project fantasy-snipe-ai

# Enable Gemini API
echo "🔧 Enabling Generative Language API..."
gcloud services enable generativelanguage.googleapis.com

echo ""
echo "✅ Gemini API enabled!"
echo ""
echo "📝 Next steps:"
echo "1. Create API key: https://console.cloud.google.com/apis/credentials?project=fantasy-snipe-ai"
echo "2. Add to Railway: GOOGLE_API_KEY=AIza..."
echo "3. Deploy your FastAPI with Gemini code"
echo ""
echo "💰 You have $100K in credits - Gemini queries are FREE!"
echo ""

