import { useRef, useEffect } from 'react'
import { Bot, User } from 'lucide-react'
import type { ChatMessage } from '@/types'
import { Card } from '@/components/ui/card'
import { SourceDisplay } from './SourceDisplay'

interface MessageListProps {
  messages: ChatMessage[]
  isTyping?: boolean
}

export function MessageList({ messages, isTyping }: MessageListProps) {
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
        <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
          <Bot className="w-16 h-16 mb-4 text-primary-500" />
          <h3 className="text-lg font-semibold mb-2">
            Chào mừng đến với Chatbot Tư vấn Tuyển sinh Quân đội
          </h3>
          <p className="text-sm max-w-md">
            Hãy hỏi tôi về điểm chuẩn, quy chế tuyển sinh, hoặc bất kỳ thông tin nào liên quan đến tuyển sinh quân đội Việt Nam.
          </p>
        </div>
      )}

      {messages.map((message, index) => (
        <div
          key={index}
          className={`flex gap-3 animate-fade-in ${
            message.role === 'user' ? 'justify-end' : 'justify-start'
          }`}
        >
          {message.role === 'assistant' && (
            <div className="flex-shrink-0">
              <div className="w-8 h-8 rounded-full bg-military-600 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
            </div>
          )}

          <div className={`flex flex-col max-w-[80%] ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
            <Card
              className={`p-3 ${
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-card border'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </Card>

            {message.sources && message.sources.length > 0 && (
              <SourceDisplay sources={message.sources} />
            )}

            <span className="text-xs text-muted-foreground mt-1">
              {new Date(message.timestamp).toLocaleTimeString('vi-VN')}
            </span>
          </div>

          {message.role === 'user' && (
            <div className="flex-shrink-0">
              <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center">
                <User className="w-5 h-5 text-white" />
              </div>
            </div>
          )}
        </div>
      ))}

      {isTyping && (
        <div className="flex gap-3 justify-start animate-fade-in">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 rounded-full bg-military-600 flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
          </div>
          <Card className="p-3 bg-card border">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-military-600 rounded-full typing-dot"></div>
              <div className="w-2 h-2 bg-military-600 rounded-full typing-dot"></div>
              <div className="w-2 h-2 bg-military-600 rounded-full typing-dot"></div>
            </div>
          </Card>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}
