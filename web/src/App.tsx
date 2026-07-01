import { BrowserRouter, Route, Routes } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AppShell } from "@/components/layout/AppShell"
import { DashboardPage } from "@/pages/DashboardPage"
import { MentionsPage } from "@/pages/MentionsPage"
import { ReportsPage } from "@/pages/ReportsPage"
import { ConfigPage } from "@/pages/ConfigPage"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

const basename = import.meta.env.BASE_URL.replace(/\/$/, "") || undefined

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename={basename}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<DashboardPage />} />
            <Route path="mentions" element={<MentionsPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="config" element={<ConfigPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
