#!/bin/bash

# Quick script to enable Gemini API and get instructions for API key

echo "🔑 Setting up Gemini API Key for fantasy-snipe-ai"
echo ""

# Enable the API
echo "Step 1: Enabling Generative Language API..."
gcloud services enable generativelanguage.googleapis.com --project=fantasy-snipe-ai

echo ""
echo "✅ API Enabled!"
echo ""
echo "Step 2: Create API Key"
echo ""
echo "Choose one option:"
echo ""
echo "A) Via Web (Easiest):"
echo "   🌐 https://aistudio.google.com/app/apikey"
echo "   1. Sign in"
echo "   2. Click 'Create API Key'"
echo "   3. Select 'fantasy-snipe-ai' project"
echo "   4. Copy the key"
echo ""
echo "B) Via Console:"
echo "   🌐 https://console.cloud.google.com/apis/credentials?project=fantasy-snipe-ai"
echo "   1. Click 'Create Credentials' → 'API Key'"
echo "   2. Copy the key"
echo ""
echo "Your key will look like: AIzaSyA8j7Twg4uNo8LC9RzkyZ1sw3imtQrPo0o"
echo ""
echo "Add to Railway:"
echo "GOOGLE_API_KEY=AIza...your-key-here"
echo ""

