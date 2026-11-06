@echo off
setlocal
cd /d %~dp0\..
call scripts\_ensure.cmd --catalogus --vsa-tool --pip-e ".[dev,rendering]" --import vsa --import pytest --import PIL
if errorlevel 1 exit /b 1
call scripts\_msg.cmd section "=== pytest ==="
python -m pytest %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  call scripts\_msg.cmd hard "ERROR  pytest exit %RC%"
  exit /b %RC%
)
call scripts\_msg.cmd ok "OK  pytest"
exit /b 0
