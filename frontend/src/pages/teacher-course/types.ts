export type TeacherCourseTab = 'students' | 'materials' | 'instructions'

export const TEACHER_COURSE_TABS: { id: TeacherCourseTab; label: string }[] = [
  { id: 'students', label: 'Studenter' },
  { id: 'materials', label: 'Læringsmateriell' },
  { id: 'instructions', label: 'Instruksjoner' },
]
