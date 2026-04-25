<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import EmptyState from '@/components/EmptyState.vue'
import InfoPanel from '@/components/InfoPanel.vue'
import StatusPill from '@/components/StatusPill.vue'
import { useAlertStore } from '@/stores/alert'
import type { AlertProcessRequest } from '@/types/domain'

const { t } = useI18n()
const alertStore = useAlertStore()
const processForm = reactive<AlertProcessRequest>({ processedBy: 'Operator', processingNotes: '', status: 'PROCESSING' })
const imageMode = ref<'processed' | 'original'>('processed')
const imageError = ref(false)

onMounted(() => { alertStore.loadAlerts().catch(() => undefined) })
watch(() => [alertStore.search, alertStore.status, alertStore.from, alertStore.to], () => {
  alertStore.page = 1
  alertStore.loadAlerts().catch(() => undefined)
})
watch(() => alertStore.selectedAlert, (alert) => {
  imageError.value = false
  processForm.processedBy = alert?.processedBy || 'Operator'
  processForm.processingNotes = alert?.processingNotes || ''
  processForm.status = (alert?.status as AlertProcessRequest['status']) || 'PROCESSING'
}, { immediate: true })

const selectedAlert = computed(() => alertStore.selectedAlert)
const prioritizedCount = computed(() => alertStore.alerts.filter((alert) => alert.processedImageUrl || alert.originalImageUrl || alert.screenshot).length)
const displayImage = computed(() => {
  if (!selectedAlert.value) return ''
  const primary = imageMode.value === 'processed' ? selectedAlert.value.processedImageUrl : selectedAlert.value.originalImageUrl
  const secondary = imageMode.value === 'processed' ? selectedAlert.value.originalImageUrl : selectedAlert.value.processedImageUrl
  return primary || secondary || selectedAlert.value.screenshot || ''
})
const canUpdate = computed(() => selectedAlert.value?.status !== 'PROCESSED')
const hasOriginalImage = computed(() => Boolean(selectedAlert.value?.originalImageUrl || selectedAlert.value?.screenshot))
const hasProcessedImage = computed(() => Boolean(selectedAlert.value?.processedImageUrl || selectedAlert.value?.screenshot))
const totalPages = computed(() => Math.max(1, Math.ceil(alertStore.total / alertStore.pageSize)))

const submitProcess = async () => {
  if (!selectedAlert.value?.id) return
  await alertStore.processAlert(selectedAlert.value.id, processForm)
}

const removeSelectedAlert = async () => {
  if (!selectedAlert.value?.id) return
  await alertStore.removeAlert(selectedAlert.value.id)
}
</script>

