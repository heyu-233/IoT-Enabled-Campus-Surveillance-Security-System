import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { authApi } from '@/api/services'
import { useUiStore } from '@/stores/ui'
import type { LoginRequest, RegisterRequest, UserDto } from '@/types/domain'

const TOKEN_KEY = 'campus-sentinel-token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const currentUser = ref<UserDto | null>(null)
  const isBootstrapped = ref(false)
  const loading = ref(false)
  const isAuthenticated = computed(() => Boolean(token.value))

  const bootstrap = async () => {
    if (isBootstrapped.value) return
    if (!token.value) {
      isBootstrapped.value = true
      return
    }

    try {
      currentUser.value = await authApi.me()
    } catch {
      token.value = null
      localStorage.removeItem(TOKEN_KEY)
    } finally {
      isBootstrapped.value = true
    }
  }

  const login = async (payload: LoginRequest) => {
    const uiStore = useUiStore()
    loading.value = true
    try {
      const response = await authApi.login(payload)
      token.value = response.token
      currentUser.value = response.user
      localStorage.setItem(TOKEN_KEY, response.token)
      uiStore.pushToast('Signed in successfully.', 'success')
      return true
    } catch {
      uiStore.pushToast('Unable to sign in with these credentials.', 'danger')
      return false
    } finally {
      loading.value = false
      isBootstrapped.value = true
    }
  }

  const register = async (payload: RegisterRequest) => {
    const uiStore = useUiStore()
    loading.value = true
    try {
      const response = await authApi.register(payload)
      token.value = response.token
      currentUser.value = response.user
      localStorage.setItem(TOKEN_KEY, response.token)
      uiStore.pushToast('Account created successfully.', 'success')
      return true
    } catch {
      uiStore.pushToast('Unable to create account right now.', 'danger')
      return false
    } finally {
      loading.value = false
      isBootstrapped.value = true
    }
  }

  const logout = async () => {
    try { await authApi.logout() } catch { }
    token.value = null
    currentUser.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  return { token, currentUser, isBootstrapped, loading, isAuthenticated, bootstrap, login, register, logout }
})

