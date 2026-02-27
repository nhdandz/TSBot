import { FileText, X } from 'lucide-react'
import { useState } from 'react'
import type { Source } from '@/types'
import { MarkdownContent } from './MarkdownContent'

interface SourceDisplayProps {
  sources: Source[]
}

function ScoreBadge({ score }: { score: number }) {
  const percent = Math.round(score * 100)
  const color =
    percent >= 80
      ? 'bg-emerald-500/15 text-emerald-600 border-emerald-500/20'
      : percent >= 60
        ? 'bg-amber-500/15 text-amber-600 border-amber-500/20'
        : 'bg-red-500/15 text-red-600 border-red-500/20'

  return (
    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-md border ${color}`}>
      {percent}%
    </span>
  )
}

function getSourceTitle(source: Source): string {
  if (source.legal_path) return source.legal_path
  if (source.article) return `Điều ${source.article}`
  if (source.document) return source.document
  if (source.title) return source.title
  return 'Nguồn tham khảo'
}

function getSourceContent(source: Source): string {
  return source.content || source.content_preview || ''
}

export function SourceDisplay({ sources }: SourceDisplayProps) {
  const [selectedSource, setSelectedSource] = useState<Source | null>(null)

  if (!sources || sources.length === 0) return null

  return (
    <>
      {/* Source badges */}
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <FileText className="w-3 h-3 text-olive" />
        {sources.map((source, index) => (
          <button
            key={index}
            onClick={() => setSelectedSource(source)}
            className="inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-[11px] font-medium bg-muted/40 border border-border/30 text-muted-foreground hover:bg-muted/70 hover:text-foreground hover:border-border/60 transition-all duration-200 cursor-pointer"
            title={getSourceTitle(source)}
          >
            <span>[{index + 1}]</span>
            {source.score != null && <ScoreBadge score={source.score} />}
          </button>
        ))}
      </div>

      {/* Modal */}
      {selectedSource && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedSource(null)}
        >
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-fade-in" />

          <div
            className="relative z-10 w-full max-w-lg max-h-[80vh] bg-background border border-border/60 rounded-2xl shadow-xl animate-scale-in flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-3 p-5 border-b border-border/40">
              <div className="flex items-start gap-3 min-w-0">
                <div className="w-9 h-9 rounded-xl bg-olive/10 flex items-center justify-center shrink-0">
                  <FileText className="w-4 h-4 text-olive" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-semibold text-foreground leading-snug">
                    {getSourceTitle(selectedSource)}
                  </h3>
                  {selectedSource.score != null && (
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className="text-[11px] text-muted-foreground">Độ liên quan:</span>
                      <div className="flex items-center gap-1.5">
                        <div className="h-1.5 w-20 rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full rounded-full bg-olive transition-all duration-500"
                            style={{ width: `${selectedSource.score * 100}%` }}
                          />
                        </div>
                        <ScoreBadge score={selectedSource.score} />
                      </div>
                    </div>
                  )}
                  {/* Extra info */}
                  <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
                    {selectedSource.document && (
                      <span className="text-[11px] text-muted-foreground">
                        📄 {selectedSource.document}
                      </span>
                    )}
                    {selectedSource.chapter && (
                      <span className="text-[11px] text-muted-foreground">
                        📑 {selectedSource.chapter}
                      </span>
                    )}
                    {selectedSource.article && (
                      <span className="text-[11px] text-muted-foreground">
                        📌 Điều {selectedSource.article}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <button
                onClick={() => setSelectedSource(null)}
                className="p-1.5 rounded-lg hover:bg-muted/60 text-muted-foreground hover:text-foreground transition-colors shrink-0"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-5 scrollbar-thin">
              {getSourceContent(selectedSource) ? (
                <div className="text-sm text-foreground/90 leading-relaxed">
                  <MarkdownContent content={getSourceContent(selectedSource)} />
                </div>
              ) : (
                <p className="text-sm text-muted-foreground italic">
                  Không có nội dung trích dẫn.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
