<script setup lang="ts">
import { computed, reactive } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import LocaleToggle from '@/components/LocaleToggle.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()
const form = reactive({ username: '', email: '', password: '', confirmPassword: '' })
const passwordMismatch = computed(() => form.confirmPassword.length > 0 && form.password !== form.confirmPassword)

const handleSubmit = async () => {
  if (passwordMismatch.value) return
  const ok = await authStore.register({ username: form.username, email: form.email, password: form.password })
  if (!ok) return
  await router.push('/overview')
}
</script>

<template>
  <div class="login-view">
    <section class="login-hero">
      <p class="eyebrow">Campus Sentinel onboarding</p>
      <h1>{{ t('auth.createAccount') }}</h1>
      <p>{{ t('auth.registerHelper') }}</p>
      <div class="login-hero__panels">
        <article><span>01</span><h3>{{ t('nav.monitoring') }}</h3><p>{{ t('auth.registerFeatureMonitoring') }}</p></article>
        <article><span>02</span><h3>{{ t('nav.alerts') }}</h3><p>{{ t('auth.registerFeatureAlerts') }}</p></article>
      </div>
    </section>

    <section class="login-card surface-card">
      <div class="login-card__tools"><ThemeToggle /><LocaleToggle /></div>
      <h2>{{ t('auth.createAccount') }}</h2>
      <p>{{ t('auth.registerSubtitle') }}</p>
      <form class="form-grid" @submit.prevent="handleSubmit">
        <label><span>{{ t('auth.username') }}</span><input v-model="form.username" required autocomplete="username" /></label>
        <label><span>{{ t('auth.email') }}</span><input v-model="form.email" type="email" required autocomplete="email" /></label>
        <label><span>{{ t('auth.password') }}</span><input v-model="form.password" type="password" required autocomplete="new-password" /></label>
        <label><span>{{ t('auth.confirmPassword') }}</span><input v-model="form.confirmPassword" type="password" required autocomplete="new-password" /></label>
        <p v-if="passwordMismatch" class="form-error form-grid__full">{{ t('auth.passwordMismatch') }}</p>
        <button class="primary-button" type="submit" :disabled="authStore.loading || passwordMismatch">
          {{ authStore.loading ? t('app.processing') : t('auth.createAccount') }}
        </button>
      </form>
      <div class="auth-switch">
        <span>{{ t('auth.haveAccount') }}</span>
        <RouterLink class="auth-switch__link" to="/login">{{ t('auth.signIn') }}</RouterLink>
      </div>
    </section>
  </div>
</template>
