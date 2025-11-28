# 🔥 Firebase Chat Setup Guide

## Your App is Already Configured!

Your v0.dev app is already set up to use Firebase for chat. You just need to enable Firestore in Firebase Console.

## ✅ What's Already Done

- ✅ Firebase SDK installed
- ✅ Firebase config in `lib/firebase.ts`
- ✅ Chat hooks created (`hooks/use-messages.ts`)
- ✅ Authentication hooks (`hooks/use-auth.ts`)
- ✅ Environment variables configured (`.env.local`)
- ✅ Deployed to production: https://snipe-chat-139ec.web.app

## 🚀 Quick Setup (5 minutes)

### Step 1: Enable Firestore Database

1. **Open Firebase Console:**
   👉 https://console.firebase.google.com/project/snipe-chat-139ec/firestore

2. **Click "Create database"**

3. **Choose location:** 
   - Select `us-central` (or closest to you)
   - Click **Next**

4. **Start in test mode:**
   - Select **"Start in test mode"** (we'll secure it next)
   - Click **Enable**
   - Wait ~30 seconds for Firestore to be created

### Step 2: Update Security Rules

1. After Firestore is created, go to the **Rules** tab
2. Replace the default rules with the rules from `firestore.rules`
3. Click **Publish**

Or deploy rules via CLI:

```bash
cd "/Users/markhenderson/Cursor Projects/NHL-API/v0.dev"
firebase deploy --only firestore:rules
```

### Step 3: Enable Authentication (Optional but Recommended)

1. **Go to Authentication:**
   👉 https://console.firebase.google.com/project/snipe-chat-139ec/authentication

2. **Click "Get started"**

3. **Enable Email/Password:**
   - Click "Email/Password"
   - Toggle "Enable"
   - Click **Save**

### Step 4: Test Your Chat!

1. **Open your app:**
   - Production: https://snipe-chat-139ec.web.app
   - Local: http://localhost:3000

2. **Navigate to the chat**

3. **Send a message** - it will appear instantly!

---

## 📊 Firestore Collections Structure

Your app uses these collections:

```
firestore/
├── messages/          # Chat messages
│   ├── id             # Auto-generated
│   ├── text           # Message content
│   ├── userId         # Sender ID
│   ├── userName       # Sender name
│   ├── userAvatar     # Sender avatar URL
│   ├── chatId         # Chat room ID
│   └── timestamp      # Message timestamp
│
├── leagues/           # Fantasy leagues
│   ├── id
│   ├── name
│   ├── settings
│   ├── members[]
│   └── commissionerId
│
├── chatRooms/         # Chat rooms
│   ├── id
│   ├── leagueId
│   ├── name
│   └── type
│
└── users/             # User profiles
    ├── uid
    ├── displayName
    ├── email
    └── photoURL
```

---

## 🔐 Security Rules Explained

The `firestore.rules` file configures:

1. **Messages:** Anyone can read, authenticated users can create
2. **Leagues:** Anyone can read, only commissioner can modify
3. **Users:** Anyone can read profiles, users can only edit their own
4. **Chat Rooms:** Anyone can read, authenticated users can create

---

## 🧪 Testing Without Authentication

For testing, you can use the chat without auth by:

1. Using hardcoded user info (current setup in `chat-view.tsx`)
2. Anyone can send messages
3. Each message shows sender info

**Current test user:**
```typescript
const CURRENT_USER = {
  id: "user123",
  name: "Mark Henderson",
  avatar: "/man.jpg",
}
```

---

## 🔑 Adding Real Authentication

To enable real authentication:

1. Enable Email/Password in Firebase Console
2. Add login/signup UI to your app
3. Update `CURRENT_USER` to use `useAuth()` hook

**Example:**

```typescript
// In chat-view.tsx
import { useAuth } from '@/hooks/use-auth'

const { user } = useAuth()

const CURRENT_USER = {
  id: user?.uid || "guest",
  name: user?.displayName || "Guest",
  avatar: user?.photoURL || "/man.jpg",
}
```

---

## 📱 Real-Time Updates

Your chat automatically updates in real-time using Firestore's `onSnapshot()`:

- New messages appear instantly
- No polling or refreshing needed
- Works across all devices
- Updates within milliseconds

---

## 🚀 Deploy Chat Updates

When you make changes:

```bash
cd "/Users/markhenderson/Cursor Projects/NHL-API/v0.dev"
pnpm build
firebase deploy --only hosting
```

---

## 🆘 Troubleshooting

### Chat not loading?
- Check Firebase Console: Firestore enabled?
- Check browser console for errors
- Verify `.env.local` has Firebase credentials

### Messages not sending?
- Check Firestore security rules
- Check browser console for permission errors
- Verify Firestore is in the right region

### Real-time not working?
- Firestore uses WebSockets - check firewall
- Verify browser supports WebSockets
- Check Firebase Console for quota limits

---

## 💰 Firebase Free Tier

Firestore free tier includes:
- ✅ 1 GB storage
- ✅ 10 GB/month network egress
- ✅ 50,000 reads/day
- ✅ 20,000 writes/day
- ✅ 20,000 deletes/day

**This is plenty for a fantasy league chat app!**

---

## ✨ Next Steps

1. ✅ Enable Firestore
2. ✅ Deploy security rules
3. 🔲 Add authentication UI
4. 🔲 Create league management
5. 🔲 Import historical league data
6. 🔲 Connect real player rosters

---

**Your chat is ready to go! Just enable Firestore and start messaging.** 🎉

