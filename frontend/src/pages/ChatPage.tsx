import { useCallback, useEffect, useRef, useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { useInfiniteQuery, useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'
import {
  ArrowLeft,
  BookOpen,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '../contexts/AuthContext'
import { Layout } from '../components/Layout'
import {
  getConversations,
  createConversation,
  deleteConversation,
  getMessages,
  renameConversation,
  sendMessage,
} from '../api/conversations'
import { getCourse } from '../api/courses'
import { updateSystemPromptMode } from '../api/preferences'
import type { MessageRead, SystemPromptMode } from '../types'
import { ChatSidebar } from './chat/ChatSidebar'
import { MessageComposer } from './chat/MessageComposer'
import { MessageList } from './chat/MessageList'
import { SourcesPanel } from './chat/SourcesPanel'
import { formatConversationDate } from './chat/format'
import { chatQueryKeys } from './chat/queryKeys'
import { usePageTitle } from '../hooks/usePageTitle'

const NO_COURSE_SOURCES_MESSAGE = 'Kunne ikke sende melding. Dette faget har ingen kilder.'
const NO_COURSE_SOURCES_DETAIL = 'This course does not currently have ingested materials.'
const COURSE_REBUILDING_MESSAGE = 'Kunne ikke sende melding. Kurset prosesserer kildematerialer. Prøv igjen senere.'
const COURSE_REBUILDING_DETAIL = 'Course materials are currently being rebuilt.'

/**
 * Course-scoped chat workspace.
 *
 * Coordinates conversation selection, message sending, source-panel display,
 * and persisted system-prompt mode changes.
 */
export function ChatPage() {
  const { courseId: routeCourseId } = useParams<{ courseId?: string }>()
  const courseId = routeCourseId ?? ''
  const navigate = useNavigate()
  const { user } = useAuth()
  const queryClient = useQueryClient()

  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null)
  const [inputValue, setInputValue] = useState('')
  const [activeSourceMessageId, setActiveSourceMessageId] = useState<string | null>(null)
  const [promptMode, setPromptMode] = useState<SystemPromptMode>(user?.system_prompt_mode ?? 1)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [pendingUserMessage, setPendingUserMessage] = useState<MessageRead | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const courseQuery = useQuery({
    queryKey: chatQueryKeys.course(courseId),
    queryFn: () => getCourse(courseId),
    enabled: !!routeCourseId,
  })
  usePageTitle(courseQuery.data?.code ? `${courseQuery.data.code} Chat` : 'Chat')

  const conversationsQuery = useInfiniteQuery({
    queryKey: chatQueryKeys.conversations(courseId),
    queryFn: ({ pageParam }) => getConversations(pageParam, 50, courseId),
    enabled: !!routeCourseId,
    initialPageParam: 1,
    getNextPageParam: (lastPage) => (
      lastPage.page < lastPage.pages ? lastPage.page + 1 : undefined
    ),
  })

  const messagesQuery = useInfiniteQuery({
    queryKey: chatQueryKeys.messages(selectedConversationId),
    queryFn: ({ pageParam }) => getMessages(selectedConversationId!, pageParam, 100),
    enabled: !!selectedConversationId,
    initialPageParam: 1,
    getNextPageParam: (lastPage) => (
      lastPage.page < lastPage.pages ? lastPage.page + 1 : undefined
    ),
  })

  const createConversationMutation = useMutation({
    mutationFn: () => createConversation(courseId),
    onSuccess: (conv) => {
      queryClient.invalidateQueries({ queryKey: chatQueryKeys.conversations(courseId) })
      setSelectedConversationId(conv.id)
      setActiveSourceMessageId(null)
    },
    onError: () => toast.error('Klarte ikke opprette samtale.'),
  })

  const deleteConversationMutation = useMutation({
    mutationFn: deleteConversation,
    onSuccess: (_data, deletedId) => {
      queryClient.invalidateQueries({ queryKey: chatQueryKeys.conversations(courseId) })
      if (selectedConversationId === deletedId) {
        setSelectedConversationId(null)
        setActiveSourceMessageId(null)
      }
    },
    onError: () => toast.error('Klarte ikke slette samtale.'),
  })

  const renameConversationMutation = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) => renameConversation(id, title),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: chatQueryKeys.conversations(courseId) }),
    onError: () => toast.error('Klarte ikke endre navn.'),
  })

  const sendMessageMutation = useMutation({
    mutationFn: ({ conversationId, content }: { conversationId: string; content: string }) => (
      sendMessage(conversationId, content)
    ),
    onSuccess: async (_message, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: chatQueryKeys.messages(variables.conversationId) }),
        queryClient.invalidateQueries({ queryKey: chatQueryKeys.conversations(courseId) }),
      ])
      setPendingUserMessage(null)
    },
    onError: (error, variables) => {
      setPendingUserMessage(null)
      setInputValue(variables.content)
      const detail = error instanceof AxiosError ? error.response?.data?.detail : undefined
      if (detail === NO_COURSE_SOURCES_DETAIL) {
        toast.error(NO_COURSE_SOURCES_MESSAGE)
      } else if (detail === COURSE_REBUILDING_DETAIL) {
        toast.error(COURSE_REBUILDING_MESSAGE)
      } else {
        toast.error('Klarte ikke sende melding.')
      }
    },
  })

  const promptModeMutation = useMutation({
    mutationFn: updateSystemPromptMode,
    onError: () => toast.error('Klarte ikke oppdatere modus.'),
  })

  const persistedMessages = messagesQuery.data
    ? messagesQuery.data.pages.flatMap((page) => page.items).reverse()
    : []
  const displayMessages = pendingUserMessage?.conversation_id === selectedConversationId
    ? [...persistedMessages, pendingUserMessage]
    : persistedMessages
  const lastMessageId = displayMessages[displayMessages.length - 1]?.id

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lastMessageId, sendMessageMutation.isPending, selectedConversationId])

  const handleSend = useCallback(() => {
    const content = inputValue.trim()
    if (!content || !selectedConversationId || sendMessageMutation.isPending) return
    setPendingUserMessage({
      id: `pending-${selectedConversationId}-${Date.now()}`,
      conversation_id: selectedConversationId,
      role: 'human',
      content,
      sources: null,
      created_at: new Date().toISOString(),
      conversation_compression_triggered: false,
    })
    setInputValue('')
    sendMessageMutation.mutate({ conversationId: selectedConversationId, content })
  }, [inputValue, selectedConversationId, sendMessageMutation])

  function handlePromptModeChange(mode: SystemPromptMode) {
    setPromptMode(mode)
    promptModeMutation.mutate(mode)
  }

  function handleShowSources(messageId: string) {
    setActiveSourceMessageId((prev) => (prev === messageId ? null : messageId))
  }

  const conversations = conversationsQuery.data?.pages.flatMap((page) => page.items) ?? []
  const selectedConversation = conversations.find((c) => c.id === selectedConversationId)

  if (!routeCourseId) {
    return <Navigate to="/" replace />
  }

  return (
    <Layout>
      <div className="flex flex-1 min-h-0 overflow-hidden">
        <ChatSidebar
          courseCode={courseQuery.data?.code}
          courseId={courseId}
          conversations={conversations}
          totalConversations={conversationsQuery.data?.pages[0]?.total}
          isLoadingConversations={conversationsQuery.isLoading}
          isLoadingMoreConversations={conversationsQuery.isFetchingNextPage}
          hasMoreConversations={conversationsQuery.hasNextPage}
          selectedConversationId={selectedConversationId}
          promptMode={promptMode}
          sidebarCollapsed={sidebarCollapsed}
          isCreatingConversation={createConversationMutation.isPending}
          onExpandSidebar={() => setSidebarCollapsed(false)}
          onCollapseSidebar={() => setSidebarCollapsed(true)}
          onPromptModeChange={handlePromptModeChange}
          onCreateConversation={() => createConversationMutation.mutate()}
          onSelectConversation={(conversationId) => {
            setSelectedConversationId(conversationId)
            setActiveSourceMessageId(null)
          }}
          onDeleteConversation={(conversationId) => deleteConversationMutation.mutate(conversationId)}
          onRenameConversation={(conversationId, title) => (
            renameConversationMutation.mutate({ id: conversationId, title })
          )}
          onLoadMoreConversations={() => conversationsQuery.fetchNextPage()}
        />

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

          <MessageList
            courseId={courseId}
            selectedConversationId={selectedConversationId}
            messages={displayMessages}
            isLoadingMessages={messagesQuery.isLoading}
            isLoadingMoreMessages={messagesQuery.isFetchingNextPage}
            hasMoreMessages={messagesQuery.hasNextPage}
            isSendingMessage={sendMessageMutation.isPending}
            activeSourceMessageId={activeSourceMessageId}
            messagesEndRef={messagesEndRef}
            onLoadMoreMessages={() => messagesQuery.fetchNextPage()}
            onShowSources={handleShowSources}
          />

          {selectedConversationId && (
            <MessageComposer
              inputValue={inputValue}
              isSendingMessage={sendMessageMutation.isPending}
              textareaRef={textareaRef}
              onInputChange={setInputValue}
              onSend={handleSend}
            />
          )}
        </div>

        {/* Right sources panel */}
        {activeSourceMessageId && selectedConversationId && (
          <SourcesPanel
            conversationId={selectedConversationId}
            messageId={activeSourceMessageId}
            onClose={() => setActiveSourceMessageId(null)}
          />
        )}
      </div>
    </Layout>
  )
}
