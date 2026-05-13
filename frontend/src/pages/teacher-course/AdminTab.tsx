import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { ConfirmDialog } from '../../components/ConfirmDialog'
import { Spinner } from '../../components/Spinner'

interface AdminTabProps {
  courseCode: string
  isDeleting: boolean
  onDelete: () => void
}

/** Destructive course administration controls for course creators and admins. */
export function AdminTab({ courseCode, isDeleting, onDelete }: AdminTabProps) {
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false)

  return (
    <section aria-labelledby="delete-course-heading" className="space-y-4">
      <div>
        <h2 id="delete-course-heading" className="text-base font-semibold text-gray-900">
          Slett emne
        </h2>
        <p className="mt-1 max-w-2xl text-sm text-gray-500">
          Dette sletter emnet, samtaler, påmeldinger og tilknyttet kildemateriale permanent.
        </p>
      </div>
      <button
        onClick={() => setConfirmDeleteOpen(true)}
        disabled={isDeleting}
        className="btn-danger"
      >
        {isDeleting ? (
          <Spinner size="sm" />
        ) : (
          <Trash2 className="h-4 w-4" aria-hidden="true" />
        )}
        Slett emne
      </button>
      <ConfirmDialog
        open={confirmDeleteOpen}
        title="Slett emne"
        description={`Er du sikker på at du vil slette ${courseCode}? Dette kan ikke angres.`}
        confirmLabel="Slett emne"
        variant="danger"
        onCancel={() => setConfirmDeleteOpen(false)}
        onConfirm={() => {
          setConfirmDeleteOpen(false)
          onDelete()
        }}
      />
    </section>
  )
}
