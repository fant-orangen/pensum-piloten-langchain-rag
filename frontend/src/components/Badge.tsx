import clsx from 'clsx'
import type { DocumentStatus, GlobalRole, RebuildStatus } from '../types'

type BadgeVariant = 'green' | 'yellow' | 'red' | 'blue' | 'gray' | 'indigo'

interface BadgeProps {
  variant: BadgeVariant
  children: React.ReactNode
  className?: string
}

/** Small status label used to keep role and workflow states visually consistent. */
export function Badge({ variant, children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        variant === 'green' && 'bg-green-100 text-green-800',
        variant === 'yellow' && 'bg-yellow-100 text-yellow-800',
        variant === 'red' && 'bg-red-100 text-red-800',
        variant === 'blue' && 'bg-blue-100 text-blue-800',
        variant === 'gray' && 'bg-gray-100 text-gray-800',
        variant === 'indigo' && 'bg-indigo-100 text-indigo-800',
        className
      )}
    >
      {children}
    </span>
  )
}

/** Render the course-document staging state in teacher material lists. */
export function DocumentStatusBadge({ status }: { status: DocumentStatus }) {
  const map: Record<DocumentStatus, { variant: BadgeVariant; label: string }> = {
    active: { variant: 'green', label: 'Aktiv' },
    pending_add: { variant: 'yellow', label: 'Venter på innlesing' },
    pending_remove: { variant: 'red', label: 'Venter på sletting' },
  }
  const { variant, label } = map[status]
  return <Badge variant={variant}>{label}</Badge>
}

/** Render the material-index rebuild state returned by the backend. */
export function RebuildStatusBadge({ status }: { status: RebuildStatus }) {
  const map: Record<RebuildStatus, { variant: BadgeVariant; label: string }> = {
    idle: { variant: 'gray', label: 'Inaktiv' },
    queued: { variant: 'yellow', label: 'I kø' },
    building: { variant: 'blue', label: 'Bygger' },
    failed: { variant: 'red', label: 'Feilet' },
  }
  const { variant, label } = map[status]
  return <Badge variant={variant}>{label}</Badge>
}

/** Render a user's global authorization role. */
export function RoleBadge({ role }: { role: GlobalRole }) {
  const map: Record<GlobalRole, { variant: BadgeVariant; label: string }> = {
    student: { variant: 'gray', label: 'Student' },
    teacher: { variant: 'indigo', label: 'Lærer' },
    admin: { variant: 'red', label: 'Admin' },
  }
  const { variant, label } = map[role]
  return <Badge variant={variant}>{label}</Badge>
}
