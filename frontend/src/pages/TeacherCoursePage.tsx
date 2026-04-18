import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Eye,
  RefreshCw,
  Trash2,
  Upload,
  UserPlus,
  FileText,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { nb } from 'date-fns/locale'
import clsx from 'clsx'
import { Layout } from '../components/Layout'
import { Spinner } from '../components/Spinner'
import { DocumentStatusBadge, RebuildStatusBadge } from '../components/Badge'
import { ConfirmDialog } from '../components/ConfirmDialog'
import {
  getCourseStudents,
  enrollStudent,
  unenrollStudent,
  previewEnrollmentImport,
  confirmEnrollmentImport,
  cancelEnrollmentImport,
  getCourseDocuments,
  uploadDocuments,
  uploadZip,
  deleteDocument,
  deleteAllDocuments,
  getDocumentsStatus,
  confirmIngestion,
  getCourseInstructions,
  updateCourseInstructions,
  getResponsibleCourses,
} from '../api/courses'
import type {
  CourseStudentRead,
  CourseDocumentRead,
  EnrollmentImportPreviewRead,
} from '../types'

type Tab = 'students' | 'materials' | 'instructions'

function formatDate(dateStr: string): string {
  try {
    return format(new Date(dateStr), 'd. MMM yyyy', { locale: nb })
  } catch {
    return dateStr
  }
}

// ─── Students Tab ────────────────────────────────────────────────────────────

interface StudentsTabProps {
  courseId: string
}

function StudentsTab({ courseId }: StudentsTabProps) {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const pageSize = 20

  const [enrollEmail, setEnrollEmail] = useState('')
  const [enrollError, setEnrollError] = useState('')

  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<EnrollmentImportPreviewRead | null>(null)
  const [confirmDeleteStudentId, setConfirmDeleteStudentId] = useState<string | null>(null)

  const studentsQuery = useQuery({
    queryKey: ['course-students', courseId, page],
    queryFn: () => getCourseStudents(courseId, page, pageSize),
  })

  const enrollMutation = useMutation({
    mutationFn: (email: string) => enrollStudent(courseId, email),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['course-students', courseId] })
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
      queryClient.invalidateQueries({ queryKey: ['course-students', courseId] })
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
    mutationFn: () => confirmEnrollmentImport(courseId, preview!.preview_id),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['course-students', courseId] })
      setPreview(null)
      setCsvFile(null)
      toast.success(
        `Importert: ${result.enrolled_emails.length} påmeldt, ${result.created_emails.length} kontoer opprettet.`
      )
    },
    onError: () => toast.error('Klarte ikke bekrefte import.'),
  })

  const cancelImportMutation = useMutation({
    mutationFn: () => cancelEnrollmentImport(courseId, preview!.preview_id),
    onSuccess: () => {
      setPreview(null)
      setCsvFile(null)
    },
    onError: () => toast.error('Klarte ikke avbryte import.'),
  })

  function handleEnroll(e: React.FormEvent) {
    e.preventDefault()
    setEnrollError('')
    if (!enrollEmail.trim()) { setEnrollError('E-post er påkrevd.'); return }
    enrollMutation.mutate(enrollEmail.trim())
  }

  const students: CourseStudentRead[] = studentsQuery.data?.items ?? []
  const total = studentsQuery.data?.total ?? 0
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="space-y-8">
      {/* Student list */}
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
                          className="text-red-500 hover:text-red-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-500 rounded text-xs"
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
                    className="btn-secondary py-1 px-3 text-xs"
                  >
                    Forrige
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="btn-secondary py-1 px-3 text-xs"
                  >
                    Neste
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </section>

      {/* Enroll single student */}
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

      {/* CSV import */}
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
            <div className="rounded-lg border border-gray-200 p-4 space-y-3">
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

// ─── Materials Tab ────────────────────────────────────────────────────────────

interface MaterialsTabProps {
  courseId: string
}

