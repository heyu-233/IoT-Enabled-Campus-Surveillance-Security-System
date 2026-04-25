import type { Alert, Behavior, EdgeCommandResponse, OptionPoint, PagedResponse } from '@/types/domain'

const asRecord = (value: unknown): Record<string, unknown> => value && typeof value === 'object' ? (value as Record<string, unknown>) : {}
const asArray = <T>(value: unknown): T[] => Array.isArray(value) ? (value as T[]) : []
const apiBase = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

export const normalizeDistribution = (payload: unknown): OptionPoint[] => {
  const data = asRecord(payload)
  return asArray<OptionPoint>(data.items)
}

export const normalizeSeries = (payload: unknown): { labels: string[]; values: number[] } => {
  const data = asRecord(payload)
  const labels = asArray<string>(data.labels)
  const values = asArray<number>(data.values)
  return { labels, values: values.map((value) => Number(value)) }
}

export const normalizeHeatmap = (payload: unknown): OptionPoint[] => {
  const data = asRecord(payload)
  return asArray<OptionPoint>(data.items)
}

export const normalizeMessage = (payload: EdgeCommandResponse | string | unknown): string => {
  if (typeof payload === 'string') return payload
  const data = asRecord(payload)
  if (typeof data.message === 'string') return data.message
  return 'Command sent.'
}

export const normalizePaged = <T>(payload: unknown): PagedResponse<T> => {
  const data = asRecord(payload)
  return {
    items: asArray<T>(data.items),
    total: Number(data.total || 0),
    page: Number(data.page || 1),
    pageSize: Number(data.pageSize || 20),
  }
}

export const resolveMediaUrl = (value?: string | null): string => {
  if (!value) return ''
  if (/^https?:\/\//i.test(value)) return value
  if (value.startsWith('/images/') || value.startsWith('/results/')) return `${apiBase}${value}`
  return value
}

export const normalizeBehaviorMedia = <T extends Behavior>(behavior: T): T => ({
  ...behavior,
  imageUrl: resolveMediaUrl(behavior.imageUrl),
  originalImageUrl: resolveMediaUrl(behavior.originalImageUrl),
  processedImageUrl: resolveMediaUrl(behavior.processedImageUrl || behavior.imageUrl),
})

export const normalizeAlertMedia = <T extends Alert>(alert: T): T => ({
  ...alert,
  screenshot: resolveMediaUrl(alert.screenshot),
  originalImageUrl: resolveMediaUrl(alert.originalImageUrl),
  processedImageUrl: resolveMediaUrl(alert.processedImageUrl || alert.screenshot),
})
