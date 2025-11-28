# Environment Variables for Cloud SQL

## ✅ Your Cloud SQL Connection String

```
postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require
```

## Add to Railway (FastAPI Backend)

Go to your Railway project: https://railway.app/project/YOUR_PROJECT

Add these environment variables:

```bash
# Database Connection
DATABASE_URL=postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require

# Google AI (Free with your $100K credits!)
GOOGLE_API_KEY=AIza...your-google-api-key
GOOGLE_CLOUD_PROJECT=fantasy-snipe-ai
```

## Add to `.env.local` (Next.js Frontend)

Create this file in `/v0.dev/.env.local`:

```bash
# Firebase (for chat)
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyA8j7Twg4uNo8LC9RzkyZ1sw3imtQrPo0o
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=snipe-chat-139ec.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=snipe-chat-139ec
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=snipe-chat-139ec.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=620721746237
NEXT_PUBLIC_FIREBASE_APP_ID=1:620721746237:web:e9106d8a1cf26a17755554

# FastAPI Backend (connects to Cloud SQL)
NEXT_PUBLIC_API_URL=https://fastapi-production-45ce.up.railway.app
```

## Test Connection

```bash
# Test from command line
psql "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require"

# Or with individual params
psql -h 34.47.23.137 -p 5432 -U postgres -d postgres
# Password: 123-new-password
```

