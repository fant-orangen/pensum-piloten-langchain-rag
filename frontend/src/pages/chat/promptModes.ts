import type { SystemPromptMode } from '../../types'

/** User-facing labels for backend system prompt modes. */
export const PROMPT_MODE_OPTIONS: { value: SystemPromptMode; label: string; description: string }[] = [
  { value: 1, label: 'Sokratisk', description: 'Guider deg med spørsmål' },
  { value: 2, label: 'Direkte', description: 'Gir direkte svar' },
  { value: 3, label: 'Eksempel', description: 'Forklarer med eksempler' },
]
