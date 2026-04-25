<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
const props = defineProps<{ title: string; subtitle?: string; option: echarts.EChartsOption }>()
const host = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null
const render = () => { if (!host.value) return; chart ??= echarts.init(host.value); chart.setOption(props.option) }
onMounted(() => { render(); window.addEventListener('resize', render) })
watch(() => props.option, render, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', render); chart?.dispose(); chart = null })
</script>

<template>
  <section class="surface-card chart-panel">
    <header class="section-header"><div><h3>{{ title }}</h3><p v-if="subtitle">{{ subtitle }}</p></div></header>
    <div ref="host" class="chart-panel__host" />
  </section>
</template>

