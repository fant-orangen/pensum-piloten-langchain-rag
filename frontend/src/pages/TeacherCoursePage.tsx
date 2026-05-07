import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Eye } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'
import { getResponsibleCourses } from '../api/courses'
import { Layout } from '../components/Layout'
import { InstructionsTab } from './teacher-course/InstructionsTab'
import { MaterialsTab } from './teacher-course/MaterialsTab'
import { StudentsTab } from './teacher-course/StudentsTab'
import { courseQueryKeys } from './teacher-course/queryKeys'
import { TEACHER_COURSE_TABS, type TeacherCourseTab } from './teacher-course/types'

export function TeacherCoursePage() {
  const { courseId } = useParams<{ courseId: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TeacherCourseTab>('students')

  const coursesQuery = useQuery({
    queryKey: courseQueryKeys.responsibleCourses,
    queryFn: getResponsibleCourses,
  })

  const course = coursesQuery.data?.find((c) => c.id === courseId)

  if (!courseId) return null

  return (
    <Layout>
      <div className="flex-1 min-h-0 overflow-y-auto">
        <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6">
          <div className="mb-6">
            <button
              onClick={() => navigate('/')}
              className="mb-4 flex items-center gap-1.5 rounded text-sm text-gray-500 transition-colors hover:text-indigo-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"
            >
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Tilbake til dashboard
            </button>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {course ? course.name : 'Emneadministrasjon'}
                </h1>
                {course && <p className="mt-1 font-mono text-sm text-gray-500">{course.code}</p>}
              </div>
              <button
                onClick={() => navigate(`/chat/${courseId}`)}
                className="flex shrink-0 items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:border-indigo-400 hover:bg-gray-50 hover:text-indigo-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"
              >
                <Eye className="h-4 w-4" aria-hidden="true" />
                Se som student
              </button>
            </div>
          </div>

          <div
            role="tablist"
            aria-label="Emneadministrasjon"
            className="mb-6 flex border-b border-gray-200"
          >
            {TEACHER_COURSE_TABS.map((tab) => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                aria-controls={`${tab.id}-panel`}
                id={`${tab.id}-tab`}
                onClick={() => setActiveTab(tab.id)}
                className={`tab-button mr-1 ${activeTab === tab.id ? 'tab-button-active' : 'tab-button-inactive'}`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div
            role="tabpanel"
            id="students-panel"
            aria-labelledby="students-tab"
            hidden={activeTab !== 'students'}
          >
            {activeTab === 'students' && <StudentsTab courseId={courseId} />}
          </div>
          <div
            role="tabpanel"
            id="materials-panel"
            aria-labelledby="materials-tab"
            hidden={activeTab !== 'materials'}
          >
            {activeTab === 'materials' && <MaterialsTab courseId={courseId} />}
          </div>
          <div
            role="tabpanel"
            id="instructions-panel"
            aria-labelledby="instructions-tab"
            hidden={activeTab !== 'instructions'}
          >
            {activeTab === 'instructions' && <InstructionsTab courseId={courseId} />}
          </div>
        </div>
      </div>
    </Layout>
  )
}
