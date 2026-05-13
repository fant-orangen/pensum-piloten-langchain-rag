import { useQuery } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { Spinner } from '../../components/Spinner'
import { getMessageSources } from '../../api/conversations'
import type { MessageSourceRead } from '../../types'
import { chatQueryKeys } from './queryKeys'

interface SourcesPanelProps {
  conversationId: string
  messageId: string
  onClose: () => void
}

/** Side panel that resolves and displays vectorstore chunks cited by an AI message. */
export function SourcesPanel({ conversationId, messageId, onClose }: SourcesPanelProps) {
  const { data: sources, isLoading, isError } = useQuery<MessageSourceRead[]>({
    queryKey: chatQueryKeys.messageSources(conversationId, messageId),
    queryFn: () => getMessageSources(conversationId, messageId),
  })

  return (
    <aside
      aria-label="Kildehenvisninger"
      className="flex w-80 shrink-0 flex-col border-l border-gray-200 bg-white"
    >
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-gray-900">Kilder</h2>
        <button
          onClick={onClose}
          className="rounded-md p-1 text-gray-400 hover:text-gray-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"
          aria-label="Lukk kildeliste"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto p-4">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Spinner size="md" className="text-indigo-600" />
          </div>
        )}
        {isError && (
          <p className="text-sm text-red-600">Klarte ikke laste kilder.</p>
        )}
        {sources && sources.length === 0 && (
          <p className="text-sm text-gray-500">Ingen kilder tilgjengelig for denne meldingen.</p>
        )}
        {sources && sources.length > 0 && (
          <ol className="space-y-4">
            {sources.map((source, idx) => (
              <li key={source.chunk_id} className="rounded-lg border border-gray-200 p-3">
                <div className="mb-2 flex items-start justify-between gap-2">
                  <span className="text-xs font-semibold text-indigo-600">Kilde {idx + 1}</span>
                  <span className="text-xs text-gray-400">Side {source.page}</span>
                </div>
                <p className="mb-1 text-xs font-medium text-gray-700 truncate" title={source.document}>
                  {source.document}
                </p>
                <p className="text-xs leading-relaxed text-gray-600 line-clamp-4">{source.content}</p>
              </li>
            ))}
          </ol>
        )}
      </div>
    </aside>
  )
}
