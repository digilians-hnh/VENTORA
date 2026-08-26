import { useState } from 'react'

import { FileDropzone } from '@/components/scoring/FileDropzone'
import { SchemaExplainer } from '@/components/scoring/SchemaExplainer'
import { ScoreResultsPanel } from '@/components/scoring/ScoreResultsPanel'
import { ValidationPanel } from '@/components/scoring/ValidationPanel'
import { ErrorState } from '@/components/ui/ErrorState'
import { PageHeader } from '@/components/ui/PageHeader'
import { ApiError } from '@/api/client'
import {
  useDemoPreview,
  useInputSchema,
  useScoreDemoData,
  useUploadAndScore,
  useValidateUpload,
} from '@/hooks/useApiQueries'

type Mode = 'prepared' | 'demo'

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message
  if (err instanceof Error) return err.message
  return 'Something went wrong.'
}

export function DataInputPage() {
  const [mode, setMode] = useState<Mode>('prepared')

  const { data: schema } = useInputSchema()

  // --- Prepared Data Upload state ---
  const [batchesFile, setBatchesFile] = useState<File | null>(null)
  const [categoryDemandFile, setCategoryDemandFile] = useState<File | null>(null)
  const validateUpload = useValidateUpload()
  const uploadAndScore = useUploadAndScore()

  // --- Demo Data state ---
  const [demoRequested, setDemoRequested] = useState(false)
  const demoPreview = useDemoPreview(demoRequested)
  const scoreDemoData = useScoreDemoData()

  function handleValidate() {
    if (!batchesFile || !categoryDemandFile) return
    uploadAndScore.reset()
    validateUpload.mutate({ batchesFile, categoryDemandFile })
  }

  function handleScorePrepared() {
    if (!batchesFile || !categoryDemandFile) return
    uploadAndScore.mutate({ batchesFile, categoryDemandFile })
  }

  function resetPrepared() {
    setBatchesFile(null)
    setCategoryDemandFile(null)
    validateUpload.reset()
    uploadAndScore.reset()
  }

  function resetDemo() {
    setDemoRequested(false)
    scoreDemoData.reset()
  }

  const canValidate = !!batchesFile && !!categoryDemandFile && !validateUpload.isPending
  const canScorePrepared = !!validateUpload.data?.valid && !uploadAndScore.isPending

  return (
    <div>
      <PageHeader
        title="Data Input"
        description="Score your own inventory batches, or try the workflow with packaged demo data — using the same live models behind every other page."
      />

      <div className="mb-5">
        <SchemaExplainer schema={schema} />
      </div>

      <div className="mb-5 flex gap-2 border-b border-border pb-3" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'prepared'}
          onClick={() => setMode('prepared')}
          className={`rounded-full px-4 py-2 text-[13px] font-semibold transition-colors ${
            mode === 'prepared'
              ? 'bg-[color:var(--color-deep-forest)] text-white'
              : 'border border-border-strong text-text-muted hover:text-text'
          }`}
        >
          Prepared Data Upload
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'demo'}
          onClick={() => setMode('demo')}
          className={`rounded-full px-4 py-2 text-[13px] font-semibold transition-colors ${
            mode === 'demo'
              ? 'bg-[color:var(--color-deep-forest)] text-white'
              : 'border border-border-strong text-text-muted hover:text-text'
          }`}
        >
          Demo / Sample Data
        </button>
      </div>

      {mode === 'prepared' ? (
        <div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <FileDropzone
              label="Batch-level CSV"
              hint="One row per batch"
              file={batchesFile}
              onFileSelected={(f) => {
                setBatchesFile(f)
                validateUpload.reset()
                uploadAndScore.reset()
              }}
              disabled={validateUpload.isPending || uploadAndScore.isPending}
            />
            <FileDropzone
              label="Category-demand CSV"
              hint="One row per category"
              file={categoryDemandFile}
              onFileSelected={(f) => {
                setCategoryDemandFile(f)
                validateUpload.reset()
                uploadAndScore.reset()
              }}
              disabled={validateUpload.isPending || uploadAndScore.isPending}
            />
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleValidate}
              disabled={!canValidate}
              className="rounded-lg bg-[color:var(--color-deep-forest)] px-4 py-2.5 text-[13px] font-semibold text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {validateUpload.isPending ? 'Validating…' : 'Validate & Preview'}
            </button>
            {(batchesFile || categoryDemandFile) && (
              <button
                type="button"
                onClick={resetPrepared}
                className="text-[12.5px] font-medium text-text-muted underline decoration-dotted underline-offset-4 hover:text-text"
              >
                Clear files
              </button>
            )}
          </div>

          {validateUpload.isError && (
            <div className="mt-4">
              <ErrorState message={errorMessage(validateUpload.error)} onRetry={handleValidate} />
            </div>
          )}

          {validateUpload.data && (
            <div className="mt-5">
              <ValidationPanel result={validateUpload.data} />

              <div className="mt-4 flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleScorePrepared}
                  disabled={!canScorePrepared}
                  className="rounded-lg bg-[color:var(--color-signature-lime)] px-5 py-2.5 text-[13px] font-semibold text-[color:var(--color-deep-forest)] transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {uploadAndScore.isPending ? 'Scoring…' : 'Score Inventory'}
                </button>
                {!validateUpload.data.valid && (
                  <span className="text-[12.5px] text-text-muted">Fix validation errors above to enable scoring.</span>
                )}
              </div>
            </div>
          )}

          {uploadAndScore.isError && (
            <div className="mt-4">
              <ErrorState message={errorMessage(uploadAndScore.error)} onRetry={handleScorePrepared} />
            </div>
          )}

          {uploadAndScore.data && (
            <div className="mt-6">
              <ScoreResultsPanel result={uploadAndScore.data} />
            </div>
          )}
        </div>
      ) : (
        <div>
          <div className="rounded-2xl border border-border bg-surface p-5">
            <p className="text-[13.5px] leading-relaxed text-text-muted">
              Load the packaged synthetic demo dataset (6 example batches across 2 categories) to see the live
              scoring workflow end to end — no files to prepare.{' '}
              <span className="font-medium text-text">This is not real company or sales data.</span>
            </p>
            <button
              type="button"
              onClick={() => setDemoRequested(true)}
              className="mt-4 rounded-lg border border-border-strong px-4 py-2.5 text-[13px] font-semibold text-text transition-colors hover:bg-surface-sunken"
            >
              {demoPreview.isFetching ? 'Loading…' : 'Load Demo Data'}
            </button>
            {demoRequested && (
              <button
                type="button"
                onClick={resetDemo}
                className="ml-3 text-[12.5px] font-medium text-text-muted underline decoration-dotted underline-offset-4 hover:text-text"
              >
                Reset
              </button>
            )}
          </div>

          {demoPreview.isError && (
            <div className="mt-4">
              <ErrorState message={errorMessage(demoPreview.error)} onRetry={() => demoPreview.refetch()} />
            </div>
          )}

          {demoPreview.data && (
            <div className="mt-5">
              <ValidationPanel result={demoPreview.data} />

              <div className="mt-4">
                <button
                  type="button"
                  onClick={() => scoreDemoData.mutate()}
                  disabled={scoreDemoData.isPending}
                  className="rounded-lg bg-[color:var(--color-signature-lime)] px-5 py-2.5 text-[13px] font-semibold text-[color:var(--color-deep-forest)] transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {scoreDemoData.isPending ? 'Scoring…' : 'Score Demo Data'}
                </button>
              </div>
            </div>
          )}

          {scoreDemoData.isError && (
            <div className="mt-4">
              <ErrorState message={errorMessage(scoreDemoData.error)} onRetry={() => scoreDemoData.mutate()} />
            </div>
          )}

          {scoreDemoData.data && (
            <div className="mt-6">
              <ScoreResultsPanel result={scoreDemoData.data} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
