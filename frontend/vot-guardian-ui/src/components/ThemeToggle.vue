<script setup lang="ts">
interface Props {
  isDark: boolean
}

interface Emits {
  (e: 'toggle'): void
}

defineProps<Props>()
defineEmits<Emits>()
</script>

<template>
  <button
    @click="$emit('toggle')"
    class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 vot-focus-ring"
    :class="isDark ? 'bg-primary-600' : 'bg-surface-200'"
  >
    <span class="sr-only">Toggle dark mode</span>
    <span
      class="inline-block h-4 w-4 transform rounded-full bg-white shadow-lg transition-transform duration-200 ease-in-out"
      :class="isDark ? 'translate-x-6' : 'translate-x-1'"
    />
  </button>
</template>

<style scoped>
/* Additional styles for smooth theme transitions */
button {
  transition: background-color 0.3s ease;
}

span:last-child {
  transition: transform 0.2s ease-in-out;
}
</style>
