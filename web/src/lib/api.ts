export interface Settings {
  vk_access_token: string
  yandex_search_api_key: string
  yandex_folder_id: string
}

export interface Mention {
  source_name: string
  title: string
  url: string
  published_at: string | null
  source_type: string
  snippet: string
}

export interface MonthSummary {
  month: string
  count: number
}

export interface ReportFile {
  filename: string
  month: string
  kind: string
  size: number
}

export interface Dashboard {
  organization: {
    full_name: string
    short_name: string
    city: string
  }
  providers: {
    vk: boolean
    yandex: boolean
    web_fallback: string
  }
  previous_month: string
  months: MonthSummary[]
  latest_reports: ReportFile[]
}

export type JobStatus = "pending" | "running" | "completed" | "failed"

export interface Job {
  id: string
  status: JobStatus
  month: string
  logs: string[]
  mentions_count: number
  report_xlsx: string | null
  report_html: string | null
  error: string | null
  started_at: string
  finished_at: string | null
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  return res.json() as Promise<T>
}

export const api = {
  dashboard: () => request<Dashboard>("/api/dashboard"),
  settings: {
    get: () => request<Settings>("/api/settings"),
    save: (data: Settings) =>
      request<Settings>("/api/settings", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
  },
  mentions: (month: string) =>
    request<Mention[]>(`/api/mentions?month=${encodeURIComponent(month)}`),
  months: () => request<MonthSummary[]>("/api/months"),
  run: (month: string) =>
    request<{ job_id: string }>("/api/run", {
      method: "POST",
      body: JSON.stringify({ month }),
    }),
  job: (id: string) => request<Job>(`/api/jobs/${id}`),
  reports: () => request<ReportFile[]>("/api/reports"),
  reportUrl: (filename: string) => `/api/reports/${filename}`,
}
