import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { cameraApi, edgeApi } from '@/api/services'
import { useUiStore } from '@/stores/ui'
import type { Camera } from '@/types/domain'

const defaultDraft = (): Camera => ({ name: '', deviceId: '', ipAddress: '', port: 1935, location: '', status: 'OFFLINE', streamUrl: '' })
const TEST_CAMERA_PATTERNS = [/test/i, /demo/i, /edge-camera-01/i, /camera1/i, /stream/i]

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms))

const getCameraScore = (camera: Camera) => {
  const haystack = [camera.name, camera.deviceId, camera.location, camera.streamUrl].filter(Boolean).join(' ')
  return TEST_CAMERA_PATTERNS.reduce((score, pattern, index) => score + (pattern.test(haystack) ? 10 - index : 0), 0)
}

const normalizeStatus = (isTestCamera: boolean, streamReady: boolean) => {
  if (!isTestCamera) return 'OFFLINE'
  if (streamReady) return 'ONLINE'
  return 'OFFLINE'
}

export const useCameraStore = defineStore('camera', () => {
  const rawCameras = ref<Camera[]>([])
  const selectedCameraId = ref<number | null>(null)
  const selectedStreamBaseUrl = ref('')
  const selectedStreamToken = ref(0)
  const streamPlaybackEnabled = ref(false)
  const loading = ref(false)
  const draft = ref<Camera>(defaultDraft())
  const streamStates = ref<Record<string, boolean>>({})
  const detectorStates = ref<Record<string, boolean>>({})
  const streamPending = ref(false)
  const detectorPending = ref(false)
  const playerConnected = ref(false)

  const testCameraId = computed<number | null>(() => {
    if (!rawCameras.value.length) return null
    const sorted = [...rawCameras.value].sort((left, right) => getCameraScore(right) - getCameraScore(left))
    return sorted[0]?.id ?? rawCameras.value[0]?.id ?? null
  })

  const streamCommandIssued = computed(() => {
    const testCamera = rawCameras.value.find((camera) => camera.id === testCameraId.value)
    const deviceId = testCamera?.deviceId?.trim() ?? ''
    return deviceId ? Boolean(streamStates.value[deviceId]) : false
  })

  const cameras = computed<Camera[]>(() =>
    rawCameras.value.map((camera) => ({
      ...camera,
      status: normalizeStatus(camera.id === testCameraId.value, playerConnected.value),
    })),
  )

  const selectedCamera = computed(() => cameras.value.find((camera) => camera.id === selectedCameraId.value) ?? null)
  const selectedDeviceId = computed(() => selectedCamera.value?.deviceId?.trim() ?? '')
  const selectedStreamUrl = computed(() => {
    if (!streamPlaybackEnabled.value || !selectedStreamBaseUrl.value) return ''
    const separator = selectedStreamBaseUrl.value.includes('?') ? '&' : '?'
    return `${selectedStreamBaseUrl.value}${separator}ts=${selectedStreamToken.value}`
  })
  const selectedStreamRunning = computed(() => playerConnected.value || streamCommandIssued.value)
  const selectedDetectionRunning = computed(() => {
    const deviceId = selectedDeviceId.value
    return deviceId ? Boolean(detectorStates.value[deviceId]) : false
  })
  const monitorLockedToTestCamera = computed(() => Boolean(testCameraId.value && selectedCameraId.value === testCameraId.value))

  const applyCameraSelection = async (preferredId?: number | null) => {
    const targetId = testCameraId.value ?? preferredId ?? rawCameras.value[0]?.id ?? null
    selectedCameraId.value = targetId
    if (!targetId) {
      selectedStreamBaseUrl.value = ''
      return
    }

    try {
      selectedStreamBaseUrl.value = await cameraApi.stream(targetId)
    } catch {
      const fallback = rawCameras.value.find((camera) => camera.id === targetId)
      selectedStreamBaseUrl.value = fallback?.streamUrl ?? ''
    }
  }

  const refreshStreamSession = () => {
    selectedStreamToken.value += 1
  }

  const loadCameras = async () => {
    loading.value = true
    try {
      rawCameras.value = await cameraApi.list()
      await applyCameraSelection(selectedCameraId.value)
    } finally {
      loading.value = false
    }
  }

  const selectCamera = async (id: number) => {
    if (testCameraId.value && id !== testCameraId.value) return
    playerConnected.value = false
    await applyCameraSelection(id)
    refreshStreamSession()
  }

  const refreshCamera = async (id: number) => {
    const updated = await cameraApi.refresh(id)
    rawCameras.value = rawCameras.value.map((camera) => (camera.id === id ? updated : camera))
    if (selectedCameraId.value === id) {
      playerConnected.value = false
      await applyCameraSelection(id)
      refreshStreamSession()
    }
  }

  const editCamera = (camera?: Camera | null) => {
    const source = camera ?? selectedCamera.value
    draft.value = source ? { ...source } : defaultDraft()
  }

  const saveCamera = async () => {
    const uiStore = useUiStore()
    if (draft.value.id) {
      const updated = await cameraApi.update(draft.value.id, draft.value)
      rawCameras.value = rawCameras.value.map((camera) => (camera.id === updated.id ? updated : camera))
    } else {
      const created = await cameraApi.create(draft.value)
      rawCameras.value = [created, ...rawCameras.value]
    }
    await applyCameraSelection(selectedCameraId.value)
    uiStore.pushToast('Changes saved.', 'success')
    draft.value = defaultDraft()
  }

  const removeCamera = async (id: number) => {
    const uiStore = useUiStore()
    await cameraApi.remove(id)
    rawCameras.value = rawCameras.value.filter((camera) => camera.id !== id)
    if (selectedCameraId.value === id) {
      playerConnected.value = false
      await applyCameraSelection(null)
      refreshStreamSession()
    }
    uiStore.pushToast('Deleted successfully.', 'success')
  }

  const softReloadStream = async (attempts = 6, intervalMs = 1200) => {
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      if (playerConnected.value) break
      refreshStreamSession()
      if (attempt < attempts - 1) await wait(intervalMs)
    }
  }

  const startStream = async () => {
    const uiStore = useUiStore()
    if (!selectedDeviceId.value || streamPending.value) return

    streamPending.value = true
    try {
      playerConnected.value = false
      await edgeApi.startStream(selectedDeviceId.value)
      streamStates.value = { ...streamStates.value, [selectedDeviceId.value]: true }
      streamPlaybackEnabled.value = true
      await applyCameraSelection(selectedCameraId.value)
      void softReloadStream()
      uiStore.pushToast('Stream started.', 'success')
    } finally {
      streamPending.value = false
    }
  }

  const stopStream = async () => {
    const uiStore = useUiStore()
    if (!selectedDeviceId.value || streamPending.value) return

    streamPending.value = true
    const previousBaseUrl = selectedStreamBaseUrl.value
    try {
      streamStates.value = { ...streamStates.value, [selectedDeviceId.value]: false }
      streamPlaybackEnabled.value = false
      playerConnected.value = false
      selectedStreamBaseUrl.value = ''
      refreshStreamSession()
      await edgeApi.stopStream(selectedDeviceId.value)
      uiStore.pushToast('Stream stopped.', 'success')
    } catch (error) {
      streamStates.value = { ...streamStates.value, [selectedDeviceId.value]: true }
      streamPlaybackEnabled.value = true
      selectedStreamBaseUrl.value = previousBaseUrl
      throw error
    } finally {
      streamPending.value = false
    }
  }

  const startDetection = async () => {
    const uiStore = useUiStore()
    if (!selectedDeviceId.value || detectorPending.value) return

    detectorPending.value = true
    try {
      await edgeApi.startDetector(selectedDeviceId.value)
      detectorStates.value = { ...detectorStates.value, [selectedDeviceId.value]: true }
      uiStore.pushToast('Detection started.', 'success')
    } finally {
      detectorPending.value = false
    }
  }

  const stopDetection = async () => {
    const uiStore = useUiStore()
    if (!selectedDeviceId.value || detectorPending.value) return

    detectorPending.value = true
    try {
      await edgeApi.stopDetector(selectedDeviceId.value)
      detectorStates.value = { ...detectorStates.value, [selectedDeviceId.value]: false }
      uiStore.pushToast('Detection stopped.', 'success')
    } finally {
      detectorPending.value = false
    }
  }

  const setStreamPresence = (connected: boolean) => {
    playerConnected.value = connected
  }

  return {
    cameras,
    selectedCameraId,
    selectedCamera,
    selectedStreamUrl,
    selectedStreamToken,
    loading,
    draft,
    streamPending,
    detectorPending,
    selectedStreamRunning,
    selectedDetectionRunning,
    testCameraId,
    monitorLockedToTestCamera,
    loadCameras,
    selectCamera,
    refreshCamera,
    editCamera,
    saveCamera,
    removeCamera,
    startStream,
    stopStream,
    startDetection,
    stopDetection,
    setStreamPresence,
  }
})
