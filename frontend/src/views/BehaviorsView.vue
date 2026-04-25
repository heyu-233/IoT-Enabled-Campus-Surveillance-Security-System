<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import EmptyState from '@/components/EmptyState.vue'
import InfoPanel from '@/components/InfoPanel.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useBehaviorStore } from '@/stores/behavior'
const { t } = useI18n(); const behaviorStore = useBehaviorStore()
onMounted(async () => { await behaviorStore.loadBehaviors(); behaviorStore.connect() })
onUnmounted(() => { behaviorStore.disconnect() })
const selectedBehavior = computed(() => behaviorStore.selectedBehavior)
const displayOriginal = computed(() => selectedBehavior.value?.originalImageUrl || '')
const displayProcessed = computed(() => selectedBehavior.value?.processedImageUrl || selectedBehavior.value?.imageUrl || '')
</script>

<template>
  <div class="alerts-layout">
    <InfoPanel :title="t('behaviors.feed')" :subtitle="t('behaviors.subtitle')">
      <template #action><StatusPill :value="behaviorStore.liveConnected ? 'ONLINE' : 'OFFLINE'" /></template>
      <div v-if="behaviorStore.behaviors.length" class="table-list">
        <button v-for="behavior in behaviorStore.behaviors" :key="behavior.id" class="table-row" @click="behaviorStore.selectedBehaviorId = behavior.id || null">
          <strong>{{ behavior.type }}</strong><span>{{ behavior.description || '--' }}</span><span>{{ behavior.confidence?.toFixed(2) || '--' }}</span><span>{{ behavior.occurredAt || behavior.createdAt || '--' }}</span>
        </button>
      </div>
      <EmptyState v-else :title="t('app.noData')" :body="t('app.comingSoon')" />
    </InfoPanel>

    <InfoPanel :title="t('behaviors.liveStream')" :subtitle="t('behaviors.feed')">
      <div v-if="selectedBehavior" class="detail-stack">
        <div class="detail-grid">
          <div><span>{{ t('app.confidence') }}</span><strong>{{ selectedBehavior.confidence?.toFixed(2) || '--' }}</strong></div>
          <div><span>{{ t('app.status') }}</span><strong>{{ selectedBehavior.type }}</strong></div>
          <div><span>Camera ID</span><strong>{{ selectedBehavior.cameraId || '--' }}</strong></div>
          <div><span>Time</span><strong>{{ selectedBehavior.occurredAt || selectedBehavior.createdAt || '--' }}</strong></div>
        </div>
        <p>{{ selectedBehavior.description || t('app.comingSoon') }}</p>
        <div v-if="displayOriginal || displayProcessed" class="image-grid">
          <img v-if="displayOriginal" :src="displayOriginal" alt="Original behavior" />
          <img v-if="displayProcessed" :src="displayProcessed" alt="Processed behavior" />
        </div>
        <EmptyState v-else title="Image unavailable" body="This behavior record does not currently have an accessible marked image." />
        <button class="ghost-button danger" type="button" :disabled="!selectedBehavior.id" @click="selectedBehavior.id && behaviorStore.removeBehavior(selectedBehavior.id)">{{ t('app.delete') }}</button>
      </div>
      <EmptyState v-else :title="t('app.noData')" :body="t('app.comingSoon')" />
    </InfoPanel>
  </div>
</template>

