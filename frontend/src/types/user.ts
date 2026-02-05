export interface User {
  id: string
  username: string
  email: string
  role: "admin" | "editor" | "viewer"
  status: "active" | "inactive" | "suspended"
  created_at: string
  last_login: string | null
}

export type UserRole = User["role"]
export type UserStatus = User["status"]
