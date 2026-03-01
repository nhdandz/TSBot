import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkBreaks from 'remark-breaks'
import { SortableTable } from './SortableTable'

interface MarkdownContentProps {
  content: string
  className?: string
}

type Segment =
  | { type: 'text'; content: string }
  | { type: 'table'; headers: string[]; rows: string[][] }

function parseContent(content: string): Segment[] {
  const lines = content.split('\n')
  const segments: Segment[] = []
  let textBuffer: string[] = []
  let tableBuffer: string[] = []
  let inTable = false

  const isTableLine = (line: string) => {
    const t = line.trim()
    return t.startsWith('|') && t.endsWith('|') && t.length > 1
  }

  const flushText = () => {
    if (textBuffer.length > 0) {
      segments.push({ type: 'text', content: textBuffer.join('\n') })
      textBuffer = []
    }
  }

  const flushTable = () => {
    // Need at least: header row + separator + one data row
    if (tableBuffer.length < 3) {
      textBuffer.push(...tableBuffer)
      tableBuffer = []
      return
    }
    const parseRow = (line: string) =>
      line.trim().split('|').slice(1, -1).map(c => c.trim())

    const headers = parseRow(tableBuffer[0])
    const rows = tableBuffer.slice(2).map(parseRow)
    segments.push({ type: 'table', headers, rows })
    tableBuffer = []
  }

  for (const line of lines) {
    if (isTableLine(line)) {
      if (!inTable) {
        flushText()
        inTable = true
      }
      tableBuffer.push(line)
    } else {
      if (inTable) {
        flushTable()
        inTable = false
      }
      textBuffer.push(line)
    }
  }

  if (inTable) flushTable()
  else flushText()

  return segments
}

const MD_COMPONENTS = {
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
}

export function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  const segments = parseContent(content)

  return (
    <div className={`markdown-content ${className}`}>
      {segments.map((seg, i) => {
        if (seg.type === 'table') {
          return <SortableTable key={i} headers={seg.headers} rows={seg.rows} />
        }
        return (
          <ReactMarkdown
            key={i}
            remarkPlugins={[remarkGfm, remarkBreaks]}
            components={MD_COMPONENTS}
          >
            {seg.content}
          </ReactMarkdown>
        )
      })}
    </div>
  )
}
