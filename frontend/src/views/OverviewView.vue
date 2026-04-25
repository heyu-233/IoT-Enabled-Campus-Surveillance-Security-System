<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import EmptyState from '@/components/EmptyState.vue'
import InfoPanel from '@/components/InfoPanel.vue'
import MetricPanel from '@/components/MetricPanel.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useAlertStore } from '@/stores/alert'
import { useAnalyticsStore } from '@/stores/analytics'
import { useBehaviorStore } from '@/stores/behavior'
import { useCameraStore } from '@/stores/camera'
const { t } = useI18n()
const cameraStore = useCameraStore(); const alertStore = useAlertStore(); const behaviorStore = useBehaviorStore(); const analyticsStore = useAnalyticsStore()
onMounted(() => { analyticsStore.loadAnalytics().catch(() => undefined); alertStore.loadAlerts().catch(() => undefined) })
const heroMetrics = computed(() => [
  { label: t('overview.systemHealth'), value: `${cameraStore.cameras.filter((camera) => camera.status?.toLowerCase() === 'online').length}/${cameraStore.cameras.length || 0}` },
  { label: t('alerts.activeQueue'), value: alertStore.alerts.filter((alert) => alert.status?.toLowerCase() !== 'processed').length, tone: 'warning' as const },
  { label: t('behaviors.liveStream'), value: behaviorStore.liveConnected ? 'SSE ON' : 'SSE OFF', tone: behaviorStore.liveConnected ? ('good' as const) : ('warning' as const) },
])
</script>

<template>
  <div class="view-grid">
    <MetricPanel :eyebrow="t('overview.title')" :title="t('overview.headline')" :summary="t('overview.quickActionsBody')" :metrics="heroMetrics" class="view-grid__hero" />

    <InfoPanel :title="t('overview.latestAlerts')" :subtitle="t('alerts.subtitle')">
      <div v-if="alertStore.alerts.length" class="list-stack">
        <article v-for="alert in alertStore.alerts.slice(0, 4)" :key="alert.id" class="list-row"><div><strong>{{ alert.type }}</strong><p>{{ alert.description || t('app.comingSoon') }}</p></div><StatusPill :value="alert.status || alert.severity" /></article>
      </div>
      <EmptyState v-else :title="t('app.noData')" body="No historical alerts have been generated yet." />
    </InfoPanel>

    <InfoPanel :title="t('overview.liveBehaviors')" :subtitle="t('behaviors.subtitle')">
      <div v-if="behaviorStore.behaviors.length" class="list-stack">
        <article v-for="behavior in behaviorStore.behaviors.slice(0, 4)" :key="behavior.id" class="list-row compact"><div><strong>{{ behavior.type }}</strong><p>{{ behavior.description || t('app.comingSoon') }}</p></div><span>{{ behavior.confidence?.toFixed(2) || '--' }}</span></article>
      </div>
      <EmptyState v-else :title="t('app.noData')" body="No behavior detections have been recorded yet." />
    </InfoPanel>

    <InfoPanel :title="t('overview.quickActions')" :subtitle="t('overview.quickActionsBody')">
      <div class="action-grid">
        <RouterLink class="action-card" to="/monitoring"><strong>{{ t('nav.monitoring') }}</strong><p>Camera list, stream window, and device edit tools.</p></RouterLink>
        <RouterLink class="action-card" to="/alerts"><strong>{{ t('nav.alerts') }}</strong><p>Search incidents, inspect images, and complete handling records.</p></RouterLink>
        <RouterLink class="action-card" to="/analytics"><strong>{{ t('nav.analytics') }}</strong><p>Charts for daily trends, type ratios, and high-risk zones.</p></RouterLink>
      </div>
    </InfoPanel>
  </div>
</template>
