@echo off
setlocal
if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" "%~dp0scripts\dev.py" %*
) else (
  python "%~dp0scripts\dev.py" %*
)
endlocal
