<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import InfoPanel from '@/components/InfoPanel.vue'
import { useCameraStore } from '@/stores/camera'
import { useConfigStore } from '@/stores/config'
const { t } = useI18n(); const configStore = useConfigStore(); const cameraStore = useCameraStore()
const edgeForm = reactive({ deviceId: 'edge-camera-01', payload: '{"device_id":"edge-camera-01","mode":"alert"}' })
onMounted(() => { configStore.loadSettings().catch(() => undefined); cameraStore.loadCameras().catch(() => undefined) })
</script>

<template>
  <div class="system-layout">
    <InfoPanel :title="t('system.alertSettings')" :subtitle="t('system.subtitle')">
      <form class="form-grid" @submit.prevent="configStore.saveSettings()">
        <label class="toggle-field"><span>{{ t('system.emailNotifications') }}</span><input v-model="configStore.alertSettings.emailNotifications" type="checkbox" /></label>
        <label class="toggle-field"><span>{{ t('system.smsNotifications') }}</span><input v-model="configStore.alertSettings.smsNotifications" type="checkbox" /></label>
        <label class="toggle-field"><span>{{ t('system.pushNotifications') }}</span><input v-model="configStore.alertSettings.pushNotifications" type="checkbox" /></label>
        <label class="form-grid__full"><span>Email</span><input v-model="configStore.alertSettings.emailRecipients" /></label>
        <label class="form-grid__full"><span>SMS</span><input v-model="configStore.alertSettings.smsRecipients" /></label>
        <label class="form-grid__full"><span>{{ t('system.severityLevels') }}</span><input v-model="configStore.alertSettings.severityLevels" /></label>
        <button class="primary-button" type="submit">{{ t('app.save') }}</button>
      </form>
    </InfoPanel>

    <InfoPanel :title="t('system.edgeTools')" :subtitle="t('system.deviceManagement')">
      <form class="form-grid" @submit.prevent>
        <label><span>{{ t('system.deviceId') }}</span><input v-model="edgeForm.deviceId" /></label>
        <label class="form-grid__full"><span>{{ t('system.configPayload') }}</span><textarea v-model="edgeForm.payload" rows="6" /></label>
        <div class="button-row form-grid__full">
          <button class="primary-button" type="button" @click="configStore.sendEdgeCommand('start_stream', edgeForm.deviceId)">Start Stream</button>
          <button class="ghost-button" type="button" @click="configStore.sendEdgeCommand('stop_stream', edgeForm.deviceId)">Stop Stream</button>
          <button class="primary-button" type="button" @click="configStore.sendEdgeCommand('start_detector', edgeForm.deviceId)">Start Detection</button>
          <button class="ghost-button" type="button" @click="configStore.sendEdgeCommand('stop_detector', edgeForm.deviceId)">Stop Detection</button>
          <button class="ghost-button" type="button" @click="configStore.sendEdgeCommand('config_detector', edgeForm.deviceId, edgeForm.payload)">{{ t('app.submit') }}</button>
          <button class="ghost-button" type="button" @click="configStore.sendEdgeCommand('buzzer_on', edgeForm.deviceId)">Buzzer On</button>
          <button class="ghost-button" type="button" @click="configStore.sendEdgeCommand('buzzer_off', edgeForm.deviceId)">Buzzer Off</button>
          <button class="ghost-button" type="button" @click="configStore.sendEdgeCommand('led_blink', edgeForm.deviceId)">LED Blink</button>
        </div>
      </form>
      <p class="response-box">{{ configStore.edgeResponse || t('app.comingSoon') }}</p>
    </InfoPanel>

    <InfoPanel :title="t('system.deviceManagement')" :subtitle="t('monitoring.cameraDirectory')">
      <div class="mini-table"><article v-for="camera in cameraStore.cameras" :key="camera.id" class="mini-table__row"><div><strong>{{ camera.name }}</strong><p>{{ camera.location || '--' }}</p></div><span>{{ camera.deviceId || '--' }}</span><span>{{ camera.status || '--' }}</span></article></div>
    </InfoPanel>
  </div>
</template>
