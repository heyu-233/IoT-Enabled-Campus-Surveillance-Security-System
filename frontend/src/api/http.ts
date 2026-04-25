import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

export const http = axios.create({ baseURL, timeout: 10000 })

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('campus-sentinel-token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) localStorage.removeItem('campus-sentinel-token')
    return Promise.reject(error)
  },
)

