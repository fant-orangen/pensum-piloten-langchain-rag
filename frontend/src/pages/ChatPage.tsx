import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
import type { SystemPromptMode } from '../types'
import { ChatSidebar } from './chat/ChatSidebar'
import { MessageComposer } from './chat/MessageComposer'
import { MessageList } from './chat/MessageList'
import { SourcesPanel } from './chat/SourcesPanel'
import { formatConversationDate } from './chat/format'
import { chatQueryKeys } from './chat/queryKeys'
import { usePageTitle } from '../hooks/usePageTitle'

/**
 * Course-scoped chat workspace.
 *
 * Coordinates conversation selection, message sending, source-panel display,
 * and persisted system-prompt mode changes.
 */
export function ChatPage() {
  const { courseId } = useParams<{ courseId?: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const queryClient = useQueryClient()

  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null)
  const [inputValue, setInputValue] = useState('')
  const [activeSourceMessageId, setActiveSourceMessageId] = useState<string | null>(null)
  const [promptMode, setPromptMode] = useState<SystemPromptMode>(user?.system_prompt_mode ?? 1)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const courseQuery = useQuery({
    queryKey: chatQueryKeys.course(courseId),
    queryFn: () => getCourse(courseId!),
    enabled: !!courseId,
  })
  usePageTitle(courseQuery.data?.code ? `${courseQuery.data.code} Chat` : 'Chat')

  const conversationsQuery = useQuery({
    queryKey: chatQueryKeys.conversations(courseId),
    queryFn: () => getConversations(1, 50, courseId),
  })

  const messagesQuery = useQuery({
    queryKey: chatQueryKeys.messages(selectedConversationId),
    queryFn: () => getMessages(selectedConversationId!, 1, 100),
    enabled: !!selectedConversationId,
  })

  const createConversationMutation = useMutation({
    mutationFn: () => createConversation(courseId!),
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
    mutationFn: (content: string) => sendMessage(selectedConversationId!, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: chatQueryKeys.messages(selectedConversationId) })
      queryClient.invalidateQueries({ queryKey: chatQueryKeys.conversations(courseId) })
    },
    onError: () => toast.error('Klarte ikke sende melding.'),
  })

  const promptModeMutation = useMutation({
    mutationFn: updateSystemPromptMode,
    onError: () => toast.error('Klarte ikke oppdatere modus.'),
  })

  const displayMessages = messagesQuery.data
    ? [...messagesQuery.data.items].reverse()
    : []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [displayMessages.length])

  const handleSend = useCallback(() => {
    const content = inputValue.trim()
    if (!content || !selectedConversationId || sendMessageMutation.isPending) return
    setInputValue('')
    sendMessageMutation.mutate(content)
  }, [inputValue, selectedConversationId, sendMessageMutation])

  function handlePromptModeChange(mode: SystemPromptMode) {
    setPromptMode(mode)
    promptModeMutation.mutate(mode)
  }

  function handleShowSources(messageId: string) {
    setActiveSourceMessageId((prev) => (prev === messageId ? null : messageId))
  }

  const conversations = conversationsQuery.data?.items ?? []
  const selectedConversation = conversations.find((c) => c.id === selectedConversationId)

  return (
    <Layout>
      <div className="flex flex-1 min-h-0 overflow-hidden">
        <ChatSidebar
          courseCode={courseQuery.data?.code}
          courseId={courseId}
          conversations={conversations}
          totalConversations={conversationsQuery.data?.total}
          isLoadingConversations={conversationsQuery.isLoading}
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
            isSendingMessage={sendMessageMutation.isPending}
            activeSourceMessageId={activeSourceMessageId}
            messagesEndRef={messagesEndRef}
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
