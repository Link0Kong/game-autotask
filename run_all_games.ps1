# Strict sequential: bh3 -> Genshin -> StarRail (one at a time)
$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sequential Run: bh3 >> Genshin >> StarRail"
Write-Host "========================================" -ForegroundColor Cyan

function Wait-ProcessExit {
    param($Proc, $Name)
    Write-Host "  Waiting for $Name to finish..." -ForegroundColor Yellow
    while (-not $Proc.HasExited) {
        Start-Sleep -Seconds 15
        $Proc.Refresh()
    }
    Write-Host "  $Name finished!" -ForegroundColor Green
}

# === 1: Honkai Impact 3rd (MFW) ===
Write-Host ""
Write-Host "[1/3] Honkai Impact 3rd - MFW" -ForegroundColor Cyan

$mfwPath = "G:\autoapps\bh3\MFW.exe"
$mfw = Get-Process -Name "MFW" -ErrorAction SilentlyContinue

if ($mfw) {
    Write-Host "  MFW already running (PID $($mfw.Id)), waiting..." -ForegroundColor Yellow
    Wait-ProcessExit -Proc $mfw -Name "MFW (bh3)"
} elseif (Test-Path $mfwPath) {
    Write-Host "  Launching MFW.exe..." -ForegroundColor Green
    $mfw = Start-Process -FilePath $mfwPath -WorkingDirectory "G:\autoapps\bh3" -PassThru
    Wait-ProcessExit -Proc $mfw -Name "MFW (bh3)"
} else {
    Write-Host "  ERROR: MFW.exe not found!" -ForegroundColor Red
}

# === 2: Genshin Impact (BetterGI) ===
Write-Host ""
Write-Host "[2/3] Genshin Impact - BetterGI" -ForegroundColor Cyan

$betterGiPath = "G:\autoapps\Genshin Impact\BetterGI\BetterGI.exe"
$betterGiDir  = "G:\autoapps\Genshin Impact\BetterGI"

if (Test-Path $betterGiPath) {
    Write-Host "  Launching BetterGI --startOneDragon..." -ForegroundColor Green
    $gi = Start-Process -FilePath $betterGiPath -ArgumentList "--startOneDragon" -WorkingDirectory $betterGiDir -PassThru
    Wait-ProcessExit -Proc $gi -Name "BetterGI (Genshin)"
} else {
    Write-Host "  ERROR: BetterGI.exe not found!" -ForegroundColor Red
}

# === 3: Star Rail (March7th Assistant) ===
Write-Host ""
Write-Host "[3/3] Star Rail - March7th Assistant" -ForegroundColor Cyan

$m7Path = "G:\autoapps\StarRail\March7thAssistant_full\March7th Assistant.exe"
$m7Dir  = "G:\autoapps\StarRail\March7thAssistant_full"

if (Test-Path $m7Path) {
    Write-Host "  Launching March7th Assistant..." -ForegroundColor Green
    $m7 = Start-Process -FilePath $m7Path -WorkingDirectory $m7Dir -PassThru
    Wait-ProcessExit -Proc $m7 -Name "March7th Assistant (StarRail)"
} else {
    Write-Host "  ERROR: March7th Assistant.exe not found!" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All 3 games done! One at a time!"
Write-Host "========================================" -ForegroundColor Cyan
