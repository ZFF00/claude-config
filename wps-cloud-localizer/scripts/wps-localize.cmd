@echo off
setlocal
if "%~1"=="" (
    echo Usage: %~nx0 "WPS cloud directory" [options]
    echo Example: %~nx0 "C:\Users\me\WPSDrive\MyFolder"
    exit /b 64
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0localize_wps_cloud.ps1" %*
exit /b %ERRORLEVEL%
