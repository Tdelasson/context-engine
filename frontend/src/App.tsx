import { Navigate, Route, Routes } from 'react-router-dom'
import { Shell } from './components/Shell'
import { KnowledgePage } from './pages/KnowledgePage'
import { RunsPage } from './pages/RunsPage'
import { AppDataProvider } from './state/AppData'

export function App() {
  return (
    <AppDataProvider>
      <Routes>
        <Route element={<Shell />}>
          <Route path="/runs" element={<RunsPage />} />
          <Route path="/runs/:runId" element={<RunsPage />} />
          <Route path="/knowledge" element={<KnowledgePage />} />
          <Route path="*" element={<Navigate to="/runs" replace />} />
        </Route>
      </Routes>
    </AppDataProvider>
  )
}
