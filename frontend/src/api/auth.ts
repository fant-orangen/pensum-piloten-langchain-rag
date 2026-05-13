import type { TokenResponse, UserResponse } from '../types'
import { apiClient } from './client'

/** Register a new student account. The API returns the created safe user object. */
export async function register(payload: {
  email: string
  password: string
  first_name: string
  last_name: string
}): Promise<UserResponse> {
  const { data } = await apiClient.post<UserResponse>('/auth/register', payload)
  return data
}

/** Exchange credentials for a JWT bearer token. */
export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/login', { email, password })
  return data
}

/** Fetch the authenticated user's profile using the current bearer token. */
export async function getMe(): Promise<UserResponse> {
  const { data } = await apiClient.get<UserResponse>('/auth/me')
  return data
}

/**
 * Change the current user's password.
 *
 * `oldPassword` may be null when the account is forced to set an initial
 * password after import/seeding.
 */
export async function changePassword(
  oldPassword: string | null,
  newPassword: string,
): Promise<void> {
  await apiClient.post('/auth/change-password', {
    old_password: oldPassword,
    new_password: newPassword,
  })
}
