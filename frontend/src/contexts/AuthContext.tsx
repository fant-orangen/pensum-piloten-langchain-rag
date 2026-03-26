import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { getMe, login as apiLogin, register as apiRegister } from '../api/auth'
import type { UserResponse } from '../types'

interface AuthContextValue {
  user: UserResponse | null
  token: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  register: (payload: {
    email: string
    password: string
    first_name: string
    last_name: string
  }) => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'))
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    try {
      const me = await getMe()
      setUser(me)
    } catch {
      setUser(null)
      setToken(null)
      localStorage.removeItem('access_token')
    }
  }, [])

  useEffect(() => {
    const stored = localStorage.getItem('access_token')
    if (stored) {
      setToken(stored)
      refreshUser().finally(() => setIsLoading(false))
    } else {
      setIsLoading(false)
    }
  }, [refreshUser])

  const login = useCallback(async (email: string, password: string) => {
    const tokenResponse = await apiLogin(email, password)
    localStorage.setItem('access_token', tokenResponse.access_token)
    setToken(tokenResponse.access_token)
    const me = await getMe()
    setUser(me)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    setToken(null)
    setUser(null)
  }, [])

  const register = useCallback(
    async (payload: {
      email: string
      password: string
      first_name: string
      last_name: string
    }) => {
      await apiRegister(payload)
      await login(payload.email, payload.password)
    },
    [login]
  )

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout, register, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
