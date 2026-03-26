import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, ShieldCheck } from 'lucide-react'
import toast from 'react-hot-toast'
import { Layout } from '../components/Layout'
import { Spinner } from '../components/Spinner'
import { RoleBadge } from '../components/Badge'
import { getAdminUsers, promoteToTeacher } from '../api/admin'

export function AdminPage() {
  const queryClient = useQueryClient()
  const [promotingId, setPromotingId] = useState<string | null>(null)

  const usersQuery = useQuery({
    queryKey: ['admin-users'],
    queryFn: getAdminUsers,
  })

  const promoteMutation = useMutation({
    mutationFn: (userId: string) => promoteToTeacher(userId),
    onMutate: (userId) => setPromotingId(userId),
    onSuccess: (updatedUser) => {
      queryClient.setQueryData<ReturnType<typeof getAdminUsers> extends Promise<infer T> ? T : never>(
        ['admin-users'],
        (old) => old?.map((u) => (u.id === updatedUser.id ? updatedUser : u)) ?? []
      )
      toast.success(`${updatedUser.first_name} ${updatedUser.last_name} er nå lærer.`)
    },
    onError: () => toast.error('Klarte ikke promotere bruker.'),
    onSettled: () => setPromotingId(null),
  })

  const users = usersQuery.data ?? []

  return (
    <Layout>
      <div className="flex-1 min-h-0 overflow-y-auto">
      <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Brukeradministrasjon</h1>
            <p className="mt-1 text-sm text-gray-500">
              Administrer brukere og rolletildelinger i systemet.
            </p>
          </div>
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['admin-users'] })}
            disabled={usersQuery.isFetching}
            className="btn-secondary"
            aria-label="Last brukerliste på nytt"
          >
            <RefreshCw className={`h-4 w-4 ${usersQuery.isFetching ? 'animate-spin' : ''}`} aria-hidden="true" />
            Oppdater
          </button>
        </div>

        {usersQuery.isLoading && (
          <div className="flex items-center gap-3 text-gray-500">
            <Spinner size="md" className="text-indigo-600" />
            <span>Laster brukere...</span>
          </div>
        )}

        {usersQuery.isError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-700">Klarte ikke laste brukerlisten. Prøv å laste siden på nytt.</p>
          </div>
        )}

        {users.length > 0 && (
          <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left font-medium text-gray-600">Navn</th>
                  <th scope="col" className="px-6 py-3 text-left font-medium text-gray-600">E-post</th>
                  <th scope="col" className="px-6 py-3 text-left font-medium text-gray-600">Rolle</th>
                  <th scope="col" className="px-6 py-3 text-right font-medium text-gray-600">Handling</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-gray-900 font-medium">
                      {user.first_name} {user.last_name}
                    </td>
                    <td className="px-6 py-4 text-gray-500">{user.email}</td>
                    <td className="px-6 py-4">
                      <RoleBadge role={user.global_role} />
                    </td>
                    <td className="px-6 py-4 text-right">
                      {user.global_role === 'student' ? (
                        <button
                          onClick={() => promoteMutation.mutate(user.id)}
                          disabled={promotingId === user.id}
                          className="btn-secondary py-1.5 text-xs"
                          aria-label={`Gjør ${user.first_name} ${user.last_name} til lærer`}
                        >
                          {promotingId === user.id ? (
                            <Spinner size="sm" />
                          ) : (
                            <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
                          )}
                          Gjør til lærer
                        </button>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="border-t border-gray-100 bg-gray-50 px-6 py-3">
              <p className="text-xs text-gray-500">{users.length} bruker(e) totalt</p>
            </div>
          </div>
        )}

        {users.length === 0 && !usersQuery.isLoading && !usersQuery.isError && (
          <p className="text-sm text-gray-500">Ingen brukere funnet.</p>
        )}
      </div>
      </div>
    </Layout>
  )
}
