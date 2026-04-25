import { ref } from 'vue'
import { defineStore } from 'pinia'

import { normalizeMessage } from '@/api/adapters'
import { configApi, edgeApi } from '@/api/services'
import { useUiStore } from '@/stores/ui'
import type { AlertSetting } from '@/types/domain'

const defaultSettings = (): AlertSetting => ({ emailNotifications: false, smsNotifications: false, pushNotifications: true, emailRecipients: '', smsRecipients: '', severityLevels: 'HIGH,CRITICAL' })

export const useConfigStore = defineStore('config', () => {
  const alertSettings = ref<AlertSetting>(defaultSettings())
  const edgeResponse = ref('')
  const loading = ref(false)

  const loadSettings = async () => {
    loading.value = true
    try { alertSettings.value = { ...defaultSettings(), ...(await configApi.getAlertSettings()) } }
    finally { loading.value = false }
  }

  const saveSettings = async () => {
    const uiStore = useUiStore()
    alertSettings.value = await configApi.updateAlertSettings(alertSettings.value)
    uiStore.pushToast('Changes saved.', 'success')
  }

  const sendEdgeCommand = async (
    action: 'start_stream' | 'stop_stream' | 'start_detector' | 'stop_detector' | 'buzzer_on' | 'buzzer_off' | 'led_blink' | 'config_detector',
    deviceId: string,
    payload = '',
  ) => {
    const uiStore = useUiStore()
    const response =
      action === 'start_stream' ? await edgeApi.startStream(deviceId)
        : action === 'stop_stream' ? await edgeApi.stopStream(deviceId)
          : action === 'start_detector' ? await edgeApi.startDetector(deviceId)
            : action === 'stop_detector' ? await edgeApi.stopDetector(deviceId)
              : action === 'buzzer_on' ? await edgeApi.buzzerOn(deviceId)
                : action === 'buzzer_off' ? await edgeApi.buzzerOff(deviceId)
                  : action === 'led_blink' ? await edgeApi.ledBlink(deviceId)
                    : await edgeApi.detectorConfig(deviceId, payload)
    edgeResponse.value = normalizeMessage(response)
    uiStore.pushToast(edgeResponse.value, response.success ? 'info' : 'danger')
  }

  return { alertSettings, edgeResponse, loading, loadSettings, saveSettings, sendEdgeCommand }
})
