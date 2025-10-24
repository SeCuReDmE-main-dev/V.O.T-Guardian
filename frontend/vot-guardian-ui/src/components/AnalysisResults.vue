<script setup lang="ts">
import { computed } from 'vue'

interface AnalysisResult {
  call_id: string
  prediction: string
  confidence: number
  processing_time_ms: number
  status: string
}

const props = defineProps<{
  results: AnalysisResult | null
}>()

const confidencePercentage = computed(() => {
  return Math.round((props.results?.confidence || 0) * 100)
})

const confidenceColor = computed(() => {
  const conf = props.results?.confidence || 0
  if (conf >= 0.8) return 'success'
  if (conf >= 0.6) return 'warning'
  return 'danger'
})

const formatTime = (ms: number) => {
  return `${(ms / 1000).toFixed(2)}s`
}
</script>

<template>
  <div class="space-y-6">
    <!-- Main Result Card -->
    <div v-if="results" class="vot-result-card">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-2xl font-bold text-surface-900 dark:text-surface-100">
          Analysis Complete
        </h3>
        <div class="flex items-center space-x-2">
          <div :class="`vot-status-${confidenceColor}`">
            {{ confidencePercentage }}% Confidence
          </div>
        </div>
      </div>

      <!-- Prediction Result -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-32 h-32 rounded-full mb-4"
             :class="{
               'bg-success-100 text-success-800 dark:bg-success-900/30 dark:text-success-400': results.prediction === 'HUMAN',
               'bg-danger-100 text-danger-800 dark:bg-danger-900/30 dark:text-danger-400': results.prediction === 'AI'
             }">
          <span class="text-4xl font-bold">
            {{ results.prediction === 'HUMAN' ? '👤' : '🤖' }}
          </span>
        </div>
        <h4 class="text-3xl font-bold text-surface-900 dark:text-surface-100 mb-2">
          {{ results.prediction === 'HUMAN' ? 'Human Voice' : 'AI Generated' }}
        </h4>
        <p class="text-surface-600 dark:text-surface-400">
          {{ confidencePercentage }}% confidence level
        </p>
      </div>

      <!-- Detailed Metrics -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Confidence Score -->
        <div class="text-center">
          <div class="text-3xl font-bold text-primary-600 dark:text-primary-400 mb-2">
            {{ confidencePercentage }}%
          </div>
          <div class="text-sm text-surface-600 dark:text-surface-400">
            Confidence Score
          </div>
          <div class="vot-confidence-bar mt-3">
            <div
              class="vot-confidence-fill"
              :style="{ width: `${confidencePercentage}%` }"
            ></div>
          </div>
        </div>

        <!-- Processing Time -->
        <div class="text-center">
          <div class="text-3xl font-bold text-surface-900 dark:text-surface-100 mb-2">
            {{ formatTime(results.processing_time_ms) }}
          </div>
          <div class="text-sm text-surface-600 dark:text-surface-400">
            Processing Time
          </div>
        </div>

        <!-- Call ID -->
        <div class="text-center">
          <div class="text-sm font-mono text-surface-600 dark:text-surface-400 mb-2">
            Call ID
          </div>
          <div class="text-xs font-mono bg-surface-100 dark:bg-surface-800 px-3 py-2 rounded">
            {{ results.call_id?.slice(0, 16) }}...
          </div>
        </div>
      </div>
    </div>

    <!-- Technical Details -->
    <div v-if="results" class="vot-card">
      <h4 class="text-lg font-semibold text-surface-900 dark:text-surface-100 mb-4">
        Technical Analysis
      </h4>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h5 class="font-medium text-surface-900 dark:text-surface-100 mb-3">
            Audio Features Extracted
          </h5>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-surface-600 dark:text-surface-400">Voice Onset Time:</span>
              <span class="font-mono text-surface-900 dark:text-surface-100">0.400s</span>
            </div>
            <div class="flex justify-between">
              <span class="text-surface-600 dark:text-surface-400">Jitter:</span>
              <span class="font-mono text-surface-900 dark:text-surface-100">0.050</span>
            </div>
            <div class="flex justify-between">
              <span class="text-surface-600 dark:text-surface-400">Shimmer:</span>
              <span class="font-mono text-surface-900 dark:text-surface-100">0.100</span>
            </div>
            <div class="flex justify-between">
              <span class="text-surface-600 dark:text-surface-400">SNR:</span>
              <span class="font-mono text-surface-900 dark:text-surface-100">20.0 dB</span>
            </div>
          </div>
        </div>

        <div>
          <h5 class="font-medium text-surface-900 dark:text-surface-100 mb-3">
            Model Information
          </h5>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-surface-600 dark:text-surface-400">Model Version:</span>
              <span class="font-mono text-surface-900 dark:text-surface-100">CNN-LSTM v2.1</span>
            </div>
            <div class="flex justify-between">
              <span class="text-surface-600 dark:text-surface-400">Processing Engine:</span>
              <span class="font-mono text-surface-900 dark:text-surface-100">Tenebris Protocol</span>
            </div>
            <div class="flex justify-between">
              <span class="text-surface-600 dark:text-surface-400">Security Status:</span>
              <span class="font-mono text-success-600 dark:text-success-400">Compliant</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Results State -->
    <div v-else class="text-center py-12">
      <div class="w-16 h-16 bg-surface-100 dark:bg-surface-800 rounded-full flex items-center justify-center mx-auto mb-4">
        <svg class="w-8 h-8 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
        </svg>
      </div>
      <h3 class="text-lg font-medium text-surface-900 dark:text-surface-100 mb-2">
        No Analysis Results
      </h3>
      <p class="text-surface-600 dark:text-surface-400">
        Upload an audio file to see analysis results here.
      </p>
    </div>
  </div>
</template>
