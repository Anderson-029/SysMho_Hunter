import { useState } from 'react'
import {
  Save,
  X,
  AlertTriangle,
  Info,
  Shield,
  DollarSign,
  Zap,
  FileText,
} from 'lucide-react'
import type { Target, BountyTiers, ActiveCampaign } from '../types'

interface TargetFormProps {
  onSubmit: (data: Partial<Target>) => Promise<void>
  onClose: () => void
  initialData?: Partial<Target>
  isLoading?: boolean
}

type Tab = 'overview' | 'highlights' | 'rewards' | 'campaign' | 'rules'

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'overview', label: 'Overview', icon: <Info size={15} /> },
  { id: 'highlights', label: 'Highlights', icon: <Shield size={15} /> },
  { id: 'rewards', label: 'Rewards', icon: <DollarSign size={15} /> },
  { id: 'campaign', label: 'Campaign', icon: <Zap size={15} /> },
  { id: 'rules', label: 'Rules & Scope', icon: <FileText size={15} /> },
]

const SEVERITIES = ['low', 'medium', 'high', 'critical'] as const
const FOCUS_AREA_OPTIONS = [
  'RCE',
  'Auth Bypass',
  'SQLi',
  'SSRF',
  'XSS',
  'XXE',
  'IDOR',
  'Broken Access Control',
  'Sensitive Data Exposure',
  'Malicious File Upload',
  'AWS Credentials Exposure',
  'Misconfigured Cloud',
  'CSRF',
  'Open Redirect',
  'Business Logic',
]

const FEATURE_OPTIONS = [
  { value: 'fast_payment', label: 'Fast Payment' },
  { value: 'gold_safe_harbor', label: 'Gold Standard Safe Harbor' },
  { value: 'platform_standards', label: 'Platform Standards' },
  { value: 'top_response_efficiency', label: 'Top Response Efficiency' },
  { value: 'managed_by_h1', label: 'Managed by HackerOne' },
  { value: 'collaboration_enabled', label: 'Collaboration Enabled' },
  { value: 'includes_retesting', label: 'Includes Retesting' },
]

const inputClass =
  'w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none text-sm'
const labelClass = 'block text-sm font-medium text-gray-300 mb-1'
const sectionClass = 'text-base font-semibold text-gray-200 mb-3'

