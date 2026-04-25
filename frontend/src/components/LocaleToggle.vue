<script setup lang="ts">
import type { LocaleMode } from '@/types/domain'
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()
const setLocale = (value: LocaleMode) => { uiStore.setLocale(value) }
</script>

<template>
  <div class="segment-toggle" role="group" aria-label="Language switcher">
    <button :class="['segment-toggle__item', { 'is-active': uiStore.locale === 'en' }]" @click="setLocale('en')">EN</button>
    <button :class="['segment-toggle__item', { 'is-active': uiStore.locale === 'zh' }]" @click="setLocale('zh')">中文</button>
  </div>
</template>
