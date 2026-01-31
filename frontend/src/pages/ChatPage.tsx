import { useEffect, useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { MessageList } from '@/components/chat/MessageList'
import { ChatInput } from '@/components/chat/ChatInput'
import { useChatStore } from '@/stores/chatStore'
import { chatService } from '@/services/chatService'
import { Button } from '@/components/ui/button'
import { RefreshCw, Shield } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import type { ChatMessage } from '@/types'

export default function ChatPage() {
  const { toast } = useToast()
  const {
    messages,
    sessionId,
    isLoading,
    isTyping,
    addMessage,
    setMessages,
    setIsLoading,
    setIsTyping,
    setError,
    resetSession,
  } = useChatStore()

  // Load chat history on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await chatService.getChatHistory(sessionId)
        const formattedMessages: ChatMessage[] = history.map((msg) => ({
          ...msg,
          sources: [],
        }))
        setMessages(formattedMessages)
      } catch (error) {
        console.error('Failed to load chat history:', error)
      }
    }
    loadHistory()
  }, [sessionId, setMessages])

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: chatService.sendMessage,
    onSuccess: (data) => {
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.response,
        timestamp: data.timestamp,
        sources: data.sources,
        intent: data.intent,
      }
      addMessage(assistantMessage)
      setIsLoading(false)
      setIsTyping(false)
    },
    onError: (error: any) => {
      setIsLoading(false)
      setIsTyping(false)
      setError(error.detail || 'Lỗi khi gửi tin nhắn')
      toast({
        title: 'Lỗi',
        description: error.detail || 'Không thể gửi tin nhắn. Vui lòng thử lại.',
        variant: 'destructive',
      })
    },
  })

  const handleSendMessage = async (content: string) => {
    // Add user message immediately
    const userMessage: ChatMessage = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    addMessage(userMessage)
    setIsLoading(true)
    setIsTyping(true)

    // Send to API
    sendMessageMutation.mutate({
      message: content,
      session_id: sessionId,
    })
  }

  const handleResetChat = () => {
    resetSession()
    toast({
      title: 'Đã reset cuộc trò chuyện',
      description: 'Bạn có thể bắt đầu một cuộc trò chuyện mới.',
    })
  }

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-primary-50 via-background to-military-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-military-600 to-primary-600 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">
                TSBot - Tư vấn Tuyển sinh Quân đội
              </h1>
              <p className="text-xs text-muted-foreground">
                Chatbot AI hỗ trợ thí sinh tìm hiểu về tuyển sinh quân sự Việt Nam
              </p>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleResetChat}
            className="gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Reset
          </Button>
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 flex flex-col max-w-5xl w-full mx-auto bg-white/60 backdrop-blur-sm shadow-lg my-4 rounded-lg overflow-hidden">
        <MessageList messages={messages} isTyping={isTyping} />
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isLoading}
          isLoading={isLoading}
        />
      </main>

      {/* Footer */}
      <footer className="border-t bg-white/80 backdrop-blur-sm py-3">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-muted-foreground">
          <p>
            © 2026 TSBot - Hệ thống chatbot AI tư vấn tuyển sinh quân đội. Phát triển bởi AI Team.
          </p>
          <p className="mt-1">
            Thông tin chỉ mang tính tham khảo. Vui lòng kiểm tra lại với cơ quan chức năng.
          </p>
        </div>
      </footer>
    </div>
  )
}
