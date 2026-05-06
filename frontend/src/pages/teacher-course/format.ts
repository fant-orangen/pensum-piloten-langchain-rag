import { format } from 'date-fns'
import { nb } from 'date-fns/locale'

export function formatCourseDate(dateStr: string): string {
  try {
    return format(new Date(dateStr), 'd. MMM yyyy', { locale: nb })
  } catch {
    return dateStr
  }
}
