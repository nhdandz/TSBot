import { FileText, ChevronDown } from 'lucide-react'
import { useState } from 'react'
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
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-muted-foreground font-medium hover:bg-muted/40 transition-all duration-300 ease-apple group"
      >
        <FileText className="w-3 h-3 text-olive" />
        <span>{sources.length} nguồn tham khảo</span>
        <ChevronDown className={`w-3 h-3 transition-transform duration-300 ease-apple ${isExpanded ? 'rotate-180' : ''}`} />
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-1.5 animate-fade-in">
          {sources.map((source, index) => (
            <div
              key={index}
              className="flex items-start gap-3 p-3 rounded-xl bg-muted/30 border border-border/30 hover:bg-muted/50 transition-all duration-200 ease-apple"
            >
              <div className="w-7 h-7 rounded-lg bg-olive/10 flex items-center justify-center shrink-0 mt-0.5">
                <FileText className="w-3.5 h-3.5 text-olive" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-foreground mb-0.5 line-clamp-1">
                  {source.title}
                </p>
                <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                  {source.content}
                </p>
                {source.score && (
                  <div className="flex items-center gap-1.5 mt-1.5">
                    <div className="h-1 flex-1 max-w-[60px] rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full rounded-full bg-olive transition-all duration-500"
                        style={{ width: `${source.score * 100}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-muted-foreground/60">
                      {(source.score * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
