// Admin service for API calls

import { apiClient, withAuth } from '@/lib/api'
import { API_ENDPOINTS } from '@/lib/config'
import type {
  Truong,
  Nganh,
  DiemChuan,
  DiemChuanView,
  DashboardStats,
  LoginRequest,
  LoginResponse,
} from '@/types'

export const adminService = {
  // Authentication
  async login(request: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>(
      API_ENDPOINTS.admin.login,
      request
    )
    if (response.access_token) {
      apiClient.setAuthToken(response.access_token)
      localStorage.setItem('auth_token', response.access_token)
    }
    return response
  },

  // Truong (Schools)
  async getTruong(): Promise<Truong[]> {
    return apiClient.get<Truong[]>(API_ENDPOINTS.admin.truong, {
      headers: withAuth(),
    })
  },

  async createTruong(data: Omit<Truong, 'created_at'>): Promise<Truong> {
    return apiClient.post<Truong>(API_ENDPOINTS.admin.truong, data, {
      headers: withAuth(),
    })
  },

  async updateTruong(schoolId: string, data: Partial<Truong>): Promise<Truong> {
    return apiClient.put<Truong>(
      `${API_ENDPOINTS.admin.truong}/${schoolId}`,
      data,
      {
        headers: withAuth(),
      }
    )
  },

  async deleteTruong(schoolId: string): Promise<{ success: boolean }> {
    return apiClient.delete(`${API_ENDPOINTS.admin.truong}/${schoolId}`, {
      headers: withAuth(),
    })
  },

  // KhoiThi (Exam blocks)
  async getKhoiThi(): Promise<{ id: number; ma_khoi: string; ten_khoi: string; mon_hoc: string }[]> {
    return apiClient.get(API_ENDPOINTS.admin.khoiThi, {
      headers: withAuth(),
    })
  },

  // Nganh (Majors)
  async getNganh(truongId?: number): Promise<Nganh[]> {
    const endpoint = truongId
      ? `${API_ENDPOINTS.admin.nganh}?truong_id=${truongId}`
      : API_ENDPOINTS.admin.nganh
    return apiClient.get<Nganh[]>(endpoint, {
      headers: withAuth(),
    })
  },

  async createNganh(data: Nganh): Promise<Nganh> {
    return apiClient.post<Nganh>(API_ENDPOINTS.admin.nganh, data, {
      headers: withAuth(),
    })
  },

  async updateNganh(majorCode: string, data: Partial<Nganh>): Promise<Nganh> {
    return apiClient.put<Nganh>(
      `${API_ENDPOINTS.admin.nganh}/${majorCode}`,
      data,
      {
        headers: withAuth(),
      }
    )
  },

  async deleteNganh(majorCode: string): Promise<{ success: boolean }> {
    return apiClient.delete(`${API_ENDPOINTS.admin.nganh}/${majorCode}`, {
      headers: withAuth(),
    })
  },

  // Diem Chuan (Admission Scores)
  async getDiemChuan(params?: {
    year?: number | null
    school_id?: string
    major_code?: string
  }): Promise<any> {
    const queryParams = new URLSearchParams()
    if (params?.year) queryParams.append('nam', params.year.toString())
    if (params?.school_id) queryParams.append('truong_id', params.school_id)

    const endpoint = queryParams.toString()
      ? `${API_ENDPOINTS.admin.diemChuan}?${queryParams}`
      : API_ENDPOINTS.admin.diemChuan

    return apiClient.get<any>(endpoint, {
      headers: withAuth(),
    })
  },

  async createDiemChuan(data: Omit<DiemChuan, 'id'>): Promise<DiemChuan> {
    return apiClient.post<DiemChuan>(API_ENDPOINTS.admin.diemChuan, data, {
      headers: withAuth(),
    })
  },

  async updateDiemChuan(id: number, data: Partial<DiemChuan>): Promise<DiemChuan> {
    return apiClient.put<DiemChuan>(
      `${API_ENDPOINTS.admin.diemChuan}/${id}`,
      data,
      {
        headers: withAuth(),
      }
    )
  },

  async deleteDiemChuan(id: number): Promise<{ success: boolean }> {
    return apiClient.delete(`${API_ENDPOINTS.admin.diemChuan}/${id}`, {
      headers: withAuth(),
    })
  },

  async bulkImportDiemChuan(data: Omit<DiemChuan, 'id'>[]): Promise<{
    success: number
    failed: number
    errors?: string[]
  }> {
    return apiClient.post(
      `${API_ENDPOINTS.admin.diemChuan}/bulk`,
      { items: data },
      {
        headers: withAuth(),
      }
    )
  },

  // Dashboard stats
  async getStats(): Promise<DashboardStats> {
    return apiClient.get<DashboardStats>(API_ENDPOINTS.admin.stats, {
      headers: withAuth(),
    })
  },

  // Documents
  async uploadDocument(file: File): Promise<{
    success: boolean
    message: string
    filename: string
    chunks: number
  }> {
    const formData = new FormData()
    formData.append('file', file)

    console.log('[AdminService] Uploading document:', file.name, file.size, file.type)

    return apiClient.post(
      '/api/v1/admin/documents/upload',
      formData,
      {
        headers: {
          ...withAuth(),
          // Don't set Content-Type - let browser set it automatically with boundary
        },
      }
    )
  },

  async getDocuments(): Promise<{
    total: number
    documents: Array<{
      filename: string
      chunks: number
      uploaded_by: string
      uploaded_at: string
    }>
  }> {
    return apiClient.get(
      '/api/v1/admin/documents',
      {
        headers: withAuth(),
      }
    )
  },

  async deleteDocument(filename: string): Promise<{
    success: boolean
    message: string
    deleted_chunks: number
  }> {
    return apiClient.delete(
      `/api/v1/admin/documents/${encodeURIComponent(filename)}`,
      {
        headers: withAuth(),
      }
    )
  },

  async reindexDocuments(): Promise<{
    success: boolean
    message: string
    total_chunks: number
    chunks_json_saved: boolean
    files_processed: Array<{ file: string; chunks: number }>
  }> {
    return apiClient.post(
      '/api/v1/admin/documents/reindex',
      {},
      { headers: withAuth() }
    )
  },

  async loadChunksJson(): Promise<{
    success: boolean
    message: string
    total_chunks: number
  }> {
    return apiClient.post(
      '/api/v1/admin/documents/load-json',
      {},
      { headers: withAuth() }
    )
  },

  // Analytics
  async getAnalyticsTrend(params: {
    truong?: string
    nganh?: string
    ma_khoi?: string
    gioi_tinh?: string
    khu_vuc?: string
  }): Promise<{
    data_points: { nam: number; diem_chuan: number }[]
    prediction: {
      nam_toi: number
      diem_du_doan: number
      confidence: number
      disclaimer: string | null
    } | null
    regression: {
      slope: number
      intercept: number
      r_squared: number
      n_points: number
    } | null
  }> {
    const q = new URLSearchParams()
    if (params.truong) q.append('truong', params.truong)
    if (params.nganh) q.append('nganh', params.nganh)
    if (params.ma_khoi) q.append('ma_khoi', params.ma_khoi)
    if (params.gioi_tinh) q.append('gioi_tinh', params.gioi_tinh)
    if (params.khu_vuc) q.append('khu_vuc', params.khu_vuc)
    return apiClient.get(`${API_ENDPOINTS.analytics.trend}?${q}`, { headers: withAuth() })
  },

  async getAnalyticsCompare(params: {
    nam?: number
    ma_khoi?: string
    gioi_tinh?: string
    khu_vuc?: string
  }): Promise<
    {
      ten_truong: string
      diem_trung_binh: number
      diem_cao_nhat: number
      diem_thap_nhat: number
      so_nganh: number
    }[]
  > {
    const q = new URLSearchParams()
    if (params.nam) q.append('nam', String(params.nam))
    if (params.ma_khoi) q.append('ma_khoi', params.ma_khoi)
    if (params.gioi_tinh) q.append('gioi_tinh', params.gioi_tinh)
    if (params.khu_vuc) q.append('khu_vuc', params.khu_vuc)
    return apiClient.get(`${API_ENDPOINTS.analytics.compare}?${q}`, { headers: withAuth() })
  },

  async getAnalyticsDistribution(params: {
    nam?: number
    ma_khoi?: string
  }): Promise<{ bins: string[]; counts: number[] }> {
    const q = new URLSearchParams()
    if (params.nam) q.append('nam', String(params.nam))
    if (params.ma_khoi) q.append('ma_khoi', params.ma_khoi)
    return apiClient.get(`${API_ENDPOINTS.analytics.distribution}?${q}`, { headers: withAuth() })
  },

  async getAnalyticsSchoolsSummary(): Promise<{
    schools: {
      ten_truong: string
      nam_dau: number
      nam_cuoi: number
      so_nam: number
      diem_tb: number
      diem_max: number
      diem_min: number
    }[]
    years_available: number[]
    total_schools: number
  }> {
    return apiClient.get(API_ENDPOINTS.analytics.schoolsSummary, { headers: withAuth() })
  },
}

