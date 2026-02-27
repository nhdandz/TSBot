import { useEffect, useState } from 'react'
import { MessageSquare, Trash2, Plus, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { chatService } from '@/services/chatService'
import { useChatStore } from '@/stores/chatStore'
import type { ChatSession } from '@/types'
import { cn } from '@/lib/utils'

interface ChatHistoryProps {
  onNewChat: () => void
}

export function ChatHistory({ onNewChat }: ChatHistoryProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(true)
  const { sessionId, setSessionId } = useChatStore()

  const fetchSessions = async () => {
    try {
      setLoading(true)
      const data = await chatService.getChatSessions()
      setSessions(data)
    } catch (error) {
      console.error('Failed to load sessions:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSessions()
  }, [])

  const handleSelectSession = (id: string) => {
    if (id !== sessionId) {
      setSessionId(id)
    }
  }

  const handleDeleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    try {
      await chatService.deleteChatSession(id)
      setSessions((prev) => prev.filter((s) => s.session_id !== id))
      if (id === sessionId) {
        onNewChat()
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Vừa xong'
    if (diffMins < 60) return `${diffMins} phút trước`
    if (diffHours < 24) return `${diffHours} giờ trước`
    if (diffDays < 7) return `${diffDays} ngày trước`
    return date.toLocaleDateString('vi-VN')
  }

  return (
    <div className="flex flex-col h-full">
      {/* New chat button */}
      <div className="p-3">
        <Button
          onClick={onNewChat}
          className="w-full gap-2 bg-gradient-military text-white hover:opacity-90"
          size="sm"
        >
          <Plus className="w-4 h-4" />
          Cuộc trò chuyện mới
        </Button>
      </div>

      {/* Sessions list */}
      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {loading ? (
          <div className="flex items-center justify-center py-8 text-muted-foreground">
            <div className="animate-spin w-5 h-5 border-2 border-current border-t-transparent rounded-full" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground text-sm">
            <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-40" />
            <p>Chưa có cuộc trò chuyện nào</p>
          </div>
        ) : (
          <div className="space-y-1">
            {sessions.map((s) => (
              <button
                key={s.session_id}
                onClick={() => handleSelectSession(s.session_id)}
                className={cn(
                  'w-full text-left px-3 py-2.5 rounded-lg transition-colors group relative',
                  'hover:bg-accent/50',
                  s.session_id === sessionId
                    ? 'bg-accent text-accent-foreground'
                    : 'text-foreground/80'
                )}
              >
                <div className="flex items-start gap-2.5">
                  <MessageSquare className="w-4 h-4 mt-0.5 shrink-0 opacity-50" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate leading-snug">
                      {s.title}
                    </p>
                    <div className="flex items-center gap-1.5 mt-1">
                      <Clock className="w-3 h-3 opacity-40" />
                      <span className="text-xs text-muted-foreground">
                        {formatDate(s.updated_at)}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(e, s.session_id)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-destructive/10 rounded"
                    title="Xóa cuộc trò chuyện"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-destructive/70" />
                  </button>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
