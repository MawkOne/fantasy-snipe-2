// Test script to add sample messages to Firebase
// Run with: npx tsx scripts/test-firebase.ts

import { initializeApp } from 'firebase/app'
import { getFirestore, collection, addDoc, serverTimestamp } from 'firebase/firestore'

// Load config from environment
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
}

const app = initializeApp(firebaseConfig)
const db = getFirestore(app)

const sampleMessages = [
  {
    text: "How about those Flames",
    userId: "user456",
    userName: "Rob Innes",
    userAvatar: "/man.jpg",
    chatId: "general-chat",
  },
  {
    text: "Hard working and good goalie",
    userId: "user789",
    userName: "Don Henderson",
    userAvatar: "/placeholder.svg",
    chatId: "general-chat",
  },
  {
    text: "Yes Wolf is very good",
    userId: "user456",
    userName: "Rob Innes",
    userAvatar: "/man.jpg",
    chatId: "general-chat",
  },
]

async function addSampleMessages() {
  console.log('Adding sample messages to Firebase...')
  
  for (const message of sampleMessages) {
    try {
      const docRef = await addDoc(collection(db, 'messages'), {
        ...message,
        timestamp: serverTimestamp(),
      })
      console.log(`✅ Added message: "${message.text}" (ID: ${docRef.id})`)
    } catch (error) {
      console.error('❌ Error adding message:', error)
    }
  }
  
  console.log('\n✨ Done! Check your app at http://localhost:3000')
  process.exit(0)
}

addSampleMessages()

