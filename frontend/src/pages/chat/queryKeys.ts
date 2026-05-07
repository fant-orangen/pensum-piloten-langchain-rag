export const chatQueryKeys = {
  course: (courseId: string | undefined) => ['course', courseId] as const,
  conversations: (courseId: string | undefined) => ['conversations', courseId] as const,
  messages: (conversationId: string | null) => ['messages', conversationId] as const,
  messageSources: (conversationId: string, messageId: string) => (
    ['message-sources', conversationId, messageId] as const
  ),
}
