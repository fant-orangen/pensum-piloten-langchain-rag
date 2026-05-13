/** Tab identifiers supported by the teacher course page. */
export type TeacherCourseTab = 'students' | 'materials' | 'instructions' | 'teachers' | 'admin'

/** Tabs visible to any course teacher. */
export const TEACHER_COURSE_TABS: { id: TeacherCourseTab; label: string }[] = [
  { id: 'students', label: 'Studenter' },
  { id: 'materials', label: 'Læringsmateriell' },
  { id: 'instructions', label: 'Instruksjoner' },
]

/** Additional tab visible only to the course creator/admin path. */
export const TEACHERS_TAB: { id: TeacherCourseTab; label: string } = {
  id: 'teachers',
  label: 'Lærere',
}

/** Destructive course administration tab visible only to creator/admin. */
export const ADMIN_TAB: { id: TeacherCourseTab; label: string } = {
  id: 'admin',
  label: 'Admin',
}
