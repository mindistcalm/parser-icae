#Requires -Version 5.1
# Установка системных требований: Python 3.10+ и Node.js 18+
$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) { Write-Host "==> $Message" -ForegroundColor Cyan }
function Write-Ok([string]$Message) { Write-Host "  OK $Message" -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host "  ! $Message" -ForegroundColor Yellow }

function Test-Python {
    foreach ($cmd in @(@{E="py";A="-3"}, @{E="python";A=""}, @{E="python3";A=""})) {
        if (-not (Get-Command $cmd.E -ErrorAction SilentlyContinue)) { continue }
        try {
            $ver = & $cmd.E $cmd.A -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
            $parts = $ver.Split(".")
            if ([int]$parts[0] -ge 3 -and [int]$parts[1] -ge 10) {
                Write-Ok "Python $ver ($($cmd.E))"
                return $true
            }
            Write-Warn "Python $ver найден, нужен 3.10+"
        } catch { }
    }
    return $false
}

function Test-Node {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) { return $false }
    $ver = (node -v) -replace "^v", ""
    $major = [int]($ver.Split(".")[0])
    if ($major -ge 18) {
        Write-Ok "Node.js $ver"
        return $true
    }
    Write-Warn "Node.js $ver найден, нужен 18+"
    return $false
}

function Install-WithWinget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget не найден. Установите App Installer из Microsoft Store."
    }
    Write-Step "Установка Python 3.12 через winget"
    winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements

    Write-Step "Установка Node.js LTS через winget"
    winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements

    Write-Warn "Перезапустите терминал после установки, затем выполните: .\run.bat"
}

Write-Step "Проверка требований ИЦАЭ Parser"
Write-Host ""

$hasPython = Test-Python
$hasNode = Test-Node

if ($hasPython -and $hasNode) {
    Write-Step "Всё установлено. Запуск: .\run.bat"
    exit 0
}

Write-Host ""
Write-Step "Чего-то не хватает — устанавливаю..."
Write-Host ""

try {
    Install-WithWinget
} catch {
    Write-Warn $_.Exception.Message
    Write-Host ""
    Write-Host "Установите вручную:" -ForegroundColor Yellow
    Write-Host "  Python 3.10+: https://www.python.org/downloads/  (отметьте Add to PATH)"
    Write-Host "  Node.js 18+:  https://nodejs.org/"
    exit 1
}
