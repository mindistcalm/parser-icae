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

export interface AppConfig {
  organization: {
    full_name: string
    short_name: string
    city: string
  }
  search_keywords: string[]
  mention_patterns: string[]
  city_patterns: string[]
  exclude_domains: string[]
  exclude_urls: string[]
  exclude_url_fragments: string[]
  exclude_url_patterns: string[]
  rss_feeds: { name: string; url: string }[]
  search: {
    max_results_per_query: number
    request_delay_seconds: number
  }
  storage: {
    database_path: string
  }
  reports: {
    output_dir: string
  }
}

export interface Dashboard {
  organization: {
    full_name: string
    short_name: string
    city: string
  }
  providers: {
    web: string
    rss: boolean
  }
  previous_month: string
  months: MonthSummary[]
  latest_reports: ReportFile[]
  config?: AppConfig
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
let manifestPromise: Promise<Dashboard> | null = null

async function getManifest(): Promise<Dashboard> {
  if (manifestCache) return manifestCache
  if (!manifestPromise) {
    manifestPromise = staticGet<Dashboard>(assetUrl("data/manifest.json"))
      .then((data) => {
        manifestCache = data
        return data
      })
      .catch((err) => {
        manifestPromise = null
        throw err
      })
  }
  return manifestPromise
}

async function getReports(): Promise<ReportFile[]> {
  const manifest = await getManifest()
  if (manifest.latest_reports?.length) return manifest.latest_reports
  const fromFile = await staticGet<ReportFile[]>(assetUrl("data/reports.json")).catch(
    () => []
  )
  if (fromFile.length) return fromFile
  return reportsFromMonths(manifest.months)
}

/** Ссылки на отчёты по списку месяцев, если reports.json пуст */
export function reportsFromMonths(months: MonthSummary[]): ReportFile[] {
  return months.flatMap((m) => {
    const [year, mon] = m.month.split("-")
    const base = `icae_mentions_${year}_${mon}`
    return [
      { filename: `${base}.html`, month: m.month, kind: "html", size: 0 },
      { filename: `${base}.xlsx`, month: m.month, kind: "xlsx", size: 0 },
    ]
  })
}

const liveApi = {
  dashboard: () => request<Dashboard>("/api/dashboard"),
  config: {
    get: () => request<AppConfig>("/api/config"),
    save: (data: AppConfig) =>
      request<AppConfig>("/api/config", {
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
  reports: () => getReports(),
  reportUrl: (filename: string) => `/api/reports/${filename}`,
}

const staticApi = {
  dashboard: getManifest,
  config: {
    get: async (): Promise<AppConfig> => {
      const manifest = await getManifest()
      if (!manifest.config) throw new Error("Конфигурация не экспортирована")
      return manifest.config
    },
    save: async () => {
      throw new Error("На GitHub Pages конфигурацию нельзя изменить")
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
  reports: getReports,
  reportUrl: (filename: string) => assetUrl(`reports/${filename}`),
}

export const api = isStaticMode ? staticApi : liveApi
