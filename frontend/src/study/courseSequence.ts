/**
 * Seeded study accounts use `g1u1@test.com` … `g3u12@test.com`. Each group
 * starts in a different `os_g*` course and cycles through the same three.
 */
export const STUDY_EMAIL_PATTERN = /^g[123]u\d+@/i

const STUDY_CODES = ['os_g1', 'os_g2', 'os_g3'] as const
export type StudyCourseCode = (typeof STUDY_CODES)[number]

/**
 * @returns The ordered course codes for this participant, or `null` if the
 * email is not a study account.
 */
export function studyCourseSequenceForEmail(email: string | undefined): StudyCourseCode[] | null {
  if (!email?.trim()) return null
  const m = email.trim().toLowerCase().match(/^g([123])u\d+@/)
  if (!m) return null
  const group = m[1] as '1' | '2' | '3'
  if (group === '1') return ['os_g1', 'os_g2', 'os_g3']
  if (group === '2') return ['os_g2', 'os_g3', 'os_g1']
  return ['os_g3', 'os_g1', 'os_g2']
}

export function isStudyParticipantEmail(email: string | undefined): boolean {
  if (!email?.trim()) return false
  return STUDY_EMAIL_PATTERN.test(email)
}

export function studyInstructionProgressKey(email: string | undefined): string | null {
  const normalizedEmail = email?.trim().toLowerCase()
  return normalizedEmail ? `study-instructions:${normalizedEmail}` : null
}
