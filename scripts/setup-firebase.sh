#!/bin/bash

# Firebase Setup Script for Stock Agent
# This script helps configure Firebase authentication and messaging

set -e

echo "🔥 Firebase Setup for Stock Agent"
echo "=================================="
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
else
    echo "📋 Found existing .env file"
fi

echo ""
echo "🔧 Firebase Configuration Steps:"
echo ""
echo "1. Go to Firebase Console: https://console.firebase.google.com/"
echo "2. Create a new project or select existing project"
echo "3. Enable Authentication:"
echo "   - Go to Authentication > Sign-in method"
echo "   - Enable Email/Password provider"
echo "4. Enable Cloud Messaging:"
echo "   - Go to Project Settings > Cloud Messaging"
echo "   - Generate Web Push certificates"
echo "5. Get your Firebase config:"
echo "   - Go to Project Settings > General"
echo "   - Add a web app if you haven't already"
echo "   - Copy the config values"
echo ""

# Function to prompt for Firebase config
prompt_firebase_config() {
    echo "📝 Enter your Firebase configuration:"
    echo ""
    
    read -p "Firebase API Key: " FIREBASE_API_KEY
    read -p "Firebase Auth Domain (e.g., your-project.firebaseapp.com): " FIREBASE_AUTH_DOMAIN
    read -p "Firebase Project ID: " FIREBASE_PROJECT_ID
    read -p "Firebase Storage Bucket (e.g., your-project.firebasestorage.app): " FIREBASE_STORAGE_BUCKET
    read -p "Firebase Messaging Sender ID: " FIREBASE_MESSAGING_SENDER_ID
    read -p "Firebase App ID: " FIREBASE_APP_ID
    read -p "Firebase VAPID Public Key: " FIREBASE_VAPID_PUBLIC_KEY
    
    echo ""
    echo "🔄 Updating .env file..."
    
    # Update .env file
    sed -i "s/FIREBASE_API_KEY=.*/FIREBASE_API_KEY=$FIREBASE_API_KEY/" .env
    sed -i "s/FIREBASE_AUTH_DOMAIN=.*/FIREBASE_AUTH_DOMAIN=$FIREBASE_AUTH_DOMAIN/" .env
    sed -i "s/FIREBASE_PROJECT_ID=.*/FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID/" .env
    sed -i "s/FIREBASE_STORAGE_BUCKET=.*/FIREBASE_STORAGE_BUCKET=$FIREBASE_STORAGE_BUCKET/" .env
    sed -i "s/FIREBASE_MESSAGING_SENDER_ID=.*/FIREBASE_MESSAGING_SENDER_ID=$FIREBASE_MESSAGING_SENDER_ID/" .env
    sed -i "s/FIREBASE_APP_ID=.*/FIREBASE_APP_ID=$FIREBASE_APP_ID/" .env
    sed -i "s/FIREBASE_VAPID_PUBLIC_KEY=.*/FIREBASE_VAPID_PUBLIC_KEY=$FIREBASE_VAPID_PUBLIC_KEY/" .env
    
    echo "✅ Firebase configuration updated in .env file"
}

# Ask user if they want to configure Firebase now
echo "❓ Do you want to configure Firebase now? (y/n)"
read -r configure_now

if [ "$configure_now" = "y" ] || [ "$configure_now" = "Y" ]; then
    prompt_firebase_config
else
    echo "⏭️  Skipping Firebase configuration"
    echo "📝 Please manually update the .env file with your Firebase config"
fi

echo ""
echo "🔐 Production Setup (Optional):"
echo ""
echo "For production environments, you'll need Firebase Admin SDK credentials:"
echo "1. Go to Firebase Console > Project Settings > Service Accounts"
echo "2. Click 'Generate new private key'"
echo "3. Download the JSON file"
echo "4. Set one of these environment variables:"
echo "   - FIREBASE_CREDS_PATH=/path/to/service-account.json"
echo "   - FIREBASE_SERVICE_ACCOUNT_JSON='{\"type\":\"service_account\",...}'"
echo ""

echo "🚀 Next Steps:"
echo ""
echo "1. Install dependencies: pip install -e ."
echo "2. Run the application: python -m stock_agent.main"
echo "3. Open http://localhost:8080/login"
echo "4. Create a Firebase account using the login form"
echo ""
echo "✅ Firebase setup complete!"