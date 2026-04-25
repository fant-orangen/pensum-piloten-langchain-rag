import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  MessageSquare,
  Pencil,
  Plus,
  Send,
  Trash2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { nb } from 'date-fns/locale'
import clsx from 'clsx'
import ReactMarkdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useAuth } from '../contexts/AuthContext'
import { Layout } from '../components/Layout'
import { Spinner } from '../components/Spinner'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { INSTRUCTION_SETS, type InstructionSetId } from '../content/studyInstructions/index.ts'
import {
  getConversations,
  createConversation,
  deleteConversation,
  getMessages,
  renameConversation,
  sendMessage,
} from '../api/conversations'
import { advanceStudyCourse, getCourse } from '../api/courses'
import type { ConversationRead, MessageRead } from '../types'
import {
  isStudyParticipantEmail,
  type StudyCourseCode,
  studyCourseSequenceForEmail,
} from '../study/courseSequence'

interface InstructionProgress {
  currentIndex: number
  completedIds: InstructionSetId[]
}

const DEFAULT_INSTRUCTION_ORDER: InstructionSetId[] = ['set-1', 'set-2', 'set-3', 'set-4']

function instructionOrderForEmail(email: string | undefined): InstructionSetId[] {
  const match = email?.match(/g[123]u(\d{1,2})@/i)
  const userNumber = match ? Number.parseInt(match[1], 10) : Number.NaN

  if (userNumber >= 1 && userNumber <= 4) {
    return ['set-1', 'set-2', 'set-3', 'set-4']
  }
  if (userNumber >= 5 && userNumber <= 8) {
    return ['set-2', 'set-3', 'set-1', 'set-4']
  }
  if (userNumber >= 9 && userNumber <= 12) {
    return ['set-3', 'set-1', 'set-2', 'set-4']
  }

  return DEFAULT_INSTRUCTION_ORDER
}

function instructionProgressStorageKey(email: string | undefined): string | null {
  const normalizedEmail = email?.trim().toLowerCase()
  return normalizedEmail ? `study-instructions:${normalizedEmail}` : null
}

function loadInstructionProgress(email: string | undefined): InstructionProgress {
  const storageKey = instructionProgressStorageKey(email)
  if (!storageKey) {
    return { currentIndex: 0, completedIds: [] }
  }

  try {
    const raw = localStorage.getItem(storageKey)
    if (!raw) {
      return { currentIndex: 0, completedIds: [] }
    }

    const parsed = JSON.parse(raw) as Partial<InstructionProgress>
    const currentIndex = Number.isInteger(parsed.currentIndex) ? Number(parsed.currentIndex) : 0
    const completedIds = Array.isArray(parsed.completedIds)
      ? parsed.completedIds.filter(
          (value): value is InstructionSetId => value === 'set-1' || value === 'set-2' || value === 'set-3'
        )
      : []

    return {
      currentIndex: Math.max(0, Math.min(currentIndex, DEFAULT_INSTRUCTION_ORDER.length - 1)),
      completedIds,
    }
  } catch {
    return { currentIndex: 0, completedIds: [] }
  }
}

function formatConversationDate(dateStr: string): string {
  try {
    return format(new Date(dateStr), 'd. MMM yyyy', { locale: nb })
  } catch {
    return dateStr
  }
}

