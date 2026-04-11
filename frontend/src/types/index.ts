// ─────────────────────────────────────────────────────────────────────────────
// BOUNTY
// ─────────────────────────────────────────────────────────────────────────────

export interface BountyRange {
  min?: number
  max?: number
  avg?: number
}

export interface BountyTierTable {
  low?: BountyRange
  medium?: BountyRange
  high?: BountyRange
  critical?: BountyRange
}

export interface BountyTiers {
  primary?: BountyTierTable
  secondary?: BountyTierTable
}

// ─────────────────────────────────────────────────────────────────────────────
// CAMPAIGN
// ─────────────────────────────────────────────────────────────────────────────

export interface CampaignMultipliers {
  low?: number
  medium?: number
  high?: number
  critical?: number
}

export interface ActiveCampaign {
  end_date?: string
  description?: string
  asset_count?: number
  bounty_multipliers?: CampaignMultipliers
}

// ─────────────────────────────────────────────────────────────────────────────
// SCOPE
// ─────────────────────────────────────────────────────────────────────────────

export interface Scope {
  id: string
  target_id: string
  scope_type: string
  value: string
  is_in_scope: boolean
  tier?: 'primary' | 'secondary'
  notes?: string
  created_at: string
}

// ─────────────────────────────────────────────────────────────────────────────
// TARGET
// ─────────────────────────────────────────────────────────────────────────────

export interface Target {
  id: string
  name: string
  organization?: string
  h1_program_slug?: string
  status: string
  priority: number
  notes?: string
  platform?: string
  program_url?: string

  // Contenido del programa
  introduction_md?: string
  rules_md?: string
  disclosure_policy?: string
  out_of_scope_notes?: string
  safe_harbor: boolean

  // Badges y features
  program_features?: string[]
  program_tags?: string[]

  // Métricas de respuesta (en horas)
  response_efficiency_pct?: number
  avg_response_hours?: number
  avg_triage_hours?: number
  avg_bounty_hours?: number
  avg_resolution_hours?: number

  // Recompensas
  bounty_tiers?: BountyTiers

  // Campaña activa
  active_campaign?: ActiveCampaign

  // Vuln types priorizadas
  focus_areas?: string[]

  scopes: Scope[]
  created_at: string
}

// ─────────────────────────────────────────────────────────────────────────────
// SCAN / FINDING / ACTIONS / LOGS
// ─────────────────────────────────────────────────────────────────────────────

export interface Scan {
  id: string
  target_id: string
  scan_type: string
  status: string
  phase?: string
  started_at?: string
  completed_at?: string
  error_message?: string
  created_at: string
}

export interface Finding {
  id: string
  scan_id?: string
  target_id: string
  title: string
  description?: string
  vuln_type?: string
  severity?: string
  cvss_score?: number
  cwe_id?: string
  url?: string
  status: string
  ml_severity?: string
  ml_confidence?: number
  brain_reasoning?: string
  discovered_at: string
}

export interface PendingAction {
  id: string
  action_type: string
  description: string
  risk_level: string
  risk_reason?: string
  status: string
  requested_by: string
  reviewed_by?: string
  created_at: string
}

export interface AgentLog {
  id?: string
  scan_id?: string
  log_level: string
  component?: string
  message: string
  created_at?: string
}
