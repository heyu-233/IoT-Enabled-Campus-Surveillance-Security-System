<script setup lang="ts">
import { reactive } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import LocaleToggle from '@/components/LocaleToggle.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { t } = useI18n()
const form = reactive({ username: '', password: '' })
const handleSubmit = async () => {
  const ok = await authStore.login(form)
  if (!ok) return
  await router.push((route.query.redirect as string) || '/overview')
}
</script>

<template>
  <div class="login-view">
    <section class="login-hero">
      <p class="eyebrow">IoT-enabled campus safety</p>
      <h1>{{ t('app.title') }}</h1>
      <p>{{ t('auth.tagline') }}</p>
      <div class="login-hero__panels">
        <article><span>01</span><h3>{{ t('overview.systemHealth') }}</h3><p>RTMP ingest, HTTP-FLV playback, MQTT relay, and browser response in one flow.</p></article>
        <article><span>02</span><h3>{{ t('overview.cameraCoverage') }}</h3><p>Use one bilingual interface for streams, alerts, analytics, and edge tools.</p></article>
      </div>
    </section>

    <section class="login-card surface-card">
      <div class="login-card__tools"><ThemeToggle /><LocaleToggle /></div>
      <h2>{{ t('auth.signIn') }}</h2>
      <p>{{ t('auth.helper') }}</p>
      <form class="form-grid" @submit.prevent="handleSubmit">
        <label><span>{{ t('auth.username') }}</span><input v-model="form.username" required autocomplete="username" /></label>
        <label><span>{{ t('auth.password') }}</span><input v-model="form.password" type="password" required autocomplete="current-password" /></label>
        <button class="primary-button" type="submit" :disabled="authStore.loading">{{ authStore.loading ? t('app.processing') : t('auth.signIn') }}</button>
      </form>
      <div class="auth-switch">
        <span>{{ t('auth.noAccount') }}</span>
        <RouterLink class="auth-switch__link" to="/register">{{ t('auth.createAccount') }}</RouterLink>
      </div>
    </section>
  </div>
</template>

