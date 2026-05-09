import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle, Upload, UserPlus } from 'lucide-react'
import toast from 'react-hot-toast'
import { ConfirmDialog } from '../../components/ConfirmDialog'
import { Spinner } from '../../components/Spinner'
import {
  cancelEnrollmentImport,
  confirmEnrollmentImport,
  enrollStudent,
  getCourseStudents,
  previewEnrollmentImport,
  unenrollStudent,
} from '../../api/courses'
import type { CourseStudentRead, EnrollmentImportPreviewRead } from '../../types'
import { courseQueryKeys, invalidateAllCourseQueries } from './queryKeys'

interface StudentsTabProps {
  courseId: string
}

const PAGE_SIZE = 20

export function StudentsTab({ courseId }: StudentsTabProps) {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [enrollEmail, setEnrollEmail] = useState('')
  const [enrollError, setEnrollError] = useState('')
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<EnrollmentImportPreviewRead | null>(null)
  const [confirmDeleteStudentId, setConfirmDeleteStudentId] = useState<string | null>(null)

  const studentsQuery = useQuery({
    queryKey: courseQueryKeys.studentsPage(courseId, page),
    queryFn: () => getCourseStudents(courseId, page, PAGE_SIZE),
  })

  const enrollMutation = useMutation({
    mutationFn: (email: string) => enrollStudent(courseId, email),
    onSuccess: () => {
      invalidateAllCourseQueries(queryClient, courseId)
      setEnrollEmail('')
      setEnrollError('')
      toast.success('Student lagt til!')
    },
    onError: () => {
      setEnrollError('Klarte ikke legge til studenten. Sjekk at e-postadressen er korrekt.')
    },
  })

  const unenrollMutation = useMutation({
    mutationFn: (userId: string) => unenrollStudent(courseId, userId),
    onSuccess: () => {
      invalidateAllCourseQueries(queryClient, courseId)
      toast.success('Student fjernet.')
    },
    onError: () => toast.error('Klarte ikke fjerne student.'),
  })

  const previewMutation = useMutation({
    mutationFn: (file: File) => previewEnrollmentImport(courseId, file),
    onSuccess: (data) => setPreview(data),
    onError: () => toast.error('Klarte ikke laste forhåndsvisning av CSV-import.'),
  })

  const confirmImportMutation = useMutation({
    mutationFn: () => {
      if (!preview) throw new Error('Missing enrollment import preview')
      return confirmEnrollmentImport(courseId, preview.preview_id)
    },
    onSuccess: (result) => {
      invalidateAllCourseQueries(queryClient, courseId)
      setPreview(null)
      setCsvFile(null)
      toast.success(
        `Importert: ${result.enrolled_emails.length} påmeldt, ${result.created_emails.length} kontoer opprettet.`
      )
    },
    onError: () => toast.error('Klarte ikke bekrefte import.'),
  })

  const cancelImportMutation = useMutation({
    mutationFn: () => {
      if (!preview) throw new Error('Missing enrollment import preview')
      return cancelEnrollmentImport(courseId, preview.preview_id)
    },
    onSuccess: () => {
      setPreview(null)
      setCsvFile(null)
    },
    onError: () => toast.error('Klarte ikke avbryte import.'),
  })

  function handleEnroll(e: FormEvent) {
    e.preventDefault()
    setEnrollError('')
    if (!enrollEmail.trim()) {
      setEnrollError('E-post er påkrevd.')
      return
    }
    enrollMutation.mutate(enrollEmail.trim())
  }

  const students: CourseStudentRead[] = studentsQuery.data?.items ?? []
  const total = studentsQuery.data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="space-y-8">
      <section aria-labelledby="students-list-heading">
        <h2 id="students-list-heading" className="mb-4 text-base font-semibold text-gray-900">
          Påmeldte studenter
          {total > 0 && <span className="ml-2 text-sm font-normal text-gray-500">({total} totalt)</span>}
        </h2>

        {studentsQuery.isLoading && (
          <div className="flex items-center gap-3 text-gray-500">
            <Spinner size="sm" className="text-indigo-600" />
            <span>Laster studenter...</span>
          </div>
        )}

        {students.length === 0 && !studentsQuery.isLoading && (
          <p className="text-sm text-gray-500">Ingen studenter påmeldt ennå.</p>
        )}

        {students.length > 0 && (
          <>
            <div className="overflow-hidden rounded-lg border border-gray-200">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-gray-600">Navn</th>
                    <th scope="col" className="px-4 py-3 text-left font-medium text-gray-600">E-post</th>
                    <th scope="col" className="px-4 py-3 text-right font-medium text-gray-600">Handling</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {students.map((student) => (
                    <tr key={student.id}>
                      <td className="px-4 py-3 text-gray-900">
                        {student.first_name} {student.last_name}
                      </td>
                      <td className="px-4 py-3 text-gray-500">{student.email}</td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => setConfirmDeleteStudentId(student.id)}
                          className="rounded text-xs text-red-500 hover:text-red-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-500"
                          aria-label={`Fjern ${student.first_name} ${student.last_name}`}
                        >
                          Fjern
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {totalPages > 1 && (
              <div className="mt-4 flex items-center justify-between">
                <p className="text-xs text-gray-500">
                  Side {page} av {totalPages}
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="btn-secondary px-3 py-1 text-xs"
                  >
                    Forrige
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="btn-secondary px-3 py-1 text-xs"
                  >
                    Neste
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </section>

      <section aria-labelledby="enroll-heading">
        <h2 id="enroll-heading" className="mb-3 text-base font-semibold text-gray-900">
          Legg til student
        </h2>
        <form onSubmit={handleEnroll} noValidate className="flex items-start gap-3">
          <div className="flex-1">
            <label htmlFor="enroll-email" className="sr-only">
              Studentens e-postadresse
            </label>
            <input
              id="enroll-email"
              type="email"
              value={enrollEmail}
              onChange={(e) => setEnrollEmail(e.target.value)}
              placeholder="student@example.com"
              className="input-field"
              aria-describedby={enrollError ? 'enroll-error' : undefined}
            />
            {enrollError && (
              <p id="enroll-error" role="alert" className="mt-1 text-xs text-red-600">
                {enrollError}
              </p>
            )}
          </div>
          <button type="submit" disabled={enrollMutation.isPending} className="btn-primary shrink-0">
            {enrollMutation.isPending ? <Spinner size="sm" /> : <UserPlus className="h-4 w-4" aria-hidden="true" />}
            Legg til
          </button>
        </form>
      </section>

      <section aria-labelledby="csv-import-heading">
        <h2 id="csv-import-heading" className="mb-3 text-base font-semibold text-gray-900">
          Importer fra CSV
        </h2>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <label htmlFor="csv-file" className="btn-secondary cursor-pointer">
              <Upload className="h-4 w-4" aria-hidden="true" />
              Velg CSV-fil
            </label>
            <input
              id="csv-file"
              type="file"
              accept=".csv"
              className="sr-only"
              onChange={(e) => {
                const file = e.target.files?.[0] ?? null
                setCsvFile(file)
                setPreview(null)
              }}
            />
            {csvFile && <span className="text-sm text-gray-600">{csvFile.name}</span>}
          </div>

          {csvFile && !preview && (
            <button
              onClick={() => previewMutation.mutate(csvFile)}
              disabled={previewMutation.isPending}
              className="btn-secondary"
            >
              {previewMutation.isPending && <Spinner size="sm" />}
              Forhåndsvis import
            </button>
          )}

          {preview && (
            <div className="space-y-3 rounded-lg border border-gray-200 p-4">
              <h3 className="text-sm font-semibold text-gray-900">Forhåndsvisning</h3>
              <dl className="grid grid-cols-2 gap-2 text-sm">
                <dt className="text-gray-500">Totalt rader:</dt>
                <dd className="font-medium text-gray-900">{preview.total_rows}</dd>
                <dt className="text-gray-500">Kan meldes opp:</dt>
                <dd className="font-medium text-green-700">{preview.accepted_email_count}</dd>
                <dt className="text-gray-500">Mangler kontoer (opprettes):</dt>
                <dd className="font-medium text-yellow-700">{preview.missing_candidates.length}</dd>
                <dt className="text-gray-500">Allerede påmeldt:</dt>
                <dd className="font-medium text-gray-700">{preview.already_enrolled_emails.length}</dd>
                <dt className="text-gray-500">Ugyldige e-poster:</dt>
                <dd className="font-medium text-red-700">{preview.invalid_emails.length}</dd>
              </dl>
              {preview.has_warnings && (
                <div className="flex items-center gap-2 rounded-md bg-yellow-50 px-3 py-2">
                  <AlertTriangle className="h-4 w-4 text-yellow-600" aria-hidden="true" />
                  <p className="text-xs text-yellow-800">Importet har advarsler. Sjekk detaljene over før du bekrefter.</p>
                </div>
              )}
              <div className="flex gap-3 pt-1">
                <button
                  onClick={() => confirmImportMutation.mutate()}
                  disabled={confirmImportMutation.isPending}
                  className="btn-primary"
                >
                  {confirmImportMutation.isPending && <Spinner size="sm" />}
                  <CheckCircle className="h-4 w-4" aria-hidden="true" />
                  Bekreft import
                </button>
                <button
                  onClick={() => cancelImportMutation.mutate()}
                  disabled={cancelImportMutation.isPending}
                  className="btn-secondary"
                >
                  Avbryt
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      <ConfirmDialog
        open={!!confirmDeleteStudentId}
        title="Fjern student"
        description="Er du sikker på at du vil fjerne denne studenten fra emnet?"
        confirmLabel="Fjern"
        variant="danger"
        onConfirm={() => {
          if (confirmDeleteStudentId) unenrollMutation.mutate(confirmDeleteStudentId)
          setConfirmDeleteStudentId(null)
        }}
        onCancel={() => setConfirmDeleteStudentId(null)}
      />
    </div>
  )
}
