import type { SystemPromptMode, SystemPromptPreferenceUpdateResponse } from '../types'
import { apiClient } from './client'

/** Persist the authenticated user's preferred tutor prompt mode. */
export async function updateSystemPromptMode(
  mode: SystemPromptMode
): Promise<SystemPromptPreferenceUpdateResponse> {
  const { data } = await apiClient.patch<SystemPromptPreferenceUpdateResponse>(
    '/preferences/system-prompt',
    { mode }
  )
  return data
}
