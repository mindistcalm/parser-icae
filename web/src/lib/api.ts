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

export const isStaticMode = import.meta.env.VITE_STATIC === "true"
const base = import.meta.env.BASE_URL

function assetUrl(path: string): string {
  return `${base}${path.replace(/^\//, "")}`
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

async function staticGet<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Не удалось загрузить ${url}`)
  return res.json() as Promise<T>
}

let manifestCache: Dashboard | null = null

async function getManifest(): Promise<Dashboard> {
  if (!manifestCache) {
    manifestCache = await staticGet<Dashboard>(assetUrl("data/manifest.json"))
  }
  return manifestCache
}

const liveApi = {
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

const staticApi = {
  dashboard: getManifest,
  settings: {
    get: async (): Promise<Settings> => ({
      vk_access_token: "",
      yandex_search_api_key: "",
      yandex_folder_id: "",
    }),
    save: async (): Promise<Settings> => {
      throw new Error("На GitHub Pages настройки недоступны — используйте локальный сервер")
    },
  },
  mentions: (month: string) =>
    staticGet<Mention[]>(assetUrl(`data/mentions-${month}.json`)).catch(() => []),
  months: async () => (await getManifest()).months,
  run: async () => {
    throw new Error("Запуск поиска недоступен на GitHub Pages")
  },
  job: async () => {
    throw new Error("Задачи недоступны на GitHub Pages")
  },
  reports: async () => (await getManifest()).latest_reports,
  reportUrl: (filename: string) => assetUrl(`reports/${filename}`),
}

export const api = isStaticMode ? staticApi : liveApi
