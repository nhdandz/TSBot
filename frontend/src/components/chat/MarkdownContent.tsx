import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkBreaks from 'remark-breaks'

interface MarkdownContentProps {
  content: string
  className?: string
}

export function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkBreaks]}
        components={{
          h1: ({ ...props }) => (
            <h1 className="text-xl font-bold text-foreground mt-4 mb-3 first:mt-0" {...props} />
          ),
          h2: ({ ...props }) => (
            <h2 className="text-lg font-semibold text-foreground mt-4 mb-2 first:mt-0" {...props} />
          ),
          h3: ({ ...props }) => (
            <h3 className="text-base font-semibold text-foreground/90 mt-3 mb-2 first:mt-0" {...props} />
          ),
          p: ({ ...props }) => (
            <p className="mb-3 leading-relaxed text-foreground/80 last:mb-0 text-sm" {...props} />
          ),
          ul: ({ ...props }) => (
            <ul className="mb-3 space-y-1.5 pl-6 list-disc" {...props} />
          ),
          ol: ({ ...props }) => (
            <ol className="mb-3 space-y-1.5 pl-6 list-decimal" {...props} />
          ),
          li: ({ ...props }) => (
            <li className="leading-relaxed text-foreground/80 text-sm" {...props} />
          ),
          code: ({ ...props }) => (
            <code className="bg-muted/60 px-1.5 py-0.5 rounded-md text-[13px] font-mono text-foreground/80" {...props} />
          ),
          pre: ({ ...props }) => (
            <pre className="bg-muted/40 p-4 rounded-xl my-3 overflow-x-auto border border-border/40" {...props} />
          ),
          blockquote: ({ ...props }) => (
            <blockquote className="border-l-4 border-olive pl-4 py-2 my-3 italic text-muted-foreground bg-muted/30 rounded-r-lg" {...props} />
          ),
          a: ({ ...props }) => (
            <a className="text-primary hover:text-primary/80 hover:underline font-medium transition-colors" target="_blank" rel="noopener noreferrer" {...props} />
          ),
          strong: ({ ...props }) => (
            <strong className="font-bold text-foreground" {...props} />
          ),
          em: ({ ...props }) => (
            <em className="italic text-foreground/80" {...props} />
          ),
          hr: ({ ...props }) => (
            <hr className="my-4 border-border/60" {...props} />
          ),
          table: ({ ...props }) => (
            <div className="overflow-x-auto my-3 rounded-xl border border-border/40">
              <table className="min-w-full" {...props} />
            </div>
          ),
          thead: ({ ...props }) => (
            <thead className="bg-muted/30" {...props} />
          ),
          tbody: ({ ...props }) => (
            <tbody {...props} />
          ),
          tr: ({ ...props }) => (
            <tr className="border-b border-border/40" {...props} />
          ),
          th: ({ ...props }) => (
            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground" {...props} />
          ),
          td: ({ ...props }) => (
            <td className="px-4 py-2 text-sm text-foreground/80" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
