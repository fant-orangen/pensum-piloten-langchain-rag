import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, KeyRound, TriangleAlert } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Layout } from '../components/Layout'
import { Spinner } from '../components/Spinner'
import { changePassword } from '../api/auth'
import { useAuth } from '../contexts/AuthContext'

/** User settings page, currently focused on normal and forced password changes. */
export function SettingsPage() {
  const navigate = useNavigate()
  const { user, refreshUser } = useAuth()

  // Note that there is a security risk here. Technically you can change this value to false in the page source and bypass the need for any password
  const mustChange = user?.must_change_password ?? false

  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [confirmError, setConfirmError] = useState('')

  const mutation = useMutation({
    mutationFn: () =>
      changePassword(mustChange ? null : oldPassword, newPassword),
    onSuccess: async () => {
      await refreshUser()
      toast.success('Passordet er oppdatert.')
      setOldPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setConfirmError('')
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      const detail = err.response?.data?.detail ?? 'Noe gikk galt. Prøv igjen.'
      toast.error(detail)
    },
  })

  function handleConfirmChange(value: string) {
    setConfirmPassword(value)
    if (confirmError && value === newPassword) {
      setConfirmError('')
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (newPassword !== confirmPassword) {
      setConfirmError('Passordene stemmer ikke overens.')
      return
    }
    setConfirmError('')
    mutation.mutate()
  }

  return (
    <Layout>
      <div className="flex-1 min-h-0 overflow-y-auto">
        <div className="mx-auto w-full max-w-2xl px-4 py-10 sm:px-6">

          {!mustChange && (
            <button
              onClick={() => navigate(-1)}
              className="mb-8 flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 rounded"
            >
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Tilbake
            </button>
          )}

          <h1 className="text-2xl font-bold text-gray-900 mb-8">Innstillinger</h1>

          {mustChange && (
            <div
              role="alert"
              className="mb-6 flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-800"
            >
              <TriangleAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-500" aria-hidden="true" />
              <div>
                <p className="font-semibold">Du må oppdatere passordet ditt</p>
                <p className="mt-1 text-amber-700">
                  Kontoen din er opprettet uten passord. Du må sette et passord
                  før du kan bruke tjenesten.
                </p>
              </div>
            </div>
          )}

          <div className="rounded-xl border border-gray-200 bg-white shadow-sm divide-y divide-gray-100">

            <section aria-labelledby="change-password-heading" className="p-6">
              <div className="mb-5 flex items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-50">
                  <KeyRound className="h-5 w-5 text-indigo-600" aria-hidden="true" />
                </div>
                <div>
                  <h2 id="change-password-heading" className="text-base font-semibold text-gray-900">
                    Endre passord
                  </h2>
                  <p className="text-sm text-gray-500">Oppdater passordet for kontoen din.</p>
                </div>
              </div>

              <form onSubmit={handleSubmit} noValidate className="space-y-4 max-w-sm">
                <div>
                  <label
                    htmlFor="old-password"
                    className={`label ${mustChange ? 'text-gray-400' : ''}`}
                  >
                    Nåværende passord
                  </label>
                  <input
                    id="old-password"
                    type="password"
                    autoComplete="current-password"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    disabled={mustChange}
                    className={`input-field mt-1 ${mustChange ? 'cursor-not-allowed bg-gray-100 text-gray-400' : ''}`}
                    placeholder={mustChange ? 'Ingen passord satt' : 'Skriv inn nåværende passord'}
                  />
                </div>

                <div>
                  <label htmlFor="new-password" className="label">
                    Nytt passord
                  </label>
                  <input
                    id="new-password"
                    type="password"
                    autoComplete="new-password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="input-field mt-1"
                    placeholder="Minst 8 tegn"
                    minLength={8}
                    required
                  />
                </div>

                <div>
                  <label htmlFor="confirm-password" className="label">
                    Bekreft nytt passord
                  </label>
                  <input
                    id="confirm-password"
                    type="password"
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => handleConfirmChange(e.target.value)}
                    className={`input-field mt-1 ${confirmError ? 'border-red-400 focus:ring-red-400' : ''}`}
                    placeholder="Gjenta det nye passordet"
                    required
                  />
                  {confirmError && (
                    <p role="alert" className="mt-1 text-sm text-red-600">
                      {confirmError}
                    </p>
                  )}
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={mutation.isPending}
                    className="btn-primary"
                  >
                    {mutation.isPending && <Spinner size="sm" />}
                    Lagre endringer
                  </button>
                </div>
              </form>
            </section>

          </div>
        </div>
      </div>
    </Layout>
  )
}
