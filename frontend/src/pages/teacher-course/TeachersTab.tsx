import { type ReactNode, useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, Search, UserPlus, UserMinus } from 'lucide-react'
import toast from 'react-hot-toast'
import { Spinner } from '../../components/Spinner'
import { getAllTeachers, getCourseTeachers, enrollStudent, unenrollStudent } from '../../api/courses'
import { courseQueryKeys, invalidateAllCourseQueries } from './queryKeys'
import type { CourseStudentRead } from '../../types'

const PAGE_SIZE = 20

interface TeachersTabProps {
  courseId: string
  creatorId: string
}

export function TeachersTab({ courseId, creatorId }: TeachersTabProps) {
  const queryClient = useQueryClient()

  const [allSearch, setAllSearch] = useState('')
  const [courseSearch, setCourseSearch] = useState('')
  const [selectedAll, setSelectedAll] = useState<Set<string>>(new Set())
  const [selectedCourse, setSelectedCourse] = useState<Set<string>>(new Set())
  const [allPage, setAllPage] = useState(1)
  const [coursePage, setCoursePage] = useState(1)

  // All teachers in the system
  const allTeachersQuery = useQuery({
    queryKey: courseQueryKeys.allTeachers,
    queryFn: getAllTeachers,
  })

  // Teachers in the current course (paginated server-side, but we fetch all for client-side filtering)
  const courseTeachersQuery = useQuery({
    queryKey: courseQueryKeys.teachers(courseId),
    queryFn: async () => {
      // Fetch all pages to get the full list for client-side search
      const first = await getCourseTeachers(courseId, 1, 100)
      return first.items
    },
  })

  const allTeachers = allTeachersQuery.data ?? []
  const courseTeachers = courseTeachersQuery.data ?? []
  const courseTeacherIds = useMemo(
    () => new Set(courseTeachers.map((t) => t.id)),
    [courseTeachers]
  )

  // Filter all teachers: only those NOT already in the course
  const lowerAll = allSearch.toLowerCase()
  const filteredAll = useMemo(
    () =>
      allTeachers.filter(
        (u) =>
          !courseTeacherIds.has(u.id) &&
          (u.first_name.toLowerCase().includes(lowerAll) ||
            u.last_name.toLowerCase().includes(lowerAll) ||
            u.email.toLowerCase().includes(lowerAll))
      ),
    [allTeachers, courseTeacherIds, lowerAll]
  )

  const lowerCourse = courseSearch.toLowerCase()
  const filteredCourse = useMemo(
    () =>
      courseTeachers.filter(
        (u) =>
          u.first_name.toLowerCase().includes(lowerCourse) ||
          u.last_name.toLowerCase().includes(lowerCourse) ||
          u.email.toLowerCase().includes(lowerCourse)
      ),
    [courseTeachers, lowerCourse]
  )

  // Pagination
  const allTotalPages = Math.max(1, Math.ceil(filteredAll.length / PAGE_SIZE))
  const courseTotalPages = Math.max(1, Math.ceil(filteredCourse.length / PAGE_SIZE))
  const pagedAll = filteredAll.slice((allPage - 1) * PAGE_SIZE, allPage * PAGE_SIZE)
  const pagedCourse = filteredCourse.slice((coursePage - 1) * PAGE_SIZE, coursePage * PAGE_SIZE)

  const handleAllSearch = (v: string) => { setAllSearch(v); setAllPage(1) }
  const handleCourseSearch = (v: string) => { setCourseSearch(v); setCoursePage(1) }

  const invalidate = () => invalidateAllCourseQueries(queryClient, courseId)

  const addMutation = useMutation({
    mutationFn: async (userIds: string[]) => {
      const allUsers = allTeachersQuery.data ?? []
      for (const id of userIds) {
        const user = allUsers.find((u) => u.id === id)
        if (user) await enrollStudent(courseId, user.email, 'teacher')
      }
    },
    onSuccess: () => {
      setSelectedAll(new Set())
      invalidate()
      toast.success('Lærer(e) lagt til i emnet.')
    },
    onError: () => toast.error('Klarte ikke legge til lærer(e).'),
  })

  const removeMutation = useMutation({
    mutationFn: async (userIds: string[]) => {
      for (const id of userIds) {
        await unenrollStudent(courseId, id)
      }
    },
    onSuccess: () => {
      setSelectedCourse(new Set())
      invalidate()
      toast.success('Lærer(e) fjernet fra emnet.')
    },
    onError: () => toast.error('Klarte ikke fjerne lærer(e).'),
  })

  const toggleAll = (id: string) => {
    setSelectedAll((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleCourse = (id: string) => {
    if (id === creatorId) return
    setSelectedCourse((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const isBusy = addMutation.isPending || removeMutation.isPending
  const isLoading = allTeachersQuery.isLoading || courseTeachersQuery.isLoading

  if (isLoading) {
    return (
      <div className="flex items-center gap-3 text-gray-500">
        <Spinner size="md" className="text-indigo-600" />
        <span>Laster lærere...</span>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {/* All teachers (not in course) */}
      <TeacherList
        title="Alle lærere"
        users={pagedAll}
        totalFiltered={filteredAll.length}
        selected={selectedAll}
        onToggle={toggleAll}
        search={allSearch}
        onSearchChange={handleAllSearch}
        page={allPage}
        totalPages={allTotalPages}
        onPageChange={setAllPage}
        actionLabel="Legg til i emnet"
        actionIcon={<UserPlus className="h-4 w-4" aria-hidden="true" />}
        actionDisabled={selectedAll.size === 0 || isBusy}
        actionLoading={addMutation.isPending}
        onAction={() => addMutation.mutate([...selectedAll])}
        creatorId={creatorId}
      />

      {/* Teachers in this course */}
      <TeacherList
        title="Lærere i emnet"
        users={pagedCourse}
        totalFiltered={filteredCourse.length}
        selected={selectedCourse}
        onToggle={toggleCourse}
        search={courseSearch}
        onSearchChange={handleCourseSearch}
        page={coursePage}
        totalPages={courseTotalPages}
        onPageChange={setCoursePage}
        actionLabel="Fjern fra emnet"
        actionIcon={<UserMinus className="h-4 w-4" aria-hidden="true" />}
        actionDisabled={selectedCourse.size === 0 || isBusy}
        actionLoading={removeMutation.isPending}
        onAction={() => removeMutation.mutate([...selectedCourse])}
        creatorId={creatorId}
      />
    </div>
  )
}

/* ------------------------------------------------------------------ */

interface TeacherListProps {
  title: string
  users: CourseStudentRead[]
  totalFiltered: number
  selected: Set<string>
  onToggle: (id: string) => void
  search: string
  onSearchChange: (v: string) => void
  page: number
  totalPages: number
  onPageChange: (p: number) => void
  actionLabel: string
  actionIcon: ReactNode
  actionDisabled: boolean
  actionLoading: boolean
  onAction: () => void
  creatorId: string
}

function TeacherList({
  title,
  users,
  totalFiltered,
  selected,
  onToggle,
  search,
  onSearchChange,
  page,
  totalPages,
  onPageChange,
  actionLabel,
  actionIcon,
  actionDisabled,
  actionLoading,
  onAction,
  creatorId,
}: TeacherListProps) {
  return (
    <div className="flex flex-col">
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-100 bg-gray-50 px-6 py-3">
          <h2 className="text-sm font-semibold text-gray-700">
            {title}{' '}
            <span className="font-normal text-gray-400">({totalFiltered})</span>
          </h2>
        </div>

        {/* Search */}
        <div className="border-b border-gray-100 px-4 py-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" aria-hidden="true" />
            <input
              type="text"
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Søk etter navn eller e-post..."
              className="input-field pl-10 py-1.5 text-sm"
              aria-label={`Søk ${title.toLowerCase()}`}
            />
          </div>
        </div>

        <div className="min-h-[320px]">
          {users.length === 0 ? (
            <p className="px-6 py-8 text-center text-sm text-gray-400">Ingen treff.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="w-10 px-4 py-2" />
                  <th scope="col" className="px-4 py-2 text-left font-medium text-gray-600">Navn</th>
                  <th scope="col" className="px-4 py-2 text-left font-medium text-gray-600">E-post</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {users.map((user) => {
                  const isCreator = user.id === creatorId
                  return (
                    <tr
                      key={user.id}
                      className={`transition-colors ${
                        isCreator
                          ? 'bg-gray-50 cursor-default'
                          : selected.has(user.id)
                            ? 'bg-indigo-50 cursor-pointer'
                            : 'hover:bg-gray-50 cursor-pointer'
                      }`}
                      onClick={() => !isCreator && onToggle(user.id)}
                    >
                      <td className="px-4 py-3 text-center">
                        {isCreator ? (
                          <span className="text-xs text-gray-400" title="Emneeier">—</span>
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
                        {isCreator && (
                          <span className="ml-2 inline-flex items-center rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700">
                            Eier
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-500">{user.email}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between border-t border-gray-100 bg-gray-50 px-6 py-2">
          <p className="text-xs text-gray-500">
            Side {page} av {totalPages}
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="rounded p-1 text-gray-500 hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="Forrige side"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="rounded p-1 text-gray-500 hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="Neste side"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
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