function messageMarkdownComponents(isHuman: boolean): Components {
  const textClassName = isHuman ? 'text-white' : 'text-gray-900'
  const mutedTextClassName = isHuman ? 'text-indigo-100' : 'text-gray-700'
  const linkClassName = isHuman ? 'text-white underline underline-offset-2' : 'text-indigo-700 underline underline-offset-2'
  const inlineCodeClassName = isHuman
    ? 'rounded bg-indigo-500/70 px-1 py-0.5 font-mono text-[0.9em] text-white'
    : 'rounded bg-gray-100 px-1 py-0.5 font-mono text-[0.9em] text-gray-900'

  return {
    p: ({ ...props }) => <p className={clsx('mb-3 leading-6 last:mb-0', textClassName)} {...props} />,
    ul: ({ ...props }) => (
      <ul className={clsx('mb-3 list-disc space-y-1 pl-5 last:mb-0', mutedTextClassName)} {...props} />
    ),
    ol: ({ ...props }) => (
      <ol className={clsx('mb-3 list-decimal space-y-1 pl-5 last:mb-0', mutedTextClassName)} {...props} />
    ),
    li: ({ ...props }) => <li className="leading-6" {...props} />,
    blockquote: ({ ...props }) => (
      <blockquote
        className={clsx(
          'mb-3 border-l-4 pl-4 italic last:mb-0',
          isHuman ? 'border-indigo-200 text-indigo-100' : 'border-gray-300 text-gray-600'
        )}
        {...props}
      />
    ),
    a: ({ ...props }) => (
      <a
        className={linkClassName}
        target="_blank"
        rel="noreferrer"
        {...props}
      />
    ),
    code({ children, className, ...props }) {
      const match = /language-(\w+)/.exec(className || '')
      const codeContent = String(children).replace(/\n$/, '')

      if (match) {
        return (
          <SyntaxHighlighter
            // `PreTag="div"` avoids nested `<pre>` tags from react-markdown.
            PreTag="div"
            language={match[1]}
            style={isHuman ? oneDark : oneLight}
            customStyle={{
              margin: '0 0 0.75rem 0',
              borderRadius: '0.75rem',
              fontSize: '0.85rem',
              padding: '1rem',
            }}
          >
            {codeContent}
          </SyntaxHighlighter>
        )
      }

      return (
        <code className={inlineCodeClassName} {...props}>
          {children}
        </code>
      )
    },
    pre: ({ ...props }) => <>{props.children}</>,
    strong: ({ ...props }) => <strong className={clsx('font-semibold', textClassName)} {...props} />,
  }
}

interface MessageBubbleProps {
  message: MessageRead
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isHuman = message.role === 'human'

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
          <div className="mt-2">
            <time dateTime={message.created_at} className="text-xs text-gray-400">
              {formatConversationDate(message.created_at)}
            </time>
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

interface ConversationItemProps {
  conversation: ConversationRead
  isActive: boolean
  onSelect: () => void
  onDelete: () => void
  onRename: (title: string) => void
}

function ConversationItem({ conversation, isActive, onSelect, onDelete, onRename }: ConversationItemProps) {
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

  function handleEditKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
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

export function ChatPage() {
  const { courseId } = useParams<{ courseId?: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const queryClient = useQueryClient()

  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null)
  const [inputValue, setInputValue] = useState('')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [instructionIndex, setInstructionIndex] = useState(0)
  const [completedInstructionIds, setCompletedInstructionIds] = useState<InstructionSetId[]>([])

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const instructionOrder = useMemo(
    () => instructionOrderForEmail(user?.email),
    [user?.email]
  )
  const currentInstructionId = instructionOrder[instructionIndex] ?? instructionOrder[0] ?? 'set-1'
  const currentInstruction = INSTRUCTION_SETS[currentInstructionId]
  const currentInstructionFinished = completedInstructionIds.includes(currentInstructionId)
  const isLastInstruction = instructionIndex >= instructionOrder.length - 1

  const courseQuery = useQuery({
    queryKey: ['course', courseId],
    queryFn: () => getCourse(courseId!),
    enabled: !!courseId,
  })

  const conversationsQuery = useQuery({
    queryKey: ['conversations', courseId],
    queryFn: () => getConversations(1, 50, courseId),
  })

  const messagesQuery = useQuery({
    queryKey: ['messages', selectedConversationId],
    queryFn: () => getMessages(selectedConversationId!, 1, 100),
    enabled: !!selectedConversationId,
  })

  const createConversationMutation = useMutation({
    mutationFn: () => createConversation(courseId!),
    onSuccess: (conv) => {
      queryClient.invalidateQueries({ queryKey: ['conversations', courseId] })
      setSelectedConversationId(conv.id)
    },
    onError: () => toast.error('Klarte ikke opprette samtale.'),
  })

  const deleteConversationMutation = useMutation({
    mutationFn: deleteConversation,
    onSuccess: (_data, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['conversations', courseId] })
      if (selectedConversationId === deletedId) {
        setSelectedConversationId(null)
      }
    },
    onError: () => toast.error('Klarte ikke slette samtale.'),
  })

