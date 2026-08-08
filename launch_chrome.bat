@echo off
title Launch Chrome with Remote Debugging Port 9222
echo ========================================================
echo   Mo Google Chrome voi Profile nguoi dung va Port 9222
echo ========================================================
echo.

set CHROME_EXE="C:\Program Files\Google\Chrome\Application\chrome.exe"
set USER_DATA="%LOCALAPPDATA%\Google\Chrome\User Data"
set PROFILE="Default"

if not exist %CHROME_EXE% (
    echo [ERROR] Khong tim thấy Chrome tai: %CHROME_EXE%
    pause
    exit /b 1
)

echo Dang mo Chrome...
start "" %CHROME_EXE% --remote-debugging-port=9222 --user-data-dir=%USER_DATA% --profile-directory=%PROFILE% --remote-allow-origins=*

echo.
echo Chrome da duoc khoi chay voi Remote Debugging Port 9222.
echo Bay gio ban co the chay script Python (open_profile.py) de ket noi.
pause
