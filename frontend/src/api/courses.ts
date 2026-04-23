import type {
  CourseMaterialsStatusRead,
  CourseCreate,
  CourseDocumentRead,
  CourseInstructionsRead,
  CourseRead,
  CourseStudentRead,
  EnrollmentImportConfirmRead,
  EnrollmentImportPreviewRead,
  EnrollmentRead,
  PaginatedResponse,
  ZipImportResultRead,
} from '../types'
import { apiClient } from './client'

export async function getCourse(courseId: string): Promise<CourseRead> {
  const { data } = await apiClient.get<CourseRead>(`/courses/${courseId}`)
  return data
}

export async function getCourses(): Promise<CourseRead[]> {
  const { data } = await apiClient.get<CourseRead[]>('/courses')
  return data
}

export async function getAvailableCourses(): Promise<CourseRead[]> {
  const { data } = await apiClient.get<CourseRead[]>('/courses/available')
  return data
}

export async function getResponsibleCourses(): Promise<CourseRead[]> {
  const { data } = await apiClient.get<CourseRead[]>('/courses/responsible')
  return data
}

export async function createCourse(payload: CourseCreate): Promise<CourseRead> {
  const { data } = await apiClient.post<CourseRead>('/courses', payload)
  return data
}

export async function advanceStudyCourse(): Promise<CourseRead> {
  const { data } = await apiClient.post<CourseRead>('/courses/advance')
  return data
}

export async function deleteCourse(courseId: string): Promise<void> {
  await apiClient.delete(`/courses/${courseId}`)
}

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

export async function getCourseDocuments(courseId: string): Promise<CourseDocumentRead[]> {
  const { data } = await apiClient.get<CourseDocumentRead[]>(`/courses/${courseId}/documents`)
  return data
}

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

export async function deleteDocument(courseId: string, documentId: string): Promise<void> {
  await apiClient.delete(`/courses/${courseId}/documents/${documentId}`)
}

export async function deleteAllDocuments(courseId: string): Promise<{ removed: number }> {
  const { data } = await apiClient.delete<{ removed: number }>(`/courses/${courseId}/documents`)
  return data
}

export async function getDocumentsStatus(courseId: string): Promise<CourseMaterialsStatusRead> {
  const { data } = await apiClient.get<CourseMaterialsStatusRead>(
    `/courses/${courseId}/documents/status`
  )
  return data
}

export async function confirmIngestion(courseId: string): Promise<CourseMaterialsStatusRead> {
  const { data } = await apiClient.post<CourseMaterialsStatusRead>(
    `/courses/${courseId}/documents/confirm`
  )
  return data
}

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

export async function unenrollStudent(courseId: string, userId: string): Promise<void> {
  await apiClient.delete(`/courses/${courseId}/enrollments/${userId}`)
}

export async function removeAllEnrollments(courseId: string): Promise<{ removed: number }> {
  const { data } = await apiClient.delete<{ removed: number }>(`/courses/${courseId}/enrollments`)
  return data
}

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

export async function confirmEnrollmentImport(
  courseId: string,
  previewId: string
): Promise<EnrollmentImportConfirmRead> {
  const { data } = await apiClient.post<EnrollmentImportConfirmRead>(
    `/courses/${courseId}/enrollment-imports/${previewId}/confirm`
  )
  return data
}

export async function cancelEnrollmentImport(courseId: string, previewId: string): Promise<void> {
  await apiClient.delete(`/courses/${courseId}/enrollment-imports/${previewId}`)
}

export async function getCourseInstructions(courseId: string): Promise<CourseInstructionsRead> {
  const { data } = await apiClient.get<CourseInstructionsRead>(`/courses/${courseId}/instructions`)
  return data
}

export async function updateCourseInstructions(
  courseId: string,
  courseSpecificInstructions: string
): Promise<CourseRead> {
  const { data } = await apiClient.patch<CourseRead>(`/courses/${courseId}/instructions`, {
    course_specific_instructions: courseSpecificInstructions,
  })
  return data
}
