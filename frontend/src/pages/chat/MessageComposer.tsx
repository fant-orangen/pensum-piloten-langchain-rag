import type { KeyboardEvent, RefObject } from 'react'
import { Send } from 'lucide-react'

interface MessageComposerProps {
  inputValue: string
  isSendingMessage: boolean
  textareaRef: RefObject<HTMLTextAreaElement>
  onInputChange: (value: string) => void
  onSend: () => void
}

/** Textarea composer that submits on Enter and allows Shift+Enter newlines. */
export function MessageComposer({
  inputValue,
  isSendingMessage,
  textareaRef,
  onInputChange,
  onSend,
}: MessageComposerProps) {
  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  return (
    <div className="border-t border-gray-200 bg-white px-6 py-4">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-3 rounded-xl border border-gray-300 bg-white px-4 py-3 shadow-sm focus-within:border-indigo-400 focus-within:ring-1 focus-within:ring-indigo-400 transition-all">
          <label htmlFor="chat-input" className="sr-only">
            Skriv en melding
          </label>
          <textarea
            id="chat-input"
            ref={textareaRef}
            rows={1}
            value={inputValue}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSendingMessage}
            placeholder="Skriv en melding... (Enter for å sende, Shift+Enter for ny linje)"
            className="flex-1 resize-none bg-transparent text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none disabled:opacity-50"
            style={{ maxHeight: '160px', overflowY: 'auto' }}
            onInput={(e) => {
              const el = e.currentTarget
              el.style.height = 'auto'
              el.style.height = `${el.scrollHeight}px`
            }}
          />
          <button
            onClick={onSend}
            disabled={!inputValue.trim() || isSendingMessage}
            className="shrink-0 rounded-lg bg-indigo-600 p-2 text-white hover:bg-indigo-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            aria-label="Send melding"
          >
            <Send className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  )
}
