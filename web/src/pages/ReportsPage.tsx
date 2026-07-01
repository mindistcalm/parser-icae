import { useQuery } from "@tanstack/react-query"
import { Download, FileText, FileSpreadsheet } from "lucide-react"
import { api } from "@/lib/api"
import { formatFileSize, formatMonthLabel } from "@/lib/utils"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"

export function ReportsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: api.reports,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Отчёты</h1>
        <p className="text-muted-foreground">
          Готовые Excel и HTML отчёты по месяцам
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Файлы отчётов</CardTitle>
          <CardDescription>
            Создаются автоматически после каждого запуска поиска
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-40 w-full" />
          ) : !data?.length ? (
            <p className="text-sm text-muted-foreground">
              Отчётов пока нет. Запустите поиск на главной странице.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Месяц</TableHead>
                  <TableHead>Тип</TableHead>
                  <TableHead>Файл</TableHead>
                  <TableHead>Размер</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((file) => (
                  <TableRow key={file.filename}>
                    <TableCell className="font-medium">
                      {formatMonthLabel(file.month)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {file.kind === "xlsx" ? "Excel" : "HTML"}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs">{file.filename}</TableCell>
                    <TableCell>{formatFileSize(file.size)}</TableCell>
                    <TableCell>
                      <a
                        href={api.reportUrl(file.filename)}
                        download={file.kind === "xlsx"}
                        target={file.kind === "html" ? "_blank" : undefined}
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                      >
                        {file.kind === "xlsx" ? (
                          <FileSpreadsheet className="h-4 w-4" />
                        ) : (
                          <FileText className="h-4 w-4" />
                        )}
                        <Download className="h-3 w-3" />
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
