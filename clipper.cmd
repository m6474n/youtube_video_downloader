@echo off
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

where antigravity-ide >nul 2>nul
if %ERRORLEVEL% equ 0 (
    antigravity-ide "%PROJECT_DIR%"
    exit /b 0
)

where antigravity >nul 2>nul
if %ERRORLEVEL% equ 0 (
    antigravity "%PROJECT_DIR%"
    exit /b 0
)

if exist "%LOCALAPPDATA%\Programs\Antigravity IDE\bin\antigravity-ide.cmd" (
    call "%LOCALAPPDATA%\Programs\Antigravity IDE\bin\antigravity-ide.cmd" "%PROJECT_DIR%"
    exit /b 0
)

if exist "%LOCALAPPDATA%\Programs\Antigravity\bin\antigravity.cmd" (
    call "%LOCALAPPDATA%\Programs\Antigravity\bin\antigravity.cmd" "%PROJECT_DIR%"
    exit /b 0
)

echo [Error] Antigravity executable not found.
exit /b 1

