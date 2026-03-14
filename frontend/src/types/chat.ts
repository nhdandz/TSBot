// Chat related types

export interface ChartDataPoint {
  x: number | string
  y: number
}

export interface ChartSeries {
  name: string
  data: ChartDataPoint[]
}

export interface ChartData {
  type: 'line' | 'bar' | 'scatter'
  title: string
  series: ChartSeries[]
}

export interface ChatMessage {
  id?: number
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  sources?: Source[]
  intent?: string
  chart_data?: ChartData
  _fromStreaming?: boolean
}

export interface Source {
  content_preview?: string
  score?: number
  legal_path?: string
  chapter?: string
  article?: string
  document?: string
  // fallback fields
  title?: string
  content?: string
  metadata?: Record<string, any>
}

export interface ChatRequest {
  message: string
  session_id?: string
}

export interface ChatResponse {
  response: string
  session_id: string
  intent?: string
  sources: Source[]
  chart_data?: ChartData
  timestamp: string
}

export interface FeedbackRequest {
  session_id: string
  message_id?: number
  rating?: number
  feedback_type: 'helpful' | 'not_helpful' | 'incorrect' | 'incomplete'
  comment?: string
}

export interface FeedbackResponse {
  success: boolean
  message: string
}

export interface ChatHistoryItem {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: Source[]
  intent?: string
}

export interface ChatSession {
  session_id: string
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

// SSE streaming event types
export interface SSEEvent {
  type: 'meta' | 'token' | 'done' | 'error'
  intent?: string
  sources?: Source[]
  content?: string
  chart_data?: ChartData
  message?: string
}

// WebSocket message types
export interface WSMessage {
  type: 'ack' | 'response' | 'error' | 'stream'
  message?: string
  response?: string
  intent?: string
  sources?: Source[]
  chunk?: string
  error?: string
}
