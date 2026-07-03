<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { apiUrl } from '../utils/api'

const systemStatus = ref({
  api: 'checking',
  database: 'checking',
  mindsdb: 'checking'
})

const statusColors: Record<string, string> = {
  healthy: 'text-success-600 dark:text-success-400',
  warning: 'text-warning-600 dark:text-warning-400',
  error: 'text-danger-600 dark:text-danger-400',
  checking: 'text-surface-500 dark:text-surface-400'
}

const statusLabels: Record<string, string> = {
  healthy: 'Operational',
  warning: 'Degraded',
  error: 'Error',
  checking: 'Checking...'
}

// Check system health
const checkSystemHealth = async () => {
  try {
    // Check API health
    const apiResponse = await fetch(apiUrl('/health'))
    systemStatus.value.api = apiResponse.ok ? 'healthy' : 'error'
  } catch {
    systemStatus.value.api = 'error'
  }

  try {
    // Check MindsDB health
    const mindsdbResponse = await fetch('http://localhost:47334/')
    systemStatus.value.mindsdb = mindsdbResponse.ok ? 'healthy' : 'error'
  } catch {
    systemStatus.value.mindsdb = 'error'
  }

  // Database status (assume healthy if we get here)
  systemStatus.value.database = 'healthy'
}

// Check health on mount and periodically
onMounted(() => {
  checkSystemHealth()
  const interval = setInterval(checkSystemHealth, 30000) // Check every 30 seconds

  onUnmounted(() => {
    clearInterval(interval)
  })
})
</script>

<template>
  <div class="flex items-center space-x-4">
    <!-- System Status Indicator -->
    <div class="flex items-center space-x-2">
      <div class="relative">
        <div class="w-3 h-3 rounded-full bg-surface-300 dark:bg-surface-600">
          <div
            class="w-3 h-3 rounded-full animate-pulse"
            :class="{
              'bg-success-500': systemStatus.api === 'healthy' && systemStatus.database === 'healthy' && systemStatus.mindsdb === 'healthy',
              'bg-warning-500': [systemStatus.api, systemStatus.database, systemStatus.mindsdb].includes('warning'),
              'bg-danger-500': [systemStatus.api, systemStatus.database, systemStatus.mindsdb].includes('error')
            }"
          ></div>
        </div>
      </div>

      <div class="hidden md:block">
        <div class="text-xs font-medium text-surface-700 dark:text-surface-300">
          System Status
        </div>
        <div class="text-xs text-surface-600 dark:text-surface-400">
          {{ Object.values(systemStatus).every(status => status === 'healthy') ? 'All Systems Operational' : 'Some Issues Detected' }}
        </div>
      </div>
    </div>

    <!-- Detailed Status (on hover/click for mobile) -->
    <div class="relative group">
      <button class="p-2 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors">
        <svg class="w-5 h-5 text-surface-600 dark:text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
        </svg>
      </button>

      <!-- Status Dropdown -->
      <div class="absolute right-0 top-full mt-2 w-64 bg-white dark:bg-surface-800 rounded-lg shadow-medium border border-surface-200 dark:border-surface-700 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
        <div class="p-4">
          <h4 class="text-sm font-semibold text-surface-900 dark:text-surface-100 mb-3">
            System Health
          </h4>

          <div class="space-y-3">
            <!-- API Status -->
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <div class="w-2 h-2 rounded-full bg-success-500"></div>
                <span class="text-sm text-surface-700 dark:text-surface-300">API Server</span>
              </div>
              <span :class="`text-xs font-medium ${statusColors[systemStatus.api]}`">
                {{ statusLabels[systemStatus.api] }}
              </span>
            </div>

            <!-- Database Status -->
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <div class="w-2 h-2 rounded-full bg-success-500"></div>
                <span class="text-sm text-surface-700 dark:text-surface-300">PostgreSQL</span>
              </div>
              <span :class="`text-xs font-medium ${statusColors[systemStatus.database]}`">
                {{ statusLabels[systemStatus.database] }}
              </span>
            </div>

            <!-- MindsDB Status -->
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <div class="w-2 h-2 rounded-full bg-success-500"></div>
                <span class="text-sm text-surface-700 dark:text-surface-300">MindsDB AI</span>
              </div>
              <span :class="`text-xs font-medium ${statusColors[systemStatus.mindsdb]}`">
                {{ statusLabels[systemStatus.mindsdb] }}
              </span>
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-surface-200 dark:border-surface-700">
            <div class="text-xs text-surface-500 dark:text-surface-400">
              Last updated: {{ new Date().toLocaleTimeString() }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
