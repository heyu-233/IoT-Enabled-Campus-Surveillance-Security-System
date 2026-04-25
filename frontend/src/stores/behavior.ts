import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { normalizeBehaviorMedia } from '@/api/adapters'
import { behaviorApi } from '@/api/services'
import { useUiStore } from '@/stores/ui'
import type { Behavior } from '@/types/domain'

export const useBehaviorStore = defineStore('behavior', () => {
  const behaviors = ref<Behavior[]>([])
  const selectedBehaviorId = ref<number | null>(null)
  const liveConnected = ref(false)
  let eventSource: EventSource | null = null

  const selectedBehavior = computed(() => behaviors.value.find((behavior) => behavior.id === selectedBehaviorId.value) ?? null)

  const loadBehaviors = async () => {
    behaviors.value = (await behaviorApi.list()).map((behavior) => normalizeBehaviorMedia(behavior))
    if (!selectedBehaviorId.value && behaviors.value[0]?.id) selectedBehaviorId.value = behaviors.value[0].id ?? null
  }

  const connect = () => {
    if (eventSource) return
    const base = import.meta.env.VITE_API_BASE_URL || '/api'
    eventSource = new EventSource(`${base}/behaviors/stream`)
    eventSource.onopen = () => { liveConnected.value = true }
    eventSource.onmessage = (event) => {
      try {
        const payload = normalizeBehaviorMedia(JSON.parse(event.data) as Behavior)
        behaviors.value = [payload, ...behaviors.value.filter((item) => item.id !== payload.id)].slice(0, 40)
      } catch { }
    }
    eventSource.onerror = () => {
      liveConnected.value = false
      eventSource?.close()
      eventSource = null
    }
  }

  const disconnect = () => {
    liveConnected.value = false
    eventSource?.close()
    eventSource = null
  }

  const removeBehavior = async (id: number) => {
    const uiStore = useUiStore()
    await behaviorApi.remove(id)
    behaviors.value = behaviors.value.filter((behavior) => behavior.id !== id)
    uiStore.pushToast('Deleted successfully.', 'success')
  }

  return { behaviors, selectedBehaviorId, selectedBehavior, liveConnected, loadBehaviors, connect, disconnect, removeBehavior }
})

