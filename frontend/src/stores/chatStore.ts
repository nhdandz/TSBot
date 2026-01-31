// Chat store

import { create } from 'zustand'
import type { ChatMessage } from '@/types'

// Generate UUID
const generateSessionId = () => {
  return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

interface ChatState {
  messages: ChatMessage[]
  sessionId: string
  isLoading: boolean
  isTyping: boolean
  error: string | null

  // Actions
  addMessage: (message: ChatMessage) => void
  setMessages: (messages: ChatMessage[]) => void
  setIsLoading: (loading: boolean) => void
  setIsTyping: (typing: boolean) => void
  setError: (error: string | null) => void
  clearMessages: () => void
  resetSession: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  sessionId: generateSessionId(),
  isLoading: false,
  isTyping: false,
  error: null,

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  setMessages: (messages) => set({ messages }),

  setIsLoading: (loading) => set({ isLoading: loading }),

  setIsTyping: (typing) => set({ isTyping: typing }),

  setError: (error) => set({ error }),

  clearMessages: () => set({ messages: [] }),

  resetSession: () =>
    set({
      messages: [],
      sessionId: generateSessionId(),
      isLoading: false,
      isTyping: false,
      error: null,
    }),
}))