export function TargetForm({
  onSubmit,
  onClose,
  initialData,
  isLoading = false,
}: TargetFormProps) {
  const [activeTab, setActiveTab] = useState<Tab>('overview')

  // ── Overview ──────────────────────────────────────────────────────────────
  const [name, setName] = useState(initialData?.name ?? '')
  const [organization, setOrganization] = useState(
    initialData?.organization ?? ''
  )
  const [h1Slug, setH1Slug] = useState(initialData?.h1_program_slug ?? '')
  const [platform, setPlatform] = useState(
    initialData?.platform ?? 'hackerone'
  )
  const [programUrl, setProgramUrl] = useState(initialData?.program_url ?? '')
  const [priority, setPriority] = useState(initialData?.priority ?? 5)
  const [notes, setNotes] = useState(initialData?.notes ?? '')

  // ── Highlights ────────────────────────────────────────────────────────────
  const [safeHarbor, setSafeHarbor] = useState(
    initialData?.safe_harbor ?? true
  )
  const [responseEfficiency, setResponseEfficiency] = useState(
    initialData?.response_efficiency_pct?.toString() ?? ''
  )
  const [avgResponse, setAvgResponse] = useState(
    initialData?.avg_response_hours?.toString() ?? ''
  )
  const [avgTriage, setAvgTriage] = useState(
    initialData?.avg_triage_hours?.toString() ?? ''
  )
  const [avgBounty, setAvgBounty] = useState(
    initialData?.avg_bounty_hours?.toString() ?? ''
  )
  const [avgResolution, setAvgResolution] = useState(
    initialData?.avg_resolution_hours?.toString() ?? ''
  )
  const [programFeatures, setProgramFeatures] = useState<string[]>(
    initialData?.program_features ?? []
  )
  const [tagInput, setTagInput] = useState('')
  const [programTags, setProgramTags] = useState<string[]>(
    initialData?.program_tags ?? []
  )

  // ── Rewards ───────────────────────────────────────────────────────────────
  const initRange = (tier: 'primary' | 'secondary', sev: string) => {
    const t = initialData?.bounty_tiers?.[tier] as Record<
      string,
      { min?: number; max?: number; avg?: number }
    >
    return {
      min: t?.[sev]?.min?.toString() ?? '',
      max: t?.[sev]?.max?.toString() ?? '',
      avg: t?.[sev]?.avg?.toString() ?? '',
    }
  }

  const [primaryBounty, setPrimaryBounty] = useState({
    low: initRange('primary', 'low'),
    medium: initRange('primary', 'medium'),
    high: initRange('primary', 'high'),
    critical: initRange('primary', 'critical'),
  })
  const [hasSecondary, setHasSecondary] = useState(
    !!initialData?.bounty_tiers?.secondary
  )
  const [secondaryBounty, setSecondaryBounty] = useState({
    low: initRange('secondary', 'low'),
    medium: initRange('secondary', 'medium'),
    high: initRange('secondary', 'high'),
    critical: initRange('secondary', 'critical'),
  })

  // ── Campaign ──────────────────────────────────────────────────────────────
  const [hasCampaign, setHasCampaign] = useState(!!initialData?.active_campaign)
  const [campaignEndDate, setCampaignEndDate] = useState(
    initialData?.active_campaign?.end_date ?? ''
  )
  const [campaignDescription, setCampaignDescription] = useState(
    initialData?.active_campaign?.description ?? ''
  )
  const [campaignMultipliers, setCampaignMultipliers] = useState({
    low: initialData?.active_campaign?.bounty_multipliers?.low?.toString() ?? '',
    medium:
      initialData?.active_campaign?.bounty_multipliers?.medium?.toString() ?? '',
    high:
      initialData?.active_campaign?.bounty_multipliers?.high?.toString() ?? '',
    critical:
      initialData?.active_campaign?.bounty_multipliers?.critical?.toString() ??
      '',
  })

  // ── Rules & Scope ─────────────────────────────────────────────────────────
  const [introductionMd, setIntroductionMd] = useState(
    initialData?.introduction_md ?? ''
  )
  const [rulesMd, setRulesMd] = useState(initialData?.rules_md ?? '')
  const [disclosurePolicy, setDisclosurePolicy] = useState(
    initialData?.disclosure_policy ?? ''
  )
  const [outOfScopeNotes, setOutOfScopeNotes] = useState(
    initialData?.out_of_scope_notes ?? ''
  )
  const [focusAreas, setFocusAreas] = useState<string[]>(
    initialData?.focus_areas ?? []
  )

  // ── Helpers ───────────────────────────────────────────────────────────────
  const toggleFeature = (f: string) =>
    setProgramFeatures(prev =>
      prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
    )

  const toggleFocusArea = (a: string) =>
    setFocusAreas(prev =>
      prev.includes(a) ? prev.filter(x => x !== a) : [...prev, a]
    )

  const addTag = () => {
    const t = tagInput.trim()
    if (t && !programTags.includes(t)) setProgramTags(prev => [...prev, t])
    setTagInput('')
  }

  const buildBountyTier = (data: typeof primaryBounty) =>
    Object.fromEntries(
      SEVERITIES.map(sev => [
        sev,
        {
          ...(data[sev].min ? { min: Number(data[sev].min) } : {}),
          ...(data[sev].max ? { max: Number(data[sev].max) } : {}),
          ...(data[sev].avg ? { avg: Number(data[sev].avg) } : {}),
        },
      ]).filter(([, v]) => Object.keys(v).length > 0)
    )

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleSubmit = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault()

    const bounty_tiers: BountyTiers = {
      primary: buildBountyTier(primaryBounty) as BountyTiers['primary'],
      ...(hasSecondary
        ? {
            secondary: buildBountyTier(
              secondaryBounty
            ) as BountyTiers['secondary'],
          }
        : {}),
    }

    const active_campaign: ActiveCampaign | undefined = hasCampaign
      ? {
          end_date: campaignEndDate || undefined,
          description: campaignDescription || undefined,
          bounty_multipliers: {
            ...(campaignMultipliers.low
              ? { low: Number(campaignMultipliers.low) }
              : {}),
            ...(campaignMultipliers.medium
              ? { medium: Number(campaignMultipliers.medium) }
              : {}),
            ...(campaignMultipliers.high
              ? { high: Number(campaignMultipliers.high) }
              : {}),
            ...(campaignMultipliers.critical
              ? { critical: Number(campaignMultipliers.critical) }
              : {}),
          },
        }
      : undefined

    await onSubmit({
      name,
      organization: organization || undefined,
      h1_program_slug: h1Slug || undefined,
      platform,
      program_url: programUrl || undefined,
      priority,
      notes: notes || undefined,
      introduction_md: introductionMd || undefined,
      rules_md: rulesMd || undefined,
      disclosure_policy: disclosurePolicy || undefined,
      out_of_scope_notes: outOfScopeNotes || undefined,
      safe_harbor: safeHarbor,
      program_features: programFeatures.length ? programFeatures : undefined,
      program_tags: programTags.length ? programTags : undefined,
      response_efficiency_pct: responseEfficiency
        ? Number(responseEfficiency)
        : undefined,
      avg_response_hours: avgResponse ? Number(avgResponse) : undefined,
      avg_triage_hours: avgTriage ? Number(avgTriage) : undefined,
      avg_bounty_hours: avgBounty ? Number(avgBounty) : undefined,
      avg_resolution_hours: avgResolution ? Number(avgResolution) : undefined,
      bounty_tiers,
      active_campaign,
      focus_areas: focusAreas.length ? focusAreas : undefined,
    })
  }

  // ── BountyRow helper component ────────────────────────────────────────────
  const BountyRow = ({
    sev,
    data,
    onChange,
  }: {
    sev: string
    data: { min: string; max: string; avg: string }
    onChange: (field: 'min' | 'max' | 'avg', val: string) => void
  }) => {
    const colors: Record<string, string> = {
      low: 'text-green-400',
      medium: 'text-yellow-400',
      high: 'text-orange-400',
      critical: 'text-red-400',
    }
    return (
      <div className="grid grid-cols-4 gap-2 items-center">
        <span className={`text-sm font-medium capitalize ${colors[sev]}`}>
          {sev}
        </span>
        {(['min', 'max', 'avg'] as const).map(field => (
          <input
            key={field}
            type="number"
            placeholder={field === 'avg' ? 'avg (opt)' : field}
            value={data[field]}
            onChange={e => onChange(field, e.target.value)}
            className={inputClass}
          />
        ))}
      </div>
    )
  }

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-3xl max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-gray-700">
          <h2 className="text-lg font-bold text-white">
            {initialData ? 'Editar Programa' : 'Crear Programa Manual'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X size={22} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700 px-6">
          {TABS.map(tab => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 transition ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <form
          onSubmit={handleSubmit}
          className="flex flex-col flex-1 overflow-hidden"
        >
          <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
            {/* ── TAB: OVERVIEW ── */}
            {activeTab === 'overview' && (
              <>
                <p className={sectionClass}>Información Básica</p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass}>Nombre del Programa *</label>
                    <input
                      required
                      type="text"
                      value={name}
                      onChange={e => setName(e.target.value)}
                      className={inputClass}
                      placeholder="ej: 23andMe Bug Bounty"
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Organización</label>
                    <input
                      type="text"
                      value={organization}
                      onChange={e => setOrganization(e.target.value)}
                      className={inputClass}
                      placeholder="ej: 23andMe"
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Plataforma</label>
                    <select
                      value={platform}
                      onChange={e => setPlatform(e.target.value)}
                      className={inputClass}
                    >
                      <option value="hackerone">HackerOne</option>
                      <option value="bugcrowd">Bugcrowd</option>
                      <option value="intigriti">Intigriti</option>
                      <option value="yeswehack">YesWeHack</option>
                    </select>
                  </div>
                  <div>
                    <label className={labelClass}>Program Slug (H1)</label>
                    <input
                      type="text"
                      value={h1Slug}
                      onChange={e => setH1Slug(e.target.value)}
                      className={inputClass}
                      placeholder="ej: 23andme"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className={labelClass}>URL del Programa</label>
                    <input
                      type="url"
                      value={programUrl}
                      onChange={e => setProgramUrl(e.target.value)}
                      className={inputClass}
                      placeholder="https://hackerone.com/23andme"
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Prioridad (1-10)</label>
                    <input
                      type="number"
                      min={1}
                      max={10}
                      value={priority}
                      onChange={e => setPriority(Number(e.target.value))}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Notas internas</label>
                    <input
                      type="text"
                      value={notes}
                      onChange={e => setNotes(e.target.value)}
                      className={inputClass}
                      placeholder="Notas personales sobre este programa"
                    />
                  </div>
                </div>
              </>
            )}

            {/* ── TAB: HIGHLIGHTS ── */}
            {activeTab === 'highlights' && (
              <>
                {/* Safe Harbor */}
                <div
                  className={`flex items-center gap-3 p-3 rounded border ${
                    safeHarbor
                      ? 'border-green-700 bg-green-900/20'
                      : 'border-yellow-700 bg-yellow-900/20'
                  }`}
                >
                  <input
                    type="checkbox"
                    id="safe_harbor"
                    checked={safeHarbor}
                    onChange={e => setSafeHarbor(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <label htmlFor="safe_harbor" className="text-sm text-gray-300">
                    El programa tiene Safe Harbor
                  </label>
                  {!safeHarbor && (
                    <div className="flex items-center gap-1 text-yellow-400 text-xs ml-auto">
                      <AlertTriangle size={14} />
                      Sin protección legal
                    </div>
                  )}
                </div>

                {/* Response efficiency */}
                <div>
                  <label className={labelClass}>
                    Response Efficiency (%)
                    <span className="text-gray-500 font-normal ml-1">
                      — ej: 90 = Top Response Efficiency
                    </span>
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={responseEfficiency}
                    onChange={e => setResponseEfficiency(e.target.value)}
                    className={inputClass}
                    placeholder="ej: 90"
                  />
                </div>

                {/* Timing stats */}
                <div>
                  <p className={sectionClass}>
                    Estadísticas de Respuesta (en horas)
                  </p>
                  <div className="grid grid-cols-2 gap-4">
                    {(
                      [
                        ['avg_response_hours', 'Avg. Time to First Response', avgResponse, setAvgResponse],
                        ['avg_triage_hours', 'Avg. Time to Triage', avgTriage, setAvgTriage],
                        ['avg_bounty_hours', 'Avg. Time to Bounty', avgBounty, setAvgBounty],
                        ['avg_resolution_hours', 'Avg. Time to Resolution', avgResolution, setAvgResolution],
                      ] as [string, string, string, (v: string) => void][]
                    ).map(([, label, val, setter]) => (
                      <div key={label}>
                        <label className={labelClass}>{label}</label>
                        <input
                          type="number"
                          min={0}
                          value={val}
                          onChange={e => setter(e.target.value)}
                          className={inputClass}
                          placeholder="horas"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Program features */}
                <div>
                  <p className={sectionClass}>Program Features / Badges</p>
                  <div className="grid grid-cols-2 gap-2">
                    {FEATURE_OPTIONS.map(f => (
                      <label
                        key={f.value}
                        className="flex items-center gap-2 p-2 rounded bg-gray-800 border border-gray-700 cursor-pointer hover:border-blue-600 transition"
                      >
                        <input
                          type="checkbox"
                          checked={programFeatures.includes(f.value)}
                          onChange={() => toggleFeature(f.value)}
                          className="w-4 h-4"
                        />
                        <span className="text-sm text-gray-300">{f.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Custom tags */}
                <div>
                  <p className={sectionClass}>Program Tags personalizados</p>
                  <div className="flex gap-2 mb-2">
                    <input
                      type="text"
                      value={tagInput}
                      onChange={e => setTagInput(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addTag())}
                      className={inputClass}
                      placeholder='ej: "Includes Retesting" y presiona Enter'
                    />
                    <button
                      type="button"
                      onClick={addTag}
                      className="px-3 py-2 bg-gray-700 text-white rounded text-sm hover:bg-gray-600"
                    >
                      +
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {programTags.map(tag => (
                      <span
                        key={tag}
                        className="flex items-center gap-1 px-2 py-1 bg-blue-900/40 border border-blue-700 text-blue-300 rounded text-xs"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() =>
                            setProgramTags(prev => prev.filter(t => t !== tag))
                          }
                          className="text-blue-400 hover:text-white"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* ── TAB: REWARDS ── */}
            {activeTab === 'rewards' && (
              <>
                <p className={sectionClass}>Primary Targets — Bounty Ranges (USD)</p>
                <div className="space-y-2">
                  <div className="grid grid-cols-4 gap-2 text-xs text-gray-500 font-medium px-0">
                    <span>Severity</span>
                    <span>Min $</span>
                    <span>Max $</span>
                    <span>Avg $ (opt)</span>
                  </div>
                  {SEVERITIES.map(sev => (
                    <BountyRow
                      key={sev}
                      sev={sev}
                      data={primaryBounty[sev]}
                      onChange={(field, val) =>
                        setPrimaryBounty(prev => ({
                          ...prev,
                          [sev]: { ...prev[sev], [field]: val },
                        }))
                      }
                    />
                  ))}
                </div>

                <div className="flex items-center gap-3 mt-4 pt-4 border-t border-gray-700">
                  <input
                    type="checkbox"
                    id="has_secondary"
                    checked={hasSecondary}
                    onChange={e => setHasSecondary(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <label
                    htmlFor="has_secondary"
                    className="text-sm text-gray-300"
                  >
                    El programa tiene Secondary Targets con bounty diferente
                  </label>
                </div>

                {hasSecondary && (
                  <div className="space-y-2 mt-3">
                    <p className={sectionClass}>
                      Secondary Targets — Bounty Ranges (USD)
                    </p>
                    <div className="grid grid-cols-4 gap-2 text-xs text-gray-500 font-medium">
                      <span>Severity</span>
                      <span>Min $</span>
                      <span>Max $</span>
                      <span>Avg $ (opt)</span>
                    </div>
                    {SEVERITIES.map(sev => (
                      <BountyRow
                        key={sev}
                        sev={sev}
                        data={secondaryBounty[sev]}
                        onChange={(field, val) =>
                          setSecondaryBounty(prev => ({
                            ...prev,
                            [sev]: { ...prev[sev], [field]: val },
                          }))
                        }
                      />
                    ))}
                  </div>
                )}
              </>
            )}

            {/* ── TAB: CAMPAIGN ── */}
            {activeTab === 'campaign' && (
              <>
                <div className="flex items-center gap-3 p-3 rounded border border-gray-700 bg-gray-800">
                  <input
                    type="checkbox"
                    id="has_campaign"
                    checked={hasCampaign}
                    onChange={e => setHasCampaign(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <label htmlFor="has_campaign" className="text-sm text-gray-300">
                    El programa tiene una campaña activa
                  </label>
                </div>

                {hasCampaign && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className={labelClass}>Fecha de fin</label>
                        <input
                          type="date"
                          value={campaignEndDate}
                          onChange={e => setCampaignEndDate(e.target.value)}
                          className={inputClass}
                        />
                      </div>
                    </div>

                    <div>
                      <label className={labelClass}>Descripción de la campaña</label>
                      <textarea
                        rows={3}
                        value={campaignDescription}
                        onChange={e => setCampaignDescription(e.target.value)}
                        className={inputClass}
                        placeholder="ej: Focused on RCE, Auth Bypass, broken access control..."
                      />
                    </div>

                    <div>
                      <p className={sectionClass}>
                        Multiplicadores de bounty durante campaña
                      </p>
                      <div className="grid grid-cols-2 gap-3">
                        {SEVERITIES.map(sev => {
                          const colors: Record<string, string> = {
                            low: 'text-green-400',
                            medium: 'text-yellow-400',
                            high: 'text-orange-400',
                            critical: 'text-red-400',
                          }
                          return (
                            <div key={sev}>
                              <label
                                className={`${labelClass} capitalize ${colors[sev]}`}
                              >
                                {sev} multiplier
                              </label>
                              <input
                                type="number"
                                step="0.25"
                                min={1}
                                value={
                                  campaignMultipliers[
                                    sev as keyof typeof campaignMultipliers
                                  ]
                                }
                                onChange={e =>
                                  setCampaignMultipliers(prev => ({
                                    ...prev,
                                    [sev]: e.target.value,
                                  }))
                                }
                                className={inputClass}
                                placeholder="ej: 1.5 = 1.5x"
                              />
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </>
                )}
              </>
            )}

            {/* ── TAB: RULES & SCOPE ── */}
            {activeTab === 'rules' && (
              <>
                <div>
                  <label className={labelClass}>
                    Introducción / Welcome Text
                  </label>
                  <textarea
                    rows={3}
                    value={introductionMd}
                    onChange={e => setIntroductionMd(e.target.value)}
                    className={`${inputClass} font-mono`}
                    placeholder="Welcome, Security Research Community!&#10;We encourage responsible disclosure..."
                  />
                </div>

                <div>
                  <label className={labelClass}>
                    Reglas del Programa (Markdown)
                  </label>
                  <textarea
                    rows={6}
                    value={rulesMd}
                    onChange={e => setRulesMd(e.target.value)}
                    className={`${inputClass} font-mono`}
                    placeholder="## Program Rules&#10;- Use your HackerOne email alias&#10;- Add X-HackerOne-Research header&#10;..."
                  />
                </div>

                <div>
                  <label className={labelClass}>
                    Focus Areas — Vulnerabilities de Alto Valor
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {FOCUS_AREA_OPTIONS.map(area => (
                      <button
                        key={area}
                        type="button"
                        onClick={() => toggleFocusArea(area)}
                        className={`px-3 py-1 rounded text-xs border transition ${
                          focusAreas.includes(area)
                            ? 'bg-red-900/40 border-red-600 text-red-300'
                            : 'bg-gray-800 border-gray-600 text-gray-400 hover:border-gray-400'
                        }`}
                      >
                        {area}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className={labelClass}>
                    Out-of-Scope Notes
                  </label>
                  <textarea
                    rows={3}
                    value={outOfScopeNotes}
                    onChange={e => setOutOfScopeNotes(e.target.value)}
                    className={inputClass}
                    placeholder="ej: No testear: Backups, Staging, Employee systems, CustomerCare Portal..."
                  />
                </div>

                <div>
                  <label className={labelClass}>Disclosure Policy</label>
                  <textarea
                    rows={2}
                    value={disclosurePolicy}
                    onChange={e => setDisclosurePolicy(e.target.value)}
                    className={inputClass}
                    placeholder="ej: Follow HackerOne's disclosure guidelines. Unauthorized public disclosure may result in disqualification."
                  />
                </div>
              </>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-between items-center px-6 py-4 border-t border-gray-700 bg-gray-900">
            <div className="flex gap-1">
              {TABS.map(tab => (
                <div
                  key={tab.id}
                  className={`w-2 h-2 rounded-full transition ${
                    activeTab === tab.id ? 'bg-blue-500' : 'bg-gray-600'
                  }`}
                />
              ))}
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={onClose}
                disabled={isLoading}
                className="px-4 py-2 text-sm text-gray-300 border border-gray-700 rounded hover:bg-gray-800 transition disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={isLoading || !name.trim()}
                className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded flex items-center gap-2 transition disabled:opacity-50"
              >
                <Save size={16} />
                {isLoading ? 'Guardando...' : initialData ? 'Guardar cambios' : 'Crear Programa'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
