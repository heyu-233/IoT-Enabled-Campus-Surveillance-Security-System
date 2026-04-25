<script setup lang="ts">
import type { MetricItem } from '@/types/domain'
defineProps<{ eyebrow: string; title: string; summary: string; metrics: MetricItem[] }>()
</script>

<template>
  <section class="metric-panel surface-card">
    <p class="eyebrow">{{ eyebrow }}</p>
    <header class="metric-panel__header"><div><h3>{{ title }}</h3><p>{{ summary }}</p></div></header>
    <div class="metric-panel__grid">
      <article v-for="metric in metrics" :key="metric.label" class="metric-panel__item">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
      </article>
    </div>
  </section>
</template>

