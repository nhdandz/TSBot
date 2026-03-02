import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
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
import { adminService } from '@/services/adminService'
import { useForm } from 'react-hook-form'
import { TrendingUp, BarChart2, Activity, Info } from 'lucide-react'

// ─── colour palette ────────────────────────────────────────────────────────
const COLORS = ['#1e3a5f', '#4a7c59', '#c5a028', '#2e6da4', '#8b4513']

// ─── Filter form shape ──────────────────────────────────────────────────────
interface FilterValues {
  truong: string
  nganh: string
  ma_khoi: string
  gioi_tinh: string
  khu_vuc: string
  nam: string
}

// ─── Tooltip ────────────────────────────────────────────────────────────────
function ViTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-md text-sm">
      <p className="font-semibold mb-1">{label}</p>
      {payload.map((e: any) => (
        <p key={e.name} style={{ color: e.color }}>
          {e.name}: <span className="font-medium">{e.value} điểm</span>
        </p>
      ))}
    </div>
  )
}

// ─── Section card wrapper ────────────────────────────────────────────────────
function Section({
  title,
  icon: Icon,
  children,
}: {
  title: string
  icon: React.ElementType
  children: React.ReactNode
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <Icon className="w-4 h-4 text-muted-foreground" />
        <h2 className="text-sm font-semibold text-foreground">{title}</h2>
      </div>
      {children}
    </div>
  )
}

