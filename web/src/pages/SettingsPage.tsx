import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Save, KeyRound, CheckCircle2 } from "lucide-react"
import { useEffect, useState } from "react"
import { api, isStaticMode, type Settings } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Alert } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { StaticModeBanner } from "@/components/StaticModeBanner"

export function SettingsPage() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<Settings>({
    vk_access_token: "",
    yandex_search_api_key: "",
    yandex_folder_id: "",
  })
  const [saved, setSaved] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ["settings"],
    queryFn: api.settings.get,
  })

  useEffect(() => {
    if (data) setForm(data)
  }, [data])

  const saveMutation = useMutation({
    mutationFn: api.settings.save,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    },
  })

  const update = (key: keyof Settings, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  if (isLoading) {
    return <Skeleton className="h-96 w-full" />
  }

  return (
    <div className="space-y-6">
      <StaticModeBanner />
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Настройки API</h1>
        <p className="text-muted-foreground">
          Ключи сохраняются в файл <code className="rounded bg-muted px-1">env.txt</code> в корне проекта
        </p>
      </div>

      <Alert className="flex items-start gap-3 border-amber-200 bg-amber-50">
        <KeyRound className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" />
        <div className="text-sm">
          Для внутреннего использования. Файл env.txt хранит токены в открытом виде.
        </div>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle>Токены и ключи</CardTitle>
          <CardDescription>
            {isStaticMode
              ? "На GitHub Pages ключи не сохраняются. Добавьте secrets в репозиторий или используйте локальный сервер."
              : "VK — для поиска постов. Yandex — для стабильного веб-поиска. Без ключей используется DuckDuckGo."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="vk">VK_ACCESS_TOKEN</Label>
              {form.vk_access_token && <Badge variant="success">задан</Badge>}
            </div>
            <Input
              id="vk"
              type="password"
              value={form.vk_access_token}
              onChange={(e) => update("vk_access_token", e.target.value)}
              placeholder="Сервисный или пользовательский токен VK"
            />
            <p className="text-xs text-muted-foreground">
              <a href="https://dev.vk.com/ru/api/access-token/getting-started" target="_blank" rel="noreferrer" className="underline">
                Как получить токен VK
              </a>
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="yandex-key">YANDEX_SEARCH_API_KEY</Label>
              {form.yandex_search_api_key && <Badge variant="success">задан</Badge>}
            </div>
            <Input
              id="yandex-key"
              type="password"
              value={form.yandex_search_api_key}
              onChange={(e) => update("yandex_search_api_key", e.target.value)}
              placeholder="Api-Key из Yandex Cloud"
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="yandex-folder">YANDEX_FOLDER_ID</Label>
              {form.yandex_folder_id && <Badge variant="success">задан</Badge>}
            </div>
            <Input
              id="yandex-folder"
              value={form.yandex_folder_id}
              onChange={(e) => update("yandex_folder_id", e.target.value)}
              placeholder="ID каталога в Yandex Cloud"
            />
            <p className="text-xs text-muted-foreground">
              <a href="https://yandex.cloud/ru/docs/search-api/" target="_blank" rel="noreferrer" className="underline">
                Документация Yandex Search API
              </a>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button
              onClick={() => saveMutation.mutate(form)}
              disabled={saveMutation.isPending || isStaticMode}
            >
              <Save className="h-4 w-4" />
              Сохранить в env.txt
            </Button>
            {saved && (
              <span className="flex items-center gap-1 text-sm text-emerald-600">
                <CheckCircle2 className="h-4 w-4" />
                Сохранено
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
