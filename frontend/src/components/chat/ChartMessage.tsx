import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { ChartData } from '@/types'

// Military theme palette — cycles through series
const SERIES_COLORS = [
  '#1e3a5f', // navy
  '#4a7c59', // olive green
  '#c5a028', // gold
  '#2e6da4', // steel blue
  '#8b4513', // saddle brown
  '#5f8e72', // sage
]

interface ChartMessageProps {
  chartData: ChartData
}

// Recharts requires a flat array of objects where each key is a series name
function buildChartRows(chartData: ChartData): Record<string, number | string>[] {
  if (chartData.type === 'bar' && chartData.series.length > 0) {
    // Bar: one row per x-value (nganh name), one key per series
    const rowMap = new Map<string, Record<string, number | string>>()
    for (const series of chartData.series) {
      for (const pt of series.data) {
        const key = String(pt.x)
        if (!rowMap.has(key)) rowMap.set(key, { label: key })
        rowMap.get(key)![series.name] = pt.y
      }
    }
    return Array.from(rowMap.values())
  }

  // Line / scatter: one row per year (x numeric), one key per series
  const rowMap = new Map<number | string, Record<string, number | string>>()
  for (const series of chartData.series) {
    for (const pt of series.data) {
      if (!rowMap.has(pt.x)) rowMap.set(pt.x, { nam: pt.x })
      rowMap.get(pt.x)![series.name] = pt.y
    }
  }
  return Array.from(rowMap.values()).sort((a, b) =>
    Number(a.nam) - Number(b.nam)
  )
}

function ViTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-md text-sm">
      <p className="font-semibold mb-1 text-foreground">{label}</p>
      {payload.map((entry: any) => (
        <p key={entry.name} style={{ color: entry.color }}>
          {entry.name}: <span className="font-medium">{entry.value} điểm</span>
        </p>
      ))}
    </div>
  )
}

export function ChartMessage({ chartData }: ChartMessageProps) {
  const rows = buildChartRows(chartData)
  const seriesNames = chartData.series.map((s) => s.name)

  return (
    <div className="mt-3 rounded-xl border border-border/40 bg-card p-4 shadow-message">
      <p className="text-xs font-semibold text-muted-foreground mb-3 leading-tight">
        {chartData.title}
      </p>

      <ResponsiveContainer width="100%" height={280}>
        {chartData.type === 'bar' ? (
          <BarChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10 }}
              angle={-35}
              textAnchor="end"
              interval={0}
            />
            <YAxis
              domain={['auto', 'auto']}
              tick={{ fontSize: 10 }}
              label={{ value: 'Điểm', angle: -90, position: 'insideLeft', offset: 10, fontSize: 10 }}
            />
            <Tooltip content={<ViTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
            {seriesNames.map((name, i) => (
              <Bar
                key={name}
                dataKey={name}
                fill={SERIES_COLORS[i % SERIES_COLORS.length]}
                radius={[3, 3, 0, 0]}
              />
            ))}
          </BarChart>
        ) : (
          <LineChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="nam" tick={{ fontSize: 11 }} />
            <YAxis
              domain={['auto', 'auto']}
              tick={{ fontSize: 11 }}
              label={{ value: 'Điểm', angle: -90, position: 'insideLeft', offset: 10, fontSize: 10 }}
            />
            <Tooltip content={<ViTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {seriesNames.map((name, i) => (
              <Line
                key={name}
                type="monotone"
                dataKey={name}
                stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  )
}
