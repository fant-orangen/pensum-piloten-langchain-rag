import type {
  CourseMaterialsStatusRead,
  CourseCreate,
  CourseDocumentRead,
  CourseInstructionsRead,
  CourseRead,
  CourseStudentRead,
  CourseSummaryRead,
  EnrollmentImportConfirmRead,
  EnrollmentImportPreviewRead,
  EnrollmentRead,
  PaginatedResponse,
  ZipImportResultRead,
} from '../types'
import { apiClient } from './client'

/** Fetch safe course metadata for chat/sidebar display. */
export async function getCourse(courseId: string): Promise<CourseSummaryRead> {
  const { data } = await apiClient.get<CourseSummaryRead>(`/courses/${courseId}`)
  return data
}

/** List all courses the current user is enrolled in. */
export async function getCourses(): Promise<CourseRead[]> {
  const { data } = await apiClient.get<CourseRead[]>('/courses')
  return data
}

/** List courses where the current teacher/admin is enrolled as a student. */
export async function getAvailableCourses(): Promise<CourseRead[]> {
  const { data } = await apiClient.get<CourseRead[]>('/courses/available')
  return data
}

/** List courses where the current teacher/admin has teacher responsibility. */
export async function getResponsibleCourses(): Promise<CourseRead[]> {
  const { data } = await apiClient.get<CourseRead[]>('/courses/responsible')
  return data
}

/** Create a course and enroll the creator as teacher. */
export async function createCourse(payload: CourseCreate): Promise<CourseRead> {
  const { data } = await apiClient.post<CourseRead>('/courses', payload)
  return data
}

/** Delete a course and its associated server-side materials. */
export async function deleteCourse(courseId: string): Promise<void> {
  await apiClient.delete(`/courses/${courseId}`)
}

/** Return a paginated page of students enrolled in a course. */
export async function getCourseStudents(
  courseId: string,
  page = 1,
  pageSize = 20
): Promise<PaginatedResponse<CourseStudentRead>> {
  const { data } = await apiClient.get<PaginatedResponse<CourseStudentRead>>(
    `/courses/${courseId}/students`,
    { params: { page, page_size: pageSize } }
  )
  return data
}

/** Return all global teachers for course-teacher assignment UI. */
export async function getAllTeachers(): Promise<CourseStudentRead[]> {
  const { data } = await apiClient.get<CourseStudentRead[]>('/courses/all-teachers')
  return data
}

/** Return a paginated page of teachers assigned to a course. */
export async function getCourseTeachers(
  courseId: string,
  page = 1,
  pageSize = 20
): Promise<PaginatedResponse<CourseStudentRead>> {
  const { data } = await apiClient.get<PaginatedResponse<CourseStudentRead>>(
    `/courses/${courseId}/teachers`,
    { params: { page, page_size: pageSize } }
  )
  return data
}

/** List active and staged source material records for a course. */
export async function getCourseDocuments(courseId: string): Promise<CourseDocumentRead[]> {
  const { data } = await apiClient.get<CourseDocumentRead[]>(`/courses/${courseId}/documents`)
  return data
}

/** Stage uploaded files as pending additions; changes become active after confirmIngestion. */
export async function uploadDocuments(courseId: string, files: File[]): Promise<CourseDocumentRead[]> {
  const form = new FormData()
  files.forEach((file) => form.append('files', file))
  const { data } = await apiClient.post<CourseDocumentRead[]>(
    `/courses/${courseId}/documents`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
  return data
}

/** Upload a zip and stage supported files, returning skipped unsupported names. */
export async function uploadZip(courseId: string, file: File): Promise<ZipImportResultRead> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<ZipImportResultRead>(
    `/courses/${courseId}/documents/zip`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
  return data
}

/** Stage an active document for removal, or delete a pending-add document immediately. */
export async function deleteDocument(courseId: string, documentId: string): Promise<void> {
  await apiClient.delete(`/courses/${courseId}/documents/${documentId}`)
}

/** Stage all course documents for removal and return the affected count. */
export async function deleteAllDocuments(courseId: string): Promise<{ removed: number }> {
  const { data } = await apiClient.delete<{ removed: number }>(`/courses/${courseId}/documents`)
  return data
}

/** Fetch rebuild status, active scope, and pending material counts. */
export async function getDocumentsStatus(courseId: string): Promise<CourseMaterialsStatusRead> {
  const { data } = await apiClient.get<CourseMaterialsStatusRead>(
    `/courses/${courseId}/documents/status`
  )
  return data
}

/** Queue a material rebuild that activates staged adds/removals when complete. */
export async function confirmIngestion(courseId: string): Promise<CourseMaterialsStatusRead> {
  const { data } = await apiClient.post<CourseMaterialsStatusRead>(
    `/courses/${courseId}/documents/confirm`
  )
  return data
}

/** Enroll an existing user by email as student or teacher. */
export async function enrollStudent(
  courseId: string,
  userEmail: string,
  role = 'student'
): Promise<EnrollmentRead> {
  const { data } = await apiClient.post<EnrollmentRead>(`/courses/${courseId}/enrollments`, {
    user_email: userEmail,
    role,
  })
  return data
}

/** Remove one user enrollment from a course. */
export async function unenrollStudent(courseId: string, userId: string): Promise<void> {
  await apiClient.delete(`/courses/${courseId}/enrollments/${userId}`)
}

/** Remove all student enrollments from a course; teacher enrollments are preserved. */
export async function removeAllEnrollments(courseId: string): Promise<{ removed: number }> {
  const { data } = await apiClient.delete<{ removed: number }>(`/courses/${courseId}/enrollments`)
  return data
}

/** Upload a CSV and receive a non-mutating enrollment import preview. */
export async function previewEnrollmentImport(
  courseId: string,
  file: File
): Promise<EnrollmentImportPreviewRead> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<EnrollmentImportPreviewRead>(
    `/courses/${courseId}/enrollment-imports/preview`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
  return data
}

/** Apply a previously generated enrollment import preview. */
export async function confirmEnrollmentImport(
  courseId: string,
  previewId: string
): Promise<EnrollmentImportConfirmRead> {
  const { data } = await apiClient.post<EnrollmentImportConfirmRead>(
    `/courses/${courseId}/enrollment-imports/${previewId}/confirm`
  )
  return data
}

/** Discard a pending enrollment import preview. */
export async function cancelEnrollmentImport(courseId: string, previewId: string): Promise<void> {
  await apiClient.delete(`/courses/${courseId}/enrollment-imports/${previewId}`)
}

/** Fetch course-specific prompt instructions. */
export async function getCourseInstructions(courseId: string): Promise<CourseInstructionsRead> {
  const { data } = await apiClient.get<CourseInstructionsRead>(`/courses/${courseId}/instructions`)
  return data
}

/** Update course-specific prompt instructions used by the tutor chain. */
export async function updateCourseInstructions(
  courseId: string,
  courseSpecificInstructions: string
): Promise<CourseRead> {
  const { data } = await apiClient.patch<CourseRead>(`/courses/${courseId}/instructions`, {
    course_specific_instructions: courseSpecificInstructions,
  })
  return data
}
