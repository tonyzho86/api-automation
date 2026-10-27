@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.cherrystudio\bin;%PATH%"
set PYTHONIOENCODING=utf-8
echo.
echo   Starting SUT (system under test) at http://127.0.0.1:18800
echo   API docs (Swagger UI): http://127.0.0.1:18800/docs
echo   Press Ctrl+C to stop.
echo.
uv run uvicorn sut.app:app --host 127.0.0.1 --port 18800 --reload
