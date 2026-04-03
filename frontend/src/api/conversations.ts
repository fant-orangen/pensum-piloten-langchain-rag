import type {
  ConversationRead,
  MessageRead,
  MessageSourceRead,
  PaginatedResponse,
} from '../types'
import { apiClient } from './client'

export async function getConversations(
  page = 1,
  pageSize = 50,
  courseId?: string
): Promise<PaginatedResponse<ConversationRead>> {
  const { data } = await apiClient.get<PaginatedResponse<ConversationRead>>('/conversations', {
    params: {
      page,
      page_size: pageSize,
      ...(courseId ? { course_id: courseId } : {}),
    },
  })
  return data
}

export async function createConversation(courseId: string): Promise<ConversationRead> {
  const { data } = await apiClient.post<ConversationRead>('/conversations', {
    course_id: courseId,
  })
  return data
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await apiClient.delete(`/conversations/${conversationId}`)
}

export async function getMessages(
  conversationId: string,
  page = 1,
  pageSize = 100
): Promise<PaginatedResponse<MessageRead>> {
  const { data } = await apiClient.get<PaginatedResponse<MessageRead>>(
    `/conversations/${conversationId}/messages`,
    { params: { page, page_size: pageSize } }
  )
  return data
}

export async function sendMessage(conversationId: string, content: string): Promise<MessageRead> {
  const { data } = await apiClient.post<MessageRead>(
    `/conversations/${conversationId}/messages`,
    { content }
  )
  return data
}

export async function getMessageSources(
  conversationId: string,
  messageId: string
): Promise<MessageSourceRead[]> {
  const { data } = await apiClient.get<MessageSourceRead[]>(
    `/conversations/${conversationId}/messages/${messageId}/sources`
  )
  return data
}
