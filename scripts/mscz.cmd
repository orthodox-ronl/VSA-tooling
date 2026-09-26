@echo off
setlocal
cd /d %~dp0\..
call scripts\_ensure.cmd --vsa-tool --import vsa
if errorlevel 1 exit /b 1
python -m vsa.cli_mscz %*
exit /b %ERRORLEVEL%
