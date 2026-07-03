<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { apiUrl } from '../utils/api'

interface TimelineEvent {
  event: string
  at_ms: number
  metadata?: Record<string, unknown>
}

interface ReviewArtifact {
  label: string
  summary: string
  confidence: number
  evidence_gap: string
  frames_received?: number
  bytes_received?: number
  raw_audio_retained?: boolean
}

interface TwilioSession {
  session_id: string
  call_sid: string
  status: string
  frames_received: number
  bytes_received: number
  raw_audio_retained: boolean
  review_state: string
  review_artifacts: ReviewArtifact[]
  timeline: TimelineEvent[]
  errors: Array<{ message: string; at_ms: number }>
}

const sessionId = ref('')
const session = ref<TwilioSession | null>(null)
const isPolling = ref(false)
const error = ref<string | null>(null)
let intervalId: number | undefined

const latestArtifact = computed(() => {
  if (!session.value?.review_artifacts.length) return null
  return session.value.review_artifacts[session.value.review_artifacts.length - 1]
})

const statusClass = computed(() => {
  const status = session.value?.status
  if (status === 'streaming') return 'vot-status-healthy'
  if (status === 'manual_review' || status === 'awaiting_consent') return 'vot-status-warning'
  if (status === 'error' || status === 'blocked') return 'vot-status-danger'
  return 'vot-status-warning'
})

const fetchSession = async () => {
  const trimmed = sessionId.value.trim()
  if (!trimmed) return

  try {
    const response = await fetch(apiUrl(`/api/v1/twilio/sessions/${encodeURIComponent(trimmed)}`))
    if (!response.ok) {
      throw new Error('Session not found')
    }
    session.value = await response.json()
    error.value = null
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Unable to load session'
  }
}

const startPolling = async () => {
  if (intervalId) {
    window.clearInterval(intervalId)
  }
  isPolling.value = true
  await fetchSession()
  intervalId = window.setInterval(fetchSession, 3000)
}

const stopPolling = () => {
  isPolling.value = false
  if (intervalId) {
    window.clearInterval(intervalId)
    intervalId = undefined
  }
}

onUnmounted(stopPolling)
</script>

<template>
  <section class="vot-card twilio-live-panel">
    <div class="twilio-live-panel__header">
      <div>
        <p class="text-sm font-medium text-primary-700 dark:text-primary-300">Twilio Media Streams</p>
        <h3 class="text-2xl font-semibold text-surface-900 dark:text-surface-100">Live Review State</h3>
      </div>
      <span v-if="session" :class="statusClass">{{ session.status.replace('_', ' ') }}</span>
    </div>

    <div class="twilio-live-panel__controls">
      <input
        v-model="sessionId"
        class="vot-input twilio-live-panel__input"
        placeholder="twilio_session_id"
        aria-label="Twilio session identifier"
      >
      <button class="vot-button-primary" type="button" @click="startPolling">
        {{ isPolling ? 'Refresh' : 'Track' }}
      </button>
      <button class="vot-button-secondary" type="button" @click="stopPolling">
        Stop
      </button>
    </div>

    <div v-if="error" class="vot-status-danger">
      {{ error }}
    </div>

    <div v-if="session" class="twilio-live-panel__grid">
      <div>
        <p class="twilio-live-panel__label">Frames</p>
        <p class="twilio-live-panel__value">{{ session.frames_received }}</p>
      </div>
      <div>
        <p class="twilio-live-panel__label">Bytes</p>
        <p class="twilio-live-panel__value">{{ session.bytes_received }}</p>
      </div>
      <div>
        <p class="twilio-live-panel__label">Retention</p>
        <p class="twilio-live-panel__value">
          {{ session.raw_audio_retained ? 'Blocked' : 'None' }}
        </p>
      </div>
      <div>
        <p class="twilio-live-panel__label">Review</p>
        <p class="twilio-live-panel__value">{{ session.review_state }}</p>
      </div>
    </div>

    <div v-if="latestArtifact" class="twilio-live-panel__artifact">
      <p class="twilio-live-panel__label">Latest Artifact</p>
      <h4>{{ latestArtifact.label }}</h4>
      <p>{{ latestArtifact.summary }}</p>
      <p>{{ latestArtifact.evidence_gap }}</p>
    </div>

    <ol v-if="session?.timeline.length" class="twilio-live-panel__timeline">
      <li v-for="item in session.timeline.slice(-5)" :key="`${item.event}-${item.at_ms}`">
        <span>{{ item.event.replace(/_/g, ' ') }}</span>
      </li>
    </ol>
  </section>
</template>