  const renameConversationMutation = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) => renameConversation(id, title),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['conversations', courseId] }),
    onError: () => toast.error('Klarte ikke endre navn.'),
  })

  const sendMessageMutation = useMutation({
    mutationFn: (content: string) => sendMessage(selectedConversationId!, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages', selectedConversationId] })
      queryClient.invalidateQueries({ queryKey: ['conversations', courseId] })
    },
    onError: () => toast.error('Klarte ikke sende melding.'),
  })

  const advanceStudyCourseMutation = useMutation({
    mutationFn: advanceStudyCourse,
    onSuccess: (nextCourse) => {
      // Study enrollment swapped server-side; drop any cached lists that still
      // reference the old course before navigating to the new one.
      queryClient.invalidateQueries({ queryKey: ['my-courses'] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      navigate(`/chat/${nextCourse.id}`, { replace: true })
    },
    onError: () => toast.error('Klarte ikke bytte til neste emne. Prøv igjen.'),
  })

  const displayMessages = messagesQuery.data
    ? [...messagesQuery.data.items].reverse()
    : []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [displayMessages.length])

  useEffect(() => {
    setSelectedConversationId(null)
  }, [courseId])

  useEffect(() => {
    const progress = loadInstructionProgress(user?.email)
    // Study accounts: index is derived from the current `os_g*` course (see
    // effect below). Stale `localStorage` would desync after a DB reset and
    // leave "Next" disabled on a false "round 3".
    if (!isStudyParticipantEmail(user?.email)) {
      setInstructionIndex(progress.currentIndex)
    }
    setCompletedInstructionIds(progress.completedIds)
  }, [user?.email])

  useEffect(() => {
    if (!user?.email || !isStudyParticipantEmail(user.email)) return
    const code = courseQuery.data?.code
    if (!code) return
    const seq = studyCourseSequenceForEmail(user.email)
    if (!seq) return
    const idx = seq.indexOf(code as StudyCourseCode)
    if (idx < 0) return

    // set-4 has no course code — the user stays on their last os_g* course.
    // If they have already advanced to set-4 (stored index = last), preserve
    // that. Only trust the stored index when the course also matches the final
    // study course (guards against a stale localStorage after a DB reset).
    const finalIdx = instructionOrder.length - 1
    const isOnLastCourse = idx === instructionOrder.length - 2
    const stored = loadInstructionProgress(user.email).currentIndex
    setInstructionIndex(isOnLastCourse && stored === finalIdx ? finalIdx : idx)
  }, [user?.email, courseQuery.data?.code, instructionOrder.length])

  useEffect(() => {
    const storageKey = instructionProgressStorageKey(user?.email)
    if (!storageKey) return

    const payload: InstructionProgress = {
      currentIndex: instructionIndex,
      completedIds: completedInstructionIds,
    }
    localStorage.setItem(storageKey, JSON.stringify(payload))
  }, [completedInstructionIds, instructionIndex, user?.email])

  const handleSend = useCallback(() => {
    const content = inputValue.trim()
    if (!content || !selectedConversationId || sendMessageMutation.isPending) return
    setInputValue('')
    sendMessageMutation.mutate(content)
  }, [inputValue, selectedConversationId, sendMessageMutation])

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleFinishTest() {
    setCompletedInstructionIds((current) =>
      current.includes(currentInstructionId) ? current : [...current, currentInstructionId]
    )
  }

  function handleNextInstruction() {
    if (!currentInstructionFinished || isLastInstruction) return
    if (advanceStudyCourseMutation.isPending) return

    // Moving from the second-to-last instruction (set-3) to the final one
    // (set-4) requires no course change — just advance the local index.
    if (instructionIndex === instructionOrder.length - 2) {
      setInstructionIndex(instructionOrder.length - 1)
      return
    }

    advanceStudyCourseMutation.mutate()
  }

  const conversations = conversationsQuery.data?.items ?? []
  const selectedConversation = conversations.find((c) => c.id === selectedConversationId)

  return (
    <Layout>
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left sidebar */}
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
                onClick={() => setSidebarCollapsed(false)}
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
                  {courseQuery.data?.code ?? 'Samtaler'}
                </h2>
                <button
                  onClick={() => setSidebarCollapsed(true)}
                  className="rounded-md p-1 text-gray-400 hover:text-gray-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"
                  aria-label="Skjul sidepanel"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
              </div>

              {/* New conversation button */}
              <div className="px-4 py-3">
                <button
                  onClick={() => createConversationMutation.mutate()}
                  disabled={!courseId || createConversationMutation.isPending}
                  className="btn-primary w-full justify-center text-xs py-2"
                  title={!courseId ? 'Velg et emne for å starte ny samtale' : undefined}
                >
                  {createConversationMutation.isPending ? (
                    <Spinner size="sm" />
                  ) : (
                    <Plus className="h-3.5 w-3.5" aria-hidden="true" />
                  )}
                  Ny samtale
                </button>
              </div>

              {/* Conversations list */}
              <nav aria-label="Samtalliste" className="flex-1 min-h-0 overflow-y-auto px-2 pb-4">
                {conversationsQuery.isLoading && (
                  <div className="flex justify-center py-6">
                    <Spinner size="sm" className="text-indigo-600" />
                  </div>
                )}
                {conversations.length === 0 && !conversationsQuery.isLoading && (
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
                        onSelect={() => setSelectedConversationId(conv.id)}
                        onDelete={() => deleteConversationMutation.mutate(conv.id)}
                        onRename={(title) => renameConversationMutation.mutate({ id: conv.id, title })}
                      />
                    </li>
                  ))}
                </ul>
                {conversationsQuery.data && (
                  <p className="mt-2 px-3 text-xs text-gray-400">
                    {conversationsQuery.data.total} samtale{conversationsQuery.data.total !== 1 ? 'r' : ''} totalt
                  </p>
                )}
              </nav>
            </>
          )}
        </aside>

        {/* Main chat area */}
        <div className="flex flex-1 min-h-0 flex-col overflow-hidden">
          {/* Chat header */}
          <div className="flex items-center gap-3 border-b border-gray-200 bg-white px-6 py-3">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm text-gray-500 hover:bg-gray-100 hover:text-gray-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 transition-colors"
              aria-label="Tilbake til dashboard"
            >
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              <span>Tilbake</span>
            </button>
            {selectedConversation && (
              <>
                <span className="text-gray-300" aria-hidden="true">/</span>
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-indigo-500" aria-hidden="true" />
                  <span className="text-sm font-medium text-gray-700">
                    {selectedConversation.title ?? `Samtale ${formatConversationDate(selectedConversation.created_at)}`}
                  </span>
                </div>
              </>
            )}
          </div>

          {/* Messages area */}
          <div className="flex-1 min-h-0 overflow-y-auto px-6 py-6">
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
            ) : messagesQuery.isLoading ? (
              <div className="flex h-full items-center justify-center">
                <Spinner size="lg" className="text-indigo-600" />
              </div>
            ) : (
              <div className="mx-auto max-w-3xl space-y-4">
                {displayMessages.length === 0 && (
                  <div className="py-8 text-center">
                    <p className="text-sm text-gray-400">
                      Ingen meldinger ennå. Still et spørsmål for å komme i gang!
                    </p>
                  </div>
                )}
                {displayMessages.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}
                {sendMessageMutation.isPending && (
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

          {/* Input area */}
          {selectedConversationId && (
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
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={sendMessageMutation.isPending}
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
                    onClick={handleSend}
                    disabled={!inputValue.trim() || sendMessageMutation.isPending}
                    className="shrink-0 rounded-lg bg-indigo-600 p-2 text-white hover:bg-indigo-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    aria-label="Send melding"
                  >
                    <Send className="h-4 w-4" aria-hidden="true" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        <aside className="flex w-96 shrink-0 flex-col border-l border-gray-200 bg-white">
          <div className="border-b border-gray-200 px-5 py-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
              Round {instructionIndex + 1} of {instructionOrder.length}
            </p>
            <h2 className="mt-1 text-lg font-semibold text-gray-900">Instructions</h2>
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
            <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <div className="text-sm text-gray-700">
                <ReactMarkdown
                  components={{
                    h1: ({ ...props }) => <h3 className="mb-3 text-base font-semibold text-gray-900" {...props} />,
                    h2: ({ ...props }) => <h3 className="mb-3 text-base font-semibold text-gray-900" {...props} />,
                    h3: ({ ...props }) => <h4 className="mb-2 text-sm font-semibold text-gray-900" {...props} />,
                    p: ({ ...props }) => <p className="mb-3 leading-6 last:mb-0" {...props} />,
                    ul: ({ ...props }) => <ul className="mb-3 list-disc space-y-1 pl-5 last:mb-0" {...props} />,
                    ol: ({ ...props }) => <ol className="mb-3 list-decimal space-y-1 pl-5 last:mb-0" {...props} />,
                    li: ({ ...props }) => <li className="leading-6" {...props} />,
                    a: ({ ...props }) => (
                      <a
                        className="text-indigo-700 underline underline-offset-2 hover:text-indigo-800"
                        target="_blank"
                        rel="noreferrer"
                        {...props}
                      />
                    ),
                    strong: ({ ...props }) => <strong className="font-semibold text-gray-900" {...props} />,
                    code: ({ ...props }) => (
                      <code className="rounded bg-gray-100 px-1 py-0.5 font-mono text-[0.9em]" {...props} />
                    ),
                  }}
                >
                  {currentInstruction.instructionsMarkdown}
                </ReactMarkdown>
              </div>
            </section>

            <a
              href={currentInstruction.surveyUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm font-medium text-indigo-700 transition-colors hover:bg-indigo-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"
            >
              <ExternalLink className="h-4 w-4" aria-hidden="true" />
              {currentInstruction.surveyLabel}
            </a>
          </div>

          {!isLastInstruction && (
            <div className="space-y-3 border-t border-gray-200 px-5 py-4">
              <button
                onClick={handleFinishTest}
                disabled={currentInstructionFinished}
                className={clsx(
                  'w-full rounded-lg px-4 py-3 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600',
                  currentInstructionFinished
                    ? 'cursor-default bg-emerald-100 text-emerald-700'
                    : 'bg-indigo-600 text-white hover:bg-indigo-700'
                )}
              >
                {currentInstructionFinished ? 'Test finished' : 'Finish test'}
              </button>

              <button
                onClick={handleNextInstruction}
                disabled={
                  !currentInstructionFinished
                  || advanceStudyCourseMutation.isPending
                }
                className={clsx(
                  'flex w-full items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600',
                  !currentInstructionFinished
                    || advanceStudyCourseMutation.isPending
                    ? 'cursor-not-allowed bg-gray-200 text-gray-500'
                    : 'bg-gray-900 text-white hover:bg-gray-800'
                )}
              >
                {advanceStudyCourseMutation.isPending ? (
                  <>
                    <Spinner size="sm" />
                    Advancing...
                  </>
                ) : (
                  <>
                    Next
                    <ArrowRight className="h-4 w-4" aria-hidden="true" />
                  </>
                )}
              </button>
            </div>
          )}
        </aside>
      </div>
    </Layout>
  )
}
