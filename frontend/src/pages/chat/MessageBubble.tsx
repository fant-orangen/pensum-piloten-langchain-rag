import clsx from 'clsx'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { MessageRead } from '../../types'
import { formatConversationDate } from './format'
import { messageMarkdownComponents } from './markdown'

interface MessageBubbleProps {
  message: MessageRead
  onShowSources: (messageId: string) => void
  activeSourceMessageId: string | null
}

/** Render one chat message with markdown formatting and optional source toggle. */
export function MessageBubble({ message, onShowSources, activeSourceMessageId }: MessageBubbleProps) {
  const isHuman = message.role === 'human'
  const isSourcesActive = activeSourceMessageId === message.id

  return (
    <article
      className={clsx(
        'flex',
        isHuman ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={clsx(
          'max-w-[80%] rounded-2xl px-4 py-3',
          isHuman
            ? 'rounded-tr-sm bg-indigo-600 text-white'
            : 'rounded-tl-sm bg-white text-gray-900 shadow-sm ring-1 ring-gray-200'
        )}
      >
        <div className="text-sm leading-relaxed">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={messageMarkdownComponents(isHuman)}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        {!isHuman && (
          <div className="mt-2 flex items-center justify-between gap-3">
            <time
              dateTime={message.created_at}
              className="text-xs text-gray-400"
            >
              {formatConversationDate(message.created_at)}
            </time>
            <button
              onClick={() => onShowSources(message.id)}
              className={clsx(
                'text-xs underline-offset-2 transition-colors hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 rounded',
                isSourcesActive ? 'text-indigo-600 font-medium' : 'text-gray-400 hover:text-indigo-600'
              )}
              aria-pressed={isSourcesActive}
            >
              Vis kilder
            </button>
          </div>
        )}
        {isHuman && (
          <time dateTime={message.created_at} className="mt-1 block text-right text-xs text-indigo-200">
            {formatConversationDate(message.created_at)}
          </time>
        )}
      </div>
    </article>
  )
}
