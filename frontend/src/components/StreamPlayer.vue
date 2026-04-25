<script setup lang="ts">
import flvjs from 'flv.js'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{ src?: string; reloadToken?: number; active?: boolean }>()
const emit = defineEmits<{ (event: 'stream-ready'): void; (event: 'stream-lost'): void }>()
const { t } = useI18n()
const videoRef = ref<HTMLVideoElement | null>(null)
const isConnecting = ref(false)
const retryCount = ref(0)
let player: flvjs.Player | null = null
let retryTimer: number | null = null

const clearRetryTimer = () => {
  if (retryTimer !== null) {
    window.clearTimeout(retryTimer)
    retryTimer = null
  }
}

const destroyPlayer = () => {
  clearRetryTimer()
  player?.pause()
  player?.unload()
  player?.detachMediaElement()
  player?.destroy()
  player = null
}

const queueReconnect = () => {
  if (!props.active || !props.src || retryTimer !== null || retryCount.value >= 7) return
  retryCount.value += 1
  retryTimer = window.setTimeout(() => {
    retryTimer = null
    mountPlayer()
  }, 900)
}

const handleReady = () => {
  if (!props.active) return
  clearRetryTimer()
  retryCount.value = 0
  isConnecting.value = false
  emit('stream-ready')
}

const handleFailure = () => {
  if (!props.active) return
  isConnecting.value = true
  emit('stream-lost')
  queueReconnect()
}

const bindVideoEvents = () => {
  const video = videoRef.value
  if (!video) return
  video.onloadeddata = handleReady
  video.onplaying = handleReady
  video.onstalled = handleFailure
  video.onwaiting = () => {
    isConnecting.value = true
  }
  video.onerror = handleFailure
}

const mountPlayer = () => {
  destroyPlayer()
  if (!props.active || !props.src || !videoRef.value || !flvjs.isSupported()) {
    isConnecting.value = false
    return
  }

  isConnecting.value = true
  bindVideoEvents()
  player = flvjs.createPlayer(
    {
      type: 'flv',
      url: props.src,
      isLive: true,
      hasAudio: false,
      hasVideo: true,
    },
    {
      enableStashBuffer: false,
      stashInitialSize: 32,
      autoCleanupSourceBuffer: true,
      autoCleanupMaxBackwardDuration: 6,
      autoCleanupMinBackwardDuration: 2,
      lazyLoad: false,
      deferLoadAfterSourceOpen: false,
      reuseRedirectedURL: true,
    },
  )

  player.on(flvjs.Events.ERROR, handleFailure)
  player.on(flvjs.Events.METADATA_ARRIVED, handleReady)
  player.attachMediaElement(videoRef.value)
  player.load()

  const playResult = player.play()
  if (playResult && typeof playResult.then === 'function') {
    playResult.catch(() => {
      handleFailure()
    })
  }
}

onMounted(mountPlayer)
watch(() => [props.src, props.reloadToken], () => {
  retryCount.value = 0
  mountPlayer()
})
watch(() => props.active, (active) => {
  if (!active) {
    isConnecting.value = false
    destroyPlayer()
    emit('stream-lost')
    return
  }
  retryCount.value = 0
  mountPlayer()
})
onBeforeUnmount(destroyPlayer)
</script>

<template>
  <div class="stream-player surface-card" :class="{ 'is-connecting': isConnecting }">
    <video v-if="src" ref="videoRef" controls muted playsinline />
    <div v-if="src && isConnecting" class="stream-player__overlay">
      <span class="stream-player__signal"></span>
      <strong>Syncing live feed...</strong>
      <p>Waiting for the test camera to publish the latest frame.</p>
    </div>
    <div v-else-if="!src" class="stream-player__fallback">
      <h4>{{ t('app.streamUnavailable') }}</h4>
      <p>{{ t('monitoring.emptyStream') }}</p>
    </div>
  </div>
</template>
