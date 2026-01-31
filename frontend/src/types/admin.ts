// Admin related types

export interface Truong {
  id?: number
  school_id: string
  school_name: string
  alias?: string
  location?: string
  website?: string
  created_at?: string
}

export interface Nganh {
  id?: number
  truong_id?: number
  school_name?: string
  major_code: string
  major_name: string
  description?: string
}

export interface KhoiThi {
  block_code: string
  subjects: string
}

export interface DiemChuan {
  id?: number
  school_id: string
  major_code: string
  block_code: string
  year: number
  gender: 'NAM' | 'NU' | 'CHUNG'
  region: 'MIEN_BAC' | 'MIEN_NAM' | 'TOAN_QUOC'
  score: number
  tieu_chi_phu?: string
  ghi_chu?: string
}

export interface DiemChuanView {
  nam: number
  truong: string
  ma_truong: string
  nganh: string
  khoi: string
  gioi_tinh: string
  khu_vuc: string
  diem_chuan: number
  tieu_chi_phu?: string
}

export interface DashboardStats {
  total_schools: number
  total_majors: number
  total_scores: number
  total_chats: number
  recent_chats: number
  avg_feedback_rating?: number
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}
