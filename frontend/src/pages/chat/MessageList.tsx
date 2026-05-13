import type { RefObject, UIEvent } from 'react'
import { MessageSquare } from 'lucide-react'
import { Spinner } from '../../components/Spinner'
import type { MessageRead } from '../../types'
import { MessageBubble } from './MessageBubble'

interface MessageListProps {
  courseId: string | undefined
  selectedConversationId: string | null
  messages: MessageRead[]
  isLoadingMessages: boolean
  isLoadingMoreMessages: boolean
  hasMoreMessages: boolean
  isSendingMessage: boolean
  activeSourceMessageId: string | null
  messagesEndRef: RefObject<HTMLDivElement>
  onLoadMoreMessages: () => void
  onShowSources: (messageId: string) => void
}

/** Scrollable message viewport with loading/empty states and source controls. */
export function MessageList({
  courseId,
  selectedConversationId,
  messages,
  isLoadingMessages,
  isLoadingMoreMessages,
  hasMoreMessages,
  isSendingMessage,
  activeSourceMessageId,
  messagesEndRef,
  onLoadMoreMessages,
  onShowSources,
}: MessageListProps) {
  function handleScroll(e: UIEvent<HTMLDivElement>) {
    if (e.currentTarget.scrollTop <= 80 && hasMoreMessages && !isLoadingMoreMessages) {
      onLoadMoreMessages()
    }
  }

  return (
    <div className="flex-1 min-h-0 overflow-y-auto px-6 py-6" onScroll={handleScroll}>
      {!selectedConversationId ? (
        <div className="flex h-full flex-col items-center justify-center text-center">
          <MessageSquare className="mb-4 h-12 w-12 text-gray-200" aria-hidden="true" />
          <h2 className="text-lg font-semibold text-gray-700">Ingen samtale valgt</h2>
          <p className="mt-2 max-w-sm text-sm text-gray-400">
            {courseId
              ? 'Velg en eksisterende samtale fra sidepanelet, eller start en ny samtale.'
              : 'Velg et emne og start en samtale for å begynne.'}
          </p>
        </div>
      ) : isLoadingMessages ? (
        <div className="flex h-full items-center justify-center">
          <Spinner size="lg" className="text-indigo-600" />
        </div>
      ) : (
        <div className="mx-auto max-w-3xl space-y-4">
          {isLoadingMoreMessages && (
            <div className="flex justify-center py-2">
              <Spinner size="sm" className="text-indigo-600" />
            </div>
          )}
          {messages.length === 0 && (
            <div className="py-8 text-center">
              <p className="text-sm text-gray-400">
                Ingen meldinger ennå. Still et spørsmål for å komme i gang!
              </p>
            </div>
          )}
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              onShowSources={onShowSources}
              activeSourceMessageId={activeSourceMessageId}
            />
          ))}
          {isSendingMessage && (
            <div className="flex justify-start">
              <div className="rounded-2xl rounded-tl-sm bg-white px-4 py-3 shadow-sm ring-1 ring-gray-200">
                <div className="flex items-center gap-2 text-gray-400">
                  <Spinner size="sm" className="text-indigo-600" />
                  <span className="text-sm">Tenker...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} aria-hidden="true" />
        </div>
      )}
    </div>
  )
}
