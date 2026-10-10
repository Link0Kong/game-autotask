# Wait for MFW + March7th to finish, then launch BetterGI
Write-Host "Monitoring: waiting for bh3 and StarRail to finish..." -ForegroundColor Cyan

# Wait for MFW
$mfw = Get-Process -Name "MFW" -ErrorAction SilentlyContinue
if ($mfw) {
    Write-Host "  Waiting for MFW (bh3) to finish... (PID $($mfw.Id))" -ForegroundColor Yellow
    while (-not $mfw.HasExited) {
        Start-Sleep -Seconds 10
        $mfw.Refresh()
    }
    Write-Host "  MFW finished!" -ForegroundColor Green
} else {
    Write-Host "  MFW not running (already done)." -ForegroundColor Gray
}

# Wait for March7th Assistant
$m7 = Get-Process -Name "March7th Assistant" -ErrorAction SilentlyContinue
if ($m7) {
    Write-Host "  Waiting for March7th Assistant (StarRail) to finish... (PID $($m7.Id))" -ForegroundColor Yellow
    while (-not $m7.HasExited) {
        Start-Sleep -Seconds 10
        $m7.Refresh()
    }
    Write-Host "  March7th Assistant finished!" -ForegroundColor Green
} else {
    Write-Host "  March7th Assistant not running (already done)." -ForegroundColor Gray
}

# Now launch BetterGI
Write-Host ""
Write-Host "Launching Genshin Impact - BetterGI..." -ForegroundColor Cyan
$betterGiPath = "G:\autoapps\Genshin Impact\BetterGI\BetterGI.exe"
$genshinDir  = "G:\autoapps\Genshin Impact\BetterGI"

if (Test-Path $betterGiPath) {
    Write-Host "  Starting BetterGI --startOneDragon..." -ForegroundColor Green
    $proc = Start-Process -FilePath $betterGiPath -ArgumentList "--startOneDragon" -WorkingDirectory $genshinDir -PassThru
    Write-Host "  Waiting for Genshin automation to complete..." -ForegroundColor Green
    while (-not $proc.HasExited) {
        Start-Sleep -Seconds 10
        $proc.Refresh()
    }
    Write-Host "  BetterGI finished!" -ForegroundColor Green
} else {
    Write-Host "  ERROR: BetterGI.exe not found at $betterGiPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "All done! Genshin completed." -ForegroundColor Cyan
