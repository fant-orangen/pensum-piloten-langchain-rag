import type { SystemPromptMode, SystemPromptPreferenceUpdateResponse } from '../types'
import { apiClient } from './client'

export async function updateSystemPromptMode(
  mode: SystemPromptMode
): Promise<SystemPromptPreferenceUpdateResponse> {
  const { data } = await apiClient.patch<SystemPromptPreferenceUpdateResponse>(
    '/preferences/system-prompt',
    { mode }
  )
  return data
}
