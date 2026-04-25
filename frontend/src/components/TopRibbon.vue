<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAlertStore } from '@/stores/alert'
import { useBehaviorStore } from '@/stores/behavior'
import { useCameraStore } from '@/stores/camera'
const { t } = useI18n()
const cameraStore = useCameraStore()
const alertStore = useAlertStore()
const behaviorStore = useBehaviorStore()
const onlineCount = computed(() => cameraStore.cameras.filter((camera) => camera.status?.toLowerCase() === 'online').length)
const activeAlerts = computed(() => alertStore.alerts.filter((alert) => alert.status?.toLowerCase() !== 'processed').length)
</script>

<template>
  <section class="top-ribbon">
    <div><span>{{ t('overview.liveRibbon') }}</span><strong>{{ onlineCount }}/{{ cameraStore.cameras.length || 0 }} {{ t('app.online') }}</strong></div>
    <div><span>{{ t('alerts.activeQueue') }}</span><strong>{{ activeAlerts }}</strong></div>
    <div><span>{{ t('behaviors.liveStream') }}</span><strong>{{ behaviorStore.liveConnected ? t('behaviors.subscribe') : t('behaviors.disconnected') }}</strong></div>
  </section>
</template>

