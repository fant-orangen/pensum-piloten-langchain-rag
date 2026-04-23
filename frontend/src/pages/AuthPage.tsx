import { useState } from 'react'
import { useNavigate, type NavigateFunction } from 'react-router-dom'
import { BookOpen } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { Spinner } from '../components/Spinner'
import { getCourses } from '../api/courses'
import { isStudyParticipantEmail } from '../study/courseSequence'

async function navigateAfterAuth(
  navigate: NavigateFunction,
  email: string
) {
  if (isStudyParticipantEmail(email)) {
    try {
      const courses = await getCourses()
      if (courses.length === 1) {
        navigate(`/chat/${courses[0].id}`, { replace: true })
        return
      }
    } catch {
      // fall through to dashboard
    }
  }
  navigate('/', { replace: true })
}

type Tab = 'login' | 'register'

function getApiErrorMessage(error: unknown): string {
  if (
    error &&
    typeof error === 'object' &&
    'response' in error &&
    error.response &&
    typeof error.response === 'object' &&
    'data' in error.response
  ) {
    const data = (error.response as { data: unknown }).data
    if (data && typeof data === 'object' && 'detail' in data) {
      const detail = (data as { detail: unknown }).detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail)) {
        return detail.map((d) => (typeof d === 'object' && d && 'msg' in d ? String((d as {msg: unknown}).msg) : String(d))).join(', ')
      }
    }
  }
  return 'En uventet feil oppstod. Prøv igjen.'
}

export function AuthPage() {
  const [activeTab, setActiveTab] = useState<Tab>('login')
  const navigate = useNavigate()
  const { login, register } = useAuth()

  const [loginEmail, setLoginEmail] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)

  const [regEmail, setRegEmail] = useState('')
  const [regPassword, setRegPassword] = useState('')
  const [regConfirmPassword, setRegConfirmPassword] = useState('')
  const [regFirstName, setRegFirstName] = useState('')
  const [regLastName, setRegLastName] = useState('')
  const [regError, setRegError] = useState('')
  const [regLoading, setRegLoading] = useState(false)

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoginError('')
    if (!loginEmail) { setLoginError('E-post er påkrevd.'); return }
    setLoginLoading(true)
    try {
      await login(loginEmail, loginPassword)
      await navigateAfterAuth(navigate, loginEmail.trim())
    } catch (err) {
      setLoginError(getApiErrorMessage(err))
    } finally {
      setLoginLoading(false)
    }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault()
    setRegError('')
    if (!regEmail) { setRegError('E-post er påkrevd.'); return }
    if (!regFirstName) { setRegError('Fornavn er påkrevd.'); return }
    if (!regLastName) { setRegError('Etternavn er påkrevd.'); return }
    if (regPassword.length < 8) { setRegError('Passord må være minst 8 tegn.'); return }
    if (regPassword !== regConfirmPassword) { setRegError('Passordene stemmer ikke overens.'); return }
    setRegLoading(true)
    try {
      await register({ email: regEmail, password: regPassword, first_name: regFirstName, last_name: regLastName })
      await navigateAfterAuth(navigate, regEmail.trim())
    } catch (err) {
      setRegError(getApiErrorMessage(err))
    } finally {
      setRegLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-indigo-600">
            <BookOpen className="h-8 w-8 text-white" aria-hidden="true" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">Pensum Piloten</h1>
          <p className="mt-2 text-sm text-gray-500">Din AI-baserte studieassistent</p>
        </div>

        <div className="rounded-xl bg-white p-8 shadow-md">
          <div role="tablist" className="mb-6 flex border-b border-gray-200">
            <button
              role="tab"
              aria-selected={activeTab === 'login'}
              aria-controls="login-panel"
              id="login-tab"
              onClick={() => { setActiveTab('login'); setLoginError('') }}
              className={`tab-button mr-1 ${activeTab === 'login' ? 'tab-button-active' : 'tab-button-inactive'}`}
            >
              Logg inn
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'register'}
              aria-controls="register-panel"
              id="register-tab"
              onClick={() => { setActiveTab('register'); setRegError('') }}
              className={`tab-button ${activeTab === 'register' ? 'tab-button-active' : 'tab-button-inactive'}`}
            >
              Registrer deg
            </button>
          </div>

          {activeTab === 'login' && (
            <section
              role="tabpanel"
              id="login-panel"
              aria-labelledby="login-tab"
            >
              <form onSubmit={handleLogin} noValidate className="space-y-5">
                <div>
                  <label htmlFor="login-email" className="label">
                    E-postadresse
                  </label>
                  <input
                    id="login-email"
                    type="email"
                    autoComplete="email"
                    required
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    className="input-field mt-1"
                    placeholder="du@example.com"
                  />
                </div>
                <div>
                  <label htmlFor="login-password" className="label">
                    Passord
                  </label>
                  <input
                    id="login-password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    className="input-field mt-1"
                  />
                </div>
                {loginError && (
                  <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                    {loginError}
                  </p>
                )}
                <button
                  type="submit"
                  disabled={loginLoading}
                  className="btn-primary w-full justify-center py-2.5"
                >
                  {loginLoading && <Spinner size="sm" />}
                  Logg inn
                </button>
              </form>
            </section>
          )}

          {activeTab === 'register' && (
            <section
              role="tabpanel"
              id="register-panel"
              aria-labelledby="register-tab"
            >
              <form onSubmit={handleRegister} noValidate className="space-y-5">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="reg-firstname" className="label">
                      Fornavn
                    </label>
                    <input
                      id="reg-firstname"
                      type="text"
                      autoComplete="given-name"
                      required
                      value={regFirstName}
                      onChange={(e) => setRegFirstName(e.target.value)}
                      className="input-field mt-1"
                    />
                  </div>
                  <div>
                    <label htmlFor="reg-lastname" className="label">
                      Etternavn
                    </label>
                    <input
                      id="reg-lastname"
                      type="text"
                      autoComplete="family-name"
                      required
                      value={regLastName}
                      onChange={(e) => setRegLastName(e.target.value)}
                      className="input-field mt-1"
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="reg-email" className="label">
                    E-postadresse
                  </label>
                  <input
                    id="reg-email"
                    type="email"
                    autoComplete="email"
                    required
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    className="input-field mt-1"
                    placeholder="du@example.com"
                  />
                </div>
                <div>
                  <label htmlFor="reg-password" className="label">
                    Passord <span className="text-xs font-normal text-gray-500">(minst 8 tegn)</span>
                  </label>
                  <input
                    id="reg-password"
                    type="password"
                    autoComplete="new-password"
                    required
                    minLength={8}
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    className="input-field mt-1"
                  />
                </div>
                <div>
                  <label htmlFor="reg-confirm-password" className="label">
                    Bekreft passord
                  </label>
                  <input
                    id="reg-confirm-password"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={regConfirmPassword}
                    onChange={(e) => setRegConfirmPassword(e.target.value)}
                    className="input-field mt-1"
                  />
                </div>
                {regError && (
                  <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                    {regError}
                  </p>
                )}
                <button
                  type="submit"
                  disabled={regLoading}
                  className="btn-primary w-full justify-center py-2.5"
                >
                  {regLoading && <Spinner size="sm" />}
                  Opprett konto
                </button>
              </form>
            </section>
          )}
        </div>
      </div>
    </div>
  )
}
