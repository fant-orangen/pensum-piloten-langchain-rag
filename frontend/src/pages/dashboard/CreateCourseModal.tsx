import { useState, type FormEvent } from 'react'
import { X } from 'lucide-react'
import { Spinner } from '../../components/Spinner'
import type { CourseCreate } from '../../types'
import { deriveCourseCode } from './courseCode'

interface CreateCourseModalProps {
  isSubmitting: boolean
  errorMessage: string
  onClose: () => void
  onSubmit: (payload: CourseCreate) => void
}

export function CreateCourseModal({
  isSubmitting,
  errorMessage,
  onClose,
  onSubmit,
}: CreateCourseModalProps) {
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [codeManuallyEdited, setCodeManuallyEdited] = useState(false)
  const [description, setDescription] = useState('')
  const [formError, setFormError] = useState('')

  function handleNameChange(value: string) {
    setName(value)
    if (!codeManuallyEdited) {
      const derived = deriveCourseCode(value)
      setCode(derived)
    }
  }

  function handleCodeChange(value: string) {
    setCode(value)
    setCodeManuallyEdited(true)
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setFormError('')
    if (!name.trim()) { setFormError('Emnenavn er påkrevd.'); return }
    if (!code.trim()) { setFormError('Emnekode er påkrevd.'); return }
    onSubmit({
      name: name.trim(),
      code: code.trim(),
      description: description.trim() || undefined,
    })
  }

  const displayedError = formError || errorMessage

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

          {displayedError && (
            <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {displayedError}
            </p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">
              Avbryt
            </button>
            <button type="submit" disabled={isSubmitting} className="btn-primary">
              {isSubmitting && <Spinner size="sm" />}
              Opprett emne
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
