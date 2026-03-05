const API_BASE = '/api/v1'
const ADMIN_BASE = `${API_BASE}/admin`
const ANALYTICS_BASE = `${API_BASE}/analytics`

export const API_ENDPOINTS = {
  chat: `${API_BASE}/chat`,
  chatStream: `${API_BASE}/chat/stream`,
  feedback: `${API_BASE}/feedback`,
  sessions: `${API_BASE}/sessions`,
  deleteSession: (sessionId: string) => `${API_BASE}/sessions/${sessionId}`,
  history: (sessionId: string) => `${API_BASE}/history/${sessionId}`,
  health: `${API_BASE}/health`,
  admin: {
    login: `${ADMIN_BASE}/login`,
    truong: `${ADMIN_BASE}/truong`,
    nganh: `${ADMIN_BASE}/nganh`,
    khoiThi: `${ADMIN_BASE}/khoi-thi`,
    diemChuan: `${ADMIN_BASE}/diem-chuan`,
    stats: `${ADMIN_BASE}/stats`,
    documents: `${ADMIN_BASE}/documents`,
  },
  analytics: {
    trend: `${ANALYTICS_BASE}/trend`,
    compare: `${ANALYTICS_BASE}/compare`,
    distribution: `${ANALYTICS_BASE}/distribution`,
    schoolsSummary: `${ANALYTICS_BASE}/schools-summary`,
  },
}
