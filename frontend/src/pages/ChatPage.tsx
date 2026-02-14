import { useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
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
    const userMessage: ChatMessage = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    addMessage(userMessage)
    setIsLoading(true)
    setIsTyping(true)

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
    <div className="flex flex-col h-screen bg-gradient-chat">
      {/* Header */}
      <header className="border-b border-border/40 glass-strong">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-military rounded-xl flex items-center justify-center shadow-soft-sm">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tighter text-foreground">
                TSBot
              </h1>
              <p className="text-xs text-muted-foreground">
                Tư vấn tuyển sinh quân đội
              </p>
            </div>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleResetChat}
            className="gap-2 text-muted-foreground hover:text-foreground"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Cuộc trò chuyện mới</span>
          </Button>
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 flex flex-col max-w-4xl w-full mx-auto overflow-hidden">
        <MessageList
          messages={messages}
          isTyping={isTyping}
          onSuggestionClick={handleSendMessage}
        />
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isLoading}
          isLoading={isLoading}
        />
      </main>

      {/* Footer */}
      <footer className="py-3 px-6">
        <p className="text-center text-[11px] text-muted-foreground/60">
          Thông tin chỉ mang tính tham khảo. Vui lòng kiểm tra lại với cơ quan chức năng.
        </p>
      </footer>
    </div>
  )
}
