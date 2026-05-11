import { format } from 'date-fns'
import { nb } from 'date-fns/locale'

/** Format an ISO timestamp for Norwegian conversation lists and message metadata. */
export function formatConversationDate(dateStr: string): string {
  try {
    return format(new Date(dateStr), 'd. MMM yyyy', { locale: nb })
  } catch {
    return dateStr
  }
}
