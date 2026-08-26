/**
 * Types mirror backend_api/schemas/responses.py field-for-field. Nothing
 * here is invented — every field corresponds to a column or metric the
 * API already returns, which in turn corresponds to a column/metric the
 * original Streamlit app already displayed.
 */

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export const RISK_LEVELS: RiskLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

export interface HealthResponse {
  status: string
  service: string
}

export interface RiskDistributionEntry {
  risk_level: RiskLevel
  count: number
  pct_of_total: number
}

export interface SpoilageRateEntry {
  risk_level: RiskLevel
  observed_spoilage_rate: number
}

export interface InterventionScopeSummary {
  batch_level: number
  replenishment_only: number
  none: number
}

export interface SummaryResponse {
  total_batches: number
  high_critical_batches: number
  high_critical_pct_of_total: number
  total_expected_waste_exposure: number
  base_scenario_waste_reduction_pct: number
  risk_distribution: RiskDistributionEntry[]
  spoilage_rate_by_risk_level: SpoilageRateEntry[]
  intervention_scope_summary: InterventionScopeSummary
}

export interface BatchRecord {
  batch_id: string
  item_id: string
  category: string
  food_category: string | null
  days_until_expiry: number
  current_inventory: number
  expected_demand_before_expiry: number | null
  potential_excess_inventory: number | null
  spoilage_probability: number | null
  expected_waste_exposure: number | null
  risk_score: number | null
  risk_level: RiskLevel
  intervention_scope: string
  recommendation: string
}

export interface RiskDfPageResponse {
  rows: BatchRecord[]
  total_rows: number
  page: number
  page_size: number
  total_pages: number
}

export interface RiskDfQueryParams {
  risk_level?: RiskLevel[]
  category?: string[]
  min_days_to_expiry?: number
  max_days_to_expiry?: number
  min_excess?: number
  page?: number
  page_size?: number
}

export interface RecommendationRecord {
  batch_id: string
  item_id: string
  category: string
  risk_level: RiskLevel
  days_until_expiry: number
  current_inventory: number
  potential_excess_inventory: number | null
  expected_waste_exposure: number | null
  intervention_scope: string
  recommendation: string
}

export interface RecommendationPageResponse {
  rows: RecommendationRecord[]
  total_rows: number
  page: number
  page_size: number
  total_pages: number
}

export interface BusinessValueScenario {
  scenario: string
  baseline_waste_units: number
  ai_assisted_waste_units: number
  waste_reduction_pct: number
  baseline_spoilage_rate: number
  ai_assisted_spoilage_rate: number
  spoilage_rate_reduction_pp: number
  intervention_count_high_critical: number
}

export interface BusinessValueResponse {
  scenarios: BusinessValueScenario[]
}

export interface ModelSummary {
  algorithm: string
  training_rows: number
  test_rows: number
  decision_threshold: number | null
}

export interface MetadataResponse {
  export_timestamp_utc: string
  chronological_split_cutoff: string
  spoilage_model: ModelSummary
  demand_model: ModelSummary
  total_evaluation_batches: number
  training_data_assumptions: string[]
}

// ---------------------------------------------------------------------
// Phase 3 — live scoring (POST /api/score, /api/score/upload, /api/score/demo)
// ---------------------------------------------------------------------

export interface BatchScoreInput {
  batch_id: string
  item_id: string
  category: string
  food_category: string
  shelf_life_days: number
  weekday_received: string
  is_holiday: number
  is_promoted: number
  qty_received: number
  trailing_mean_7: number
  trailing_mean_28: number
  demand_cv_28: number
  no_trailing_demand_28: number
  snap_days_in_life: number
  event_days_in_life: number
  current_inventory: number
  days_until_expiry: number
}

export interface CategoryDemandScoreInput {
  category: string
  lag_1: number
  lag_7: number
  lag_14: number
  roll_mean_7: number
  roll_mean_28: number
  month: number
  day_of_week: string
}

export interface ScoreRequest {
  batches: BatchScoreInput[]
  category_demand: CategoryDemandScoreInput[]
}

export interface ScoredBatchRecord {
  batch_id: string
  item_id: string
  category: string
  food_category: string | null
  days_until_expiry: number
  current_inventory: number
  expected_demand_before_expiry: number | null
  potential_excess_inventory: number | null
  spoilage_probability: number | null
  expected_waste_exposure: number | null
  risk_score: number | null
  risk_level: RiskLevel | null
  intervention_scope: string
  recommendation: string
  risk_score_note: string | null
}

export interface ScoreSummary {
  total_records_scored: number
  risk_distribution: RiskDistributionEntry[]
  high_critical_count: number
  average_risk_score: number | null
  average_spoilage_probability: number | null
  total_expected_waste_exposure: number | null
  unresolved_count: number
}

export interface ScoreResponse {
  rows: ScoredBatchRecord[]
  summary: ScoreSummary
  methodology_note: string
}

export interface FieldValidationError {
  row: number | null
  field: string
  message: string
}

export interface ValidationResponse {
  valid: boolean
  n_rows: number
  n_valid_rows: number
  n_invalid_rows: number
  errors: FieldValidationError[]
  preview: Record<string, unknown>[]
}

export interface InputSchemaField {
  name: string
  type: string
  required: boolean
  allowed_values: string[] | null
  description: string
}

export interface InputSchemaResponse {
  batch_fields: InputSchemaField[]
  category_demand_fields: InputSchemaField[]
  notes: string[]
}
