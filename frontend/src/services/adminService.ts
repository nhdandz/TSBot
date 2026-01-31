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

  // Nganh (Majors)
  async getNganh(): Promise<Nganh[]> {
    return apiClient.get<Nganh[]>(API_ENDPOINTS.admin.nganh, {
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
    year?: number
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
}
