import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, BookOpen, X, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../contexts/AuthContext'
import { Layout } from '../components/Layout'
import { Spinner } from '../components/Spinner'
import { RoleBadge } from '../components/Badge'
import {
  getCourses,
  getAvailableCourses,
  getResponsibleCourses,
  createCourse,
} from '../api/courses'
import type { CourseRead } from '../types'
import { isStudyParticipantEmail } from '../study/courseSequence'

function CourseCard({
  course,
  onClick,
}: {
  course: CourseRead
  onClick: () => void
}) {
  return (
    <article>
      <button
        onClick={onClick}
        className="group flex w-full items-center justify-between rounded-lg border border-gray-200 bg-white p-5 text-left shadow-sm hover:border-indigo-300 hover:shadow-md transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"
      >
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-50">
            <BookOpen className="h-5 w-5 text-indigo-600" aria-hidden="true" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 group-hover:text-indigo-700 transition-colors">
              {course.name}
            </h3>
            <p className="mt-0.5 text-sm text-gray-500">{course.code}</p>
          </div>
        </div>
        <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-indigo-600 transition-colors" aria-hidden="true" />
      </button>
    </article>
  )
}

function deriveCode(name: string): string {
  return name.toUpperCase().replace(/\s+/g, '_').slice(0, 20)
}

interface CreateCourseModalProps {
  onClose: () => void
  onCreated: () => void
}

