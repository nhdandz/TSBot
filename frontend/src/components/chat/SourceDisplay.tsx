import { FileText, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { Card } from '@/components/ui/card'
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
        className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700 font-medium"
      >
        <FileText className="w-3 h-3" />
        <span>{sources.length} nguồn tham khảo</span>
        {isExpanded ? (
          <ChevronUp className="w-3 h-3" />
        ) : (
          <ChevronDown className="w-3 h-3" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-2">
          {sources.map((source, index) => (
            <Card key={index} className="p-3 bg-muted/50 border">
              <div className="flex items-start gap-2">
                <FileText className="w-4 h-4 text-military-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-foreground mb-1">
                    {source.title}
                  </p>
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {source.content}
                  </p>
                  {source.score && (
                    <p className="text-xs text-military-600 mt-1">
                      Độ liên quan: {(source.score * 100).toFixed(1)}%
                    </p>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
