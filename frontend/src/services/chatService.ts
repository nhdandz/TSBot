// Chat service for API calls

import { apiClient } from '@/lib/api'
import { API_ENDPOINTS } from '@/lib/config'
import type {
  ChatRequest,
  ChatResponse,
  FeedbackRequest,
  FeedbackResponse,
  ChatHistoryItem,
  ChatSession,
} from '@/types'

export const chatService = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return apiClient.post<ChatResponse>(API_ENDPOINTS.chat, request)
  },

  async submitFeedback(request: FeedbackRequest): Promise<FeedbackResponse> {
    return apiClient.post<FeedbackResponse>(API_ENDPOINTS.feedback, request)
  },

  async getChatHistory(sessionId: string, limit = 50): Promise<ChatHistoryItem[]> {
    return apiClient.get<ChatHistoryItem[]>(
      `${API_ENDPOINTS.history(sessionId)}?limit=${limit}`
    )
  },

  async getChatSessions(limit = 50): Promise<ChatSession[]> {
    return apiClient.get<ChatSession[]>(`${API_ENDPOINTS.sessions}?limit=${limit}`)
  },

  async deleteChatSession(sessionId: string): Promise<{ success: boolean; message: string }> {
    return apiClient.delete(`${API_ENDPOINTS.deleteSession(sessionId)}`)
  },

  async checkHealth(): Promise<{ status: string; services: Record<string, string> }> {
    return apiClient.get(API_ENDPOINTS.health)
  },
}
