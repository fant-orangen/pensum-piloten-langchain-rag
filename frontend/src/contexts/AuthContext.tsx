import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { getMe, login as apiLogin, register as apiRegister } from '../api/auth'
import type { UserResponse } from '../types'
import { studyInstructionProgressKey } from '../study/courseSequence'

/**
 * Shape of the value exposed by {@link AuthContext}.
 *
 * Consumers should access this through the {@link useAuth} hook rather than
 * reading the context directly.
 */
interface AuthContextValue {
  /**
   * The currently authenticated user, or `null` when no session is active.
   * Populated immediately after a successful {@link login} or session restore.
   */
  user: UserResponse | null

  /**
   * The raw JWT access token persisted in `localStorage`, or `null` when the
   * user is not authenticated. This value mirrors what is stored under the key
   * `access_token` and is kept in sync with `localStorage` at all times.
   */
  token: string | null

  /**
   * `true` while the initial session-restore check is in progress on mount.
   * Components that guard authenticated routes should not render protected
   * content until this flag is `false`.
   */
  isLoading: boolean

  /**
   * Authenticates the user with the given credentials.
   * On success, persists the JWT to `localStorage`, updates {@link token}, and
   * fetches the current user profile to populate {@link user}.
   *
   * @param email - The user's email address.
   * @param password - The user's plaintext password.
   * @throws {Error} Rejects if the API returns an authentication error.
   */
  login: (email: string, password: string) => Promise<void>

  /**
   * Ends the current session by removing the JWT from `localStorage` and
   * clearing both {@link token} and {@link user} from state.
   */
  logout: () => void

  /**
   * Registers a new user account and immediately authenticates them.
   * Delegates registration to the API and, on success, calls {@link login}
   * with the supplied credentials so the session is active straight away.
   *
   * @param payload - Registration details for the new account.
   * @param payload.email - Email address for the new account.
   * @param payload.password - Plaintext password for the new account.
   * @param payload.first_name - User's first name.
   * @param payload.last_name - User's last name.
   * @throws {Error} Rejects if the registration or subsequent login fails.
   */
  register: (payload: {
    email: string
    password: string
    first_name: string
    last_name: string
  }) => Promise<void>

  /**
   * Re-fetches the authenticated user's profile from `GET /auth/me` and
   * updates {@link user} in state. If the request fails (e.g. the token has
   * expired), the session is cleared: {@link user} and {@link token} are set
   * to `null` and the JWT is removed from `localStorage`.
   *
   * @throws Never — errors are caught internally and result in session teardown.
   */
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

/**
 * Provides authentication state and actions to the component tree.
 *
 * Wrap the application (or any subtree that requires auth) with this component.
 * On mount it attempts to restore an existing session from `localStorage`; the
 * {@link AuthContextValue.isLoading} flag remains `true` until that check
 * completes. All descendants can access the context via the {@link useAuth}
 * hook.
 *
 * @param children - The React subtree to render inside the provider.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'))
  const [isLoading, setIsLoading] = useState(true)

  /** @see {@link AuthContextValue.refreshUser} */
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

  /**
   * Session-restore effect — runs once on mount.
   *
   * If a JWT is found in `localStorage` under the key `access_token`, the
   * token is written to state and {@link refreshUser} is called to validate it
   * and hydrate the user profile. `isLoading` is set to `false` only after
   * the attempt completes (whether it succeeds or fails). When no stored token
   * exists, `isLoading` is cleared immediately without making a network request.
   */
  useEffect(() => {
    const stored = localStorage.getItem('access_token')
    if (stored) {
      setToken(stored)
      refreshUser().finally(() => setIsLoading(false))
    } else {
      setIsLoading(false)
    }
  }, [refreshUser])

  /** @see {@link AuthContextValue.login} */
  const login = useCallback(async (email: string, password: string) => {
    const tokenResponse = await apiLogin(email, password)
    localStorage.setItem('access_token', tokenResponse.access_token)
    setToken(tokenResponse.access_token)
    const me = await getMe()
    setUser(me)
  }, [])

  /** @see {@link AuthContextValue.logout} */
  const logout = useCallback(() => {
    const progressKey = studyInstructionProgressKey(user?.email)
    if (progressKey) localStorage.removeItem(progressKey)
    localStorage.removeItem('access_token')
    setToken(null)
    setUser(null)
  }, [user?.email])

  /** @see {@link AuthContextValue.register} */
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

/**
 * Returns the nearest {@link AuthContext} value.
 *
 * Must be called from a component that is rendered inside {@link AuthProvider}.
 * Throws a descriptive error if no provider is found in the tree, making
 * accidental misuse easy to diagnose.
 *
 * @returns The current {@link AuthContextValue} with user state and auth actions.
 * @throws {Error} If called outside of an {@link AuthProvider}.
 *
 * @example
 * ```tsx
 * function ProfileButton() {
 *   const { user, logout } = useAuth()
 *   return <button onClick={logout}>{user?.first_name}</button>
 * }
 * ```
 */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
