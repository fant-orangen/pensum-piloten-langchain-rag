import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Spinner } from './Spinner'
import type { GlobalRole } from '../types'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRole?: GlobalRole
}

export function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner size="lg" className="text-indigo-600" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/auth" replace />
  }

  if (user.must_change_password && location.pathname !== '/settings') {
    return <Navigate to="/settings" replace />
  }

  // Admin users can only access the admin page
  if (user.global_role === 'admin' && location.pathname !== '/admin') {
    return <Navigate to="/admin" replace />
  }

  if (requiredRole) {
    const roleHierarchy: GlobalRole[] = ['student', 'teacher', 'admin']
    const userLevel = roleHierarchy.indexOf(user.global_role)
    const requiredLevel = roleHierarchy.indexOf(requiredRole)
    if (userLevel < requiredLevel) {
      return <Navigate to="/" replace />
    }
  }

  return <>{children}</>
}
