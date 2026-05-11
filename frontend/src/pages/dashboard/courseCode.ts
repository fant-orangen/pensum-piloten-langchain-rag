/** Derive a compact uppercase course code suggestion from a course name. */
export function deriveCourseCode(name: string): string {
  return name.toUpperCase().replace(/\s+/g, '_').slice(0, 20)
}
