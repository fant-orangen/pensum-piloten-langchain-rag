import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/auth': 'http://localhost:8000',
      '/courses': 'http://localhost:8000',
      '/conversations': 'http://localhost:8000',
      '/admin': 'http://localhost:8000',
      '/preferences': 'http://localhost:8000',
    },
  },
})
