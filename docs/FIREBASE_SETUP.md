# 🔥 Firebase Authentication Setup

This guide will help you set up Firebase Authentication for the Stock Agent application.

## Prerequisites

- A Google account
- Access to [Firebase Console](https://console.firebase.google.com/)

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or "Add project"
3. Enter your project name (e.g., "stock-agent")
4. Choose whether to enable Google Analytics (optional)
5. Click "Create project"

## Step 2: Enable Authentication

1. In your Firebase project, go to **Authentication** in the left sidebar
2. Click on the **Sign-in method** tab
3. Enable **Email/Password** provider:
   - Click on "Email/Password"
   - Toggle "Enable" to ON
   - Click "Save"

## Step 3: Enable Cloud Messaging (for notifications)

1. Go to **Project Settings** (gear icon) > **Cloud Messaging** tab
2. Under "Web Push certificates", click **Generate key pair**
3. Copy the generated VAPID key (you'll need this later)

## Step 4: Get Firebase Configuration

1. Go to **Project Settings** (gear icon) > **General** tab
2. Scroll down to "Your apps" section
3. Click **Add app** and select the **Web** platform (</> icon)
4. Enter an app nickname (e.g., "stock-agent-web")
5. Click "Register app"
6. Copy the Firebase configuration object

## Step 5: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update the Firebase configuration in `.env`:
   ```bash
   FIREBASE_API_KEY=your_api_key_here
   FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
   FIREBASE_MESSAGING_SENDER_ID=123456789012
   FIREBASE_APP_ID=1:123456789012:web:abcdef123456789
   FIREBASE_VAPID_PUBLIC_KEY=your_vapid_key_here
   ```

## Step 6: Set up Firebase Admin SDK (Production)

For production environments, you need Firebase Admin SDK credentials:

1. Go to **Project Settings** > **Service accounts** tab
2. Click **Generate new private key**
3. Download the JSON file
4. Set the environment variable:
   ```bash
   FIREBASE_CREDS_PATH=/path/to/service-account.json
   ```

   Or set the JSON content directly:
   ```bash
   FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
   ```

## Step 7: Test the Setup

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Run the application:
   ```bash
   python -m stock_agent.main
   ```

3. Open http://localhost:8080/login
4. Create a test account using the "Create Account" button
5. Sign in with your credentials

## Automated Setup

You can use the setup script to configure Firebase interactively:

```bash
./scripts/setup-firebase.sh
```

## Troubleshooting

### Common Issues

1. **"Firebase configuration not found"**
   - Check that all Firebase environment variables are set correctly
   - Verify the Firebase project ID matches your actual project

2. **"Authentication failed"**
   - Ensure Email/Password provider is enabled in Firebase Console
   - Check that the API key has the correct permissions

3. **"Service worker registration failed"**
   - Ensure the application is served over HTTPS (or localhost)
   - Check browser console for detailed error messages

4. **"Admin SDK initialization failed"**
   - Verify the service account JSON file path is correct
   - Ensure the service account has the necessary permissions

### Firebase Console Links

- [Authentication Settings](https://console.firebase.google.com/project/_/authentication/providers)
- [Project Settings](https://console.firebase.google.com/project/_/settings/general)
- [Cloud Messaging](https://console.firebase.google.com/project/_/settings/cloudmessaging)
- [Service Accounts](https://console.firebase.google.com/project/_/settings/serviceaccounts/adminsdk)

## Security Best Practices

1. **Never commit Firebase credentials to version control**
2. **Use environment variables for all sensitive configuration**
3. **Enable Firebase Security Rules for production**
4. **Regularly rotate service account keys**
5. **Monitor authentication logs in Firebase Console**

## Next Steps

After setting up Firebase Authentication:

1. Configure Firebase Security Rules
2. Set up user roles and permissions
3. Implement password reset functionality
4. Add social login providers (Google, GitHub, etc.)
5. Set up Firebase Analytics for user tracking