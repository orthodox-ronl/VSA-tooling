@echo off
setlocal EnableExtensions

cd /d "%~dp0"

if "%~1"=="" (
  echo Gebruik: %~nx0 naam[.mvsa] ^| all
  echo Voorbeeld: %~nx0 alleluia-toon-1
  echo           %~nx0 all
  exit /b 1
)

if /i "%~1"=="all" goto :all

call :one "%~1"
exit /b %errorlevel%

:all
set "FAILED=0"
for %%i in (*.mvsa) do (
  rem Skip genormaliseerde afgeleiden: naam.mvsa.mvsa (%%~ni eindigt dan op .mvsa)
  echo %%~ni| findstr /i /e ".mvsa" >nul
  if errorlevel 1 (
    call :one "%%i"
    if errorlevel 1 set "FAILED=1"
  )
)
if not "%FAILED%"=="0" exit /b 1

echo.
echo === validate genormaliseerde bestanden ^(*.mvsa.mvsa^) ===
for %%i in (*.mvsa.mvsa) do (
  echo.
  echo validate %%i
  vsa mvsa validate "%%i"
  if errorlevel 1 set "FAILED=1"
)
if not "%FAILED%"=="0" exit /b 1
exit /b 0

:one
rem Accepteer zowel "naam" als "naam.mvsa" (en eventueel een pad).
set "BASE=%~n1"
set "SRC=%BASE%.mvsa"

if not exist "%SRC%" (
  echo Bestand niet gevonden: %SRC%
  exit /b 1
)

echo.
echo === %SRC% ===
echo validate %SRC%
vsa mvsa validate "%SRC%"
if errorlevel 1 exit /b 1

echo.
echo normalize %SRC%
vsa mvsa normalize "%SRC%" -o "%SRC%.mvsa"
if errorlevel 1 exit /b 1

echo.
echo make mxl %SRC%
vsa mvsa musicxml "%SRC%" -o "%SRC%.mxl"
if errorlevel 1 exit /b 1

echo.
echo make mscz %SRC%
vsa mvsa mscz "%SRC%" -o "%SRC%.mscz"
if errorlevel 1 exit /b 1

echo.
echo make pdf %SRC% ^(zangers / MuseScore-partituur^)
vsa mvsa pdf "%SRC%.mscz" -o "%SRC%.pdf"
if errorlevel 1 exit /b 1

exit /b 0
