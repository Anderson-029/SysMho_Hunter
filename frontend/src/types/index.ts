export interface Target {
  id: string
  name: string
  organization?: string
  h1_program_slug?: string
  status: string
  priority: number
  platform?: string
  program_url?: string
  rules_md?: string
  bounty_table?: Record<string, string>
  out_of_scope_notes?: string
  safe_harbor: boolean
  scopes: Scope[]
  created_at: string
}

export interface Scope {
  id: string
  scope_type: string
  value: string
  is_in_scope: boolean
}

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
