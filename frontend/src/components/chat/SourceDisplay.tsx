import { FileText, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { Source } from '@/types'

interface SourceDisplayProps {
  sources: Source[]
}

export function SourceDisplay({ sources }: SourceDisplayProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!sources || sources.length === 0) return null

  return (
    <div className="mt-2 w-full">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1.5 text-[12px] text-indigo-500 dark:text-indigo-400/70 hover:text-indigo-600 dark:hover:text-indigo-400 font-medium transition-colors"
      >
        <FileText className="w-3 h-3" />
        <span>{sources.length} nguồn tham khảo</span>
        {isExpanded ? (
          <ChevronUp className="w-3 h-3" />
        ) : (
          <ChevronDown className="w-3 h-3" />
        )}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <div className="mt-2 space-y-2">
              {sources.map((source, index) => (
                <div
                  key={index}
                  className="p-3 rounded-xl bg-gray-50 dark:bg-white/[0.02] border border-gray-200 dark:border-white/[0.05]"
                >
                  <div className="flex items-start gap-2.5">
                    <FileText className="w-3.5 h-3.5 text-indigo-400 dark:text-indigo-400/50 flex-shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] font-medium text-gray-700 dark:text-white/70 mb-0.5">
                        {source.title}
                      </p>
                      <p className="text-[11px] text-gray-400 dark:text-white/30 line-clamp-2 leading-relaxed">
                        {source.content}
                      </p>
                      {source.score && (
                        <p className="text-[11px] text-indigo-500 dark:text-indigo-400/50 mt-1">
                          Độ liên quan: {(source.score * 100).toFixed(0)}%
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
