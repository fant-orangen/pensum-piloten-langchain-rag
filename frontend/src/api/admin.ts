import type { AdminUserRead } from '../types'
import { apiClient } from './client'

export async function getAdminUsers(): Promise<AdminUserRead[]> {
  const { data } = await apiClient.get<AdminUserRead[]>('/admin/users')
  return data
}

export async function promoteToTeacher(userId: string): Promise<AdminUserRead> {
  const { data } = await apiClient.post<AdminUserRead>(`/admin/users/${userId}/promote-teacher`)
  return data
}

export async function demoteToStudent(userId: string): Promise<AdminUserRead> {
  const { data } = await apiClient.post<AdminUserRead>(`/admin/users/${userId}/demote-student`)
  return data
}
