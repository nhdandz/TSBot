import { useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { MessageList } from '@/components/chat/MessageList'
import { ChatInput } from '@/components/chat/ChatInput'
import { useChatStore } from '@/stores/chatStore'
import { chatService } from '@/services/chatService'
import { Bot, ArrowLeft, RotateCcw } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import type { ChatMessage } from '@/types'

const ease = [0.22, 1, 0.36, 1] as const

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
      title: 'Đã reset',
      description: 'Bạn có thể bắt đầu cuộc trò chuyện mới.',
    })
  }

  return (
    <div className="flex flex-col h-screen bg-[#fafafa] dark:bg-[#08080c] noise-bg transition-colors duration-300">
      {/* ambient glows */}
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute top-[-20%] left-1/2 -translate-x-1/2 w-[700px] h-[500px] rounded-full bg-indigo-200/30 dark:bg-indigo-500/[0.05] blur-[120px] transition-colors duration-500" />
      </div>

      {/* header */}
      <motion.header
        className="relative z-20 border-b border-gray-200/80 dark:border-white/[0.06] bg-white/60 dark:bg-[#08080c]/60 backdrop-blur-2xl transition-colors duration-300"
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease }}
      >
        <div className="max-w-5xl mx-auto px-5 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="flex items-center justify-center w-8 h-8 rounded-lg bg-gray-100 dark:bg-white/[0.04] border border-gray-200 dark:border-white/[0.06] text-gray-400 dark:text-white/40 hover:text-gray-700 dark:hover:text-white/80 hover:bg-gray-200 dark:hover:bg-white/[0.07] transition-all"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center">
                <Bot className="w-[18px] h-[18px] text-white" />
              </div>
              <div>
                <h1 className="text-[14px] font-semibold tracking-tight text-gray-900 dark:text-white/90">
                  TSBot
                </h1>
                <p className="text-[11px] text-gray-400 dark:text-white/30 leading-none">
                  AI Tư vấn tuyển sinh
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <button
              onClick={handleResetChat}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-white/[0.04] border border-gray-200 dark:border-white/[0.06] text-[12px] font-medium text-gray-400 dark:text-white/40 hover:text-gray-700 dark:hover:text-white/80 hover:bg-gray-200 dark:hover:bg-white/[0.07] transition-all"
            >
              <RotateCcw className="w-3 h-3" />
              <span className="hidden sm:inline">Cuộc trò chuyện mới</span>
            </button>
          </div>
        </div>
      </motion.header>

      {/* chat area */}
      <main className="relative z-10 flex-1 flex flex-col max-w-3xl w-full mx-auto overflow-hidden">
        <MessageList messages={messages} isTyping={isTyping} />
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isLoading}
          isLoading={isLoading}
        />
      </main>
    </div>
  )
}
