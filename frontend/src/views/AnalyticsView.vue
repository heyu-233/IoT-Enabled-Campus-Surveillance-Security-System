<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { EChartsOption } from 'echarts'

import ChartPanel from '@/components/ChartPanel.vue'
import EmptyState from '@/components/EmptyState.vue'
import InfoPanel from '@/components/InfoPanel.vue'
import { useAnalyticsStore } from '@/stores/analytics'
import { useUiStore } from '@/stores/ui'

const { t } = useI18n()
const analyticsStore = useAnalyticsStore()
const uiStore = useUiStore()

const palette = computed(() => uiStore.theme === 'night'
  ? ['#7dd3c7', '#f5b971', '#ff7f7f', '#7ea6ff', '#ceb5ff']
  : ['#1f8a78', '#c7772f', '#cd4f38', '#2b69c9', '#8458d1'])
const chartText = computed(() => uiStore.theme === 'night' ? '#f4efe7' : '#1f1b18')
const chartSubtle = computed(() => uiStore.theme === 'night' ? 'rgba(255,255,255,0.1)' : 'rgba(35,26,20,0.08)')
const chartBg = computed(() => uiStore.theme === 'night' ? '#17161d' : '#fff9f1')

onMounted(() => { analyticsStore.loadAnalytics().catch(() => undefined) })

const summaryMetrics = computed(() => [
  { label: t('analytics.totalEvents'), value: analyticsStore.totalEvents },
  { label: t('analytics.selectedType'), value: analyticsStore.selectedType || '--' },
  { label: t('analytics.topArea'), value: analyticsStore.topArea || '--' },
])

const pieOption = computed<EChartsOption>(() => ({
  color: palette.value,
  backgroundColor: 'transparent',
  tooltip: { trigger: 'item', backgroundColor: chartBg.value, borderWidth: 0, textStyle: { color: chartText.value } },
  series: [{
    type: 'pie',
    radius: ['48%', '78%'],
    center: ['50%', '54%'],
    itemStyle: { borderRadius: 18, borderColor: chartBg.value, borderWidth: 6 },
    label: { color: chartText.value, formatter: '{b}\n{d}%' },
    data: analyticsStore.distribution,
  }],
}))

const lineOption = computed<EChartsOption>(() => ({
  color: [palette.value[0]],
  backgroundColor: 'transparent',
  grid: { left: 20, right: 20, top: 30, bottom: 20, containLabel: true },
  tooltip: { trigger: 'axis', backgroundColor: chartBg.value, borderWidth: 0, textStyle: { color: chartText.value } },
  xAxis: { type: 'category', data: analyticsStore.daily.labels, boundaryGap: false, axisLabel: { color: chartText.value }, axisLine: { lineStyle: { color: chartSubtle.value } } },
  yAxis: { type: 'value', axisLabel: { color: chartText.value }, splitLine: { lineStyle: { color: chartSubtle.value } } },
  series: [{
    type: 'line',
    smooth: true,
    symbolSize: 8,
    lineStyle: { width: 3 },
    areaStyle: { color: uiStore.theme === 'night' ? 'rgba(125, 211, 199, 0.18)' : 'rgba(31, 138, 120, 0.16)' },
    data: analyticsStore.daily.values,
  }],
}))

const heatmapOption = computed<EChartsOption>(() => ({
  color: [palette.value[1]],
  backgroundColor: 'transparent',
  grid: { left: 20, right: 20, top: 24, bottom: 20, containLabel: true },
  tooltip: { trigger: 'axis', backgroundColor: chartBg.value, borderWidth: 0, textStyle: { color: chartText.value } },
  xAxis: { type: 'value', axisLabel: { color: chartText.value }, splitLine: { lineStyle: { color: chartSubtle.value } } },
  yAxis: { type: 'category', data: analyticsStore.heatmap.map((item) => item.name), axisLabel: { color: chartText.value }, axisLine: { show: false } },
  series: [{
    type: 'bar',
    data: analyticsStore.heatmap.map((item) => item.value),
    barWidth: 18,
    showBackground: true,
    backgroundStyle: { color: chartSubtle.value, borderRadius: 999 },
    itemStyle: { borderRadius: 999 },
  }],
}))

const detailOption = computed<EChartsOption>(() => ({
  color: [palette.value[3]],
  backgroundColor: 'transparent',
  grid: { left: 20, right: 20, top: 24, bottom: 20, containLabel: true },
  tooltip: { trigger: 'axis', backgroundColor: chartBg.value, borderWidth: 0, textStyle: { color: chartText.value } },
  xAxis: { type: 'category', data: analyticsStore.typeDetails.labels, axisLabel: { color: chartText.value }, axisLine: { lineStyle: { color: chartSubtle.value } } },
  yAxis: { type: 'value', axisLabel: { color: chartText.value }, splitLine: { lineStyle: { color: chartSubtle.value } } },
  series: [{
    type: 'bar',
    data: analyticsStore.typeDetails.values,
    barWidth: '42%',
    itemStyle: { borderRadius: [14, 14, 4, 4] },
  }],
}))
</script>

<template>
  <div v-if="analyticsStore.hasData" class="analytics-wall">
    <InfoPanel :title="t('analytics.spotlight')" :subtitle="t('analytics.trendNarrative')" class="analytics-wall__hero">
      <div class="analytics-summary">
        <article v-for="metric in summaryMetrics" :key="metric.label" class="analytics-summary__card">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
        </article>
      </div>
      <div class="analytics-type-picker">
        <span>{{ t('analytics.selectType') }}</span>
        <div class="analytics-type-picker__chips">
          <button
            v-for="item in analyticsStore.distribution"
            :key="item.name"
            :class="['chip-toggle', { 'is-active': analyticsStore.selectedType === item.name }]"
            type="button"
            @click="analyticsStore.loadTypeDetails(item.name)"
          >
            <span>{{ item.name }}</span>
            <strong>{{ item.value }}</strong>
          </button>
        </div>
      </div>
    </InfoPanel>

    <ChartPanel :title="t('analytics.typeDistribution')" subtitle="Alert and behavior composition" :option="pieOption" />
    <ChartPanel :title="t('analytics.dailyAlerts')" subtitle="Recent incident rhythm" :option="lineOption" />
    <ChartPanel :title="t('analytics.areaHeatmap')" subtitle="Campus hotspots by location" :option="heatmapOption" />
    <ChartPanel :title="t('analytics.typeDetails')" :subtitle="analyticsStore.selectedType || '--'" :option="detailOption" />
  </div>
  <EmptyState v-else :title="t('analytics.title')" :body="t('analytics.empty')" />
</template>
