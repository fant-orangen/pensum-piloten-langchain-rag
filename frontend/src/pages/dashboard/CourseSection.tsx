import type { ReactNode } from 'react'
import { Spinner } from '../../components/Spinner'
import type { CourseRead } from '../../types'
import { CourseCard } from './CourseCard'

interface CourseSectionProps {
  headingId: string
  title: string
  courses: CourseRead[] | undefined
  isLoading: boolean
  isError: boolean
  errorMessage: string
  emptyMessage?: string
  emptyState?: ReactNode
  onCourseClick: (course: CourseRead) => void
}

/** Dashboard section grouping courses under a heading with loading/empty states. */
export function CourseSection({
  headingId,
  title,
  courses,
  isLoading,
  isError,
  errorMessage,
  emptyMessage,
  emptyState,
  onCourseClick,
}: CourseSectionProps) {
  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId} className="mb-4 text-lg font-semibold text-gray-800">
        {title}
      </h2>
      {isLoading && (
        <div className="flex items-center gap-3 text-gray-500">
          <Spinner size="sm" className="text-indigo-600" />
          <span>Laster emner...</span>
        </div>
      )}
      {isError && (
        <p className="text-sm text-red-600">{errorMessage}</p>
      )}
      {courses && courses.length === 0 && (
        emptyState ?? <p className="text-sm text-gray-500">{emptyMessage}</p>
      )}
      {courses && courses.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {courses.map((course) => (
            <CourseCard
              key={course.id}
              course={course}
              onClick={() => onCourseClick(course)}
            />
          ))}
        </div>
      )}
    </section>
  )
}
