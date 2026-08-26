import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import { BusinessImpactPage } from '@/pages/BusinessImpactPage'
import { HomePage } from '@/pages/HomePage'
import { OverviewPage } from '@/pages/OverviewPage'
import { RecommendationsPage } from '@/pages/RecommendationsPage'
import { RiskExplorerPage } from '@/pages/RiskExplorerPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/overview" element={<OverviewPage />} />
            <Route path="/risk-explorer" element={<RiskExplorerPage />} />
            <Route path="/recommendations" element={<RecommendationsPage />} />
            <Route path="/business-impact" element={<BusinessImpactPage />} />
            {/* Live Scoring / Data Input is intentionally not user-facing; send stray links home. */}
            <Route path="/data-input" element={<Navigate to="/" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
