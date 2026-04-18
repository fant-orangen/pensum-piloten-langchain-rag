import set1Instructions from './set-1.md?raw'
import set2Instructions from './set-2.md?raw'
import set3Instructions from './set-3.md?raw'

export type InstructionSetId = 'set-1' | 'set-2' | 'set-3'

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
    surveyLabel: 'Open survey',
    surveyUrl: 'https://example.com/survey/round-1',
  },
  'set-2': {
    id: 'set-2',
    instructionsMarkdown: set2Instructions,
    surveyLabel: 'Open survey',
    surveyUrl: 'https://example.com/survey/round-2',
  },
  'set-3': {
    id: 'set-3',
    instructionsMarkdown: set3Instructions,
    surveyLabel: 'Open survey',
    surveyUrl: 'https://example.com/survey/round-3',
  },
}
