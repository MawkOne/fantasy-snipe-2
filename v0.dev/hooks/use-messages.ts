import { useEffect, useState } from 'react'
import {
  collection,
  addDoc,
  query,
  orderBy,
  onSnapshot,
  serverTimestamp,
  Timestamp,
} from 'firebase/firestore'
import { db } from '@/lib/firebase'

export interface Message {
  id: string
  text: string
  userId: string
  userName: string
  userAvatar?: string
  timestamp: Timestamp
  chatId: string
}

export function useMessages(chatId: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!chatId) {
      setLoading(false)
      return
    }

    // Create a query for messages in this chat
    const messagesRef = collection(db, 'messages')
    const q = query(
      messagesRef,
      orderBy('timestamp', 'asc')
    )

    // Listen for real-time updates
    const unsubscribe = onSnapshot(q, (snapshot) => {
      const msgs = snapshot.docs
        .map((doc) => ({
          id: doc.id,
          ...doc.data(),
        }))
        .filter((msg) => msg.chatId === chatId) as Message[]

      setMessages(msgs)
      setLoading(false)
    })

    return unsubscribe
  }, [chatId])

  const sendMessage = async (
    text: string,
    userId: string,
    userName: string,
    userAvatar?: string
  ) => {
    try {
      await addDoc(collection(db, 'messages'), {
        text,
        userId,
        userName,
        userAvatar,
        chatId,
        timestamp: serverTimestamp(),
      })
      return { error: null }
    } catch (error: any) {
      return { error: error.message }
    }
  }

  return {
    messages,
    loading,
    sendMessage,
  }
}

