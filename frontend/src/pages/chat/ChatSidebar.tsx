import clsx from 'clsx'
import { ChevronLeft, ChevronRight, Plus } from 'lucide-react'
import { Spinner } from '../../components/Spinner'
import type { ConversationRead, SystemPromptMode } from '../../types'
import { ConversationItem } from './ConversationItem'
import { PROMPT_MODE_OPTIONS } from './promptModes'

interface ChatSidebarProps {
  courseCode: string | undefined
  courseId: string | undefined
  conversations: ConversationRead[]
  totalConversations: number | undefined
  isLoadingConversations: boolean
  selectedConversationId: string | null
  promptMode: SystemPromptMode
  sidebarCollapsed: boolean
  isCreatingConversation: boolean
  onExpandSidebar: () => void
  onCollapseSidebar: () => void
  onPromptModeChange: (mode: SystemPromptMode) => void
  onCreateConversation: () => void
  onSelectConversation: (conversationId: string) => void
  onDeleteConversation: (conversationId: string) => void
  onRenameConversation: (conversationId: string, title: string) => void
}

/**
 * Conversation navigation and tutor-mode selector for the chat workspace.
 *
 * Mutations are delegated to the parent so this component only renders sidebar
 * state and forwards user intents.
 */
export function ChatSidebar({
  courseCode,
  courseId,
  conversations,
  totalConversations,
  isLoadingConversations,
  selectedConversationId,
  promptMode,
  sidebarCollapsed,
  isCreatingConversation,
  onExpandSidebar,
  onCollapseSidebar,
  onPromptModeChange,
  onCreateConversation,
  onSelectConversation,
  onDeleteConversation,
  onRenameConversation,
}: ChatSidebarProps) {
  return (
    <aside
      aria-label="Samtaler"
      className={clsx(
        'flex flex-col border-r border-gray-200 bg-white transition-all duration-200',
        sidebarCollapsed ? 'w-12' : 'w-72'
      )}
    >
      {sidebarCollapsed ? (
        <div className="flex flex-1 flex-col items-center py-4 gap-3">
          <button
            onClick={onExpandSidebar}
            className="rounded-md p-2 text-gray-500 hover:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"
            aria-label="Utvid sidepanel"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
            <h2 className="text-sm font-semibold text-gray-700">
              {courseCode ?? 'Samtaler'}
            </h2>
            <button
              onClick={onCollapseSidebar}
              className="rounded-md p-1 text-gray-400 hover:text-gray-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"
              aria-label="Skjul sidepanel"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
          </div>

          <div className="border-b border-gray-100 px-4 py-3">
            <p className="mb-2 text-xs font-medium text-gray-500 uppercase tracking-wide">Læringsmodus</p>
            <fieldset>
              <legend className="sr-only">Velg læringsmodus</legend>
              <div className="space-y-1">
                {PROMPT_MODE_OPTIONS.map((opt) => (
                  <label
                    key={opt.value}
                    className={clsx(
                      'flex cursor-pointer items-center gap-2.5 rounded-md px-2 py-1.5 text-sm transition-colors',
                      promptMode === opt.value
                        ? 'bg-indigo-50 text-indigo-900'
                        : 'text-gray-600 hover:bg-gray-50'
                    )}
                  >
                    <input
                      type="radio"
                      name="prompt-mode"
                      value={opt.value}
                      checked={promptMode === opt.value}
                      onChange={() => onPromptModeChange(opt.value)}
                      className="h-3.5 w-3.5 accent-indigo-600"
                    />
                    <div>
                      <span className="font-medium">{opt.label}</span>
                      <span className="ml-1 text-xs text-gray-400">{opt.description}</span>
                    </div>
                  </label>
                ))}
              </div>
            </fieldset>
          </div>

          <div className="px-4 py-3">
            <button
              onClick={onCreateConversation}
              disabled={!courseId || isCreatingConversation}
              className="btn-primary w-full justify-center text-xs py-2"
              title={!courseId ? 'Velg et emne for å starte ny samtale' : undefined}
            >
              {isCreatingConversation ? (
                <Spinner size="sm" />
              ) : (
                <Plus className="h-3.5 w-3.5" aria-hidden="true" />
              )}
              Ny samtale
            </button>
          </div>

          <nav aria-label="Samtalliste" className="flex-1 min-h-0 overflow-y-auto px-2 pb-4">
            {isLoadingConversations && (
              <div className="flex justify-center py-6">
                <Spinner size="sm" className="text-indigo-600" />
              </div>
            )}
            {conversations.length === 0 && !isLoadingConversations && (
              <p className="px-3 py-4 text-xs text-gray-400">
                {courseId ? 'Ingen samtaler ennå. Start en ny samtale!' : 'Ingen samtaler.'}
              </p>
            )}
            <ul>
              {conversations.map((conv) => (
                <li key={conv.id}>
                  <ConversationItem
                    conversation={conv}
                    isActive={selectedConversationId === conv.id}
                    onSelect={() => onSelectConversation(conv.id)}
                    onDelete={() => onDeleteConversation(conv.id)}
                    onRename={(title) => onRenameConversation(conv.id, title)}
                  />
                </li>
              ))}
            </ul>
            {totalConversations !== undefined && (
              <p className="mt-2 px-3 text-xs text-gray-400">
                {totalConversations} samtale{totalConversations !== 1 ? 'r' : ''} totalt
              </p>
            )}
          </nav>
        </>
      )}
    </aside>
  )
}
