<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ value?: string }>()
const tone = computed(() => {
  const value = (props.value || '').toLowerCase()
  if (['online', 'active', 'processed', 'resolved', 'ok'].includes(value)) return 'good'
  if (['warning', 'pending', 'medium'].includes(value)) return 'warning'
  if (['critical', 'high', 'offline', 'error'].includes(value)) return 'danger'
  return 'neutral'
})
</script>

<template>
  <span :class="['status-pill', `status-pill--${tone}`]">{{ value || 'Unknown' }}</span>
</template>

