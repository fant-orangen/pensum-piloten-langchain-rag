/** Global authorization role assigned to a user. */
export type GlobalRole = 'student' | 'teacher' | 'admin'
/** Tutor prompt variant persisted per user/conversation. */
export type SystemPromptMode = 1 | 2 | 3
/** Lifecycle state for source material before/after a rebuild. */
export type DocumentStatus = 'pending_add' | 'active' | 'pending_remove'
/** Backend material-index rebuild state. */
export type RebuildStatus = 'idle' | 'queued' | 'building' | 'failed'
/** Persisted chat message author. */
export type MessageRole = 'human' | 'ai'
/** Retrieval mode supported by backend chains. */
export type RagMode = 'kg_rag' | 'rag' | 'no_rag'

/** Safe user profile returned by auth endpoints. */
export interface UserResponse {
  id: string
  email: string
  first_name: string
  last_name: string
  global_role: GlobalRole
  system_prompt_mode: SystemPromptMode
  must_change_password: boolean
}

/** JWT payload returned by login. */
export interface TokenResponse {
  access_token: string
  token_type: string
}

/** Full course model used by dashboard and teacher pages. */
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
  created_by_id: string
}

/** Minimal course model used by chat routing and headers. */
export interface CourseSummaryRead {
  id: string
  name: string
  code: string
}

/** Payload for creating a course. */
export interface CourseCreate {
  name: string
  code: string
  chroma_collection?: string
  documents_dir: string
  description?: string
  course_specific_instructions?: string
}

/** Course-specific prompt instructions read model. */
export interface CourseInstructionsRead {
  course_id: string
  course_specific_instructions: string | null
}

/** Enrollment relation returned after user/course membership changes. */
export interface EnrollmentRead {
  user_id: string
  course_id: string
  role: string
}

/** Compact user row for course student/teacher lists. */
export interface CourseStudentRead {
  id: string
  email: string
  first_name: string
  last_name: string
}

/** Source material record and current staging status. */
export interface CourseDocumentRead {
  id: string
  course_id: string
  original_filename: string
  content_type: string | null
  status: DocumentStatus
  created_at: string
  updated_at: string
}

/** Aggregate material rebuild status and pending document counts. */
export interface CourseMaterialsStatusRead {
  course_id: string
  rebuild_status: RebuildStatus
  rebuild_error: string | null
  index_version: number
  active_scope: string | null
  pending_additions: number
  pending_removals: number
}

/** Result of zip upload extraction and staging. */
export interface ZipImportResultRead {
  staged: CourseDocumentRead[]
  staged_count: number
  skipped_count: number
  skipped_names: string[]
}

/** CSV import candidate without an existing user account. */
export interface MissingCandidateRead {
  email: string
  first_name: string
  last_name: string
}

/** Non-mutating preview of a CSV enrollment import. */
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

/** Result after applying an enrollment import preview. */
export interface EnrollmentImportConfirmRead {
  course_id: string
  requested_role: string
  enrolled_emails: string[]
  created_emails: string[]
  already_enrolled_emails: string[]
}

/** Conversation summary row for sidebar navigation. */
export interface ConversationRead {
  id: string
  course_id: string
  title: string | null
  created_at: string
  updated_at: string
}

/** Persisted chat message returned by conversation endpoints. */
export interface MessageRead {
  id: string
  conversation_id: string
  role: MessageRole
  content: string
  sources: unknown
  created_at: string
  conversation_compression_triggered: boolean
}

/** Resolved source chunk for an AI message. */
export interface MessageSourceRead {
  chunk_id: string
  document: string
  page: string
  content: string
}

/** User row shown in admin role-management views. */
export interface AdminUserRead {
  id: string
  email: string
  first_name: string
  last_name: string
  global_role: GlobalRole
  is_course_owner: boolean
}

/** Generic paginated response envelope. */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
}

/** Response from updating the user's prompt mode preference. */
export interface SystemPromptPreferenceUpdateResponse {
  success: boolean
  message: string
  mode: SystemPromptMode
}