function MaterialsTab({ courseId }: MaterialsTabProps) {
  const queryClient = useQueryClient()
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set())
  const [isDragging, setIsDragging] = useState(false)
  const [confirmDeleteAll, setConfirmDeleteAll] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const zipInputRef = useRef<HTMLInputElement>(null)

  async function refreshMaterialsQueries() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['course-documents', courseId] }),
      queryClient.invalidateQueries({ queryKey: ['course-documents-status', courseId] }),
    ])
  }

  const documentsQuery = useQuery({
    queryKey: ['course-documents', courseId],
    queryFn: () => getCourseDocuments(courseId),
  })

  const statusQuery = useQuery({
    queryKey: ['course-documents-status', courseId],
    queryFn: () => getDocumentsStatus(courseId),
    refetchInterval: (query) => {
      const status = query.state.data?.rebuild_status
      return status === 'building' || status === 'queued' ? 3000 : false
    },
  })

  const uploadMutation = useMutation({
    mutationFn: (files: File[]) => uploadDocuments(courseId, files),
    onSuccess: async (docs) => {
      await refreshMaterialsQueries()
      toast.success(`${docs.length} fil(er) lastet opp.`)
    },
    onError: () => toast.error('Filopplasting feilet.'),
  })

  const uploadZipMutation = useMutation({
    mutationFn: (file: File) => uploadZip(courseId, file),
    onSuccess: async (result) => {
      await refreshMaterialsQueries()
      toast.success(
        `ZIP-import: ${result.staged_count} klargjort${result.skipped_count > 0 ? `, ${result.skipped_count} hoppet over` : ''}.`
      )
    },
    onError: () => toast.error('ZIP-opplasting feilet.'),
  })

  const deleteDocMutation = useMutation({
    mutationFn: (docId: string) => deleteDocument(courseId, docId),
    onSuccess: async () => {
      await refreshMaterialsQueries()
      toast.success('Dokument fjernet.')
    },
    onError: () => toast.error('Klarte ikke fjerne dokument.'),
  })

  const deleteAllMutation = useMutation({
    mutationFn: () => deleteAllDocuments(courseId),
    onSuccess: async (result) => {
      await refreshMaterialsQueries()
      setSelectedDocIds(new Set())
      toast.success(`${result.removed} dokument(er) fjernet.`)
    },
    onError: () => toast.error('Klarte ikke fjerne alle dokumenter.'),
  })

  const confirmMutation = useMutation({
    mutationFn: () => confirmIngestion(courseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['course-documents-status', courseId] })
      toast.success('Innlesing startet!')
    },
    onError: () => toast.error('Klarte ikke starte innlesing.'),
  })

  function handleFileDrop(e: React.DragEvent) {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files)
    const zipFiles = files.filter((f) => f.name.endsWith('.zip'))
    const regularFiles = files.filter((f) => !f.name.endsWith('.zip'))
    if (zipFiles.length > 0) zipInputMutation(zipFiles[0])
    if (regularFiles.length > 0) uploadMutation.mutate(regularFiles)
  }

  function zipInputMutation(file: File) {
    uploadZipMutation.mutate(file)
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    if (files.length > 0) uploadMutation.mutate(files)
    e.target.value = ''
  }

  function handleZipInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) uploadZipMutation.mutate(file)
    e.target.value = ''
  }

  function toggleSelectDoc(id: string) {
    setSelectedDocIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleSelectAll(docs: CourseDocumentRead[]) {
    if (selectedDocIds.size === docs.length) {
      setSelectedDocIds(new Set())
    } else {
      setSelectedDocIds(new Set(docs.map((d) => d.id)))
    }
  }

  async function deleteSelected() {
    for (const id of selectedDocIds) {
      await deleteDocument(courseId, id)
    }
    await refreshMaterialsQueries()
    setSelectedDocIds(new Set())
    toast.success('Valgte dokumenter fjernet.')
  }

  const documents = documentsQuery.data ?? []
  const isUploading = uploadMutation.isPending || uploadZipMutation.isPending
  const status = statusQuery.data

  return (
    <div className="space-y-6">
      {/* Status card */}
      <section aria-labelledby="ingestion-status-heading" className="rounded-lg border border-gray-200 p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 id="ingestion-status-heading" className="text-sm font-semibold text-gray-900">
            Innlesingstatus
          </h2>
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['course-documents-status', courseId] })}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-indigo-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 rounded transition-colors"
            aria-label="Oppdater status"
          >
            <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
            Oppdater
          </button>
        </div>
        {statusQuery.isLoading ? (
          <Spinner size="sm" className="text-indigo-600" />
        ) : status ? (
          <dl className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-xs text-gray-500">Status</dt>
              <dd className="mt-0.5"><RebuildStatusBadge status={status.rebuild_status} /></dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Indeksversjon</dt>
              <dd className="mt-0.5 font-medium text-gray-900">{status.index_version}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Venter på innlesing</dt>
              <dd className="mt-0.5 font-medium text-yellow-700">{status.pending_additions}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Venter på sletting</dt>
              <dd className="mt-0.5 font-medium text-red-700">{status.pending_removals}</dd>
            </div>
            {status.rebuild_error && (
              <div className="col-span-4">
                <dt className="text-xs text-gray-500">Feilmelding</dt>
                <dd className="mt-0.5 rounded bg-red-50 px-2 py-1 font-mono text-xs text-red-700">
                  {status.rebuild_error}
                </dd>
              </div>
            )}
          </dl>
        ) : (
          <p className="text-sm text-gray-400">Ingen statusdata tilgjengelig.</p>
        )}
        <div className="mt-4">
          <button
            onClick={() => confirmMutation.mutate()}
            disabled={
              isUploading ||
              confirmMutation.isPending ||
              !status ||
              (status.pending_additions === 0 && status.pending_removals === 0)
            }
            className="btn-primary"
          >
            {confirmMutation.isPending && <Spinner size="sm" />}
            Start innlesing
          </button>
        </div>
      </section>

      <section aria-labelledby="upload-file-types-heading" className="rounded-lg border border-gray-200 p-4">
        <h2 id="upload-file-types-heading" className="text-sm font-semibold text-gray-900">
          Hva kan du laste opp?
        </h2>
        <div className="mt-2 space-y-2 text-sm text-gray-600">
          <p>
            Systemet fungerer best med vanlige dokumenter og tekstbaserte filer, som
            PDF, Word-dokumenter (.docx), tekstfiler, Markdown og enkle tabellfiler
            som CSV.
          </p>
          <p>
            Du kan også laste opp en ZIP-fil hvis du vil sende inn flere støttede filer
            samtidig. Bilder, video og lyd støttes ikke i innlesingen.
          </p>
        </div>
      </section>

      {/* Upload area */}
      <section aria-labelledby="upload-heading">
        <h2 id="upload-heading" className="mb-3 text-sm font-semibold text-gray-900">
          Last opp filer
        </h2>
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleFileDrop}
          className={clsx(
            'rounded-lg border-2 border-dashed p-8 text-center transition-colors',
            isDragging ? 'border-indigo-400 bg-indigo-50' : 'border-gray-300 bg-gray-50 hover:border-gray-400'
          )}
        >
          <Upload className="mx-auto mb-3 h-8 w-8 text-gray-400" aria-hidden="true" />
          <p className="text-sm text-gray-600">
            Dra og slipp filer her, eller velg filer nedenfor
          </p>
          <p className="mt-1 text-xs text-gray-400">
            Vanlige filer lastes opp direkte. ZIP-filer pakkes ut automatisk.
          </p>
          <div className="mt-4 flex justify-center gap-3">
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="btn-secondary text-xs"
            >
              {(uploadMutation.isPending) ? <Spinner size="sm" /> : <FileText className="h-3.5 w-3.5" aria-hidden="true" />}
              Velg filer
            </button>
            <button
              onClick={() => zipInputRef.current?.click()}
              disabled={isUploading}
              className="btn-secondary text-xs"
            >
              {(uploadZipMutation.isPending) ? <Spinner size="sm" /> : <Upload className="h-3.5 w-3.5" aria-hidden="true" />}
              Last opp ZIP
            </button>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="sr-only"
            onChange={handleFileInput}
            aria-label="Velg filer"
          />
          <input
            ref={zipInputRef}
            type="file"
            accept=".zip"
            className="sr-only"
            onChange={handleZipInput}
            aria-label="Velg ZIP-fil"
          />
        </div>
      </section>

      {/* Documents table */}
      <section aria-labelledby="documents-heading">
        <div className="mb-3 flex items-center justify-between">
          <h2 id="documents-heading" className="text-sm font-semibold text-gray-900">
            Dokumenter
            {documents.length > 0 && (
              <span className="ml-2 text-xs font-normal text-gray-500">({documents.length})</span>
            )}
          </h2>
          <div className="flex gap-2">
            {selectedDocIds.size > 0 && (
              <button
                onClick={deleteSelected}
                className="btn-danger text-xs py-1.5"
              >
                <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                Slett valgte ({selectedDocIds.size})
              </button>
            )}
            {documents.length > 0 && (
              <button
                onClick={() => setConfirmDeleteAll(true)}
                className="btn-secondary text-xs py-1.5"
              >
                <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                Slett alle
              </button>
            )}
          </div>
        </div>

        {documentsQuery.isLoading && (
          <div className="flex items-center gap-3 text-gray-500">
            <Spinner size="sm" className="text-indigo-600" />
            <span>Laster dokumenter...</span>
          </div>
        )}

        {documents.length === 0 && !documentsQuery.isLoading && (
          <p className="text-sm text-gray-500">Ingen dokumenter lastet opp ennå.</p>
        )}

        {documents.length > 0 && (
          <div className="overflow-hidden rounded-lg border border-gray-200">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="w-10 px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selectedDocIds.size === documents.length && documents.length > 0}
                      onChange={() => toggleSelectAll(documents)}
                      aria-label="Velg alle dokumenter"
                      className="rounded accent-indigo-600"
                    />
                  </th>
                  <th scope="col" className="px-4 py-3 text-left font-medium text-gray-600">Filnavn</th>
                  <th scope="col" className="px-4 py-3 text-left font-medium text-gray-600">Status</th>
                  <th scope="col" className="px-4 py-3 text-left font-medium text-gray-600">Dato</th>
                  <th scope="col" className="px-4 py-3 text-right font-medium text-gray-600">Handling</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {documents.map((doc) => (
                  <tr key={doc.id}>
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedDocIds.has(doc.id)}
                        onChange={() => toggleSelectDoc(doc.id)}
                        aria-label={`Velg ${doc.original_filename}`}
                        className="rounded accent-indigo-600"
                      />
                    </td>
                    <td className="px-4 py-3 text-gray-900 font-mono text-xs">{doc.original_filename}</td>
                    <td className="px-4 py-3">
                      <DocumentStatusBadge status={doc.status} />
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(doc.created_at)}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => deleteDocMutation.mutate(doc.id)}
                        disabled={deleteDocMutation.isPending}
                        className="text-red-500 hover:text-red-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-500 rounded text-xs"
                        aria-label={`Slett ${doc.original_filename}`}
                      >
                        Slett
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <ConfirmDialog
        open={confirmDeleteAll}
        title="Slett alle dokumenter"
        description="Er du sikker på at du vil slette alle dokumenter i dette emnet? Denne handlingen kan ikke angres."
        confirmLabel="Slett alle"
        variant="danger"
        onConfirm={() => { setConfirmDeleteAll(false); deleteAllMutation.mutate() }}
        onCancel={() => setConfirmDeleteAll(false)}
      />
    </div>
  )
}

