export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'
export const USE_MOCK: boolean = String(import.meta.env.VITE_USE_MOCK ?? 'false').toLowerCase() === 'true'

export function apiUrl(path: string): string {
  if (!path.startsWith('/')) {
    path = '/' + path
  }
  return `${API_BASE_URL}${path}`
}
