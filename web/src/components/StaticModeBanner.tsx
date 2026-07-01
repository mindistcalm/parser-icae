import { Globe } from "lucide-react"
import { Alert } from "@/components/ui/alert"
import { isStaticMode } from "@/lib/api"

export function StaticModeBanner() {
  if (!isStaticMode) return null

  return (
    <Alert className="flex items-start gap-3 border-blue-200 bg-blue-50">
      <Globe className="mt-0.5 h-4 w-4 shrink-0 text-blue-700" />
      <div className="text-sm">
        <p className="font-medium text-blue-900">Режим GitHub Pages</p>
        <p className="text-blue-800">
          Отображаются сохранённые отчёты. Запуск поиска и настройка API-ключей — только в локальной версии (
          <code className="rounded bg-blue-100 px-1">./start-web.sh</code>
          ).
        </p>
      </div>
    </Alert>
  )
}
