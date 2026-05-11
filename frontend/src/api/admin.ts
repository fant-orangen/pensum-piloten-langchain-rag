import type { AdminUserRead } from '../types'
import { apiClient } from './client'

/** Return all users visible to admins, including course-owner protection flags. */
export async function getAdminUsers(): Promise<AdminUserRead[]> {
  const { data } = await apiClient.get<AdminUserRead[]>('/admin/users')
  return data
}

/** Promote a user to global teacher role. Fails if the caller is not admin. */
export async function promoteToTeacher(userId: string): Promise<AdminUserRead> {
  const { data } = await apiClient.post<AdminUserRead>(`/admin/users/${userId}/promote-teacher`)
  return data
}

/** Demote a teacher to student unless they own courses that block demotion. */
export async function demoteToStudent(userId: string): Promise<AdminUserRead> {
  const { data } = await apiClient.post<AdminUserRead>(`/admin/users/${userId}/demote-student`)
  return data
}
