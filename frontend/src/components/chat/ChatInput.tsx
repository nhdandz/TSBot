import { useState, KeyboardEvent } from 'react'
import { ArrowUp, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
  isLoading?: boolean
}

export function ChatInput({ onSendMessage, disabled, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('')

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim())
      setMessage('')
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="p-4 pb-6">
      <div className="max-w-3xl mx-auto">
        <div className="flex gap-3 items-end p-3 rounded-2xl glass-strong border border-border/40 shadow-input-float transition-all duration-300 ease-apple focus-within:shadow-soft-lg focus-within:border-border">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Nhập câu hỏi của bạn..."
            disabled={disabled || isLoading}
            rows={1}
            className="flex-1 bg-transparent border-none outline-none text-sm placeholder:text-muted-foreground/50 disabled:opacity-50 disabled:cursor-not-allowed min-h-[40px] max-h-[120px] resize-none py-1.5 px-1 leading-relaxed"
          />
          <Button
            onClick={handleSend}
            disabled={!message.trim() || disabled || isLoading}
            size="icon"
            className="h-9 w-9 rounded-xl shrink-0 disabled:bg-muted disabled:text-muted-foreground disabled:shadow-none"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <ArrowUp className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
