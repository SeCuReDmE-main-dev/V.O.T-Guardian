import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'
import { apiUrl, USE_MOCK } from '../utils/api'
import {
  receiveEducationArtifactPointer,
  type GuardianArtifactPointerV1,
  type GuardianProtectionPlanV1,
} from '../utils/educationArtifactReceiver'

interface AnalysisResult {
  call_id: string
  prediction: string
  confidence: number
  processing_time_ms: number
  status: string
}

export const useAnalysisStore = defineStore('analysis', () => {
  // State
  const currentAnalysis = ref<AnalysisResult | null>(null)
  const history = ref<AnalysisResult[]>([])
  const latestEducationPlan = ref<GuardianProtectionPlanV1 | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const hasResults = computed(() => !!currentAnalysis.value)
  const latestConfidence = computed(() => currentAnalysis.value?.confidence || 0)
  const isHumanVoice = computed(() => currentAnalysis.value?.prediction === 'HUMAN')
  const isAIVoice = computed(() => currentAnalysis.value?.prediction === 'AI')
  const hasEducationPlan = computed(() => !!latestEducationPlan.value)

  // Actions
  const startAnalysis = async (audioFile?: File) => {
    isLoading.value = true
    error.value = null

    try {
      if (USE_MOCK) {
        const response = await axios.post(apiUrl('/api/v1/analyze'))
        const mock = response.data as { is_ai_voice: boolean; score: number; message: string }

        const results: AnalysisResult = {
          call_id: `mock_${Date.now()}`,
          prediction: mock.is_ai_voice ? 'AI' : 'HUMAN',
          confidence: mock.score,
          processing_time_ms: 0,
          status: 'success',
        }

        currentAnalysis.value = results
        history.value.unshift(results)
        if (history.value.length > 10) history.value = history.value.slice(0, 10)
        return results
      } else {
        if (!audioFile) throw new Error('Audio file is required when VITE_USE_MOCK=false')

        const formData = new FormData()
        formData.append('audio', audioFile)
        formData.append('call_id', `web_${Date.now()}`)

        const response = await axios.post(apiUrl('/analyze'), formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })

        const results: AnalysisResult = response.data
        currentAnalysis.value = results
        history.value.unshift(results)
        if (history.value.length > 10) history.value = history.value.slice(0, 10)
        return results
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        error.value = err.response?.data?.message || 'Failed to analyze audio file'
      } else {
        error.value = 'An unexpected error occurred'
      }
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Mocked analysis: calls backend /api/v1/analyze and maps response to AnalysisResult
   */
  const startAnalysisMock = async () => startAnalysis()

  const clearResults = () => {
    currentAnalysis.value = null
    error.value = null
  }

  const clearHistory = () => {
    history.value = []
  }

  const retryAnalysis = async (audioFile: File) => {
    return await startAnalysis(audioFile)
  }

  const receiveAlgoQuestArtifact = (pointer: GuardianArtifactPointerV1) => {
    const plan = receiveEducationArtifactPointer(pointer)
    latestEducationPlan.value = plan
    return plan
  }

  return {
    // State
    currentAnalysis,
    history,
    latestEducationPlan,
    isLoading,
    error,

    // Getters
    hasResults,
    latestConfidence,
    isHumanVoice,
    isAIVoice,
    hasEducationPlan,

    // Actions
  startAnalysis,
  startAnalysisMock,
    clearResults,
    clearHistory,
    retryAnalysis,
    receiveAlgoQuestArtifact,
  }
})
