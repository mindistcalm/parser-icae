import { useEffect, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { CheckCircle2, Save, Settings2 } from "lucide-react"
import { api, isStaticMode, type AppConfig } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { StaticModeBanner } from "@/components/StaticModeBanner"
import { RssFeedListField, StringListField } from "@/components/config/ConfigFields"

const emptyConfig = (): AppConfig => ({
  organization: { full_name: "", short_name: "", city: "" },
  search_keywords: [],
  mention_patterns: [],
  city_patterns: [],
  exclude_domains: [],
  exclude_urls: [],
  exclude_url_fragments: [],
  exclude_url_patterns: [],
  rss_feeds: [],
  search: { max_results_per_query: 50, request_delay_seconds: 1.5 },
  storage: { database_path: "data/mentions.db" },
  reports: { output_dir: "reports" },
})

export function ConfigPage() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<AppConfig>(emptyConfig())
  const [saved, setSaved] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ["config"],
    queryFn: api.config.get,
  })

  useEffect(() => {
    if (data) setForm(data)
  }, [data])

  const saveMutation = useMutation({
    mutationFn: api.config.save,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["config"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    },
  })

  const update = <K extends keyof AppConfig>(key: K, value: AppConfig[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  if (isLoading) {
    return <Skeleton className="h-96 w-full" />
  }

  return (
    <div className="space-y-6">
      <StaticModeBanner />
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight">
            <Settings2 className="h-6 w-6" />
            Настройки
          </h1>
          <p className="text-muted-foreground">
            Редактирование <code className="rounded bg-muted px-1">config.yaml</code>
          </p>
        </div>
        <Button
          onClick={() => saveMutation.mutate(form)}
          disabled={saveMutation.isPending || isStaticMode}
        >
          <Save className="h-4 w-4" />
          Сохранить
        </Button>
      </div>

      {isStaticMode && (
        <p className="text-sm text-muted-foreground">
          На GitHub Pages конфигурация доступна только для просмотра.
        </p>
      )}

      {saved && (
        <p className="flex items-center gap-1 text-sm text-emerald-600">
          <CheckCircle2 className="h-4 w-4" />
          config.yaml сохранён
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Организация</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="full_name">Полное название</Label>
            <Input
              id="full_name"
              value={form.organization.full_name}
              disabled={isStaticMode}
              onChange={(e) =>
                update("organization", { ...form.organization, full_name: e.target.value })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="short_name">Сокращение</Label>
            <Input
              id="short_name"
              value={form.organization.short_name}
              disabled={isStaticMode}
              onChange={(e) =>
                update("organization", { ...form.organization, short_name: e.target.value })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="city">Город</Label>
            <Input
              id="city"
              value={form.organization.city}
              disabled={isStaticMode}
              onChange={(e) =>
                update("organization", { ...form.organization, city: e.target.value })
              }
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Поиск</CardTitle>
          <CardDescription>Ключевые фразы и параметры запросов</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <StringListField
            label="Поисковые фразы"
            description="Варианты написания для DuckDuckGo"
            value={form.search_keywords}
            onChange={(v) => update("search_keywords", v)}
            rows={8}
            disabled={isStaticMode}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="max_results">Макс. результатов на запрос</Label>
              <Input
                id="max_results"
                type="number"
                min={1}
                max={200}
                disabled={isStaticMode}
                value={form.search.max_results_per_query}
                onChange={(e) =>
                  update("search", {
                    ...form.search,
                    max_results_per_query: Number(e.target.value),
                  })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="delay">Пауза между запросами (сек)</Label>
              <Input
                id="delay"
                type="number"
                min={0.5}
                max={10}
                step={0.5}
                disabled={isStaticMode}
                value={form.search.request_delay_seconds}
                onChange={(e) =>
                  update("search", {
                    ...form.search,
                    request_delay_seconds: Number(e.target.value),
                  })
                }
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Фильтры релевантности</CardTitle>
          <CardDescription>Как определять, что упоминание относится к ИЦАЭ Томска</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6 lg:grid-cols-2">
          <StringListField
            label="Паттерны упоминания"
            value={form.mention_patterns}
            onChange={(v) => update("mention_patterns", v)}
            disabled={isStaticMode}
          />
          <StringListField
            label="Паттерны города"
            value={form.city_patterns}
            onChange={(v) => update("city_patterns", v)}
            disabled={isStaticMode}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Исключения</CardTitle>
          <CardDescription>Свои ресурсы и статические страницы, которые не попадают в отчёт</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-6 lg:grid-cols-2">
          <StringListField
            label="Домены"
            value={form.exclude_domains}
            onChange={(v) => update("exclude_domains", v)}
            disabled={isStaticMode}
          />
          <StringListField
            label="URL (фрагменты)"
            value={form.exclude_urls}
            onChange={(v) => update("exclude_urls", v)}
            disabled={isStaticMode}
          />
          <StringListField
            label="Фрагменты URL"
            value={form.exclude_url_fragments}
            onChange={(v) => update("exclude_url_fragments", v)}
            disabled={isStaticMode}
          />
          <StringListField
            label="Шаблоны статических страниц"
            value={form.exclude_url_patterns}
            onChange={(v) => update("exclude_url_patterns", v)}
            disabled={isStaticMode}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>RSS-ленты</CardTitle>
        </CardHeader>
        <CardContent>
          <RssFeedListField
            value={form.rss_feeds}
            onChange={(v) => update("rss_feeds", v)}
            disabled={isStaticMode}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Хранение</CardTitle>
          <CardDescription>Пути к базе данных и папке отчётов</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="db_path">База данных</Label>
            <Input
              id="db_path"
              disabled={isStaticMode}
              value={form.storage.database_path}
              onChange={(e) =>
                update("storage", { database_path: e.target.value })
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="reports_dir">Папка отчётов</Label>
            <Input
              id="reports_dir"
              disabled={isStaticMode}
              value={form.reports.output_dir}
              onChange={(e) =>
                update("reports", { output_dir: e.target.value })
              }
            />
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button
          onClick={() => saveMutation.mutate(form)}
          disabled={saveMutation.isPending || isStaticMode}
          size="lg"
        >
          <Save className="h-4 w-4" />
          Сохранить config.yaml
        </Button>
      </div>

      {saveMutation.isError && (
        <p className="text-sm text-red-600">
          {(saveMutation.error as Error).message}
        </p>
      )}
    </div>
  )
}
