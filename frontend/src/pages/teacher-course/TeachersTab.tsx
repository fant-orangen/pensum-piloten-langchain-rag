import { type ReactNode, type UIEvent, useEffect, useMemo, useState } from 'react'
import { useInfiniteQuery, useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, UserPlus, UserMinus } from 'lucide-react'
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

/**
 * Course-owner tab for assigning and removing course teachers.
 *
 * The course creator cannot be removed; the backend enforces the same rule.
 */
export function TeachersTab({ courseId, creatorId }: TeachersTabProps) {
  const queryClient = useQueryClient()

  const [allSearch, setAllSearch] = useState('')
  const [courseSearch, setCourseSearch] = useState('')
  const [selectedAll, setSelectedAll] = useState<Set<string>>(new Set())
  const [selectedCourse, setSelectedCourse] = useState<Set<string>>(new Set())
  const [allVisibleCount, setAllVisibleCount] = useState(PAGE_SIZE)

  // All teachers in the system
  const allTeachersQuery = useQuery({
    queryKey: courseQueryKeys.allTeachers,
    queryFn: getAllTeachers,
  })

  // Teachers in the current course (paginated server-side, but we fetch all for client-side filtering)
  const courseTeachersQuery = useInfiniteQuery({
    queryKey: courseQueryKeys.teachers(courseId),
    queryFn: ({ pageParam }) => getCourseTeachers(courseId, pageParam, PAGE_SIZE),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => (
      lastPage.page < lastPage.pages ? lastPage.page + 1 : undefined
    ),
  })

  const allTeachers = allTeachersQuery.data ?? []
  const courseTeachers = courseTeachersQuery.data?.pages.flatMap((page) => page.items) ?? []
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

  useEffect(() => {
    if (
      courseSearch.trim() &&
      filteredCourse.length === 0 &&
      courseTeachersQuery.hasNextPage &&
      !courseTeachersQuery.isFetchingNextPage
    ) {
      courseTeachersQuery.fetchNextPage()
    }
  }, [courseSearch, filteredCourse.length, courseTeachersQuery])

  const pagedAll = filteredAll.slice(0, allVisibleCount)

  const handleAllSearch = (v: string) => { setAllSearch(v); setAllVisibleCount(PAGE_SIZE) }
  const handleCourseSearch = (v: string) => setCourseSearch(v)
  const handleAllLoadMore = () => {
    setAllVisibleCount((count) => Math.min(filteredAll.length, count + PAGE_SIZE))
  }
  const handleCourseLoadMore = () => {
    if (courseTeachersQuery.hasNextPage && !courseTeachersQuery.isFetchingNextPage) {
      courseTeachersQuery.fetchNextPage()
    }
  }

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
        hasMore={pagedAll.length < filteredAll.length}
        isLoadingMore={false}
        selected={selectedAll}
        onToggle={toggleAll}
        search={allSearch}
        onSearchChange={handleAllSearch}
        onLoadMore={handleAllLoadMore}
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
        users={filteredCourse}
        totalFiltered={filteredCourse.length}
        hasMore={courseTeachersQuery.hasNextPage}
        isLoadingMore={courseTeachersQuery.isFetchingNextPage}
        selected={selectedCourse}
        onToggle={toggleCourse}
        search={courseSearch}
        onSearchChange={handleCourseSearch}
        onLoadMore={handleCourseLoadMore}
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
  hasMore: boolean
  isLoadingMore: boolean
  selected: Set<string>
  onToggle: (id: string) => void
  search: string
  onSearchChange: (v: string) => void
  onLoadMore: () => void
  actionLabel: string
  actionIcon: ReactNode
  actionDisabled: boolean
  actionLoading: boolean
  onAction: () => void
  creatorId: string
}

/** Selectable teacher table with search, pagination, and creator-protection UI. */
function TeacherList({
  title,
  users,
  totalFiltered,
  hasMore,
  isLoadingMore,
  selected,
  onToggle,
  search,
  onSearchChange,
  onLoadMore,
  actionLabel,
  actionIcon,
  actionDisabled,
  actionLoading,
  onAction,
  creatorId,
}: TeacherListProps) {
  function handleScroll(e: UIEvent<HTMLDivElement>) {
    const el = e.currentTarget
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 80 && hasMore && !isLoadingMore) {
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
          {isLoadingMore && (
            <div className="flex justify-center py-3">
              <Spinner size="sm" className="text-indigo-600" />
            </div>
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
