@echo off

sc config Audiosrv start= auto >nul
net start Audiosrv >nul 2>&1
net start "RtkAudioUniversalService" >nul 2>&1