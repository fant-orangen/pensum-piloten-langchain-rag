import set1Instructions from './set-1.md?raw'
import set2Instructions from './set-2.md?raw'
import set3Instructions from './set-3.md?raw'
import set4Instructions from './set-4.md?raw'

export type InstructionSetId = 'set-1' | 'set-2' | 'set-3' | 'set-4'

export interface InstructionSet {
  id: InstructionSetId
  instructionsMarkdown: string
  surveyLabel: string
  surveyUrl: string
}

export const INSTRUCTION_SETS: Record<InstructionSetId, InstructionSet> = {
  'set-1': {
    id: 'set-1',
    instructionsMarkdown: set1Instructions,
    surveyLabel: 'Open quiz',
    surveyUrl: 'https://nettskjema.no/a/623950',
  },
  'set-2': {
    id: 'set-2',
    instructionsMarkdown: set2Instructions,
    surveyLabel: 'Open quiz',
    surveyUrl: 'https://nettskjema.no/a/623937',
  },
  'set-3': {
    id: 'set-3',
    instructionsMarkdown: set3Instructions,
    surveyLabel: 'Open quiz',
    surveyUrl: 'https://nettskjema.no/a/620892',
  },
  'set-4': {
    id: 'set-4',
    instructionsMarkdown: set4Instructions,
    surveyLabel: 'Open A-B evaluation survey',
    surveyUrl: 'https://nettskjema.no/a/623951',
  },
}
