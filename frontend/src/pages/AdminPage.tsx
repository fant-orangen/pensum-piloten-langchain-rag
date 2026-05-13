import { type ReactNode, type UIEvent, useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, Search, ShieldCheck, ShieldMinus } from 'lucide-react'
import toast from 'react-hot-toast'
import { Layout } from '../components/Layout'
import { Spinner } from '../components/Spinner'
import { RoleBadge } from '../components/Badge'
import { getAdminUsers, promoteToTeacher, demoteToStudent } from '../api/admin'
import type { AdminUserRead } from '../types'
import { usePageTitle } from '../hooks/usePageTitle'

const PAGE_SIZE = 20

/** Admin dashboard for promoting students and demoting teachers. */
export function AdminPage() {
  usePageTitle('Brukeradministrasjon')
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [selectedStudents, setSelectedStudents] = useState<Set<string>>(new Set())
  const [selectedTeachers, setSelectedTeachers] = useState<Set<string>>(new Set())
  const [studentVisibleCount, setStudentVisibleCount] = useState(PAGE_SIZE)
  const [teacherVisibleCount, setTeacherVisibleCount] = useState(PAGE_SIZE)

  const usersQuery = useQuery({
    queryKey: ['admin-users'],
    queryFn: getAdminUsers,
  })

  const users = usersQuery.data ?? []
  const lowerSearch = search.toLowerCase()

  const filteredStudents = useMemo(
    () =>
      users.filter(
        (u) =>
          u.global_role === 'student' &&
          (u.first_name.toLowerCase().includes(lowerSearch) ||
            u.last_name.toLowerCase().includes(lowerSearch) ||
            u.email.toLowerCase().includes(lowerSearch))
      ),
    [users, lowerSearch]
  )

  const filteredTeachers = useMemo(
    () =>
      users.filter(
        (u) =>
          u.global_role === 'teacher' &&
          (u.first_name.toLowerCase().includes(lowerSearch) ||
            u.last_name.toLowerCase().includes(lowerSearch) ||
            u.email.toLowerCase().includes(lowerSearch))
      ),
    [users, lowerSearch]
  )

  const handleSearchChange = (value: string) => {
    setSearch(value)
    setStudentVisibleCount(PAGE_SIZE)
    setTeacherVisibleCount(PAGE_SIZE)
  }

  const pagedStudents = filteredStudents.slice(0, studentVisibleCount)
  const pagedTeachers = filteredTeachers.slice(0, teacherVisibleCount)

  const handleStudentLoadMore = () => {
    setStudentVisibleCount((count) => Math.min(filteredStudents.length, count + PAGE_SIZE))
  }

  const handleTeacherLoadMore = () => {
    setTeacherVisibleCount((count) => Math.min(filteredTeachers.length, count + PAGE_SIZE))
  }

  // Clear selections that are no longer visible after data changes
  const updateUsersCache = (updatedUser: AdminUserRead) => {
    queryClient.setQueryData<AdminUserRead[]>(['admin-users'], (old) =>
      old?.map((u) => (u.id === updatedUser.id ? updatedUser : u)) ?? []
    )
  }

  const promoteMutation = useMutation({
    mutationFn: async (userIds: string[]) => {
      const results: AdminUserRead[] = []
      for (const id of userIds) {
        results.push(await promoteToTeacher(id))
      }
      return results
    },
    onSuccess: (updatedUsers) => {
      for (const u of updatedUsers) updateUsersCache(u)
      setSelectedStudents(new Set())
      toast.success(`${updatedUsers.length} bruker(e) promotert til lærer.`)
    },
    onError: () => toast.error('Klarte ikke promotere bruker(e).'),
  })

  const demoteMutation = useMutation({
    mutationFn: async (userIds: string[]) => {
      const results: AdminUserRead[] = []
      for (const id of userIds) {
        results.push(await demoteToStudent(id))
      }
      return results
    },
    onSuccess: (updatedUsers) => {
      for (const u of updatedUsers) updateUsersCache(u)
      setSelectedTeachers(new Set())
      toast.success(`${updatedUsers.length} bruker(e) degradert til student.`)
    },
    onError: () => toast.error('Klarte ikke degradere bruker(e).'),
  })

  const toggleStudent = (id: string) => {
    setSelectedStudents((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const courseOwnerIds = useMemo(
    () => new Set(users.filter((u) => u.is_course_owner).map((u) => u.id)),
    [users]
  )

  const toggleTeacher = (id: string) => {
    if (courseOwnerIds.has(id)) return
    setSelectedTeachers((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const isBusy = promoteMutation.isPending || demoteMutation.isPending

  return (
    <Layout>
      <div className="flex-1 min-h-0 overflow-y-auto">
        <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6">
          {/* Header */}
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

          {/* Search bar */}
          <div className="relative mb-6">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" aria-hidden="true" />
            <input
              type="text"
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Søk etter navn eller e-post..."
              className="input-field pl-10"
              aria-label="Søk brukere"
            />
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

          {!usersQuery.isLoading && !usersQuery.isError && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* Students list */}
              <UserList
                title="Studenter"
                users={pagedStudents}
                totalFiltered={filteredStudents.length}
                hasMore={pagedStudents.length < filteredStudents.length}
                selected={selectedStudents}
                onToggle={toggleStudent}
                onLoadMore={handleStudentLoadMore}
                actionLabel="Promoter til lærer"
                actionIcon={<ShieldCheck className="h-4 w-4" aria-hidden="true" />}
                actionDisabled={selectedStudents.size === 0 || isBusy}
                actionLoading={promoteMutation.isPending}
                onAction={() => promoteMutation.mutate([...selectedStudents])}
              />

              {/* Teachers list */}
              <UserList
                title="Lærere"
                users={pagedTeachers}
                totalFiltered={filteredTeachers.length}
                hasMore={pagedTeachers.length < filteredTeachers.length}
                selected={selectedTeachers}
                onToggle={toggleTeacher}
                onLoadMore={handleTeacherLoadMore}
                actionLabel="Degrader til student"
                actionIcon={<ShieldMinus className="h-4 w-4" aria-hidden="true" />}
                actionDisabled={selectedTeachers.size === 0 || isBusy}
                actionLoading={demoteMutation.isPending}
                onAction={() => demoteMutation.mutate([...selectedTeachers])}
                disabledIds={courseOwnerIds}
                disabledReason="Kurseier kan ikke degraderes"
              />
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}

/* ------------------------------------------------------------------ */

interface UserListProps {
  title: string
  users: AdminUserRead[]
  totalFiltered: number
  hasMore: boolean
  selected: Set<string>
  onToggle: (id: string) => void
  onLoadMore: () => void
  actionLabel: string
  actionIcon: ReactNode
  actionDisabled: boolean
  actionLoading: boolean
  onAction: () => void
  disabledIds?: Set<string>
  disabledReason?: string
}

/** Reusable selectable user table used for student and teacher role changes. */
function UserList({
  title,
  users,
  totalFiltered,
  hasMore,
  selected,
  onToggle,
  onLoadMore,
  actionLabel,
  actionIcon,
  actionDisabled,
  actionLoading,
  onAction,
  disabledIds,
  disabledReason,
}: UserListProps) {
  function handleScroll(e: UIEvent<HTMLDivElement>) {
    const el = e.currentTarget
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 80 && hasMore) {
      onLoadMore()
    }
  }

  return (
    <div className="flex flex-col">
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-100 bg-gray-50 px-6 py-3">
          <h2 className="text-sm font-semibold text-gray-700">
            {title}{' '}
            <span className="font-normal text-gray-400">({totalFiltered})</span>
          </h2>
        </div>

        <div className="max-h-[420px] min-h-[320px] overflow-y-auto" onScroll={handleScroll}>
          {users.length === 0 ? (
            <p className="px-6 py-8 text-center text-sm text-gray-400">Ingen treff.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="w-10 px-4 py-2" />
                  <th scope="col" className="px-4 py-2 text-left font-medium text-gray-600">Navn</th>
                  <th scope="col" className="px-4 py-2 text-left font-medium text-gray-600">E-post</th>
                  <th scope="col" className="px-4 py-2 text-left font-medium text-gray-600">Rolle</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.map((user) => {
                  const isDisabled = disabledIds?.has(user.id) ?? false
                  return (
                    <tr
                      key={user.id}
                      className={`transition-colors ${
                        isDisabled
                          ? 'bg-gray-50 cursor-default'
                          : selected.has(user.id)
                            ? 'bg-indigo-50 cursor-pointer'
                            : 'hover:bg-gray-50 cursor-pointer'
                      }`}
                      onClick={() => !isDisabled && onToggle(user.id)}
                    >
                      <td className="px-4 py-3 text-center">
                        {isDisabled ? (
                          <span className="text-xs text-gray-400" title={disabledReason}>—</span>
                        ) : (
                          <input
                            type="checkbox"
                            checked={selected.has(user.id)}
                            onChange={() => onToggle(user.id)}
                            onClick={(e) => e.stopPropagation()}
                            className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                            aria-label={`Velg ${user.first_name} ${user.last_name}`}
                          />
                        )}
                      </td>
                      <td className="px-4 py-3 font-medium text-gray-900">
                        {user.first_name} {user.last_name}
                        {isDisabled && disabledReason && (
                          <span className="ml-2 inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                            {disabledReason}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-500">{user.email}</td>
                      <td className="px-4 py-3">
                        <RoleBadge role={user.global_role} />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Action button */}
      <button
        onClick={onAction}
        disabled={actionDisabled}
        className="btn-primary mt-3 w-full justify-center disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {actionLoading ? <Spinner size="sm" /> : actionIcon}
        {actionLabel}
        {selected.size > 0 && ` (${selected.size})`}
      </button>
    </div>
  )
}
