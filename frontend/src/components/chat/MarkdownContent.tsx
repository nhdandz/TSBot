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
          // Headings với spacing tốt hơn
          h1: ({ ...props }) => (
            <h1 className="text-xl font-bold text-gray-900 mt-4 mb-3 first:mt-0" {...props} />
          ),
          h2: ({ ...props }) => (
            <h2 className="text-lg font-semibold text-gray-900 mt-4 mb-2 first:mt-0" {...props} />
          ),
          h3: ({ ...props }) => (
            <h3 className="text-base font-semibold text-gray-800 mt-3 mb-2 first:mt-0" {...props} />
          ),

          // Paragraphs với spacing tốt
          p: ({ ...props }) => (
            <p className="mb-3 leading-relaxed text-gray-700 last:mb-0" {...props} />
          ),

          // Lists với spacing và indent tốt hơn
          ul: ({ ...props }) => (
            <ul className="mb-3 space-y-1.5 pl-6 list-disc" {...props} />
          ),
          ol: ({ ...props }) => (
            <ol className="mb-3 space-y-1.5 pl-6 list-decimal" {...props} />
          ),
          li: ({ ...props }) => (
            <li className="leading-relaxed text-gray-700" {...props} />
          ),

          // Code blocks
          code: ({ ...props }) => (
            <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800" {...props} />
          ),

          // Pre (code blocks)
          pre: ({ ...props }) => (
            <pre className="bg-gray-100 p-3 rounded-lg my-3 overflow-x-auto" {...props} />
          ),

          // Blockquotes
          blockquote: ({ ...props }) => (
            <blockquote className="border-l-4 border-primary-500 pl-4 py-2 my-3 italic text-gray-600 bg-gray-50 rounded-r" {...props} />
          ),

          // Links
          a: ({ ...props }) => (
            <a className="text-primary-600 hover:text-primary-700 hover:underline font-medium" target="_blank" rel="noopener noreferrer" {...props} />
          ),

          // Strong/Bold
          strong: ({ ...props }) => (
            <strong className="font-bold text-gray-900" {...props} />
          ),

          // Emphasis/Italic
          em: ({ ...props }) => (
            <em className="italic text-gray-700" {...props} />
          ),

          // Horizontal rule
          hr: ({ ...props }) => (
            <hr className="my-4 border-gray-300" {...props} />
          ),

          // Tables
          table: ({ ...props }) => (
            <div className="overflow-x-auto my-3">
              <table className="min-w-full border border-gray-300" {...props} />
            </div>
          ),
          thead: ({ ...props }) => (
            <thead className="bg-gray-100" {...props} />
          ),
          tbody: ({ ...props }) => (
            <tbody {...props} />
          ),
          tr: ({ ...props }) => (
            <tr className="border-b border-gray-200" {...props} />
          ),
          th: ({ ...props }) => (
            <th className="px-4 py-2 text-left font-semibold text-gray-900" {...props} />
          ),
          td: ({ ...props }) => (
            <td className="px-4 py-2 text-gray-700" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
