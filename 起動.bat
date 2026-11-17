@echo off
setlocal
set "APP_DIR=%~dp0"
set "PYW="

for %%P in (pythonw.exe) do if not defined PYW if exist "%%~$PATH:P" set "PYW=%%~$PATH:P"
if not defined PYW if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" set "PYW=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
if not defined PYW if exist "%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe" set "PYW=%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"

if not defined PYW (
    echo Python 3.9以降が見つかりません。Pythonをインストールしてから再度お試しください。
    pause
    exit /b 1
)

start "" "%PYW%" "%APP_DIR%gpw_battery.py"
