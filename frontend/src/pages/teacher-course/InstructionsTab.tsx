import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import toast from 'react-hot-toast'
import { Spinner } from '../../components/Spinner'
import { getCourseInstructions, updateCourseInstructions } from '../../api/courses'
import { courseQueryKeys, invalidateAllCourseQueries } from './queryKeys'

interface InstructionsTabProps {
  courseId: string
}

const MAX_INSTRUCTIONS_CHARS = 3000

export function InstructionsTab({ courseId }: InstructionsTabProps) {
  const queryClient = useQueryClient()
  const [instructions, setInstructions] = useState('')

  const instructionsQuery = useQuery({
    queryKey: courseQueryKeys.instructions(courseId),
    queryFn: () => getCourseInstructions(courseId),
  })

  useEffect(() => {
    setInstructions(instructionsQuery.data?.course_specific_instructions ?? '')
  }, [courseId, instructionsQuery.data])

  const saveMutation = useMutation({
    mutationFn: (text: string) => updateCourseInstructions(courseId, text),
    onSuccess: () => {
      invalidateAllCourseQueries(queryClient, courseId)
      toast.success('Instruksjoner lagret!')
    },
    onError: () => toast.error('Klarte ikke lagre instruksjoner.'),
  })

  const charsLeft = MAX_INSTRUCTIONS_CHARS - instructions.length

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="course-instructions" className="label mb-2">
          Emnespesifikke instruksjoner
        </label>
        <p className="mb-3 text-sm text-gray-500">
          Disse instruksjonene brukes av AI-assistenten for å tilpasse svar til emnet. Du kan for
          eksempel beskrive fagets temaer, pensum, eller pedagogiske mål.
        </p>
        {instructionsQuery.isLoading ? (
          <div className="flex items-center gap-3 text-gray-500">
            <Spinner size="sm" className="text-indigo-600" />
            <span>Laster instruksjoner...</span>
          </div>
        ) : (
          <>
            <textarea
              id="course-instructions"
              rows={14}
              value={instructions}
              onChange={(e) => setInstructions(e.target.value.slice(0, MAX_INSTRUCTIONS_CHARS))}
              className="input-field resize-none font-mono text-xs"
              placeholder="Beskriv fagets innhold, mål og pedagogiske tilnærming..."
              aria-describedby="chars-left"
            />
            <p
              id="chars-left"
              className={clsx(
                'mt-1.5 text-right text-xs',
                charsLeft < 200 ? 'text-orange-600' : 'text-gray-400'
              )}
            >
              {charsLeft} tegn igjen
            </p>
          </>
        )}
      </div>

      <button
        onClick={() => saveMutation.mutate(instructions)}
        disabled={saveMutation.isPending || instructionsQuery.isLoading}
        className="btn-primary"
      >
        {saveMutation.isPending && <Spinner size="sm" />}
        Lagre instruksjoner
      </button>
    </div>
  )
}
