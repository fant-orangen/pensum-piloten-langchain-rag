import { useRef, useState, type ChangeEvent, type DragEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { FileText, RefreshCw, Trash2, Upload } from 'lucide-react'
import toast from 'react-hot-toast'
import { ConfirmDialog } from '../../components/ConfirmDialog'
import { DocumentStatusBadge, RebuildStatusBadge } from '../../components/Badge'
import { Spinner } from '../../components/Spinner'
import {
  confirmIngestion,
  deleteAllDocuments,
  deleteDocument,
  getCourseDocuments,
  getDocumentsStatus,
  uploadDocuments,
  uploadZip,
} from '../../api/courses'
import type { CourseDocumentRead } from '../../types'
import { formatCourseDate } from './format'
import { courseQueryKeys, invalidateAllCourseQueries } from './queryKeys'

interface MaterialsTabProps {
  courseId: string
}

export function MaterialsTab({ courseId }: MaterialsTabProps) {
  const queryClient = useQueryClient()
  const [selectedDocIds, setSelectedDocIds] = useState<Set<string>>(new Set())
  const [isDragging, setIsDragging] = useState(false)
  const [confirmDeleteAll, setConfirmDeleteAll] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const zipInputRef = useRef<HTMLInputElement>(null)

  const documentsQuery = useQuery({
    queryKey: courseQueryKeys.documents(courseId),
    queryFn: () => getCourseDocuments(courseId),
  })

  const statusQuery = useQuery({
    queryKey: courseQueryKeys.documentStatus(courseId),
    queryFn: () => getDocumentsStatus(courseId),
    refetchInterval: (query) => {
      const status = query.state.data?.rebuild_status
      return status === 'building' || status === 'queued' ? 3000 : false
    },
  })

  const uploadMutation = useMutation({
    mutationFn: (files: File[]) => uploadDocuments(courseId, files),
    onSuccess: (docs) => {
      invalidateAllCourseQueries(queryClient, courseId)
      toast.success(`${docs.length} fil(er) lastet opp.`)
    },
    onError: () => toast.error('Filopplasting feilet.'),
  })

  const uploadZipMutation = useMutation({
    mutationFn: (file: File) => uploadZip(courseId, file),
    onSuccess: (result) => {
      invalidateAllCourseQueries(queryClient, courseId)
      toast.success(
        `ZIP-import: ${result.staged_count} klargjort${result.skipped_count > 0 ? `, ${result.skipped_count} hoppet over` : ''}.`
      )
    },
    onError: () => toast.error('ZIP-opplasting feilet.'),
  })

  const deleteDocMutation = useMutation({
    mutationFn: (docId: string) => deleteDocument(courseId, docId),
    onSuccess: () => {
      invalidateAllCourseQueries(queryClient, courseId)
      toast.success('Dokument fjernet.')
    },
    onError: () => toast.error('Klarte ikke fjerne dokument.'),
  })

  const deleteSelectedMutation = useMutation({
    mutationFn: async (docIds: string[]) => {
      await Promise.all(docIds.map((docId) => deleteDocument(courseId, docId)))
    },
    onSuccess: () => {
      invalidateAllCourseQueries(queryClient, courseId)
      setSelectedDocIds(new Set())
      toast.success('Valgte dokumenter fjernet.')
    },
    onError: () => toast.error('Klarte ikke fjerne valgte dokumenter.'),
  })

  const deleteAllMutation = useMutation({
    mutationFn: () => deleteAllDocuments(courseId),
    onSuccess: (result) => {
      invalidateAllCourseQueries(queryClient, courseId)
      setSelectedDocIds(new Set())
      toast.success(`${result.removed} dokument(er) fjernet.`)
    },
    onError: () => toast.error('Klarte ikke fjerne alle dokumenter.'),
  })

  const confirmMutation = useMutation({
    mutationFn: () => confirmIngestion(courseId),
    onSuccess: () => {
      invalidateAllCourseQueries(queryClient, courseId)
      toast.success('Innlesing startet!')
    },
    onError: () => toast.error('Klarte ikke starte innlesing.'),
  })

  function handleFileDrop(e: DragEvent) {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files)
    const zipFiles = files.filter((f) => f.name.endsWith('.zip'))
    const regularFiles = files.filter((f) => !f.name.endsWith('.zip'))
    if (zipFiles.length > 0) uploadZipMutation.mutate(zipFiles[0])
    if (regularFiles.length > 0) uploadMutation.mutate(regularFiles)
  }

  function handleFileInput(e: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    if (files.length > 0) uploadMutation.mutate(files)
    e.target.value = ''
  }

  function handleZipInput(e: ChangeEvent<HTMLInputElement>) {
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

  const documents = documentsQuery.data ?? []
  const isUploading = uploadMutation.isPending || uploadZipMutation.isPending
  const status = statusQuery.data
  const isDeletingSelected = deleteSelectedMutation.isPending

  return (
    <div className="space-y-6">
      <section aria-labelledby="ingestion-status-heading" className="rounded-lg border border-gray-200 p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 id="ingestion-status-heading" className="text-sm font-semibold text-gray-900">
            Innlesingstatus
          </h2>
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: courseQueryKeys.documentStatus(courseId) })}
            className="flex items-center gap-1.5 rounded text-xs text-gray-500 transition-colors hover:text-indigo-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"
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
            disabled={confirmMutation.isPending || !status || (status.pending_additions === 0 && status.pending_removals === 0)}
            className="btn-primary"
          >
            {confirmMutation.isPending && <Spinner size="sm" />}
            Start innlesing
          </button>
        </div>
      </section>

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
              {uploadMutation.isPending ? <Spinner size="sm" /> : <FileText className="h-3.5 w-3.5" aria-hidden="true" />}
              Velg filer
            </button>
            <button
              onClick={() => zipInputRef.current?.click()}
              disabled={isUploading}
              className="btn-secondary text-xs"
            >
              {uploadZipMutation.isPending ? <Spinner size="sm" /> : <Upload className="h-3.5 w-3.5" aria-hidden="true" />}
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
                onClick={() => deleteSelectedMutation.mutate(Array.from(selectedDocIds))}
                disabled={isDeletingSelected}
                className="btn-danger py-1.5 text-xs"
              >
                {isDeletingSelected ? <Spinner size="sm" /> : <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />}
                Slett valgte ({selectedDocIds.size})
              </button>
            )}
            {documents.length > 0 && (
              <button
                onClick={() => setConfirmDeleteAll(true)}
                className="btn-secondary py-1.5 text-xs"
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
                    <td className="px-4 py-3 font-mono text-xs text-gray-900">{doc.original_filename}</td>
                    <td className="px-4 py-3">
                      <DocumentStatusBadge status={doc.status} />
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">{formatCourseDate(doc.created_at)}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => deleteDocMutation.mutate(doc.id)}
                        disabled={deleteDocMutation.isPending}
                        className="rounded text-xs text-red-500 hover:text-red-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-500"
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
