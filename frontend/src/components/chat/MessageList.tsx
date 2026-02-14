import { useRef, useEffect } from 'react'
import { Bot, Shield } from 'lucide-react'
import type { ChatMessage } from '@/types'
import { SourceDisplay } from './SourceDisplay'
import { MarkdownContent } from './MarkdownContent'

interface MessageListProps {
  messages: ChatMessage[]
  isTyping?: boolean
  onSuggestionClick?: (question: string) => void
}

const suggestions = [
  'Điểm chuẩn các trường quân đội năm 2025?',
  'Điều kiện sức khỏe xét tuyển?',
  'Hồ sơ tuyển sinh cần những gì?',
]

export function MessageList({ messages, isTyping, onSuggestionClick }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
      {messages.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full text-center px-8">
          <div className="w-16 h-16 bg-gradient-military rounded-2xl flex items-center justify-center shadow-soft-md mb-6">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h3 className="text-lg font-semibold tracking-tighter mb-2 text-foreground">
            Chào mừng đến với TSBot
          </h3>
          <p className="text-sm text-muted-foreground max-w-sm leading-relaxed">
            Hỏi tôi về điểm chuẩn, quy chế tuyển sinh, hoặc bất kỳ thông tin nào
            liên quan đến tuyển sinh quân đội Việt Nam.
          </p>
          <div className="flex flex-wrap gap-2 mt-6 justify-center max-w-md">
            {suggestions.map((q) => (
              <button
                key={q}
                onClick={() => onSuggestionClick?.(q)}
                className="px-4 py-2 rounded-xl border border-border/60 text-xs text-muted-foreground hover:bg-muted/50 hover:border-border hover:text-foreground transition-all duration-300 ease-apple"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {messages.map((message, index) => (
        <div
          key={index}
          className={`animate-message-in flex gap-3 ${
            message.role === 'user' ? 'justify-end' : 'justify-start'
          }`}
        >
          {message.role === 'assistant' && (
            <div className="flex-shrink-0 mt-1">
              <div className="w-7 h-7 rounded-lg bg-gradient-military flex items-center justify-center shadow-soft-sm">
                <Bot className="w-4 h-4 text-white" />
              </div>
            </div>
          )}

          <div className={`flex flex-col max-w-[88%] ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div
              className={
                message.role === 'user'
                  ? 'px-4 py-3 rounded-2xl rounded-tr-md bg-primary text-primary-foreground shadow-message'
                  : 'px-4 py-3 rounded-2xl rounded-tl-md bg-card border border-border/40 shadow-message'
              }
            >
              {message.role === 'user' ? (
                <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
              ) : (
                <MarkdownContent content={message.content} />
              )}
            </div>

            {message.sources && message.sources.length > 0 && (
              <SourceDisplay sources={message.sources} />
            )}

            <span className="text-[10px] text-muted-foreground/50 mt-1.5 px-1">
              {new Date(message.timestamp).toLocaleTimeString('vi-VN')}
            </span>
          </div>
        </div>
      ))}

      {isTyping && (
        <div className="animate-message-in flex gap-3 justify-start">
          <div className="flex-shrink-0 mt-1">
            <div className="w-7 h-7 rounded-lg bg-gradient-military flex items-center justify-center shadow-soft-sm">
              <Bot className="w-4 h-4 text-white" />
            </div>
          </div>
          <div className="px-4 py-3 rounded-2xl rounded-tl-md bg-card border border-border/40 shadow-message">
            <div className="flex gap-1.5">
              <div className="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full typing-dot" />
              <div className="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full typing-dot" />
              <div className="w-1.5 h-1.5 bg-muted-foreground/40 rounded-full typing-dot" />
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}
