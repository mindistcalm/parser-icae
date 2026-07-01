import { useEffect, useMemo, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Play, CheckCircle2, AlertCircle, Loader2 } from "lucide-react"
import { api, isStaticMode, type Job } from "@/lib/api"
import { formatMonthLabel } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { StaticModeBanner } from "@/components/StaticModeBanner"

function previousMonthValue() {
  const d = new Date()
  d.setMonth(d.getMonth() - 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`
}

export function DashboardPage() {
  const queryClient = useQueryClient()
  const [month, setMonth] = useState(previousMonthValue())
  const [jobId, setJobId] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.dashboard,
  })

  const { data: job } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.job(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = (query.state.data as Job | undefined)?.status
      return status === "running" || status === "pending" ? 1500 : false
    },
  })

  const runMutation = useMutation({
    mutationFn: () => api.run(month),
    onSuccess: (res) => setJobId(res.job_id),
  })

  useEffect(() => {
    if (job?.status === "completed") {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      queryClient.invalidateQueries({ queryKey: ["mentions"] })
      queryClient.invalidateQueries({ queryKey: ["reports"] })
    }
  }, [job?.status, queryClient])

  const monthCount = useMemo(
    () => data?.months.find((m) => m.month === month)?.count ?? 0,
    [data, month]
  )

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <StaticModeBanner />
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Мониторинг ИЦАЭ</h1>
        <p className="text-muted-foreground">
          {data?.organization.full_name} · {data?.organization.city}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Веб-поиск</CardDescription>
            <CardTitle className="text-lg">{data?.providers.web_fallback}</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={data?.providers.yandex ? "success" : "secondary"}>
              {data?.providers.yandex ? "Yandex API" : "без API-ключа"}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>ВКонтакте</CardDescription>
            <CardTitle className="text-lg">
              {data?.providers.vk ? "Подключён" : "Не настроен"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={data?.providers.vk ? "success" : "warning"}>
              {data?.providers.vk ? "токен задан" : "нужен VK_ACCESS_TOKEN"}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>За {formatMonthLabel(month)}</CardDescription>
            <CardTitle className="text-3xl">{monthCount}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">упоминаний в базе</CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{isStaticMode ? "Сбор данных" : "Запустить сбор за месяц"}</CardTitle>
          <CardDescription>
            {isStaticMode
              ? "На GitHub Pages доступен только просмотр. Для нового поиска запустите локально или включите workflow с опцией run_parser."
              : "Поиск упоминаний и автоматическое формирование Excel/HTML отчёта"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!isStaticMode && (
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
            <div className="space-y-2">
              <Label htmlFor="month">Месяц отчёта</Label>
              <Input
                id="month"
                type="month"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
                className="w-48"
              />
            </div>
            <Button
              onClick={() => runMutation.mutate()}
              disabled={runMutation.isPending || job?.status === "running"}
              className="sm:mb-0"
            >
              {job?.status === "running" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              Запустить поиск
            </Button>
            <Button
              variant="outline"
              onClick={() => setMonth(previousMonthValue())}
            >
              Прошлый месяц
            </Button>
          </div>
          )}

          {isStaticMode && data?.latest_reports && data.latest_reports.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {data.latest_reports.slice(0, 4).map((r) => (
                <a
                  key={r.filename}
                  href={api.reportUrl(r.filename)}
                  download={r.kind === "xlsx"}
                  target={r.kind === "html" ? "_blank" : undefined}
                  rel="noreferrer"
                  className="inline-flex h-8 items-center rounded-md border px-3 text-xs font-medium hover:bg-accent"
                >
                  {r.kind === "xlsx" ? "Excel" : "HTML"} · {formatMonthLabel(r.month)}
                </a>
              ))}
            </div>
          )}

          {!isStaticMode && job && (
            <Alert
              className={
                job.status === "failed"
                  ? "border-red-200 bg-red-50"
                  : job.status === "completed"
                    ? "border-emerald-200 bg-emerald-50"
                    : "border-blue-200 bg-blue-50"
              }
            >
              <div className="flex items-start gap-2">
                {job.status === "completed" && <CheckCircle2 className="mt-0.5 h-4 w-4 text-emerald-600" />}
                {job.status === "failed" && <AlertCircle className="mt-0.5 h-4 w-4 text-red-600" />}
                {job.status === "running" && <Loader2 className="mt-0.5 h-4 w-4 animate-spin text-blue-600" />}
                <div className="flex-1 space-y-2">
                  <div className="font-medium">
                    {job.status === "completed" && `Найдено ${job.mentions_count} упоминаний`}
                    {job.status === "running" && "Поиск выполняется…"}
                    {job.status === "pending" && "Задача в очереди…"}
                    {job.status === "failed" && `Ошибка: ${job.error}`}
                  </div>
                  {job.logs.length > 0 && (
                    <pre className="max-h-48 overflow-auto rounded bg-black/5 p-3 text-xs leading-relaxed">
                      {job.logs.slice(-20).join("\n")}
                    </pre>
                  )}
                  {job.status === "completed" && (
                    <div className="flex flex-wrap gap-2">
                      {job.report_xlsx && (
                        <a
                          href={api.reportUrl(job.report_xlsx)}
                          download
                          className="inline-flex h-8 items-center rounded-md border px-3 text-xs font-medium hover:bg-accent"
                        >
                          Скачать Excel
                        </a>
                      )}
                      {job.report_html && (
                        <a
                          href={api.reportUrl(job.report_html)}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex h-8 items-center rounded-md border px-3 text-xs font-medium hover:bg-accent"
                        >
                          Открыть HTML
                        </a>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </Alert>
          )}
        </CardContent>
      </Card>

      {data && data.months.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>История по месяцам</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {data.months.map((m) => (
                <Button
                  key={m.month}
                  variant={m.month === month ? "default" : "outline"}
                  size="sm"
                  onClick={() => setMonth(m.month)}
                >
                  {formatMonthLabel(m.month)} · {m.count}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
