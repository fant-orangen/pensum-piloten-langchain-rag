export type GlobalRole = 'student' | 'teacher' | 'admin'
export type SystemPromptMode = 1 | 2 | 3
export type DocumentStatus = 'pending_add' | 'active' | 'pending_remove'
export type RebuildStatus = 'idle' | 'queued' | 'building' | 'failed'
export type MessageRole = 'human' | 'ai'
export type RagMode = 'kg_rag' | 'rag' | 'reranked_rag' | 'no_rag'

export interface UserResponse {
  id: string
  email: string
  first_name: string
  last_name: string
  global_role: GlobalRole
  system_prompt_mode: SystemPromptMode
  must_change_password: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface CourseRead {
  id: string
  name: string
  code: string
  rag_mode: RagMode
  chroma_collection: string | null
  course_specific_instructions: string | null
  index_version: number
  rebuild_status: RebuildStatus
  rebuild_error: string | null
}

export interface CourseCreate {
  name: string
  code: string
  chroma_collection?: string
  documents_dir: string
  description?: string
  course_specific_instructions?: string
}

export interface CourseInstructionsRead {
  course_id: string
  course_specific_instructions: string | null
}

export interface EnrollmentRead {
  user_id: string
  course_id: string
  role: string
}

export interface CourseStudentRead {
  id: string
  email: string
  first_name: string
  last_name: string
}

export interface CourseDocumentRead {
  id: string
  course_id: string
  original_filename: string
  content_type: string | null
  status: DocumentStatus
  created_at: string
  updated_at: string
}

export interface CourseMaterialsStatusRead {
  course_id: string
  rebuild_status: RebuildStatus
  rebuild_error: string | null
  index_version: number
  active_scope: string | null
  pending_additions: number
  pending_removals: number
}

export interface ZipImportResultRead {
  staged: CourseDocumentRead[]
  staged_count: number
  skipped_count: number
  skipped_names: string[]
}

export interface MissingCandidateRead {
  email: string
  first_name: string
  last_name: string
}

export interface EnrollmentImportPreviewRead {
  preview_id: string
  course_id: string
  uploaded_filename: string | null
  requested_role: string
  total_rows: number
  accepted_email_count: number
  enrollable_emails: string[]
  missing_candidates: MissingCandidateRead[]
  already_enrolled_emails: string[]
  duplicate_emails: string[]
  invalid_emails: string[]
  has_warnings: boolean
}

export interface EnrollmentImportConfirmRead {
  course_id: string
  requested_role: string
  enrolled_emails: string[]
  created_emails: string[]
  already_enrolled_emails: string[]
}

export interface ConversationRead {
  id: string
  course_id: string
  title: string | null
  created_at: string
  updated_at: string
}

export interface MessageRead {
  id: string
  conversation_id: string
  role: MessageRole
  content: string
  created_at: string
  conversation_compression_triggered: boolean
}

export interface AdminUserRead {
  id: string
  email: string
  first_name: string
  last_name: string
  global_role: GlobalRole
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
}
