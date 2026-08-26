/**
 * Centralized API client for the VENTORA FastAPI backend.
 *
 * The base URL is read once from VITE_API_BASE_URL (see .env.example) and
 * used everywhere — no endpoint in this app hardcodes a host. Every
 * function here is a thin, typed wrapper around a single GET request; none
 * of them compute, transform, or reinterpret the values the API returns.
 */
import type {
  BusinessValueResponse,
  HealthResponse,
  InputSchemaResponse,
  MetadataResponse,
  RecommendationPageResponse,
  RiskDfPageResponse,
  RiskDfQueryParams,
  RiskLevel,
  ScoreRequest,
  ScoreResponse,
  SummaryResponse,
  ValidationResponse,
} from '@/types/api'

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/+$/, '') ??
  'http://localhost:8000'

export class ApiError extends Error {
  status: number
  /** Raw JSON body of the error response, when available (e.g. a
   *  ValidationResponse from /api/score/upload's 400 detail). */
  payload?: unknown
  constructor(message: string, status: number, payload?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

async function parseErrorResponse(response: Response): Promise<ApiError> {
  let detail: string = response.statusText
  let payload: unknown
  try {
    payload = await response.json()
    const body = payload as { detail?: unknown }
    if (typeof body?.detail === 'string') {
      detail = body.detail
    } else if (body?.detail && typeof body.detail === 'object') {
      // FastAPI 422 validation errors, or our own ValidationResponse detail
      detail = summarizeStructuredDetail(body.detail)
    }
  } catch {
    // response body wasn't JSON — fall back to statusText
  }
  return new ApiError(detail, response.status, payload)
}

function summarizeStructuredDetail(detail: unknown): string {
  if (Array.isArray(detail)) {
    // FastAPI's default 422 shape: [{ loc, msg, type }, ...]
    const first = detail[0] as { msg?: string } | undefined
    return first?.msg ?? 'Invalid request.'
  }
  if (detail && typeof detail === 'object' && 'errors' in detail) {
    // Our ValidationResponse shape
    const errors = (detail as { errors?: { message?: string }[] }).errors ?? []
    return errors[0]?.message ?? 'Validation failed.'
  }
  return 'Request failed.'
}

async function getJson<T>(path: string, params?: Record<string, string | number | string[] | undefined>): Promise<T> {
  const url = new URL(`${API_BASE_URL}${path}`)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null) continue
      if (Array.isArray(value)) {
        for (const v of value) url.searchParams.append(key, String(v))
      } else {
        url.searchParams.set(key, String(value))
      }
    }
  }

  let response: Response
  try {
    response = await fetch(url.toString(), { headers: { Accept: 'application/json' } })
  } catch {
    throw new ApiError(
      `Could not reach the VENTORA API at ${API_BASE_URL}. Is the backend running?`,
      0,
    )
  }

  if (!response.ok) throw await parseErrorResponse(response)
  return (await response.json()) as T
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new ApiError(
      `Could not reach the VENTORA API at ${API_BASE_URL}. Is the backend running?`,
      0,
    )
  }

  if (!response.ok) throw await parseErrorResponse(response)
  return (await response.json()) as T
}

async function postForm<T>(path: string, form: FormData): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      body: form,
    })
  } catch {
    throw new ApiError(
      `Could not reach the VENTORA API at ${API_BASE_URL}. Is the backend running?`,
      0,
    )
  }

  if (!response.ok) throw await parseErrorResponse(response)
  return (await response.json()) as T
}

async function postEmpty<T>(path: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
    })
  } catch {
    throw new ApiError(
      `Could not reach the VENTORA API at ${API_BASE_URL}. Is the backend running?`,
      0,
    )
  }

  if (!response.ok) throw await parseErrorResponse(response)
  return (await response.json()) as T
}

export const api = {
  health: () => getJson<HealthResponse>('/api/health'),

  summary: () => getJson<SummaryResponse>('/api/summary'),

  riskDf: (params: RiskDfQueryParams = {}) =>
    getJson<RiskDfPageResponse>('/api/risk-df', {
      risk_level: params.risk_level,
      category: params.category,
      min_days_to_expiry: params.min_days_to_expiry,
      max_days_to_expiry: params.max_days_to_expiry,
      min_excess: params.min_excess,
      page: params.page,
      page_size: params.page_size,
    }),

  recommendations: (level: RiskLevel | undefined, page: number, pageSize: number) =>
    getJson<RecommendationPageResponse>('/api/recommendations', {
      level,
      page,
      page_size: pageSize,
    }),

  businessValue: () => getJson<BusinessValueResponse>('/api/business-value'),

  metadata: () => getJson<MetadataResponse>('/api/metadata'),

  // --- Phase 3: live scoring ---

  getInputSchema: () => getJson<InputSchemaResponse>('/api/input-schema'),

  scoreRecords: (request: ScoreRequest) => postJson<ScoreResponse>('/api/score', request),

  validateUpload: (batchesFile: File, categoryDemandFile: File) => {
    const form = new FormData()
    form.append('batches_file', batchesFile)
    form.append('category_demand_file', categoryDemandFile)
    return postForm<ValidationResponse>('/api/score/validate', form)
  },

  uploadAndScore: (batchesFile: File, categoryDemandFile: File) => {
    const form = new FormData()
    form.append('batches_file', batchesFile)
    form.append('category_demand_file', categoryDemandFile)
    return postForm<ScoreResponse>('/api/score/upload', form)
  },

  getDemoPreview: () => getJson<ValidationResponse>('/api/score/demo'),

  scoreDemoData: () => postEmpty<ScoreResponse>('/api/score/demo'),
}
