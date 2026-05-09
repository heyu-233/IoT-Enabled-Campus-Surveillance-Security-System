import { http } from './http'
import type { Alert, AlertProcessRequest, AlertSetting, AuthResponse, Behavior, Camera, EdgeCommandResponse, LoginRequest, PagedResponse, RegisterRequest, UserDto } from '@/types/domain'

export const authApi = {
  login: async (payload: LoginRequest) => (await http.post<AuthResponse>('/auth/login', payload)).data,
  register: async (payload: RegisterRequest) => (await http.post<AuthResponse>('/auth/register', payload)).data,
  me: async () => (await http.get<UserDto>('/auth/me')).data,
  logout: async () => http.post('/auth/logout'),
}

export const cameraApi = {
  list: async (params?: Record<string, unknown>) => (await http.get<Camera[]>('/cameras', { params })).data,
  detail: async (id: number) => (await http.get<Camera>(`/cameras/${id}`)).data,
  stream: async (id: number) => (await http.get<string>(`/cameras/${id}/stream`)).data,
  refresh: async (id: number) => (await http.post<Camera>(`/cameras/${id}/refresh`)).data,
  create: async (payload: Camera) => (await http.post<Camera>('/cameras', payload)).data,
  update: async (id: number, payload: Camera) => (await http.put<Camera>(`/cameras/${id}`, payload)).data,
  remove: async (id: number) => http.delete(`/cameras/${id}`),
}

export const alertApi = {
  list: async (params?: Record<string, unknown>) => (await http.get<PagedResponse<Alert>>('/alerts', { params })).data,
  search: async (params?: Record<string, unknown>) => (await http.get<PagedResponse<Alert>>('/alerts/search', { params })).data,
  detail: async (id: number) => (await http.get<Alert>(`/alerts/${id}`)).data,
  process: async (id: number, payload: AlertProcessRequest) => (await http.post<Alert>(`/alerts/${id}/process`, payload)).data,
  remove: async (id: number) => http.delete(`/alerts/${id}`),
}

export const behaviorApi = {
  list: async (params?: Record<string, unknown>) => (await http.get<Behavior[]>('/behaviors', { params })).data,
  remove: async (id: number) => http.delete(`/behaviors/${id}`),
}

export const analyticsApi = {
  distribution: async (params?: Record<string, unknown>) => (await http.get<Record<string, unknown>>('/analytics/type-distribution', { params })).data,
  dailyAlerts: async (params?: Record<string, unknown>) => (await http.get<Record<string, unknown>>('/analytics/daily-alerts', { params })).data,
  heatmap: async (params?: Record<string, unknown>) => (await http.get<Record<string, unknown>>('/analytics/area-heatmap', { params })).data,
  typeDetails: async (type: string, params?: Record<string, unknown>) => (await http.get<Record<string, unknown>>(`/analytics/types/${type}`, { params })).data,
}

export const configApi = {
  getAlertSettings: async () => (await http.get<AlertSetting>('/config/alert-settings')).data,
  updateAlertSettings: async (payload: AlertSetting) => (await http.put<AlertSetting>('/config/alert-settings', payload)).data,
}

export const edgeApi = {
  startStream: async (deviceId: string) => (await http.post<EdgeCommandResponse>('/edge/stream/start', null, { params: { deviceId } })).data,
  stopStream: async (deviceId: string) => (await http.post<EdgeCommandResponse>('/edge/stream/stop', null, { params: { deviceId } })).data,
  startDetector: async (deviceId: string, config?: string) => (await http.post<EdgeCommandResponse>('/host/detector/start', config ?? null, { params: { deviceId }, headers: config ? { 'Content-Type': 'application/json' } : undefined })).data,
  stopDetector: async (deviceId: string) => (await http.post<EdgeCommandResponse>('/host/detector/stop', null, { params: { deviceId } })).data,
  detectorStatus: async () => (await http.post<EdgeCommandResponse>('/host/detector/status')).data,
  buzzerOn: async (deviceId: string) => (await http.post<EdgeCommandResponse>('/edge/buzzer/on', null, { params: { deviceId } })).data,
  buzzerOff: async (deviceId: string) => (await http.post<EdgeCommandResponse>('/edge/buzzer/off', null, { params: { deviceId } })).data,
  ledBlink: async (deviceId: string) => (await http.post<EdgeCommandResponse>('/edge/led/blink', null, { params: { deviceId } })).data,
  detectorConfig: async (deviceId: string, config: string) => (await http.post<EdgeCommandResponse>('/host/detector/config', config, { params: { deviceId }, headers: { 'Content-Type': 'application/json' } })).data,
}
