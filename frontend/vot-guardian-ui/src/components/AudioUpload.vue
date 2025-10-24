<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAnalysisStore } from '../stores/analysis'

interface AnalysisResult {
  call_id: string
  prediction: string
  confidence: number
  processing_time_ms: number
  status: string
}

interface Emits {
  (e: 'analysis-complete', results: AnalysisResult): void
}

const emit = defineEmits<Emits>()
const analysisStore = useAnalysisStore()

// Reactive state
const isDragOver = ref(false)
const isUploading = ref(false)
const selectedFile = ref<File | null>(null)
const uploadProgress = ref(0)
const errorMessage = ref('')

// File validation
const maxFileSize = 10 * 1024 * 1024 // 10MB
const allowedTypes = [
  'audio/wav',
  'audio/mpeg',
  'audio/mp3',
  'audio/ogg',
  'audio/opus'
]

const isValidFile = computed(() => {
  if (!selectedFile.value) return false

  const file = selectedFile.value
  return file.size <= maxFileSize && allowedTypes.includes(file.type)
})

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Drag and drop handlers
const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = (e: DragEvent) => {
  e.preventDefault()
  isDragOver.value = false
}

const handleDrop = (e: DragEvent) => {
  e.preventDefault()
  isDragOver.value = false

  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    const file = files[0]
    if (file) {
      handleFileSelection(file)
    }
  }
}

// File input handler
const handleFileInput = (e: Event) => {
  const files = (e.target as HTMLInputElement).files
  if (files && files.length > 0) {
    const file = files[0]
    if (file) {
      handleFileSelection(file)
    }
  }
}

// File selection logic
const handleFileSelection = (file: File | null) => {
  if (!file) return

  errorMessage.value = ''

  // Validate file type
  if (!allowedTypes.includes(file.type)) {
    errorMessage.value = 'Please select a valid audio file (WAV, MP3, OGG, OPUS)'
    return
  }

  // Validate file size
  if (file.size > maxFileSize) {
    errorMessage.value = 'File size must be less than 10MB'
    return
  }

  selectedFile.value = file
}

// Remove selected file
const removeFile = () => {
  selectedFile.value = null
  errorMessage.value = ''
  uploadProgress.value = 0
}

// Upload and analyze
const uploadAndAnalyze = async () => {
  if (!selectedFile.value || !isValidFile.value) return

  isUploading.value = true
  uploadProgress.value = 0

  try {
    // Simulate progress updates
    const progressInterval = setInterval(() => {
      uploadProgress.value += Math.random() * 15
      if (uploadProgress.value > 90) {
        uploadProgress.value = 90
        clearInterval(progressInterval)
      }
    }, 200)

    // Use store to analyze; store decides mock vs real based on VITE_USE_MOCK
    const results = await analysisStore.startAnalysis(selectedFile.value)

    clearInterval(progressInterval)
    uploadProgress.value = 100

    // Simulate processing time
    await new Promise(resolve => setTimeout(resolve, 1000))

    // Emit results
    emit('analysis-complete', results)

  } catch (error) {
    console.error('Upload error:', error)
    errorMessage.value = analysisStore.error || 'Failed to analyze audio file. Please try again.'
  } finally {
    isUploading.value = false
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <!-- Upload Zone -->
    <div
      class="vot-upload-zone"
      :class="{ 'drag-over': isDragOver }"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
    >
      <!-- File Input (Hidden) -->
      <input
        type="file"
        accept="audio/*"
        @change="handleFileInput"
        class="hidden"
        id="audio-file-input"
      />

      <!-- Upload Interface -->
      <div v-if="!selectedFile" class="text-center">
        <!-- Cloud Upload Icon -->
        <div class="w-16 h-16 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg class="w-8 h-8 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
          </svg>
        </div>

        <!-- Main Message -->
        <h3 class="text-xl font-semibold text-surface-900 dark:text-surface-100 mb-2">
          Upload Audio File
        </h3>
        <p class="text-surface-600 dark:text-surface-400 mb-6">
          Drag and drop your audio file here, or click to browse
        </p>

        <!-- File Requirements -->
        <div class="bg-surface-50 dark:bg-surface-800 rounded-lg p-4 mb-6 max-w-md mx-auto">
          <h4 class="text-sm font-medium text-surface-900 dark:text-surface-100 mb-2">
            Supported Formats:
          </h4>
          <div class="text-sm text-surface-600 dark:text-surface-400 space-y-1">
            <div>• WAV, MP3, OGG, OPUS audio files</div>
            <div>• Maximum file size: 10MB</div>
            <div>• Recommended: 16kHz sample rate</div>
          </div>
        </div>

        <!-- Browse Button -->
        <label
          for="audio-file-input"
          class="vot-button-primary cursor-pointer inline-flex items-center space-x-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
          </svg>
          <span>Choose Audio File</span>
        </label>
      </div>

      <!-- Selected File Preview -->
      <div v-else class="text-center">
        <!-- File Info Card -->
        <div class="vot-card max-w-md mx-auto mb-6">
          <div class="flex items-center space-x-4">
            <!-- Audio Icon -->
            <div class="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/>
              </svg>
            </div>

            <!-- File Details -->
            <div class="flex-1 text-left">
              <h4 class="font-medium text-surface-900 dark:text-surface-100 truncate">
                {{ selectedFile.name }}
              </h4>
              <p class="text-sm text-surface-600 dark:text-surface-400">
                {{ formatFileSize(selectedFile.size) }} • {{ selectedFile.type }}
              </p>
            </div>

            <!-- Remove Button -->
            <button
              @click="removeFile"
              class="p-2 text-surface-400 hover:text-danger-500 rounded-lg hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded-lg p-4 mb-6">
          <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-danger-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span class="text-danger-700 dark:text-danger-300">{{ errorMessage }}</span>
          </div>
        </div>

        <!-- Upload Progress -->
        <div v-if="analysisStore.isLoading" class="mb-6">
          <div class="flex items-center justify-center space-x-4 mb-4">
            <div class="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin"></div>
            <span class="text-surface-700 dark:text-surface-300">Analyzing audio file...</span>
          </div>

          <!-- Progress Bar -->
          <div class="w-full max-w-md mx-auto bg-surface-200 dark:bg-surface-700 rounded-full h-2">
            <div
              class="bg-primary-600 h-2 rounded-full transition-all duration-300 ease-out"
              :style="{ width: `${uploadProgress}%` }"
            ></div>
          </div>
          <p class="text-center text-sm text-surface-600 dark:text-surface-400 mt-2">
            {{ Math.round(uploadProgress) }}% complete
          </p>
        </div>

        <!-- Analyze Button -->
        <div v-if="!isUploading" class="space-y-4">
          <button
            v-if="isValidFile"
            @click="uploadAndAnalyze"
            class="vot-button-primary text-lg px-8 py-4"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
            Analyze Audio
          </button>

          <p v-else class="text-surface-500 dark:text-surface-400">
            Please select a valid audio file to continue
          </p>
        </div>
      </div>
    </div>

    <!-- Security Notice -->
    <div class="mt-8 text-center">
      <div class="inline-flex items-center space-x-2 text-sm text-surface-600 dark:text-surface-400 bg-surface-50 dark:bg-surface-800 px-4 py-2 rounded-lg">
        <svg class="w-4 h-4 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
        </svg>
  <span>Secured by Tenebris Protocol • Automatic data destruction in &lt;100ms</span>
      </div>
    </div>
  </div>
</template>
