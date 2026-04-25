import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { normalizeDistribution, normalizeHeatmap, normalizeSeries } from '@/api/adapters'
import { analyticsApi } from '@/api/services'
import type { OptionPoint } from '@/types/domain'

export const useAnalyticsStore = defineStore('analytics', () => {
  const distribution = ref<OptionPoint[]>([])
  const daily = ref<{ labels: string[]; values: number[] }>({ labels: [], values: [] })
  const heatmap = ref<OptionPoint[]>([])
  const typeDetails = ref<{ labels: string[]; values: number[] }>({ labels: [], values: [] })
  const selectedType = ref('')
  const loading = ref(false)
  const totalEvents = computed(() => distribution.value.reduce((sum, item) => sum + item.value, 0))
  const topType = computed(() => distribution.value[0]?.name || '')
  const topArea = computed(() => heatmap.value[0]?.name || '')

  const hasData = computed(() => distribution.value.length > 0 || daily.value.values.length > 0 || heatmap.value.length > 0)

  const loadAnalytics = async () => {
    loading.value = true
    try {
      const [distributionPayload, dailyPayload, heatmapPayload] = await Promise.all([
        analyticsApi.distribution(), analyticsApi.dailyAlerts(), analyticsApi.heatmap(),
      ])
      distribution.value = normalizeDistribution(distributionPayload)
      daily.value = normalizeSeries(dailyPayload)
      heatmap.value = normalizeHeatmap(heatmapPayload)
      selectedType.value = distribution.value[0]?.name || 'intrusion'
      const detailPayload = await analyticsApi.typeDetails(selectedType.value)
      typeDetails.value = normalizeSeries(detailPayload)
    } finally { loading.value = false }
  }

  const loadTypeDetails = async (type: string) => {
    selectedType.value = type
    const payload = await analyticsApi.typeDetails(type)
    typeDetails.value = normalizeSeries(payload)
  }

  return { distribution, daily, heatmap, typeDetails, selectedType, loading, hasData, totalEvents, topType, topArea, loadAnalytics, loadTypeDetails }
})
