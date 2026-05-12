import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BookOpen, Plus } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../contexts/AuthContext'
import { Layout } from '../components/Layout'
import { RoleBadge } from '../components/Badge'
import {
  createCourse,
  getAvailableCourses,
  getCourses,
  getResponsibleCourses,
} from '../api/courses'
import type { CourseCreate } from '../types'
import { CourseSection } from './dashboard/CourseSection'
import { CreateCourseModal } from './dashboard/CreateCourseModal'
import { dashboardQueryKeys } from './dashboard/queryKeys'
import { usePageTitle } from '../hooks/usePageTitle'

/** Home dashboard showing student courses and teacher course-management entry points. */
export function DashboardPage() {
  usePageTitle('Dashboard')
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createCourseError, setCreateCourseError] = useState('')

  const isTeacher = user?.global_role === 'teacher' || user?.global_role === 'admin'

  const responsibleQuery = useQuery({
    queryKey: dashboardQueryKeys.responsibleCourses,
    queryFn: getResponsibleCourses,
    enabled: isTeacher,
  })

  const availableQuery = useQuery({
    queryKey: dashboardQueryKeys.availableCourses,
    queryFn: getAvailableCourses,
    enabled: isTeacher,
  })

  const studentCoursesQuery = useQuery({
    queryKey: dashboardQueryKeys.studentCourses,
    queryFn: getCourses,
    enabled: !isTeacher,
  })

  const createCourseMutation = useMutation({
    mutationFn: createCourse,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardQueryKeys.responsibleCourses })
      toast.success('Emne opprettet!')
      setShowCreateModal(false)
    },
    onError: () => {
      setCreateCourseError('Klarte ikke opprette emnet. Sjekk at alle felter er utfylt korrekt.')
    },
  })

  function handleOpenCreateModal() {
    setCreateCourseError('')
    setShowCreateModal(true)
  }

  function handleCloseCreateModal() {
    setCreateCourseError('')
    setShowCreateModal(false)
  }

  function handleCreateCourse(payload: CourseCreate) {
    setCreateCourseError('')
    createCourseMutation.mutate(payload)
  }

  return (
    <Layout>
      <div className="flex-1 min-h-0 overflow-y-auto">
        <div className="mx-auto w-full max-w-5xl px-4 py-10 sm:px-6">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Hei, {user?.first_name}!
              </h1>
              <div className="mt-1 flex items-center gap-2">
                <p className="text-sm text-gray-500">{user?.email}</p>
                {user && <RoleBadge role={user.global_role} />}
              </div>
            </div>
            {isTeacher && (
              <button
                onClick={handleOpenCreateModal}
                className="btn-primary"
              >
                <Plus className="h-4 w-4" aria-hidden="true" />
                Opprett nytt emne
              </button>
            )}
          </div>

          {isTeacher ? (
            <div className="space-y-10">
              <CourseSection
                headingId="my-courses-heading"
                title="Mine emner"
                courses={responsibleQuery.data}
                isLoading={responsibleQuery.isLoading}
                isError={responsibleQuery.isError}
                errorMessage="Klarte ikke laste emner. Prøv å laste siden på nytt."
                emptyMessage="Du har ingen emner ennå. Opprett et nytt emne for å komme i gang."
                onCourseClick={(course) => navigate(`/manage/${course.id}`)}
              />

              <CourseSection
                headingId="available-courses-heading"
                title="Tilgjengelige emner"
                courses={availableQuery.data}
                isLoading={availableQuery.isLoading}
                isError={availableQuery.isError}
                errorMessage="Klarte ikke laste tilgjengelige emner."
                emptyMessage="Ingen tilgjengelige emner."
                onCourseClick={(course) => navigate(`/chat/${course.id}`)}
              />
            </div>
          ) : (
            <CourseSection
              headingId="student-courses-heading"
              title="Mine emner"
              courses={studentCoursesQuery.data}
              isLoading={studentCoursesQuery.isLoading}
              isError={studentCoursesQuery.isError}
              errorMessage="Klarte ikke laste emner. Prøv å laste siden på nytt."
              emptyState={
                <div className="rounded-lg border border-dashed border-gray-300 p-10 text-center">
                  <BookOpen className="mx-auto mb-3 h-10 w-10 text-gray-300" aria-hidden="true" />
                  <p className="text-sm text-gray-500">Du er ikke meldt opp i noen emner ennå.</p>
                  <p className="mt-1 text-sm text-gray-400">Ta kontakt med emneansvarlig for å bli meldt opp.</p>
                </div>
              }
              onCourseClick={(course) => navigate(`/chat/${course.id}`)}
            />
          )}
        </div>
      </div>
      {showCreateModal && (
        <CreateCourseModal
          isSubmitting={createCourseMutation.isPending}
          errorMessage={createCourseError}
          onClose={handleCloseCreateModal}
          onSubmit={handleCreateCourse}
        />
      )}
    </Layout>
  )
}
