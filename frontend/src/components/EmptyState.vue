<script setup lang="ts">
defineProps<{ title: string; body: string }>()
</script>

<template>
  <div class="empty-state"><div class="empty-state__orb" /><h4>{{ title }}</h4><p>{{ body }}</p></div>
</template>

