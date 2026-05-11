/// <reference types="vite/client" />
import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? ''

/**
 * Shared Axios client for all backend calls.
 *
 * Request interceptors attach the JWT from localStorage. Response interceptors
 * clear invalid sessions on 401 responses outside the login flow.
 */
export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLoginRequest = error.config?.url?.includes('/auth/login')
    if (error.response?.status === 401 && !isLoginRequest) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
