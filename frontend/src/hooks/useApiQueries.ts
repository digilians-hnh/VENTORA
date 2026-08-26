import { useMutation, useQuery } from '@tanstack/react-query'

import { api } from '@/api/client'
import type { RiskDfQueryParams, RiskLevel, ScoreRequest } from '@/types/api'

/** Executive Overview KPIs + chart data, from GET /api/summary. */
export function useSummary() {
  return useQuery({
    queryKey: ['summary'],
    queryFn: api.summary,
    staleTime: 60_000,
  })
}

/** Risk Explorer table, server-filtered + paginated, from GET /api/risk-df. */
export function useRiskDf(params: RiskDfQueryParams) {
  return useQuery({
    queryKey: ['risk-df', params],
    queryFn: () => api.riskDf(params),
    placeholderData: (previousData) => previousData,
    staleTime: 60_000,
  })
}

/** Recommendations for one risk level (or all), from GET /api/recommendations. */
export function useRecommendations(level: RiskLevel | undefined, page: number, pageSize: number) {
  return useQuery({
    queryKey: ['recommendations', level, page, pageSize],
    queryFn: () => api.recommendations(level, page, pageSize),
    placeholderData: (previousData) => previousData,
    staleTime: 60_000,
  })
}

/** Business Impact scenario table, from GET /api/business-value. */
export function useBusinessValue() {
  return useQuery({
    queryKey: ['business-value'],
    queryFn: api.businessValue,
    staleTime: 60_000,
  })
}

/** Model/project metadata, from GET /api/metadata. */
export function useMetadata() {
  return useQuery({
    queryKey: ['metadata'],
    queryFn: api.metadata,
    staleTime: 5 * 60_000,
  })
}

// --- Phase 3: live scoring ---

/** Input schema for the scoring endpoints, from GET /api/input-schema. */
export function useInputSchema() {
  return useQuery({
    queryKey: ['input-schema'],
    queryFn: api.getInputSchema,
    staleTime: 10 * 60_000,
  })
}

/** POST /api/score — JSON scoring. */
export function useScoreRecords() {
  return useMutation({
    mutationFn: (request: ScoreRequest) => api.scoreRecords(request),
  })
}

/** POST /api/score/validate — validate + preview two uploaded CSVs, no scoring. */
export function useValidateUpload() {
  return useMutation({
    mutationFn: ({ batchesFile, categoryDemandFile }: { batchesFile: File; categoryDemandFile: File }) =>
      api.validateUpload(batchesFile, categoryDemandFile),
  })
}

/** POST /api/score/upload — validate then score two uploaded CSVs. */
export function useUploadAndScore() {
  return useMutation({
    mutationFn: ({ batchesFile, categoryDemandFile }: { batchesFile: File; categoryDemandFile: File }) =>
      api.uploadAndScore(batchesFile, categoryDemandFile),
  })
}

/** GET /api/score/demo — preview the packaged synthetic demo dataset. */
export function useDemoPreview(enabled: boolean) {
  return useQuery({
    queryKey: ['score-demo-preview'],
    queryFn: api.getDemoPreview,
    enabled,
    staleTime: 10 * 60_000,
  })
}

/** POST /api/score/demo — score the packaged synthetic demo dataset. */
export function useScoreDemoData() {
  return useMutation({
    mutationFn: () => api.scoreDemoData(),
  })
}
