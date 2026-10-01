import axios from 'axios'

export interface User { id: number; full_name: string; email: string; is_active: boolean; roles: string[] }
export interface AuthResponse { access_token: string; refresh_token: string; token_type: string; user: User }
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api' })
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
export default api
