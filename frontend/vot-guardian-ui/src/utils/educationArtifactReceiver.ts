export interface GuardianArtifactPointerV1 {
  schema: 'securedme.education.artifact-pointer.v1'
  pointer_id: string
  source_app: 'visual-algorithm' | string
  target_app: 'vot-guardian'
  artifact_ref: string
  risk_flags: string[]
  consent_required: true
  consent_scope: 'tool' | 'suite'
  created_at: string
  contract_version: 'v1'
  raw_payload_embedded: false
  raw_secret_stored: false
}

export const GUARDIAN_OUTBOX_STORAGE_KEY = 'securedme.education.vot-guardian.outbox.v1'

export interface GuardianProtectionPlanV1 {
  schema: 'securedme.education.guardian-protection-plan.v1'
  plan_id: string
  artifact_ref: string
  source_app: string
  target_app: 'vot-guardian'
  accepted: boolean
  redaction_status: 'pointer-only'
  recommended_actions: string[]
  risk_flags: string[]
  created_at: string
  contract_version: 'v1'
  raw_payload_embedded: false
  raw_secret_stored: false
}

const forbiddenKeys = new Set([
  '.env',
  'api_key',
  'browser_session',
  'client_secret',
  'cookie',
  'oauth_token',
  'password',
  'raw_chat_log',
  'raw_prompt',
  'roster',
  'secret',
  'session_cookie',
  'student_email',
  'student_id',
  'student_name',
  'token',
])

const allowedRawProofKeys = new Set(['raw_payload_embedded', 'raw_secret_stored', 'raw_values_printed'])

function stableId(prefix: string, seed: string): string {
  let hash = 0
  for (let index = 0; index < seed.length; index += 1) {
    hash = (hash << 5) - hash + seed.charCodeAt(index)
    hash |= 0
  }
  return `${prefix}-${Math.abs(hash).toString(16).padStart(8, '0')}`
}

export function hasSecretLikeField(value: unknown): boolean {
  if (Array.isArray(value)) {
    return value.some(hasSecretLikeField)
  }

  if (value && typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>).some(([key, nested]) => {
      const normalized = key.toLowerCase()
      if (allowedRawProofKeys.has(normalized)) {
        return false
      }
      return forbiddenKeys.has(normalized) || normalized.startsWith('raw_') || hasSecretLikeField(nested)
    })
  }

  if (typeof value === 'string') {
    return /((api[_-]?key|access[_-]?token|refresh[_-]?token|oauth[_-]?token|oauth|token|cookie|password|client[_-]?secret)\s*[:=])|bearer\s+[a-z0-9._~+/=-]{12,}/i.test(
      value,
    )
  }

  return false
}

export function validateEducationArtifactPointer(pointer: GuardianArtifactPointerV1): string[] {
  const errors: string[] = []

  if (pointer.schema !== 'securedme.education.artifact-pointer.v1') {
    errors.push('invalid-schema')
  }
  if (pointer.target_app !== 'vot-guardian') {
    errors.push('wrong-target-app')
  }
  if (!pointer.artifact_ref || !pointer.artifact_ref.startsWith('vad:validated-algorithm:')) {
    errors.push('invalid-artifact-ref')
  }
  if (pointer.consent_required !== true) {
    errors.push('missing-consent-requirement')
  }
  if (pointer.raw_payload_embedded !== false || pointer.raw_secret_stored !== false) {
    errors.push('raw-payload-or-secret-present')
  }
  if (hasSecretLikeField(pointer)) {
    errors.push('secret-like-material')
  }

  return errors
}

export function receiveEducationArtifactPointer(pointer: GuardianArtifactPointerV1): GuardianProtectionPlanV1 {
  const errors = validateEducationArtifactPointer(pointer)
  if (errors.length > 0) {
    throw new Error(`Guardian rejected education artifact pointer: ${errors.join(',')}`)
  }

  const riskFlags = Array.from(new Set(pointer.risk_flags)).sort()
  const recommendedActions = [
    'Review artifact through pointer-only mode.',
    riskFlags.includes('secret') ? 'Run secret-handling checklist before sharing.' : 'Confirm no secret-like content is requested.',
    riskFlags.includes('privacy') ? 'Keep learner identity redacted in all exports.' : 'Keep export aggregate-only.',
  ]

  return {
    schema: 'securedme.education.guardian-protection-plan.v1',
    plan_id: stableId('guardian-plan', `${pointer.artifact_ref}:${pointer.pointer_id}`),
    artifact_ref: pointer.artifact_ref,
    source_app: pointer.source_app,
    target_app: 'vot-guardian',
    accepted: true,
    redaction_status: 'pointer-only',
    recommended_actions: recommendedActions,
    risk_flags: riskFlags,
    created_at: new Date().toISOString(),
    contract_version: 'v1',
    raw_payload_embedded: false,
    raw_secret_stored: false,
  }
}

export function readLatestEducationArtifactPointer(): GuardianArtifactPointerV1 | null {
  if (typeof window === 'undefined') {
    return null
  }

  try {
    const parsed = JSON.parse(window.localStorage.getItem(GUARDIAN_OUTBOX_STORAGE_KEY) || '[]')
    if (!Array.isArray(parsed)) {
      return null
    }
    return parsed.find((candidate) => validateEducationArtifactPointer(candidate).length === 0) ?? null
  } catch {
    return null
  }
}
