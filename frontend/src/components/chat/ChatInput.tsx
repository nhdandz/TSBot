import { useState, KeyboardEvent } from 'react'
import { motion } from 'framer-motion'
import { ArrowUp, Loader2 } from 'lucide-react'

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

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const canSend = message.trim() && !disabled && !isLoading

  return (
    <motion.div
      className="relative z-10 border-t border-gray-200/80 dark:border-white/[0.04] bg-white/60 dark:bg-[#08080c]/60 backdrop-blur-xl px-5 py-4 transition-colors duration-300"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="relative flex items-end gap-3 max-w-3xl mx-auto">
        <div className="flex-1 relative">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Nhập câu hỏi của bạn..."
            disabled={disabled || isLoading}
            rows={1}
            className="w-full resize-none rounded-xl bg-gray-50 dark:bg-white/[0.04] border border-gray-200 dark:border-white/[0.08] px-4 py-3 text-[14px] text-gray-900 dark:text-white/90 placeholder:text-gray-300 dark:placeholder:text-white/25 focus:outline-none focus:border-indigo-300 dark:focus:border-indigo-500/30 focus:bg-white dark:focus:bg-white/[0.06] transition-all disabled:opacity-40"
            style={{ minHeight: '44px', maxHeight: '120px' }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement
              target.style.height = 'auto'
              target.style.height = Math.min(target.scrollHeight, 120) + 'px'
            }}
          />
        </div>
        <button
          onClick={handleSend}
          disabled={!canSend}
          className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
            canSend
              ? 'bg-indigo-500 hover:bg-indigo-600 text-white shadow-[0_0_20px_rgba(99,102,241,0.25)]'
              : 'bg-gray-100 dark:bg-white/[0.04] text-gray-300 dark:text-white/20 cursor-not-allowed'
          }`}
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <ArrowUp className="w-4 h-4" />
          )}
        </button>
      </div>
      <p className="text-center text-[11px] text-gray-300 dark:text-white/15 mt-3">
        Thông tin chỉ mang tính tham khảo. Vui lòng kiểm tra với cơ quan chức năng.
      </p>
    </motion.div>
  )
}
