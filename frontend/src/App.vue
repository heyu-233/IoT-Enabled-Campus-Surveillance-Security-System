<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const authStore = useAuthStore()
const uiStore = useUiStore()
const { locale } = useI18n()

onMounted(async () => {
  uiStore.bootstrap()
  locale.value = uiStore.locale
  await authStore.bootstrap()
})

watch(
  () => uiStore.locale,
  (value) => {
    locale.value = value
    document.documentElement.lang = value
  },
  { immediate: true },
)

watch(
  () => uiStore.theme,
  (value) => {
    document.documentElement.dataset.theme = value
  },
  { immediate: true },
)
</script>

<template>
  <RouterView />
</template>