// ─── Main page ───────────────────────────────────────────────────────────────
export default function AnalyticsPage() {
  const { register, watch, handleSubmit } = useForm<FilterValues>({
    defaultValues: {
      truong: 'hoc vien ky thuat quan su',
      nganh: '',
      ma_khoi: '',
      gioi_tinh: '',
      khu_vuc: '',
      nam: '2024',
    },
  })

  const [appliedFilters, setAppliedFilters] = useState<FilterValues>({
    truong: 'hoc vien ky thuat quan su',
    nganh: '',
    ma_khoi: '',
    gioi_tinh: '',
    khu_vuc: '',
    nam: '2024',
  })

  const onApply = (values: FilterValues) => setAppliedFilters(values)

  // ── Trend query ──────────────────────────────────────────────────────────
  const trendQuery = useQuery({
    queryKey: ['analytics-trend', appliedFilters],
    queryFn: () =>
      adminService.getAnalyticsTrend({
        truong: appliedFilters.truong || undefined,
        nganh: appliedFilters.nganh || undefined,
        ma_khoi: appliedFilters.ma_khoi || undefined,
        gioi_tinh: appliedFilters.gioi_tinh || undefined,
        khu_vuc: appliedFilters.khu_vuc || undefined,
      }),
  })

  // ── Compare query ────────────────────────────────────────────────────────
  const compareQuery = useQuery({
    queryKey: ['analytics-compare', appliedFilters.nam, appliedFilters.ma_khoi, appliedFilters.gioi_tinh],
    queryFn: () =>
      adminService.getAnalyticsCompare({
        nam: appliedFilters.nam ? Number(appliedFilters.nam) : undefined,
        ma_khoi: appliedFilters.ma_khoi || undefined,
        gioi_tinh: appliedFilters.gioi_tinh || undefined,
      }),
  })

  // ── Distribution query ───────────────────────────────────────────────────
  const distQuery = useQuery({
    queryKey: ['analytics-dist', appliedFilters.nam, appliedFilters.ma_khoi],
    queryFn: () =>
      adminService.getAnalyticsDistribution({
        nam: appliedFilters.nam ? Number(appliedFilters.nam) : undefined,
        ma_khoi: appliedFilters.ma_khoi || undefined,
      }),
  })

  // ─── Derived data for charts ─────────────────────────────────────────────
  const trendRows = (trendQuery.data?.data_points ?? []).map((p) => ({
    nam: p.nam,
    'Điểm TB': p.diem_chuan,
  }))

  const compareRows = (compareQuery.data ?? []).slice(0, 15).map((s) => ({
    label: s.ten_truong.length > 20 ? s.ten_truong.slice(0, 20) + '…' : s.ten_truong,
    'TB': s.diem_trung_binh,
    'Cao nhất': s.diem_cao_nhat,
    'Thấp nhất': s.diem_thap_nhat,
  }))

  const distRows = (distQuery.data?.bins ?? []).map((b, i) => ({
    bin: b,
    'Số lượng': distQuery.data!.counts[i],
  }))

  const pred = trendQuery.data?.prediction
  const reg = trendQuery.data?.regression

  return (
    <div className="space-y-6">
      {/* Page title */}
      <div>
        <h1 className="text-xl font-bold tracking-tight text-foreground">Phân tích & Dự đoán</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Xu hướng điểm chuẩn, so sánh trường và dự đoán năm tiếp theo
        </p>
      </div>

      {/* ── Filter bar ──────────────────────────────────────────────────── */}
      <form
        onSubmit={handleSubmit(onApply)}
        className="flex flex-wrap gap-3 items-end rounded-xl border border-border bg-card p-4"
      >
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Trường (không dấu)</label>
          <input
            {...register('truong')}
            className="h-8 rounded-md border border-input bg-background px-2 text-sm w-52"
            placeholder="hoc vien ky thuat quan su"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Khối thi</label>
          <select
            {...register('ma_khoi')}
            className="h-8 rounded-md border border-input bg-background px-2 text-sm"
          >
            <option value="">Tất cả</option>
            <option value="A00">A00</option>
            <option value="A01">A01</option>
            <option value="B00">B00</option>
            <option value="C00">C00</option>
            <option value="D01">D01</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Giới tính</label>
          <select
            {...register('gioi_tinh')}
            className="h-8 rounded-md border border-input bg-background px-2 text-sm"
          >
            <option value="">Tất cả</option>
            <option value="nam">Nam</option>
            <option value="nu">Nữ</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Khu vực</label>
          <select
            {...register('khu_vuc')}
            className="h-8 rounded-md border border-input bg-background px-2 text-sm"
          >
            <option value="">Tất cả</option>
            <option value="mien_bac">Miền Bắc</option>
            <option value="mien_nam">Miền Nam</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Năm so sánh</label>
          <select
            {...register('nam')}
            className="h-8 rounded-md border border-input bg-background px-2 text-sm"
          >
            <option value="">Tất cả</option>
            <option value="2024">2024</option>
            <option value="2023">2023</option>
          </select>
        </div>
        <button
          type="submit"
          className="h-8 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          Áp dụng
        </button>
      </form>

      {/* ── Row 1: Trend + Compare ───────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trend */}
        <Section title="Xu hướng điểm qua các năm" icon={TrendingUp}>
          {trendQuery.isLoading ? (
            <div className="h-60 flex items-center justify-center text-sm text-muted-foreground">
              Đang tải...
            </div>
          ) : trendRows.length === 0 ? (
            <div className="h-60 flex items-center justify-center text-sm text-muted-foreground">
              Không có dữ liệu
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trendRows} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="nam" tick={{ fontSize: 11 }} />
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 11 }} />
                <Tooltip content={<ViTooltip />} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line
                  type="monotone"
                  dataKey="Điểm TB"
                  stroke={COLORS[0]}
                  strokeWidth={2}
                  dot={{ r: 5 }}
                  activeDot={{ r: 7 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </Section>

        {/* Compare */}
        <Section title="So sánh các trường" icon={BarChart2}>
          {compareQuery.isLoading ? (
            <div className="h-60 flex items-center justify-center text-sm text-muted-foreground">
              Đang tải...
            </div>
          ) : compareRows.length === 0 ? (
            <div className="h-60 flex items-center justify-center text-sm text-muted-foreground">
              Không có dữ liệu
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={compareRows}
                layout="vertical"
                margin={{ top: 4, right: 16, left: 8, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis type="number" domain={['auto', 'auto']} tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="label" width={130} tick={{ fontSize: 10 }} />
                <Tooltip content={<ViTooltip />} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="TB" fill={COLORS[0]} radius={[0, 3, 3, 0]} />
                <Bar dataKey="Cao nhất" fill={COLORS[2]} radius={[0, 3, 3, 0]} />
                <Bar dataKey="Thấp nhất" fill={COLORS[1]} radius={[0, 3, 3, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Section>
      </div>

      {/* ── Row 2: Prediction + Distribution ────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Prediction */}
        <Section title="Dự đoán năm tiếp theo" icon={Info}>
          {trendQuery.isLoading ? (
            <div className="text-sm text-muted-foreground">Đang tải...</div>
          ) : !pred ? (
            <p className="text-sm text-muted-foreground">
              Không đủ dữ liệu để dự đoán (cần ít nhất 2 năm).
            </p>
          ) : (
            <div className="space-y-3">
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-foreground">
                  {pred.diem_du_doan}
                </span>
                <span className="text-sm text-muted-foreground">điểm dự đoán năm {pred.nam_toi}</span>
              </div>

              <div className="flex gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground text-xs">Confidence</p>
                  <p className="font-semibold">{Math.round(pred.confidence * 100)}%</p>
                </div>
                {reg && (
                  <>
                    <div>
                      <p className="text-muted-foreground text-xs">R²</p>
                      <p className="font-semibold">{reg.r_squared}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">Slope</p>
                      <p className="font-semibold">{reg.slope > 0 ? '+' : ''}{reg.slope}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">Số năm</p>
                      <p className="font-semibold">{reg.n_points}</p>
                    </div>
                  </>
                )}
              </div>

              {pred.disclaimer && (
                <p className="text-xs text-amber-600 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg px-3 py-2">
                  ⚠ {pred.disclaimer}
                </p>
              )}
            </div>
          )}
        </Section>

        {/* Distribution */}
        <Section title="Phân phối điểm chuẩn" icon={Activity}>
          {distQuery.isLoading ? (
            <div className="h-60 flex items-center justify-center text-sm text-muted-foreground">
              Đang tải...
            </div>
          ) : distRows.length === 0 ? (
            <div className="h-60 flex items-center justify-center text-sm text-muted-foreground">
              Không có dữ liệu
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={distRows} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="bin" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip content={<ViTooltip />} />
                <Bar dataKey="Số lượng" fill={COLORS[1]} radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Section>
      </div>
    </div>
  )
}
