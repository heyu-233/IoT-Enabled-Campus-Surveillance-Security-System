<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import EmptyState from '@/components/EmptyState.vue'
import InfoPanel from '@/components/InfoPanel.vue'
import StatusPill from '@/components/StatusPill.vue'
import StreamPlayer from '@/components/StreamPlayer.vue'
import { useCameraStore } from '@/stores/camera'
import type { Camera } from '@/types/domain'

const { t } = useI18n()
const cameraStore = useCameraStore()

onMounted(async () => {
  await cameraStore.loadCameras()
  if (cameraStore.selectedCameraId) await cameraStore.selectCamera(cameraStore.selectedCameraId)
  cameraStore.connectLightStream()
})

const selectedCamera = computed(() => cameraStore.selectedCamera)

const openEditor = (camera?: Camera | null) => {
  cameraStore.editCamera(camera)
}

const submitCamera = async () => {
  await cameraStore.saveCamera()
}
</script>

<template>
  <div class="monitoring-layout monitoring-layout--focused">
    <InfoPanel :title="t('monitoring.cameraDirectory')" :subtitle="t('monitoring.subtitle')">
      <template #action>
        <button class="ghost-button" type="button" @click="openEditor()">{{ t('monitoring.addCamera') }}</button>
      </template>

      <div v-if="cameraStore.cameras.length" class="camera-list camera-list--ops">
        <button
          v-for="camera in cameraStore.cameras"
          :key="camera.id"
          :class="[
            'camera-card',
            'camera-card--ops',
            {
              'is-selected': camera.id === cameraStore.selectedCameraId,
            },
          ]"
          @click="camera.id && cameraStore.selectCamera(camera.id)"
        >
          <div class="camera-card__meta">
            <span class="camera-card__eyebrow">{{ camera.id === cameraStore.testCameraId ? 'Edge RTMP Feed' : 'Demo Source' }}</span>
            <p>{{ camera.name }}</p>
            <span>{{ camera.location || '--' }}</span>
          </div>
          <div class="camera-card__badges">
            <StatusPill :value="camera.status" />
            <span class="camera-card__lock">{{ camera.id === cameraStore.selectedCameraId ? 'Selected console' : 'Available' }}</span>
          </div>
        </button>
      </div>
      <EmptyState v-else :title="t('app.noData')" :body="t('app.comingSoon')" />
    </InfoPanel>

    <InfoPanel :title="t('monitoring.streamWindow')" subtitle="Test camera live view.">
      <div class="stream-command-deck">
        <div class="stream-command-deck__status">
          <div class="stream-command-deck__headline">
            <span class="eyebrow">Command Deck</span>
            <strong>{{ selectedCamera ? 'Camera source selected' : 'Awaiting camera profile' }}</strong>
          </div>
          <div class="stream-command-deck__chips">
            <StatusPill :value="selectedCamera?.status || 'OFFLINE'" />
            <StatusPill :value="cameraStore.selectedDetectionRunning ? 'ACTIVE' : 'STOPPED'" />
            <StatusPill :value="cameraStore.lightConnected ? cameraStore.lightLevelLabel : 'disconnected'" />
          </div>
        </div>

        <div class="stream-command-deck__actions">
          <button class="ghost-button" type="button" :disabled="!selectedCamera?.id" @click="selectedCamera?.id && cameraStore.refreshCamera(selectedCamera.id)">
            Refresh Link
          </button>
          <button class="primary-button" type="button" :disabled="!selectedCamera?.id" @click="selectedCamera?.id && cameraStore.selectCamera(selectedCamera.id)">
            Reload Feed
          </button>
        </div>

        <div class="stream-command-deck__controls">
          <div class="stream-command-group">
            <span class="stream-command-group__label">Transport</span>
            <div class="stream-command-group__buttons">
              <button class="primary-button" type="button" :disabled="!selectedCamera?.deviceId || cameraStore.streamPending || cameraStore.selectedStreamRunning" @click="cameraStore.startStream()">
                Start Stream
              </button>
              <button class="ghost-button danger" type="button" :disabled="!selectedCamera?.deviceId || cameraStore.streamPending || !cameraStore.selectedStreamRunning" @click="cameraStore.stopStream()">
                Stop Stream
              </button>
            </div>
          </div>

          <div class="stream-command-group">
            <span class="stream-command-group__label">Inference</span>
            <div class="stream-command-group__buttons">
              <button class="primary-button" type="button" :disabled="!selectedCamera?.deviceId || cameraStore.detectorPending || cameraStore.selectedDetectionRunning" @click="cameraStore.startDetection()">
                Start Detection
              </button>
              <button class="ghost-button danger" type="button" :disabled="!selectedCamera?.deviceId || cameraStore.detectorPending || !cameraStore.selectedDetectionRunning" @click="cameraStore.stopDetection()">
                Stop Detection
              </button>
            </div>
          </div>

          <div class="stream-command-group">
            <span class="stream-command-group__label">{{ t('monitoring.alarm') }}</span>
            <div class="stream-command-group__buttons">
              <button
                class="primary-button emergency"
                type="button"
                :disabled="!selectedCamera?.deviceId"
                @click="cameraStore.triggerAlarm()"
              >
                {{ t('monitoring.triggerAlarm') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <StreamPlayer
        :key="cameraStore.selectedDeviceId || 'empty-stream'"
        :src="cameraStore.selectedStreamUrl"
        :reload-token="cameraStore.selectedStreamToken"
        :active="cameraStore.selectedStreamRunning"
        @stream-ready="cameraStore.setStreamPresence(true)"
        @stream-lost="cameraStore.setStreamPresence(false)"
      />
    </InfoPanel>

    <InfoPanel :title="t('monitoring.details')" subtitle="Test camera status.">
      <div v-if="selectedCamera" class="detail-grid detail-grid--ops">
        <div><span>{{ t('monitoring.name') }}</span><strong>{{ selectedCamera.name }}</strong></div>
        <div><span>Device ID</span><strong>{{ selectedCamera.deviceId || '--' }}</strong></div>
        <div><span>{{ t('app.location') }}</span><strong>{{ selectedCamera.location || '--' }}</strong></div>
        <div><span>{{ t('monitoring.ipAddress') }}</span><strong>{{ selectedCamera.ipAddress || '--' }}</strong></div>
        <div><span>{{ t('monitoring.port') }}</span><strong>{{ selectedCamera.port || '--' }}</strong></div>
        <div><span>{{ t('monitoring.lastActive') }}</span><strong>{{ selectedCamera.lastActive || '--' }}</strong></div>
        <div><span>Stream</span><strong>{{ selectedCamera.status === 'ONLINE' ? 'LIVE' : 'IDLE' }}</strong></div>
        <div><span>Detection</span><strong>{{ cameraStore.selectedDetectionRunning ? 'ARMED' : 'STANDBY' }}</strong></div>
        <div><span>Console</span><strong>{{ selectedCamera ? 'MULTI-SOURCE DEMO' : 'WAITING' }}</strong></div>
      </div>
      <EmptyState v-else :title="t('app.noData')" :body="t('monitoring.emptyStream')" />

      <form class="form-grid panel-form" @submit.prevent="submitCamera">
        <label><span>{{ t('monitoring.name') }}</span><input v-model="cameraStore.draft.name" required /></label>
        <label><span>Device ID</span><input v-model="cameraStore.draft.deviceId" required /></label>
        <label><span>{{ t('app.location') }}</span><input v-model="cameraStore.draft.location" /></label>
        <label><span>{{ t('monitoring.ipAddress') }}</span><input v-model="cameraStore.draft.ipAddress" /></label>
        <label><span>{{ t('monitoring.port') }}</span><input v-model.number="cameraStore.draft.port" type="number" /></label>
        <label class="form-grid__full"><span>{{ t('monitoring.streamUrl') }}</span><input v-model="cameraStore.draft.streamUrl" /></label>
        <div class="button-row form-grid__full">
          <button class="primary-button" type="submit">{{ t('app.save') }}</button>
          <button class="ghost-button" type="button" @click="openEditor(selectedCamera)">{{ t('app.edit') }}</button>
          <button class="ghost-button danger" type="button" :disabled="!selectedCamera?.id" @click="selectedCamera?.id && cameraStore.removeCamera(selectedCamera.id)">
            {{ t('app.delete') }}
          </button>
        </div>
      </form>
    </InfoPanel>
  </div>
</template>
