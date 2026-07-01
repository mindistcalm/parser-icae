#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot
Set-Location $Root

$Port = if ($env:PORT) { [int]$env:PORT } else { 8000 }
$SkipBuild = $env:SKIP_BUILD -eq "1"

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Find-Python {
    $candidates = @(
        @{ Cmd = "py"; Args = @("-3") },
        @{ Cmd = "python"; Args = @() },
        @{ Cmd = "python3"; Args = @() }
    )
    foreach ($c in $candidates) {
        if (-not (Get-Command $c.Cmd -ErrorAction SilentlyContinue)) { continue }
        try {
            & $c.Cmd @($c.Args + @("-c", "import sys; print(sys.version)")) | Out-Null
            return @{ Cmd = $c.Cmd; Args = $c.Args }
        } catch { }
    }
    throw "Python 3 не найден. Установите с https://www.python.org/downloads/ (отметьте 'Add to PATH')"
}

function Free-Port([int]$TargetPort) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $TargetPort -State Listen -ErrorAction SilentlyContinue
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $pids) {
            if ($procId -and $procId -ne 0) {
                Write-Step "Порт $TargetPort занят — останавливаю PID $procId"
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            }
        }
        Start-Sleep -Seconds 1
    } catch {
        # fallback для старых систем
        $line = netstat -ano | Select-String ":$TargetPort\s" | Select-Object -First 1
        if ($line -match "\s+(\d+)\s*$") {
            $procId = [int]$Matches[1]
            Write-Step "Порт $TargetPort занят — останавливаю PID $procId"
            taskkill /PID $procId /F | Out-Null
        }
    }
}

$pythonInfo = Find-Python
$pythonLabel = "$($pythonInfo.Cmd) $($pythonInfo.Args -join ' ')"
Write-Step "Python: $pythonLabel"

if (-not (Test-Path ".venv")) {
    Write-Step "Создаю виртуальное окружение .venv"
    & $pythonInfo.Cmd @($pythonInfo.Args + @("-m", "venv", ".venv"))
}

$pip = Join-Path $Root ".venv\Scripts\pip.exe"
$icaeWeb = Join-Path $Root ".venv\Scripts\icae-web.exe"
$pythonVenv = Join-Path $Root ".venv\Scripts\python.exe"

Write-Step "Устанавливаю зависимости Python"
& $pip install -e . -q

if ($SkipBuild) {
    Write-Host "SKIP_BUILD=1 — сборка фронтенда пропущена"
} elseif (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Step "Node: $(node -v), npm: $(npm -v)"
    Push-Location (Join-Path $Root "web")
    try {
        if (-not (Test-Path "node_modules")) {
            Write-Step "npm install (первый запуск)"
            if (Test-Path "package-lock.json") { npm ci } else { npm install }
        }
        Write-Step "Сборка фронтенда"
        npm run build
    } finally {
        Pop-Location
    }
} else {
    Write-Warning "npm не найден — установите Node.js 18+ с https://nodejs.org"
    Write-Warning "Фронтенд не собран. API будет доступен на http://localhost:$Port/api/"
}

Free-Port -TargetPort $Port

Write-Step "Запуск на http://localhost:$Port"
Write-Host "Остановка: Ctrl+C" -ForegroundColor DarkGray

$env:PORT = "$Port"
if (Test-Path $icaeWeb) {
    & $icaeWeb
} else {
    & $pythonVenv -m parser.api.server
}