// ─── Instructions Tab ─────────────────────────────────────────────────────────

interface InstructionsTabProps {
  courseId: string
}

const MAX_INSTRUCTIONS_CHARS = 3000

function InstructionsTab({ courseId }: InstructionsTabProps) {
  const queryClient = useQueryClient()
  const [instructions, setInstructions] = useState('')
  const [loaded, setLoaded] = useState(false)

  const instructionsQuery = useQuery({
    queryKey: ['course-instructions', courseId],
    queryFn: () => getCourseInstructions(courseId),
  })

  useEffect(() => {
    if (instructionsQuery.data && !loaded) {
      setInstructions(instructionsQuery.data.course_specific_instructions ?? '')
      setLoaded(true)
    }
  }, [instructionsQuery.data, loaded])

  const saveMutation = useMutation({
    mutationFn: (text: string) => updateCourseInstructions(courseId, text),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['course-instructions', courseId] })
      toast.success('Instruksjoner lagret!')
    },
    onError: () => toast.error('Klarte ikke lagre instruksjoner.'),
  })

  const charsLeft = MAX_INSTRUCTIONS_CHARS - instructions.length

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="course-instructions" className="label mb-2">
          Emnespesifikke instruksjoner
        </label>
        <p className="mb-3 text-sm text-gray-500">
          Disse instruksjonene brukes av AI-assistenten for å tilpasse svar til emnet. Du kan for
          eksempel beskrive fagets temaer, pensum, eller pedagogiske mål.
        </p>
        {instructionsQuery.isLoading ? (
          <div className="flex items-center gap-3 text-gray-500">
            <Spinner size="sm" className="text-indigo-600" />
            <span>Laster instruksjoner...</span>
          </div>
        ) : (
          <>
            <textarea
              id="course-instructions"
              rows={14}
              value={instructions}
              onChange={(e) => setInstructions(e.target.value.slice(0, MAX_INSTRUCTIONS_CHARS))}
              className="input-field resize-none font-mono text-xs"
              placeholder="Beskriv fagets innhold, mål og pedagogiske tilnærming..."
              aria-describedby="chars-left"
            />
            <p
              id="chars-left"
              className={clsx(
                'mt-1.5 text-right text-xs',
                charsLeft < 200 ? 'text-orange-600' : 'text-gray-400'
              )}
            >
              {charsLeft} tegn igjen
            </p>
          </>
        )}
      </div>

      <button
        onClick={() => saveMutation.mutate(instructions)}
        disabled={saveMutation.isPending || instructionsQuery.isLoading}
        className="btn-primary"
      >
        {saveMutation.isPending && <Spinner size="sm" />}
        Lagre instruksjoner
      </button>
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function TeacherCoursePage() {
  const { courseId } = useParams<{ courseId: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<Tab>('students')

  const coursesQuery = useQuery({
    queryKey: ['responsible-courses'],
    queryFn: getResponsibleCourses,
  })

  const course = coursesQuery.data?.find((c) => c.id === courseId)

  if (!courseId) return null

  const tabs: { id: Tab; label: string }[] = [
    { id: 'students', label: 'Studenter' },
    { id: 'materials', label: 'Læringsmateriell' },
    { id: 'instructions', label: 'Instruksjoner' },
  ]

  return (
    <Layout>
      <div className="flex-1 min-h-0 overflow-y-auto">
      <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/')}
            className="mb-4 flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 rounded transition-colors"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Tilbake til dashboard
          </button>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {course ? course.name : 'Emneadministrasjon'}
              </h1>
              {course && (
                <p className="mt-1 font-mono text-sm text-gray-500">{course.code}</p>
              )}
            </div>
            <button
              onClick={() => navigate(`/chat/${courseId}`)}
              className="flex shrink-0 items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 hover:border-indigo-400 hover:text-indigo-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 transition-colors"
            >
              <Eye className="h-4 w-4" aria-hidden="true" />
              Se som student
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div
          role="tablist"
          aria-label="Emneadministrasjon"
          className="mb-6 flex border-b border-gray-200"
        >
          {tabs.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              aria-controls={`${tab.id}-panel`}
              id={`${tab.id}-tab`}
              onClick={() => setActiveTab(tab.id)}
              className={`tab-button mr-1 ${activeTab === tab.id ? 'tab-button-active' : 'tab-button-inactive'}`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab panels */}
        <div
          role="tabpanel"
          id="students-panel"
          aria-labelledby="students-tab"
          hidden={activeTab !== 'students'}
        >
          {activeTab === 'students' && <StudentsTab courseId={courseId} />}
        </div>
        <div
          role="tabpanel"
          id="materials-panel"
          aria-labelledby="materials-tab"
          hidden={activeTab !== 'materials'}
        >
          {activeTab === 'materials' && <MaterialsTab courseId={courseId} />}
        </div>
        <div
          role="tabpanel"
          id="instructions-panel"
          aria-labelledby="instructions-tab"
          hidden={activeTab !== 'instructions'}
        >
          {activeTab === 'instructions' && <InstructionsTab courseId={courseId} />}
        </div>
      </div>
      </div>
    </Layout>
  )
}
