<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import LocaleToggle from '@/components/LocaleToggle.vue'
import StatusPill from '@/components/StatusPill.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import TopRibbon from '@/components/TopRibbon.vue'
import { useAlertStore } from '@/stores/alert'
import { useAuthStore } from '@/stores/auth'
import { useBehaviorStore } from '@/stores/behavior'
import { useCameraStore } from '@/stores/camera'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const cameraStore = useCameraStore()
const alertStore = useAlertStore()
const behaviorStore = useBehaviorStore()
const uiStore = useUiStore()
let alertPollTimer: number | null = null
const seenAlertIds = new Set<number>()
let alertPopupCutoff = Date.now()

const getAlertTime = (value?: string) => {
  if (!value) return 0
  const parsed = new Date(value).getTime()
  return Number.isFinite(parsed) ? parsed : 0
}

const navItems = computed(() => [
  { to: '/overview', label: t('nav.overview') },
  { to: '/monitoring', label: t('nav.monitoring') },
  { to: '/alerts', label: t('nav.alerts') },
  { to: '/behaviors', label: t('nav.behaviors') },
  { to: '/analytics', label: t('nav.analytics') },
  { to: '/system', label: t('nav.system') },
])

const handleLogout = async () => {
  await authStore.logout()
  behaviorStore.disconnect()
  await router.push('/login')
}

onMounted(async () => {
  alertPopupCutoff = Date.now()
  await Promise.allSettled([cameraStore.loadCameras(), alertStore.loadAlerts(), behaviorStore.loadBehaviors()])
  behaviorStore.connect()

  const seedAlerts = await alertStore.fetchLatestOpenAlerts().catch(() => [])
  seedAlerts.forEach((alert) => {
    if (alert.id) seenAlertIds.add(alert.id)
  })

  alertPollTimer = window.setInterval(async () => {
    const latestAlerts = await alertStore.fetchLatestOpenAlerts().catch(() => [])
    const newAlerts = latestAlerts.filter((alert) => {
      if (!alert.id || seenAlertIds.has(alert.id)) return false
      const createdAt = getAlertTime(alert.createdAt || alert.behaviorOccurredAt)
      return createdAt >= alertPopupCutoff
    })

    if (!newAlerts.length) return

    newAlerts.forEach((alert) => {
      if (alert.id) seenAlertIds.add(alert.id)
      uiStore.pushAlertPopup({
        alertId: alert.id,
        title: `${alert.type || 'Alert'} detected`,
        body: alert.description || 'A new unprocessed alert has entered the queue.',
        severity: alert.severity,
        location: alert.cameraLocation || alert.cameraName || 'Test camera zone',
        imageUrl: alert.processedImageUrl || alert.originalImageUrl || alert.screenshot,
      })
    })

    await alertStore.loadAlerts().catch(() => undefined)
  }, 4000)
})

onBeforeUnmount(() => {
  if (alertPollTimer !== null) {
    window.clearInterval(alertPollTimer)
    alertPollTimer = null
  }
})
</script>

<template>
  <div class="app-shell">
    <aside class="shell-nav">
      <div class="shell-brand">
        <p>Campus Sentinel</p>
        <h1>{{ t('app.subtitle') }}</h1>
        <span>{{ authStore.currentUser?.role || 'Operator' }}</span>
      </div>
      <nav class="shell-menu">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" :class="['shell-menu__link', { 'is-active': route.path === item.to }]">{{ item.label }}</RouterLink>
      </nav>
      <div class="shell-footer">
        <ThemeToggle />
        <LocaleToggle />
        <button class="ghost-button" type="button" @click="handleLogout">{{ t('nav.logout') }}</button>
      </div>
    </aside>

    <main class="shell-main">
      <TopRibbon />
      <header class="page-banner">
        <div>
          <p class="eyebrow">Campus surveillance interface</p>
          <h2>{{ t(`nav.${(route.name as string) || 'overview'}`) }}</h2>
          <p>{{ t('app.welcome') }}</p>
        </div>
        <div class="page-banner__user">
          <span class="page-banner__user-name">{{ authStore.currentUser?.username || 'Guest' }}</span>
          <strong class="page-banner__theme">{{ uiStore.theme === 'day' ? t('app.day') : t('app.night') }}</strong>
        </div>
      </header>
      <RouterView />
    </main>

    <div class="alert-popup-stack">
      <article v-for="popup in uiStore.alertPopups" :key="popup.id" class="alert-popup surface-card">
        <button class="alert-popup__close" type="button" @click="uiStore.dismissAlertPopup(popup.id)">×</button>
        <div class="alert-popup__header">
          <span class="eyebrow">Live Alert</span>
          <StatusPill :value="popup.severity || 'UNPROCESSED'" />
        </div>
        <strong>{{ popup.title }}</strong>
        <p>{{ popup.body }}</p>
        <span>{{ popup.location || 'Monitoring zone' }}</span>
        <img v-if="popup.imageUrl" :src="popup.imageUrl" alt="Alert snapshot" />
        <RouterLink class="ghost-button" to="/alerts">Open Alerts</RouterLink>
      </article>
    </div>

    <div class="toast-stack"><article v-for="toast in uiStore.toasts" :key="toast.id" :class="['toast-item', `is-${toast.tone}`]">{{ toast.text }}</article></div>
  </div>
</template>

