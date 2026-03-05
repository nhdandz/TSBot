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
  SSEEvent,
} from '@/types'

export const chatService = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return apiClient.post<ChatResponse>(API_ENDPOINTS.chat, request)
  },

  async *sendMessageStream(request: ChatRequest): AsyncGenerator<SSEEvent, void, unknown> {
    const response = await fetch(API_ENDPOINTS.chatStream, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Lỗi kết nối' }))
      yield { type: 'error', message: error.detail || 'Lỗi kết nối server' }
      return
    }

    const reader = response.body?.getReader()
    if (!reader) {
      yield { type: 'error', message: 'Trình duyệt không hỗ trợ streaming' }
      return
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event: SSEEvent = JSON.parse(line.slice(6))
              yield event
            } catch {
              // ignore malformed events
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
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
