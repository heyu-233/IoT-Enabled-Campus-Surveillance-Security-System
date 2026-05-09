import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { cameraApi, edgeApi } from '@/api/services'
import { useUiStore } from '@/stores/ui'
import type { Camera } from '@/types/domain'

const defaultDraft = (): Camera => ({ name: '', deviceId: '', ipAddress: '', port: 1935, location: '', status: 'OFFLINE', streamUrl: '' })
const TEST_CAMERA_PATTERNS = [/test/i, /demo/i, /edge-camera-01/i, /camera1/i, /stream/i]
const FIRE_DEMO_MP4_DISPLAY_URL = import.meta.env.VITE_FIRE_DEMO_MP4_DISPLAY_URL || '/demo-videos/0_Wildfire_Field_Fire_3840x2160.mp4'
const FIRE_DEMO_MP4_DETECTOR_SOURCE = import.meta.env.VITE_FIRE_DEMO_MP4_DETECTOR_SOURCE || 'D:/codex_project/Iot_securit_system/video/0_Wildfire_Field_Fire_3840x2160.mp4'
const FIGHT_DEMO_MP4_DISPLAY_URL = import.meta.env.VITE_FIGHT_DEMO_MP4_DISPLAY_URL || '/demo-videos/fight_demo_sample_2.mp4'
const FIGHT_DEMO_MP4_DETECTOR_SOURCE = import.meta.env.VITE_FIGHT_DEMO_MP4_DETECTOR_SOURCE || 'D:/codex_project/Iot_securit_system/video/fight_demo_sample_2.mp4'
const FLV_BASE_URL = import.meta.env.VITE_FLV_BASE_URL || 'http://127.0.0.1:8080/live'
const EDGE_RTMP_DETECTOR_SOURCE = import.meta.env.VITE_EDGE_RTMP_DETECTOR_SOURCE || 'rtmp://127.0.0.1:1935/myapp/stream'

const demoSourceOverrides: Record<string, Partial<Camera> & { detectorSource?: string }> = {
  'legacy-camera-1': {
    name: 'Camera 1 - Laptop Webcam',
    location: 'Local Browser Camera',
    status: 'ONLINE',
    streamUrl: 'webcam://local',
    detectorSource: '0',
  },
  'legacy-camera-2': {
    name: 'Camera 2 - MP4 Demo Feed',
    location: 'Prepared Demo Video',
    status: 'ONLINE',
    streamUrl: FIRE_DEMO_MP4_DISPLAY_URL,
    detectorSource: FIRE_DEMO_MP4_DETECTOR_SOURCE,
  },
  'legacy-camera-3': {
    name: 'Camera 3 - Fight MP4 Demo',
    location: 'Prepared Fight Demo Video',
    status: 'ONLINE',
    streamUrl: FIGHT_DEMO_MP4_DISPLAY_URL,
    detectorSource: FIGHT_DEMO_MP4_DETECTOR_SOURCE,
  },
  'edge-camera-02': {
    name: 'Camera 2 - Laptop Webcam',
    location: 'Local Browser Camera',
    status: 'ONLINE',
    streamUrl: 'webcam://local',
    detectorSource: '0',
  },
  'edge-camera-03': {
    name: 'Camera 3 - MP4 Demo Feed',
    location: 'Prepared Demo Video',
    status: 'ONLINE',
    streamUrl: FIRE_DEMO_MP4_DISPLAY_URL,
    detectorSource: FIRE_DEMO_MP4_DETECTOR_SOURCE,
  },
}

const detectorSourceOverrides: Record<string, string> = {
  'legacy-camera-1': '0',
  'legacy-camera-2': FIRE_DEMO_MP4_DETECTOR_SOURCE,
  'legacy-camera-3': FIGHT_DEMO_MP4_DETECTOR_SOURCE,
  'edge-camera-01': EDGE_RTMP_DETECTOR_SOURCE,
  'edge-camera-02': '0',
  'edge-camera-03': FIRE_DEMO_MP4_DETECTOR_SOURCE,
}

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms))

