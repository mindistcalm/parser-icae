import { useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { ExternalLink, Search } from "lucide-react"
import { api } from "@/lib/api"
import { formatDate, formatMonthLabel } from "@/lib/utils"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"

function previousMonthValue() {
  const d = new Date()
  d.setMonth(d.getMonth() - 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`
}

export function MentionsPage() {
  const [month, setMonth] = useState(previousMonthValue())
  const [filter, setFilter] = useState("")

  const { data: months } = useQuery({
    queryKey: ["months"],
    queryFn: api.months,
  })

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["mentions", month],
    queryFn: () => api.mentions(month),
  })

  const filtered = useMemo(() => {
    if (!data) return []
    const q = filter.trim().toLowerCase()
    if (!q) return data
    return data.filter(
      (m) =>
        m.title.toLowerCase().includes(q) ||
        m.source_name.toLowerCase().includes(q) ||
        m.url.toLowerCase().includes(q)
    )
  }, [data, filter])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Упоминания</h1>
        <p className="text-muted-foreground">
          Все найденные публикации за выбранный месяц
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Фильтры</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="space-y-2">
            <Label htmlFor="mentions-month">Месяц</Label>
            <Input
              id="mentions-month"
              type="month"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              className="w-48"
            />
          </div>
          <div className="flex-1 space-y-2">
            <Label htmlFor="search">Поиск по таблице</Label>
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                id="search"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                placeholder="Заголовок, ресурс или ссылка…"
                className="pl-9"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {months && months.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {months.map((m) => (
            <Button
              key={m.month}
              variant={m.month === month ? "default" : "outline"}
              size="sm"
              onClick={() => setMonth(m.month)}
            >
              {formatMonthLabel(m.month)} ({m.count})
            </Button>
          ))}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{formatMonthLabel(month)}</CardTitle>
          <CardDescription>
            {isFetching ? "Обновление…" : `${filtered.length} записей`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : filtered.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Нет данных за этот месяц. Запустите поиск на главной странице.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">№</TableHead>
                  <TableHead>Ресурс</TableHead>
                  <TableHead>Заголовок</TableHead>
                  <TableHead>Дата</TableHead>
                  <TableHead className="w-10" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((m, i) => (
                  <TableRow key={m.url}>
                    <TableCell>{i + 1}</TableCell>
                    <TableCell>
                      <div className="font-medium">{m.source_name}</div>
                      <Badge variant="outline" className="mt-1">
                        {m.source_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="max-w-md font-medium">{m.title}</div>
                      {m.snippet && (
                        <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                          {m.snippet}
                        </p>
                      )}
                    </TableCell>
                    <TableCell className="whitespace-nowrap">
                      {formatDate(m.published_at)}
                    </TableCell>
                    <TableCell>
                      <a
                        href={m.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex text-primary hover:underline"
                        title="Открыть"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