<template>
  <div class="alerts-layout alerts-layout--wide">
    <InfoPanel :title="t('alerts.activeQueue')" :subtitle="`${alertStore.total} records - ${prioritizedCount} with images prioritized`">
      <template #action>
        <div class="alerts-filters">
          <input v-model="alertStore.search" class="inline-input" :placeholder="t('alerts.searchPlaceholder')" />
          <select v-model="alertStore.status" class="inline-input inline-select">
            <option value="">All status</option>
            <option value="UNPROCESSED">Unprocessed</option>
            <option value="PROCESSING">Processing</option>
            <option value="PROCESSED">Processed</option>
          </select>
        </div>
      </template>
      <div class="alerts-filters alerts-filters--secondary">
        <input v-model="alertStore.from" class="inline-input" type="date" />
        <input v-model="alertStore.to" class="inline-input" type="date" />
      </div>
      <div v-if="alertStore.alerts.length" class="table-list">
        <button v-for="alert in alertStore.alerts" :key="alert.id" class="table-row table-row--alert" @click="alert.id && alertStore.selectAlert(alert.id)">
          <div>
            <strong>{{ alert.type }}</strong>
            <span>{{ alert.description || '--' }}</span>
          </div>
          <span class="table-row__image-flag" :class="{ 'is-on': alert.processedImageUrl || alert.originalImageUrl || alert.screenshot }">
            {{ alert.processedImageUrl || alert.originalImageUrl || alert.screenshot ? 'Image' : 'No image' }}
          </span>
          <span>{{ alert.cameraLocation || alert.cameraName || '--' }}</span>
          <span>{{ alert.createdAt || '--' }}</span>
          <StatusPill :value="alert.severity" />
          <StatusPill :value="alert.status" />
        </button>
      </div>
      <EmptyState v-else :title="t('app.noData')" body="No historical alerts match the current filters." />
      <div class="button-row pagination-row">
        <button class="ghost-button" type="button" :disabled="alertStore.page <= 1" @click="alertStore.page -= 1; alertStore.loadAlerts()">Prev</button>
        <span>Page {{ alertStore.page }} / {{ totalPages }}</span>
        <button class="ghost-button" type="button" :disabled="alertStore.page >= totalPages" @click="alertStore.page += 1; alertStore.loadAlerts()">Next</button>
      </div>
    </InfoPanel>

    <InfoPanel :title="t('alerts.detail')" :subtitle="t('alerts.process')">
      <div v-if="selectedAlert" class="detail-stack">
        <div class="detail-grid">
          <div><span>{{ t('app.severity') }}</span><strong>{{ selectedAlert.severity || '--' }}</strong></div>
          <div><span>{{ t('app.status') }}</span><strong>{{ selectedAlert.status || '--' }}</strong></div>
          <div><span>{{ t('alerts.processedBy') }}</span><strong>{{ selectedAlert.processedBy || '--' }}</strong></div>
          <div><span>{{ t('alerts.processedAt') }}</span><strong>{{ selectedAlert.processedAt || '--' }}</strong></div>
          <div><span>Camera</span><strong>{{ selectedAlert.cameraName || '--' }}</strong></div>
          <div><span>{{ t('app.confidence') }}</span><strong>{{ selectedAlert.confidence?.toFixed(2) || '--' }}</strong></div>
        </div>
        <p>{{ selectedAlert.description || t('app.comingSoon') }}</p>
        <div class="button-row image-toggle-row">
          <button class="ghost-button" type="button" :disabled="!hasProcessedImage" @click="imageMode = 'processed'">Processed image</button>
          <button class="ghost-button" type="button" :disabled="!hasOriginalImage" @click="imageMode = 'original'">Original image</button>
        </div>
        <div v-if="displayImage && !imageError" class="detail-image-viewer surface-card">
          <img :src="displayImage" alt="Alert evidence" @error="imageError = true" />
        </div>
        <EmptyState v-else title="Image unavailable" body="No alert image is available for this record or it failed to load." />
        <form class="form-grid" @submit.prevent="submitProcess">
          <label>
            <span>{{ t('alerts.processedBy') }}</span>
            <input v-model="processForm.processedBy" />
          </label>
          <label>
            <span>Status</span>
            <select v-model="processForm.status" class="inline-input inline-select">
              <option value="PROCESSING">PROCESSING</option>
              <option value="PROCESSED">PROCESSED</option>
              <option value="UNPROCESSED">UNPROCESSED</option>
            </select>
          </label>
          <label class="form-grid__full">
            <span>{{ t('app.notes') }}</span>
            <textarea v-model="processForm.processingNotes" rows="5" :placeholder="t('alerts.notesPlaceholder')" />
          </label>
          <div class="button-row form-grid__full">
            <button class="primary-button" type="submit" :disabled="!canUpdate">{{ canUpdate ? t('alerts.process') : 'Already processed' }}</button>
            <button class="ghost-button danger" type="button" @click="removeSelectedAlert">Delete alert</button>
          </div>
        </form>
      </div>
      <EmptyState v-else :title="t('app.noData')" body="Select a historical alert to inspect its images and handling record." />
    </InfoPanel>
  </div>
</template>