const isDemoPlaybackSource = (source?: string) => Boolean(source?.startsWith('webcam://') || source?.includes('.mp4'))

const convertRtmpToHttpFlv = (source?: string) => {
  if (!source?.startsWith('rtmp://')) return source ?? ''

  try {
    const rtmpUrl = new URL(source)
    const parts = rtmpUrl.pathname.split('/').filter(Boolean)
    const app = parts[0] || 'myapp'
    const stream = parts.slice(1).join('/') || 'stream'
    const flvUrl = new URL(FLV_BASE_URL)
    flvUrl.searchParams.set('app', app)
    flvUrl.searchParams.set('stream', stream)
    return flvUrl.toString()
  } catch {
    return source
  }
}

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
  const loading = ref(false)
  const draft = ref<Camera>(defaultDraft())
  const streamStates = ref<Record<string, boolean>>({})
  const streamBaseUrls = ref<Record<string, string>>({})
  const streamTokens = ref<Record<string, number>>({})
  const playerConnectedStates = ref<Record<string, boolean>>({})
  const detectorStates = ref<Record<string, boolean>>({})
  const streamPending = ref(false)
  const detectorPending = ref(false)

  const applyDemoSource = (camera: Camera): Camera => {
    const override = camera.deviceId ? demoSourceOverrides[camera.deviceId] : null
    return override ? { ...camera, ...override } : camera
  }

  const resolveDisplayStreamUrl = async (camera: Camera) => {
    const demoCamera = applyDemoSource(camera)
    if (demoCamera.deviceId && demoSourceOverrides[demoCamera.deviceId]) return demoCamera.streamUrl ?? ''
    try {
      return convertRtmpToHttpFlv(await cameraApi.stream(camera.id!))
    } catch {
      return convertRtmpToHttpFlv(demoCamera.streamUrl)
    }
  }

  const selectedDetectorSource = computed(() => {
    const camera = selectedCamera.value
    if (!camera?.deviceId) return ''
    const override = detectorSourceOverrides[camera.deviceId] ?? demoSourceOverrides[camera.deviceId]?.detectorSource
    if (override) return override
    if (camera.streamUrl?.startsWith('webcam://')) return '0'
    return camera.streamUrl || 'rtmp://127.0.0.1/myapp/stream'
  })

  const testCameraId = computed<number | null>(() => {
    if (!rawCameras.value.length) return null
    const sorted = [...rawCameras.value].sort((left, right) => getCameraScore(right) - getCameraScore(left))
    return sorted[0]?.id ?? rawCameras.value[0]?.id ?? null
  })

  const cameras = computed<Camera[]>(() =>
    rawCameras.value.map((camera) => {
      const demoCamera = applyDemoSource(camera)
      return {
        ...demoCamera,
        status: demoCamera.deviceId && demoSourceOverrides[demoCamera.deviceId]
          ? demoCamera.status
          : normalizeStatus(camera.id === testCameraId.value, Boolean(playerConnectedStates.value[demoCamera.deviceId ?? ''])),
      }
    }),
  )

  const selectedCamera = computed(() => cameras.value.find((camera) => camera.id === selectedCameraId.value) ?? null)
  const selectedDeviceId = computed(() => selectedCamera.value?.deviceId?.trim() ?? '')
  const selectedStreamCommandIssued = computed(() => {
    const deviceId = selectedDeviceId.value
    return deviceId ? Boolean(streamStates.value[deviceId]) : false
  })
  const selectedStreamBaseUrl = computed(() => {
    const deviceId = selectedDeviceId.value
    return deviceId ? streamBaseUrls.value[deviceId] ?? '' : ''
  })
  const selectedStreamToken = computed(() => {
    const deviceId = selectedDeviceId.value
    return deviceId ? streamTokens.value[deviceId] ?? 0 : 0
  })
  const selectedPlayerConnected = computed(() => {
    const deviceId = selectedDeviceId.value
    return deviceId ? Boolean(playerConnectedStates.value[deviceId]) : false
  })
  const selectedStreamUrl = computed(() => {
    if (!selectedStreamCommandIssued.value || !selectedStreamBaseUrl.value) return ''
    const separator = selectedStreamBaseUrl.value.includes('?') ? '&' : '?'
    return `${selectedStreamBaseUrl.value}${separator}ts=${selectedStreamToken.value}`
  })
  const selectedStreamRunning = computed(() => selectedPlayerConnected.value || selectedStreamCommandIssued.value)
  const selectedDetectionRunning = computed(() => {
    const deviceId = selectedDeviceId.value
    return deviceId ? Boolean(detectorStates.value[deviceId]) : false
  })
  const monitorLockedToTestCamera = computed(() => Boolean(testCameraId.value && selectedCameraId.value === testCameraId.value))

  const applyCameraSelection = async (preferredId?: number | null) => {
    const targetId = preferredId ?? testCameraId.value ?? rawCameras.value[0]?.id ?? null
    selectedCameraId.value = targetId
    if (!targetId) return

    const fallback = rawCameras.value.find((camera) => camera.id === targetId)
    if (!fallback?.deviceId) return
    const deviceId = fallback.deviceId.trim()
    streamBaseUrls.value = { ...streamBaseUrls.value, [deviceId]: await resolveDisplayStreamUrl(fallback) }
  }

  const refreshStreamSession = (targetDeviceId?: string) => {
    const deviceId = targetDeviceId ?? selectedDeviceId.value
    if (!deviceId) return
    streamTokens.value = { ...streamTokens.value, [deviceId]: (streamTokens.value[deviceId] ?? 0) + 1 }
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
    await applyCameraSelection(id)
    refreshStreamSession()
  }

  const refreshCamera = async (id: number) => {
    const updated = await cameraApi.refresh(id)
    rawCameras.value = rawCameras.value.map((camera) => (camera.id === id ? updated : camera))
    if (selectedCameraId.value === id) {
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
      await applyCameraSelection(null)
      refreshStreamSession()
    }
    uiStore.pushToast('Deleted successfully.', 'success')
  }

  const softReloadStream = async (targetDeviceId = selectedDeviceId.value, attempts = 6, intervalMs = 1200) => {
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      if (targetDeviceId && playerConnectedStates.value[targetDeviceId]) break
      refreshStreamSession(targetDeviceId)
      if (attempt < attempts - 1) await wait(intervalMs)
    }
  }

  const startStream = async () => {
    const uiStore = useUiStore()
    if (!selectedDeviceId.value || streamPending.value) return

    const deviceId = selectedDeviceId.value
    const camera = selectedCamera.value
    streamPending.value = true
    try {
      playerConnectedStates.value = { ...playerConnectedStates.value, [deviceId]: false }
      const demoSource = isDemoPlaybackSource(camera?.streamUrl)
      if (!demoSource) {
        await edgeApi.startStream(deviceId)
      }
      streamStates.value = { ...streamStates.value, [deviceId]: true }
      await applyCameraSelection(camera?.id ?? selectedCameraId.value)
      refreshStreamSession(deviceId)
      void softReloadStream(deviceId)
      uiStore.pushToast('Stream started.', 'success')
    } finally {
      streamPending.value = false
    }
  }

  const stopStream = async () => {
    const uiStore = useUiStore()
    if (!selectedDeviceId.value || streamPending.value) return

    streamPending.value = true
    const deviceId = selectedDeviceId.value
    const camera = selectedCamera.value
    const previousBaseUrl = streamBaseUrls.value[deviceId] ?? ''
    try {
      streamStates.value = { ...streamStates.value, [deviceId]: false }
      playerConnectedStates.value = { ...playerConnectedStates.value, [deviceId]: false }
      streamBaseUrls.value = { ...streamBaseUrls.value, [deviceId]: '' }
      refreshStreamSession(deviceId)
      const demoSource = isDemoPlaybackSource(camera?.streamUrl)
      if (!demoSource) {
        await edgeApi.stopStream(deviceId)
      }
      uiStore.pushToast('Stream stopped.', 'success')
    } catch (error) {
      streamStates.value = { ...streamStates.value, [deviceId]: true }
      streamBaseUrls.value = { ...streamBaseUrls.value, [deviceId]: previousBaseUrl }
      throw error
    } finally {
      streamPending.value = false
    }
  }

  const startDetection = async () => {
    const uiStore = useUiStore()
    if (!selectedDeviceId.value || detectorPending.value) return

    const deviceId = selectedDeviceId.value
    const detectorSource = selectedDetectorSource.value
    detectorPending.value = true
    try {
      const detectorConfig = detectorSource ? JSON.stringify({
        device_id: deviceId,
        rtmp_url: detectorSource,
        detect_fps: 5,
      }) : undefined
      if (detectorSource) {
        const configResponse = await edgeApi.detectorConfig(deviceId, detectorConfig!)
        if (!configResponse.success) throw new Error(configResponse.message || 'Detector config failed.')
      }
      const startResponse = await edgeApi.startDetector(deviceId, detectorConfig)
      if (!startResponse.success) throw new Error(startResponse.message || 'Detector start failed.')
      detectorStates.value = { ...detectorStates.value, [deviceId]: true }
      uiStore.pushToast('Detection started.', 'success')
    } finally {
      detectorPending.value = false
    }
  }

  const stopDetection = async () => {
    const uiStore = useUiStore()
    if (!selectedDeviceId.value || detectorPending.value) return

    const deviceId = selectedDeviceId.value
    detectorPending.value = true
    try {
      const stopResponse = await edgeApi.stopDetector(deviceId)
      if (!stopResponse.success) throw new Error(stopResponse.message || 'Detector stop failed.')
      detectorStates.value = { ...detectorStates.value, [deviceId]: false }
      uiStore.pushToast('Detection stopped.', 'success')
    } finally {
      detectorPending.value = false
    }
  }

  const triggerAlarm = async () => {
    const deviceId = selectedDeviceId.value
    if (!deviceId) return
    const uiStore = useUiStore()
    const response = await edgeApi.buzzerOn(deviceId)
    uiStore.pushToast(response.success ? 'Alarm triggered.' : 'Alarm failed.', response.success ? 'success' : 'danger')
  }

  const lightAlsValue = ref(0)
  const lightLevel = ref(0)
  const lightConnected = ref(false)
  let lightEventSource: EventSource | null = null

  const lightLevelLabel = computed(() => {
    if (lightLevel.value === 2) return 'very-dark'
    if (lightLevel.value === 1) return 'slightly-dark'
    if (lightLevel.value === -1) return 'slightly-bright'
    if (lightLevel.value === -2) return 'very-bright'
    return 'normal'
  })

  const connectLightStream = () => {
    if (lightEventSource) return
    const base = import.meta.env.VITE_API_BASE_URL || '/api'
    lightEventSource = new EventSource(`${base}/behaviors/light/stream`)
    lightEventSource.onopen = () => { lightConnected.value = true }
    lightEventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        lightAlsValue.value = payload.alsValue ?? 0
        lightLevel.value = payload.level ?? 0
      } catch { /* ignore parse errors */ }
    }
    lightEventSource.onerror = () => {
      lightConnected.value = false
      lightEventSource?.close()
      lightEventSource = null
    }
  }

  const disconnectLightStream = () => {
    lightConnected.value = false
    lightEventSource?.close()
    lightEventSource = null
  }

  const setStreamPresence = (connected: boolean) => {
    const deviceId = selectedDeviceId.value
    if (!deviceId) return
    playerConnectedStates.value = { ...playerConnectedStates.value, [deviceId]: connected }
  }

  return {
    cameras,
    selectedCameraId,
    selectedCamera,
    selectedDeviceId,
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
    triggerAlarm,
    setStreamPresence,
    lightAlsValue,
    lightLevel,
    lightConnected,
    lightLevelLabel,
    connectLightStream,
    disconnectLightStream,
  }
})
