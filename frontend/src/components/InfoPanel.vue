<script setup lang="ts">
defineProps<{ title: string; subtitle?: string }>()
</script>

<template>
  <section class="surface-card info-panel">
    <header class="section-header">
      <div><h3>{{ title }}</h3><p v-if="subtitle">{{ subtitle }}</p></div>
      <slot name="action" />
    </header>
    <slot />
  </section>
</template>

