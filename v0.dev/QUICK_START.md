# 🚀 Quick Start - Get Your Messenger Running

## What I Just Set Up For You:

✅ **Installed Firebase SDK** (`firebase` package)  
✅ **Created Firebase config** (`lib/firebase.ts`)  
✅ **Created auth hook** (`hooks/use-auth.ts`) - for login/signup  
✅ **Created messages hook** (`hooks/use-messages.ts`) - for real-time chat  
✅ **Created setup guide** (`FIREBASE_SETUP.md`) - step-by-step instructions  

---

## 📋 What You Need To Do (15 minutes):

### 1. Create Firebase Project

Open **`FIREBASE_SETUP.md`** and follow Steps 1-5 to:
- Create a Firebase project
- Enable Firestore (database)
- Enable Authentication (login)
- Enable Storage (images/memes)
- Get your config values

### 2. Add Config to `.env.local`

```bash
# In the v0.dev directory, create .env.local:
cp .env.example .env.local

# Then edit .env.local with your Firebase values from Step 1
```

Your `.env.local` should look like:
```bash
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSy...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456:web:abc123
```

### 3. Test the Connection

```bash
cd /Users/markhenderson/Cursor\ Projects/NHL-API/v0.dev
pnpm dev
```

Open http://localhost:3000 - if it loads without errors, Firebase is connected! 🎉

---

## 🔮 What's Next (After Setup):

Once Firebase is connected, I'll:

1. **Update ChatView** - Replace mock messages with real Firebase data
2. **Add Login/Signup** - Simple email/password auth
3. **Real-time Sync** - Messages appear instantly for all users
4. **Add Image Upload** - Share memes and images
5. **Import Your NHL Data** - Connect league history JSON to the app

---

## 📁 Files I Created:

```
v0.dev/
├── lib/
│   └── firebase.ts                 # Firebase initialization
├── hooks/
│   ├── use-auth.ts                 # Authentication hook
│   └── use-messages.ts             # Real-time messages hook
├── .env.example                    # Environment variables template
├── FIREBASE_SETUP.md               # Detailed setup instructions
└── QUICK_START.md                  # This file
```

---

## 🆘 Need Help?

**Stuck on Firebase Console?**  
→ Open `FIREBASE_SETUP.md` - it has screenshots-level detail

**Environment variables not working?**  
→ Make sure `.env.local` exists (not `.env.example`)  
→ Restart dev server after creating/editing `.env.local`

**Firebase errors in console?**  
→ Check that all 6 env variables are filled in  
→ Make sure Firestore is in "test mode" (Step 3 in setup guide)

---

**Ready to start?** Open `FIREBASE_SETUP.md` and follow the steps! 🔥

