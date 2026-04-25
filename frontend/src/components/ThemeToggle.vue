<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useUiStore } from '@/stores/ui'
const uiStore = useUiStore()
const { t } = useI18n()
</script>

<template>
  <button class="chip-toggle" type="button" @click="uiStore.toggleTheme()">
    <span>{{ t('app.theme') }}</span>
    <strong>{{ uiStore.theme === 'day' ? t('app.day') : t('app.night') }}</strong>
  </button>
</template>

