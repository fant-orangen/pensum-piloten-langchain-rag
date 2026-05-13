import { useEffect } from 'react'

const APP_TITLE = 'PensumPiloten'

export function usePageTitle(title?: string) {
  useEffect(() => {
    document.title = title ? `${title} - ${APP_TITLE}` : APP_TITLE
  }, [title])
}
