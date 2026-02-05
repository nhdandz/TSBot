import { useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, User, Sparkles } from 'lucide-react'
import type { ChatMessage } from '@/types'
import { SourceDisplay } from './SourceDisplay'

interface MessageListProps {
  messages: ChatMessage[]
  isTyping?: boolean
}

const ease = [0.22, 1, 0.36, 1] as const

export function MessageList({ messages, isTyping }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  return (
    <div className="flex-1 overflow-y-auto px-5 py-6 space-y-5 scrollbar-thin">
      {messages.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, ease }}
          >
            <div className="w-16 h-16 rounded-2xl bg-indigo-50 dark:bg-indigo-500/[0.08] border border-indigo-200/60 dark:border-indigo-500/[0.12] flex items-center justify-center mb-5">
              <Sparkles className="w-7 h-7 text-indigo-500 dark:text-indigo-400" />
            </div>
          </motion.div>
          <motion.h3
            className="text-lg font-semibold tracking-tight text-gray-800 dark:text-white/80 mb-2"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1, ease }}
          >
            Chào mừng đến với TSBot
          </motion.h3>
          <motion.p
            className="text-[13px] text-gray-400 dark:text-white/30 max-w-sm leading-relaxed"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2, ease }}
          >
            Hỏi tôi bất cứ điều gì về điểm chuẩn, quy chế tuyển sinh, hoặc
            thông tin tuyển sinh quân đội Việt Nam.
          </motion.p>

          {/* suggested questions */}
          <motion.div
            className="mt-8 flex flex-wrap justify-center gap-2"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3, ease }}
          >
            {[
              'Điểm chuẩn Học viện Quân y 2024?',
              'Điều kiện thi vào trường quân đội?',
              'Danh sách các trường quân sự?',
            ].map((q) => (
              <span
                key={q}
                className="px-3.5 py-2 rounded-xl bg-gray-50 dark:bg-white/[0.03] border border-gray-200 dark:border-white/[0.06] text-[12px] text-gray-400 dark:text-white/35 cursor-default"
              >
                {q}
              </span>
            ))}
          </motion.div>
        </div>
      )}

      <AnimatePresence mode="popLayout">
        {messages.map((message, index) => (
          <motion.div
            key={index}
            layout
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease }}
            className={`flex gap-3 ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0 mt-0.5">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              </div>
            )}

            <div
              className={`flex flex-col max-w-[80%] ${
                message.role === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              <div
                className={`px-4 py-3 rounded-2xl ${
                  message.role === 'user'
                    ? 'bg-indigo-500 text-white rounded-br-md'
                    : 'bg-white dark:bg-white/[0.04] border border-gray-200 dark:border-white/[0.06] text-gray-800 dark:text-white/80 rounded-bl-md shadow-sm dark:shadow-none'
                }`}
              >
                <p className="text-[14px] leading-relaxed whitespace-pre-wrap">
                  {message.content}
                </p>
              </div>

              {message.sources && message.sources.length > 0 && (
                <SourceDisplay sources={message.sources} />
              )}

              <span className="text-[11px] text-gray-300 dark:text-white/20 mt-1.5 px-1">
                {new Date(message.timestamp).toLocaleTimeString('vi-VN', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>

            {message.role === 'user' && (
              <div className="flex-shrink-0 mt-0.5">
                <div className="w-7 h-7 rounded-lg bg-gray-100 dark:bg-white/[0.08] border border-gray-200 dark:border-white/[0.06] flex items-center justify-center">
                  <User className="w-4 h-4 text-gray-400 dark:text-white/50" />
                </div>
              </div>
            )}
          </motion.div>
        ))}
      </AnimatePresence>

      {/* typing indicator */}
      <AnimatePresence>
        {isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3, ease }}
            className="flex gap-3 justify-start"
          >
            <div className="flex-shrink-0">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
            </div>
            <div className="px-4 py-3.5 rounded-2xl rounded-bl-md bg-white dark:bg-white/[0.04] border border-gray-200 dark:border-white/[0.06] shadow-sm dark:shadow-none">
              <div className="flex gap-1.5">
                <div className="w-1.5 h-1.5 bg-indigo-400 dark:bg-indigo-400/60 rounded-full typing-dot" />
                <div className="w-1.5 h-1.5 bg-indigo-400 dark:bg-indigo-400/60 rounded-full typing-dot" />
                <div className="w-1.5 h-1.5 bg-indigo-400 dark:bg-indigo-400/60 rounded-full typing-dot" />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div ref={messagesEndRef} />
    </div>
  )
}
