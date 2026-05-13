import { BookOpen, ChevronRight } from 'lucide-react'
import type { CourseRead } from '../../types'

interface CourseCardProps {
  course: CourseRead
  onClick: () => void
}

/** Clickable dashboard card for one course. */
export function CourseCard({ course, onClick }: CourseCardProps) {
  return (
    <article>
      <button
        onClick={onClick}
        className="group flex w-full items-center justify-between rounded-lg border border-gray-200 bg-white p-5 text-left shadow-sm hover:border-indigo-300 hover:shadow-md transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"
      >
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-50">
            <BookOpen className="h-5 w-5 text-indigo-600" aria-hidden="true" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 group-hover:text-indigo-700 transition-colors">
              {course.name}
            </h3>
            <p className="mt-0.5 text-sm text-gray-500">{course.code}</p>
          </div>
        </div>
        <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-indigo-600 transition-colors" aria-hidden="true" />
      </button>
    </article>
  )
}
