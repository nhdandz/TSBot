import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { MessageList } from '@/components/chat/MessageList'
import { ChatInput } from '@/components/chat/ChatInput'
import { ChatHistory } from '@/components/chat/ChatHistory'
import { useChatStore } from '@/stores/chatStore'
import { chatService } from '@/services/chatService'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { RefreshCw, Shield, History, PanelLeftClose, PanelLeft } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import type { ChatMessage } from '@/types'

export default function ChatPage() {
  const { toast } = useToast()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [desktopSidebar, setDesktopSidebar] = useState(true)
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
          sources: msg.sources || [],
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
    setSidebarOpen(false)
    toast({
      title: 'Đã reset cuộc trò chuyện',
      description: 'Bạn có thể bắt đầu một cuộc trò chuyện mới.',
    })
  }

  return (
    <div className="flex h-screen bg-gradient-chat">
      {/* Desktop Sidebar */}
      <aside
        className={`hidden md:flex flex-col border-r border-border/40 bg-background/80 backdrop-blur-sm transition-all duration-300 ${
          desktopSidebar ? 'w-72' : 'w-0 overflow-hidden'
        }`}
      >
        <ChatHistory onNewChat={handleResetChat} />
      </aside>

      {/* Mobile Sidebar (Sheet) */}
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="left" className="w-80 p-0">
          <SheetHeader className="p-4 border-b border-border/40">
            <SheetTitle className="flex items-center gap-2 text-base">
              <History className="w-4 h-4" />
              Lịch sử trò chuyện
            </SheetTitle>
          </SheetHeader>
          <ChatHistory onNewChat={handleResetChat} />
        </SheetContent>
      </Sheet>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="border-b border-border/40 glass-strong">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Toggle sidebar - desktop */}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setDesktopSidebar(!desktopSidebar)}
                className="hidden md:flex h-9 w-9 text-muted-foreground hover:text-foreground"
              >
                {desktopSidebar ? (
                  <PanelLeftClose className="w-4 h-4" />
                ) : (
                  <PanelLeft className="w-4 h-4" />
                )}
              </Button>

              {/* Toggle sidebar - mobile */}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(true)}
                className="md:hidden h-9 w-9 text-muted-foreground hover:text-foreground"
              >
                <History className="w-4 h-4" />
              </Button>

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

{/* Nút cuộc trò chuyện mới chỉ hiện khi sidebar đang ẩn */}
            {!desktopSidebar && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleResetChat}
                className="hidden md:flex gap-2 text-muted-foreground hover:text-foreground"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Cuộc trò chuyện mới</span>
              </Button>
            )}
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
    </div>
  )
}
