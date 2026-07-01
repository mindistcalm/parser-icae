import { NavLink, Outlet } from "react-router-dom"
import {
  LayoutDashboard,
  List,
  FileSpreadsheet,
  Settings,
  Atom,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Separator } from "@/components/ui/separator"

const nav = [
  { to: "/", label: "Главная", icon: LayoutDashboard },
  { to: "/mentions", label: "Упоминания", icon: List },
  { to: "/reports", label: "Отчёты", icon: FileSpreadsheet },
  { to: "/settings", label: "Настройки", icon: Settings },
]

export function AppShell() {
  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r bg-card md:block">
        <div className="flex h-16 items-center gap-2 px-6">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Atom className="h-5 w-5" />
          </div>
          <div>
            <div className="text-sm font-semibold">ИЦАЭ Parser</div>
            <div className="text-xs text-muted-foreground">Мониторинг упоминаний</div>
          </div>
        </div>
        <Separator />
        <nav className="flex flex-col gap-1 p-4">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="md:pl-64">
        <header className="sticky top-0 z-20 border-b bg-background/95 backdrop-blur md:hidden">
          <div className="flex h-14 items-center justify-between px-4">
            <div className="font-semibold">ИЦАЭ Parser</div>
            <nav className="flex gap-2">
              {nav.map(({ to, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/"}
                  className={({ isActive }) =>
                    cn(
                      "rounded-md px-2 py-1 text-xs",
                      isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground"
                    )
                  }
                >
                  {label}
                </NavLink>
              ))}
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-6xl p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
