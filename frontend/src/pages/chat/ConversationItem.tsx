import { useState, type KeyboardEvent } from 'react'
import clsx from 'clsx'
import { MessageSquare, Pencil, Trash2 } from 'lucide-react'
import { ConfirmDialog } from '../../components/ConfirmDialog'
import type { ConversationRead } from '../../types'
import { formatConversationDate } from './format'

interface ConversationItemProps {
  conversation: ConversationRead
  isActive: boolean
  onSelect: () => void
  onDelete: () => void
  onRename: (title: string) => void
}

/** Single sidebar conversation row with inline rename and delete controls. */
export function ConversationItem({ conversation, isActive, onSelect, onDelete, onRename }: ConversationItemProps) {
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState('')

  function startEditing() {
    setEditValue(conversation.title ?? `Samtale ${formatConversationDate(conversation.created_at)}`)
    setIsEditing(true)
  }

  function commitRename() {
    const trimmed = editValue.trim()
    if (trimmed) onRename(trimmed)
    setIsEditing(false)
  }

  function handleEditKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') commitRename()
    if (e.key === 'Escape') setIsEditing(false)
  }

  return (
    <>
      <div
        className={clsx(
          'group relative flex items-center rounded-lg px-3 py-2.5 transition-colors',
          isActive ? 'bg-indigo-50 text-indigo-900' : 'hover:bg-gray-100 text-gray-700'
        )}
      >
        {isEditing ? (
          <input
            autoFocus
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleEditKeyDown}
            onBlur={commitRename}
            className="flex-1 rounded border border-indigo-300 bg-white px-2 py-0.5 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-indigo-400"
          />
        ) : (
          <button
            onClick={onSelect}
            className="flex flex-1 items-start gap-2 text-left focus-visible:outline-none"
            aria-current={isActive ? 'page' : undefined}
          >
            <MessageSquare className="mt-0.5 h-4 w-4 shrink-0 text-gray-400" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">
                {conversation.title ?? `Samtale ${formatConversationDate(conversation.created_at)}`}
              </p>
              <p className="text-xs text-gray-400">
                {formatConversationDate(conversation.updated_at)}
              </p>
            </div>
          </button>
        )}

        {!isEditing && (
          <div className="ml-1 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
            <button
              onClick={(e) => { e.stopPropagation(); startEditing() }}
              className="rounded p-1 text-gray-300 hover:text-indigo-500 focus-visible:opacity-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-500"
              aria-label="Gi nytt navn"
            >
              <Pencil className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => setConfirmDelete(true)}
              className="rounded p-1 text-gray-300 hover:text-red-500 focus-visible:opacity-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-red-500"
              aria-label="Slett samtale"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        )}
      </div>

      <ConfirmDialog
        open={confirmDelete}
        title="Slett samtale"
        description="Er du sikker på at du vil slette denne samtalen? Denne handlingen kan ikke angres."
        confirmLabel="Slett"
        variant="danger"
        onConfirm={() => { setConfirmDelete(false); onDelete() }}
        onCancel={() => setConfirmDelete(false)}
      />
    </>
  )
}
