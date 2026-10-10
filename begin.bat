@echo off
setlocal

:: 停止服务（静默）
net stop "RtkAudioUniversalService" >nul 2>&1
net stop AudioSrv >nul 2>&1

exit