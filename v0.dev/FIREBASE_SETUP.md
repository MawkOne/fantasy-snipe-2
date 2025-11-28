# 🔥 Firebase Setup Guide for NHL Messenger

Follow these steps to get your messenger connected to Firebase.

## Step 1: Create Firebase Project (5 minutes)

1. **Go to Firebase Console:**
   - Visit: https://console.firebase.google.com
   - Sign in with your Google account

2. **Create a new project:**
   - Click "Add project"
   - Project name: `nhl-messenger` (or whatever you like)
   - Click "Continue"
   - **Disable Google Analytics** (you don't need it for now)
   - Click "Create project"
   - Wait ~30 seconds for it to be created
   - Click "Continue"

## Step 2: Register Your Web App (2 minutes)

1. **Add a web app:**
   - On the project homepage, click the **`</>`** (web) icon
   - App nickname: `NHL Messenger Web`
   - **Do NOT check** "Firebase Hosting"
   - Click "Register app"

2. **Copy your config:**
   - You'll see a code block with `firebaseConfig`
   - It looks like this:
   ```javascript
   const firebaseConfig = {
     apiKey: "AIza...",
     authDomain: "nhl-messenger-xxxxx.firebaseapp.com",
     projectId: "nhl-messenger-xxxxx",
     storageBucket: "nhl-messenger-xxxxx.appspot.com",
     messagingSenderId: "123456789",
     appId: "1:123456789:web:abcdef123456"
   };
   ```
   - **Keep this tab open** (you'll need these values in Step 4)
   - Click "Continue to console"

## Step 3: Enable Firestore Database (2 minutes)

1. **Create database:**
   - In the left sidebar, click **"Firestore Database"**
   - Click **"Create database"**
   - Location: Choose closest to you (e.g., `us-central` for North America)
   - Click "Next"

2. **Set security rules:**
   - Select **"Start in test mode"** (we'll secure it later)
   - Click "Enable"
   - Wait ~30 seconds for database to be created

## Step 4: Enable Authentication (1 minute)

1. **Set up auth:**
   - In the left sidebar, click **"Authentication"**
   - Click **"Get started"**
   - Click on **"Email/Password"** sign-in method
   - Toggle **"Email/Password"** to **ENABLED**
   - Click "Save"

## Step 5: Enable Storage (1 minute)

1. **Set up storage:**
   - In the left sidebar, click **"Storage"**
   - Click **"Get started"**
   - Click "Next" (keep default rules)
   - Location: Same as Firestore
   - Click "Done"

## Step 6: Configure Your Local Environment

1. **Copy the example env file:**
   ```bash
   cd /Users/markhenderson/Cursor\ Projects/NHL-API/v0.dev
   cp .env.local.example .env.local
   ```

2. **Edit `.env.local`:**
   - Open the file in your editor
   - Copy the values from Step 2 (Firebase config) into the file:
   ```bash
   NEXT_PUBLIC_FIREBASE_API_KEY=AIza...
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=nhl-messenger-xxxxx.firebaseapp.com
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=nhl-messenger-xxxxx
   NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=nhl-messenger-xxxxx.appspot.com
   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
   NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abcdef123456
   ```
   - Save the file

## Step 7: Test the Connection

1. **Start the dev server:**
   ```bash
   cd /Users/markhenderson/Cursor\ Projects/NHL-API/v0.dev
   pnpm dev
   ```

2. **Open the app:**
   - Go to http://localhost:3000
   - The app should load without errors
   - Check the browser console (F12) - no Firebase errors means success!

## ✅ You're Done!

Your messenger is now connected to Firebase. Next steps:
- I'll update the components to use Firebase instead of mock data
- You'll be able to send real messages that sync across all users
- Authentication will work for login/signup

---

## 🆘 Troubleshooting

**"Firebase: Error (auth/configuration-not-found)"**
- Make sure you copied ALL the env variables correctly
- Check for typos in `.env.local`
- Restart the dev server (`pnpm dev`)

**"Missing or insufficient permissions"**
- Go back to Firestore Database > Rules
- Make sure you're in "test mode" (rules allow read/write)

**"Storage bucket not found"**
- Go to Storage in Firebase Console
- Make sure it's enabled
- Check the bucket name matches your `.env.local`

---

Need help? Just ask! 🚀

