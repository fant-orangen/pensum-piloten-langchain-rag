export const courseQueryKeys = {
  responsibleCourses: ['responsible-courses'] as const,
  students: (courseId: string) => ['course-students', courseId] as const,
  studentsPage: (courseId: string, page: number) => ['course-students', courseId, page] as const,
  documents: (courseId: string) => ['course-documents', courseId] as const,
  documentStatus: (courseId: string) => ['course-documents-status', courseId] as const,
  instructions: (courseId: string) => ['course-instructions', courseId] as const,
}
