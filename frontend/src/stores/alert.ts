import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { normalizeAlertMedia } from '@/api/adapters'
import { alertApi } from '@/api/services'
import { useUiStore } from '@/stores/ui'
import type { Alert, AlertProcessRequest } from '@/types/domain'

const getAlertTimestamp = (alert: Alert) => {
  const value = alert.createdAt || alert.processedAt || alert.behaviorOccurredAt
  return value ? new Date(value).getTime() : 0
}

const hasAlertImage = (alert: Alert) => Boolean(
  alert.processedImageUrl || alert.originalImageUrl || alert.screenshot,
)

const sortAlertsForShowcase = (items: Alert[]) => [...items].sort((left, right) => {
  const imageDelta = Number(hasAlertImage(right)) - Number(hasAlertImage(left))
  if (imageDelta !== 0) return imageDelta
  return getAlertTimestamp(right) - getAlertTimestamp(left)
})

export const useAlertStore = defineStore('alert', () => {
  const alerts = ref<Alert[]>([])
  const search = ref('')
  const status = ref('')
  const from = ref('')
  const to = ref('')
  const selectedAlertId = ref<number | null>(null)
  const loading = ref(false)
  const page = ref(1)
  const pageSize = ref(20)
  const total = ref(0)

  const selectedAlert = computed(() => alerts.value.find((alert) => alert.id === selectedAlertId.value) ?? null)

  const query = computed(() => ({
    page: page.value,
    pageSize: pageSize.value,
    ...(search.value ? { keyword: search.value } : {}),
    ...(status.value ? { status: status.value } : {}),
    ...(from.value ? { from: from.value } : {}),
    ...(to.value ? { to: to.value } : {}),
  }))

  const loadAlerts = async () => {
    loading.value = true
    try {
      const response = search.value || status.value || from.value || to.value
        ? await alertApi.search(query.value)
        : await alertApi.list(query.value)
      alerts.value = sortAlertsForShowcase(response.items.map((alert) => normalizeAlertMedia(alert)))
      total.value = response.total
      page.value = response.page
      pageSize.value = response.pageSize
      if ((!selectedAlertId.value || !alerts.value.some((alert) => alert.id === selectedAlertId.value)) && alerts.value[0]?.id) {
        selectedAlertId.value = alerts.value[0].id ?? null
      }
    } finally {
      loading.value = false
    }
  }

  const selectAlert = async (id: number) => {
    selectedAlertId.value = id
    const detail = normalizeAlertMedia(await alertApi.detail(id))
    alerts.value = sortAlertsForShowcase(alerts.value.map((alert) => alert.id === id ? { ...alert, ...detail } : alert))
  }

  const processAlert = async (id: number, payload: AlertProcessRequest) => {
    const uiStore = useUiStore()
    const updated = normalizeAlertMedia(await alertApi.process(id, payload))
    alerts.value = sortAlertsForShowcase(alerts.value.map((alert) => alert.id === id ? updated : alert))
    uiStore.pushToast(`Alert updated to ${updated.status || payload.status}.`, 'success')
  }

  const removeAlert = async (id: number) => {
    const uiStore = useUiStore()
    await alertApi.remove(id)
    alerts.value = alerts.value.filter((alert) => alert.id !== id)
    total.value = Math.max(0, total.value - 1)
    if (selectedAlertId.value === id) {
      selectedAlertId.value = alerts.value[0]?.id ?? null
    }
    uiStore.pushToast('Alert deleted.', 'success')
  }

  const fetchLatestOpenAlerts = async (size = 5) => {
    const response = await alertApi.list({ page: 1, pageSize: size, status: 'UNPROCESSED' })
    return sortAlertsForShowcase(response.items.map((alert) => normalizeAlertMedia(alert)))
  }

  return {
    alerts,
    search,
    status,
    from,
    to,
    loading,
    selectedAlert,
    selectedAlertId,
    page,
    pageSize,
    total,
    loadAlerts,
    selectAlert,
    processAlert,
    removeAlert,
    fetchLatestOpenAlerts,
  }
})
