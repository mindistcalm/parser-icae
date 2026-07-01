import { Plus, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

type Props = {
  label: string
  description?: string
  value: string[]
  onChange: (value: string[]) => void
  placeholder?: string
  rows?: number
  disabled?: boolean
}

export function StringListField({
  label,
  description,
  value,
  onChange,
  placeholder,
  rows = 6,
  disabled = false,
}: Props) {
  const text = value.join("\n")

  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {description && <p className="text-xs text-muted-foreground">{description}</p>}
      <Textarea
        rows={rows}
        disabled={disabled}
        value={text}
        onChange={(e) => {
          const items = e.target.value
            .split("\n")
            .map((s) => s.trim())
            .filter(Boolean)
          onChange(items)
        }}
        placeholder={placeholder ?? "По одному значению на строку"}
        className="font-mono text-sm"
      />
      <p className="text-xs text-muted-foreground">{value.length} элементов</p>
    </div>
  )
}

type RssFeed = { name: string; url: string }

type RssProps = {
  value: RssFeed[]
  onChange: (value: RssFeed[]) => void
  disabled?: boolean
}

export function RssFeedListField({ value, onChange, disabled = false }: RssProps) {
  const update = (index: number, field: keyof RssFeed, val: string) => {
    const next = value.map((item, i) =>
      i === index ? { ...item, [field]: val } : item
    )
    onChange(next)
  }

  return (
    <div className="space-y-3">
      <Label>RSS-ленты</Label>
      <p className="text-xs text-muted-foreground">
        Дополнительные источники новостей. Оставьте пустым, если не используете.
      </p>
      {value.length === 0 && (
        <p className="text-sm text-muted-foreground">Ленты не добавлены</p>
      )}
      {value.map((feed, index) => (
        <div key={index} className="flex flex-col gap-2 rounded-lg border p-3 sm:flex-row sm:items-end">
          <div className="flex-1 space-y-2">
            <Label htmlFor={`rss-name-${index}`}>Название</Label>
            <Input
              id={`rss-name-${index}`}
              disabled={disabled}
              value={feed.name}
              onChange={(e) => update(index, "name", e.target.value)}
              placeholder="Например: Новости ТГУ"
            />
          </div>
          <div className="flex-[2] space-y-2">
            <Label htmlFor={`rss-url-${index}`}>URL</Label>
            <Input
              id={`rss-url-${index}`}
              disabled={disabled}
              value={feed.url}
              onChange={(e) => update(index, "url", e.target.value)}
              placeholder="https://example.com/rss/"
            />
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            disabled={disabled}
            onClick={() => onChange(value.filter((_, i) => i !== index))}
            title="Удалить"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ))}
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={disabled}
        onClick={() => onChange([...value, { name: "", url: "" }])}
      >
        <Plus className="h-4 w-4" />
        Добавить ленту
      </Button>
    </div>
  )
}
