<script setup lang="ts">
import { ref } from 'vue'
import AudioUpload from './components/AudioUpload.vue'
import AnalysisResults from './components/AnalysisResults.vue'
import SystemStatus from './components/SystemStatus.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import { useAnalysisStore } from './stores/analysis'

interface AnalysisResult {
  call_id: string
  prediction: string
  confidence: number
  processing_time_ms: number
  status: string
}

const analysisStore = useAnalysisStore()
const currentView = ref<'upload' | 'results'>('upload')
const isDark = ref(false)

// Toggle dark mode
const toggleDarkMode = () => {
  isDark.value = !isDark.value
  if (isDark.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// Handle analysis completion
const handleAnalysisComplete = (results: AnalysisResult) => {
  analysisStore.currentAnalysis = results
  currentView.value = 'results'
}

// Handle new analysis request
const handleNewAnalysis = () => {
  analysisStore.clearResults()
  currentView.value = 'upload'
}
</script>

<template>
  <div class="vot-guardian-app min-h-screen transition-colors duration-300"
       :class="{ 'dark': isDark }">

    <!-- Header -->
    <header class="vot-glass backdrop-blur-md border-b border-surface-200 dark:border-surface-700 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">

          <!-- Logo & Title -->
          <div class="flex items-center space-x-4">
            <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center shadow-security">
              <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div>
              <h1 class="text-2xl font-bold vot-text-gradient">V.O.T. Guardian</h1>
              <p class="text-sm text-surface-600 dark:text-surface-400">AI Voice Authentication System</p>
            </div>
          </div>

          <!-- Controls -->
          <div class="flex items-center space-x-4">
            <SystemStatus />
            <ThemeToggle :is-dark="isDark" @toggle="toggleDarkMode" />
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

      <!-- Upload View -->
      <div v-if="currentView === 'upload'" class="space-y-8">
        <!-- Hero Section -->
        <div class="text-center space-y-6">
          <div class="inline-flex items-center px-4 py-2 bg-primary-100 dark:bg-primary-900/30 text-primary-800 dark:text-primary-300 rounded-full text-sm font-medium">
            <div class="w-2 h-2 bg-primary-500 rounded-full mr-2 animate-pulse"></div>
            System Ready for Analysis
          </div>

          <h2 class="text-4xl font-bold text-surface-900 dark:text-surface-100">
            Advanced AI Voice Detection
          </h2>

          <p class="text-xl text-surface-600 dark:text-surface-400 max-w-3xl mx-auto">
            Upload audio files for real-time analysis using our advanced CNN-LSTM model.
            Detect AI-generated voices with industry-leading accuracy and compliance.
          </p>
        </div>

        <!-- Upload Component -->
        <AudioUpload @analysis-complete="handleAnalysisComplete" />
      </div>

      <!-- Results View -->
      <div v-if="currentView === 'results'" class="space-y-8">
        <div class="flex items-center justify-between">
          <h2 class="text-3xl font-bold text-surface-900 dark:text-surface-100">
            Analysis Results
          </h2>
          <button
            @click="handleNewAnalysis"
            class="vot-button-secondary"
          >
            New Analysis
          </button>
        </div>

        <AnalysisResults :results="analysisStore.currentAnalysis" />
      </div>
    </main>

    <!-- Footer -->
    <footer class="vot-glass backdrop-blur-md border-t border-surface-200 dark:border-surface-700 mt-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <div class="flex items-center space-x-4">
            <div class="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <div>
              <p class="text-sm font-medium text-surface-900 dark:text-surface-100">V.O.T. Guardian</p>
              <p class="text-xs text-surface-600 dark:text-surface-400">AI Voice Authentication Platform</p>
            </div>
          </div>

          <div class="flex items-center space-x-6 text-sm text-surface-600 dark:text-surface-400">
            <span>Secured by Tenebris Protocol</span>
            <div class="flex items-center space-x-1">
              <div class="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
              <span>System Operational</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<style>
/* Additional custom styles for V.O.T. Guardian */
.vot-text-gradient {
  background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>
