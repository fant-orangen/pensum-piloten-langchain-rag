export type TeacherCourseTab = 'students' | 'materials' | 'instructions' | 'teachers'

export const TEACHER_COURSE_TABS: { id: TeacherCourseTab; label: string }[] = [
  { id: 'students', label: 'Studenter' },
  { id: 'materials', label: 'Læringsmateriell' },
  { id: 'instructions', label: 'Instruksjoner' },
]

export const TEACHERS_TAB: { id: TeacherCourseTab; label: string } = {
  id: 'teachers',
  label: 'Lærere',
}
