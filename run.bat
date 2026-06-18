@echo off
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    set PYCMD=python
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set PYCMD=py
    ) else (
        echo Python not found. Install it from python.org and check "Add to PATH".
        pause
        exit /b 1
    )
)

start "" "watcher.html"
%PYCMD% relay.py
pause
