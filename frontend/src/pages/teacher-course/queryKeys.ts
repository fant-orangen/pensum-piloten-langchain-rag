import type { QueryClient } from '@tanstack/react-query'

export const courseQueryKeys = {
  responsibleCourses: ['responsible-courses'] as const,
  students: (courseId: string) => ['course-students', courseId] as const,
  studentsPage: (courseId: string, search = '') => ['course-students', courseId, search] as const,
  allTeachers: ['all-teachers'] as const,
  teachers: (courseId: string) => ['course-teachers', courseId] as const,
  teachersPage: (courseId: string, page: number) => ['course-teachers', courseId, page] as const,
  documents: (courseId: string) => ['course-documents', courseId] as const,
  documentStatus: (courseId: string) => ['course-documents-status', courseId] as const,
  instructions: (courseId: string) => ['course-instructions', courseId] as const,
}

export function invalidateAllCourseQueries(queryClient: QueryClient, courseId: string) {
  queryClient.invalidateQueries({ queryKey: courseQueryKeys.students(courseId) })
  queryClient.invalidateQueries({ queryKey: courseQueryKeys.allTeachers })
  queryClient.invalidateQueries({ queryKey: courseQueryKeys.teachers(courseId) })
  queryClient.invalidateQueries({ queryKey: courseQueryKeys.documents(courseId) })
  queryClient.invalidateQueries({ queryKey: courseQueryKeys.documentStatus(courseId) })
  queryClient.invalidateQueries({ queryKey: courseQueryKeys.instructions(courseId) })
}
