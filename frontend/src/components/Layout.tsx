import { Link, useNavigate } from 'react-router-dom'
import { BookOpen, LogOut, Moon, Settings, Shield, Sun } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../hooks/useTheme'
import { RoleBadge } from './Badge'

interface LayoutProps {
  children: React.ReactNode
}

/** Authenticated application shell with top navigation, theme toggle, and logout. */
export function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const { theme, toggleTheme } = useTheme()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-gray-50">
      <header className="shrink-0 border-b border-gray-200 bg-white shadow-sm">
        <nav
          aria-label="Hovednavigasjon"
          className="mx-auto flex max-w-screen-2xl items-center justify-between px-4 py-3 sm:px-6"
        >
          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="flex items-center gap-2 text-lg font-bold text-indigo-600 hover:text-indigo-700 focus-visible:rounded focus-visible:outline"
            >
              <BookOpen className="h-6 w-6" aria-hidden="true" />
              <span>Pensum Piloten</span>
            </Link>
          </div>

          {user && (
            <div className="flex items-center gap-4">
              {user.global_role === 'admin' && (
                <Link
                  to="/dashboard/admin"
                  className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-indigo-600 focus-visible:rounded focus-visible:outline"
                >
                  <Shield className="h-4 w-4" aria-hidden="true" />
                  <span>Admin</span>
                </Link>
              )}
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <span className="hidden sm:inline">
                  {user.first_name} {user.last_name}
                </span>
                <RoleBadge role={user.global_role} />
              </div>
              <button
                onClick={toggleTheme}
                className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 transition-colors"
                aria-label={theme === 'dark' ? 'Bytt til lyst tema' : 'Bytt til mørkt tema'}
              >
                {theme === 'dark'
                  ? <Sun className="h-4 w-4" aria-hidden="true" />
                  : <Moon className="h-4 w-4" aria-hidden="true" />}
              </button>
              <Link
                to="/settings"
                className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 hover:text-gray-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 transition-colors"
                aria-label="Innstillinger"
              >
                <Settings className="h-4 w-4" aria-hidden="true" />
              </Link>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 hover:text-gray-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 transition-colors"
                aria-label="Logg ut"
              >
                <LogOut className="h-4 w-4" aria-hidden="true" />
                <span className="hidden sm:inline">Logg ut</span>
              </button>
            </div>
          )}
        </nav>
      </header>

      <main className="flex flex-1 flex-col min-h-0">
        {children}
      </main>
    </div>
  )
}