function CreateCourseModal({ onClose, onCreated }: CreateCourseModalProps) {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [codeManuallyEdited, setCodeManuallyEdited] = useState(false)
  const [description, setDescription] = useState('')
  const [documentsDir, setDocumentsDir] = useState('')
  const [formError, setFormError] = useState('')

  const mutation = useMutation({
    mutationFn: createCourse,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['responsible-courses'] })
      toast.success('Emne opprettet!')
      onCreated()
    },
    onError: () => {
      setFormError('Klarte ikke opprette emnet. Sjekk at alle felter er utfylt korrekt.')
    },
  })

  function handleNameChange(value: string) {
    setName(value)
    if (!codeManuallyEdited) {
      const derived = deriveCode(value)
      setCode(derived)
      setDocumentsDir(`data/documents/${derived.toLowerCase()}`)
    }
  }

  function handleCodeChange(value: string) {
    setCode(value)
    setCodeManuallyEdited(true)
    setDocumentsDir(`data/documents/${value.toLowerCase()}`)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormError('')
    if (!name.trim()) { setFormError('Emnenavn er påkrevd.'); return }
    if (!code.trim()) { setFormError('Emnekode er påkrevd.'); return }
    if (!documentsDir.trim()) { setFormError('Dokumentmappe er påkrevd.'); return }
    mutation.mutate({ name: name.trim(), code: code.trim(), description: description.trim() || undefined, documents_dir: documentsDir.trim() })
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-course-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div className="fixed inset-0 bg-black/40" onClick={onClose} aria-hidden="true" />
      <div className="relative z-10 w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-5 flex items-center justify-between">
          <h2 id="create-course-title" className="text-lg font-semibold text-gray-900">
            Opprett nytt emne
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-gray-400 hover:text-gray-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"
            aria-label="Lukk"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          <div>
            <label htmlFor="course-name" className="label">
              Emnenavn <span aria-hidden="true">*</span>
            </label>
            <input
              id="course-name"
              type="text"
              required
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              className="input-field mt-1"
              placeholder="f.eks. Introduksjon til maskinlæring"
            />
          </div>

          <div>
            <label htmlFor="course-code" className="label">
              Emnekode <span aria-hidden="true">*</span>
            </label>
            <input
              id="course-code"
              type="text"
              required
              value={code}
              onChange={(e) => handleCodeChange(e.target.value.toUpperCase().slice(0, 20))}
              className="input-field mt-1 font-mono uppercase"
              placeholder="f.eks. TDT4173"
              maxLength={20}
            />
          </div>

          <div>
            <label htmlFor="course-description" className="label">
              Beskrivelse
            </label>
            <textarea
              id="course-description"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input-field mt-1 resize-none"
              placeholder="Valgfri beskrivelse av emnet"
            />
          </div>

          <div>
            <label htmlFor="course-docs-dir" className="label">
              Dokumentmappe <span aria-hidden="true">*</span>
            </label>
            <input
              id="course-docs-dir"
              type="text"
              required
              value={documentsDir}
              onChange={(e) => setDocumentsDir(e.target.value)}
              className="input-field mt-1 font-mono text-xs"
            />
          </div>

          {formError && (
            <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {formError}
            </p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">
              Avbryt
            </button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending && <Spinner size="sm" />}
              Opprett emne
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [showCreateModal, setShowCreateModal] = useState(false)

  const isTeacher = user?.global_role === 'teacher' || user?.global_role === 'admin'

  const responsibleQuery = useQuery({
    queryKey: ['responsible-courses'],
    queryFn: getResponsibleCourses,
    enabled: isTeacher,
  })

  const availableQuery = useQuery({
    queryKey: ['available-courses'],
    queryFn: getAvailableCourses,
    enabled: isTeacher,
  })

  const studentCoursesQuery = useQuery({
    queryKey: ['my-courses'],
    queryFn: getCourses,
    enabled: !isTeacher,
  })

  const isStudyParticipant = !isTeacher && isStudyParticipantEmail(user?.email)
  useEffect(() => {
    if (!isStudyParticipant || !studentCoursesQuery.isSuccess) return
    const courses = studentCoursesQuery.data
    if (!courses || courses.length !== 1) return
    navigate(`/chat/${courses[0].id}`, { replace: true })
  }, [isStudyParticipant, studentCoursesQuery.isSuccess, studentCoursesQuery.data, navigate])

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
              onClick={() => setShowCreateModal(true)}
              className="btn-primary"
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              Opprett nytt emne
            </button>
          )}
        </div>

        {isTeacher ? (
          <div className="space-y-10">
            <section aria-labelledby="my-courses-heading">
              <h2 id="my-courses-heading" className="mb-4 text-lg font-semibold text-gray-800">
                Mine emner
              </h2>
              {responsibleQuery.isLoading && (
                <div className="flex items-center gap-3 text-gray-500">
                  <Spinner size="sm" className="text-indigo-600" />
                  <span>Laster emner...</span>
                </div>
              )}
              {responsibleQuery.isError && (
                <p className="text-sm text-red-600">Klarte ikke laste emner. Prøv å laste siden på nytt.</p>
              )}
              {responsibleQuery.data && responsibleQuery.data.length === 0 && (
                <p className="text-sm text-gray-500">Du har ingen emner ennå. Opprett et nytt emne for å komme i gang.</p>
              )}
              {responsibleQuery.data && responsibleQuery.data.length > 0 && (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {responsibleQuery.data.map((course) => (
                    <CourseCard
                      key={course.id}
                      course={course}
                      onClick={() => navigate(`/courses/${course.id}`)}
                    />
                  ))}
                </div>
              )}
            </section>

            <section aria-labelledby="available-courses-heading">
              <h2 id="available-courses-heading" className="mb-4 text-lg font-semibold text-gray-800">
                Tilgjengelige emner
              </h2>
              {availableQuery.isLoading && (
                <div className="flex items-center gap-3 text-gray-500">
                  <Spinner size="sm" className="text-indigo-600" />
                  <span>Laster emner...</span>
                </div>
              )}
              {availableQuery.isError && (
                <p className="text-sm text-red-600">Klarte ikke laste tilgjengelige emner.</p>
              )}
              {availableQuery.data && availableQuery.data.length === 0 && (
                <p className="text-sm text-gray-500">Ingen tilgjengelige emner.</p>
              )}
              {availableQuery.data && availableQuery.data.length > 0 && (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {availableQuery.data.map((course) => (
                    <CourseCard
                      key={course.id}
                      course={course}
                      onClick={() => navigate(`/chat/${course.id}`)}
                    />
                  ))}
                </div>
              )}
            </section>
          </div>
        ) : (
          <section aria-labelledby="student-courses-heading">
            <h2 id="student-courses-heading" className="mb-4 text-lg font-semibold text-gray-800">
              Mine emner
            </h2>
            {studentCoursesQuery.isLoading && (
              <div className="flex items-center gap-3 text-gray-500">
                <Spinner size="sm" className="text-indigo-600" />
                <span>Laster emner...</span>
              </div>
            )}
            {studentCoursesQuery.isError && (
              <p className="text-sm text-red-600">Klarte ikke laste emner. Prøv å laste siden på nytt.</p>
            )}
            {studentCoursesQuery.data && studentCoursesQuery.data.length === 0 && (
              <div className="rounded-lg border border-dashed border-gray-300 p-10 text-center">
                <BookOpen className="mx-auto mb-3 h-10 w-10 text-gray-300" aria-hidden="true" />
                <p className="text-sm text-gray-500">Du er ikke meldt opp i noen emner ennå.</p>
                <p className="mt-1 text-sm text-gray-400">Ta kontakt med emneansvarlig for å bli meldt opp.</p>
              </div>
            )}
            {studentCoursesQuery.data && studentCoursesQuery.data.length > 0 && (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {studentCoursesQuery.data.map((course) => (
                  <CourseCard
                    key={course.id}
                    course={course}
                    onClick={() => navigate(`/chat/${course.id}`)}
                  />
                ))}
              </div>
            )}
          </section>
        )}
      </div>
      </div>
      {showCreateModal && (
        <CreateCourseModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => setShowCreateModal(false)}
        />
      )}
    </Layout>
  )
}
