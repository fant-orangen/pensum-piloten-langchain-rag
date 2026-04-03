import type { TokenResponse, UserResponse } from '../types'
import { apiClient } from './client'

export async function register(payload: {
  email: string
  password: string
  first_name: string
  last_name: string
}): Promise<UserResponse> {
  const { data } = await apiClient.post<UserResponse>('/auth/register', payload)
  return data
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/login', { email, password })
  return data
}

export async function getMe(): Promise<UserResponse> {
  const { data } = await apiClient.get<UserResponse>('/auth/me')
  return data
}

export async function changePassword(
  oldPassword: string,
  newPassword: string,
): Promise<void> {
  await apiClient.post('/auth/change-password', {
    old_password: oldPassword,
    new_password: newPassword,
  })
}
