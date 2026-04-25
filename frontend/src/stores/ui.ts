import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import type { AlertPopup, LocaleMode, ThemeMode, ToastMessage } from '@/types/domain'

const THEME_KEY = 'campus-sentinel-theme'
const LOCALE_KEY = 'campus-sentinel-locale'

export const useUiStore = defineStore('ui', () => {
  const theme = ref<ThemeMode>('day')
  const locale = ref<LocaleMode>('en')
  const toasts = ref<ToastMessage[]>([])
  const alertPopups = ref<AlertPopup[]>([])
  let toastId = 1
  let alertPopupId = 1

  const isNight = computed(() => theme.value === 'night')

  const bootstrap = () => {
    theme.value = (localStorage.getItem(THEME_KEY) as ThemeMode) || 'day'
    locale.value = (localStorage.getItem(LOCALE_KEY) as LocaleMode) || 'en'
    document.documentElement.dataset.theme = theme.value
  }

  const setTheme = (value: ThemeMode) => {
    theme.value = value
    localStorage.setItem(THEME_KEY, value)
    document.documentElement.dataset.theme = value
  }

  const toggleTheme = () => setTheme(theme.value === 'day' ? 'night' : 'day')

  const setLocale = (value: LocaleMode) => {
    locale.value = value
    localStorage.setItem(LOCALE_KEY, value)
  }

  const pushToast = (text: string, tone: ToastMessage['tone'] = 'info') => {
    const id = toastId++
    toasts.value.push({ id, text, tone })
    window.setTimeout(() => {
      toasts.value = toasts.value.filter((toast) => toast.id !== id)
    }, 3600)
  }

  const pushAlertPopup = (payload: Omit<AlertPopup, 'id'>) => {
    const id = alertPopupId++
    alertPopups.value = [{ id, ...payload }, ...alertPopups.value.filter((item) => item.alertId !== payload.alertId)].slice(0, 3)
    window.setTimeout(() => {
      alertPopups.value = alertPopups.value.filter((popup) => popup.id !== id)
    }, 12000)
  }

  const dismissAlertPopup = (id: number) => {
    alertPopups.value = alertPopups.value.filter((popup) => popup.id !== id)
  }

  return {
    theme,
    locale,
    toasts,
    alertPopups,
    isNight,
    bootstrap,
    setTheme,
    toggleTheme,
    setLocale,
    pushToast,
    pushAlertPopup,
    dismissAlertPopup,
  }
})

