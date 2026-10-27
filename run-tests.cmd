@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.cherrystudio\bin;%PATH%"
set PYTHONIOENCODING=utf-8
uv run pytest %*
