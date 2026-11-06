@echo off
REM Gekleurde console-regel (bron/docs/specs/repo-scripts.md Console-output).
REM Gebruik: call scripts\_msg.cmd <rol> "tekst"
REM Rollen: section ok work hard refuse note info detail
REM Respecteert NO_COLOR / FORCE_COLOR. detail alleen bij verbose-env.
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0.."

set "ROLE=%~1"
set "MSG=%~2"
if not defined ROLE goto usage
if "%MSG%"=="" goto usage

if /I "%ROLE%"=="detail" (
  if /I "%BIBLIOTHEEK_VERBOSE%"=="1" goto emit
  if /I "%BIBLIOTHEEK_VERBOSE%"=="true" goto emit
  if /I "%BIBLIOTHEEK_VERBOSE%"=="yes" goto emit
  if /I "%VSA_VERBOSE%"=="1" goto emit
  if /I "%REPO_SCRIPTS_VERBOSE%"=="1" goto emit
  if /I "%VERBOSE%"=="1" goto emit
  endlocal
  exit /b 0
)

:emit
if defined NO_COLOR if not "%NO_COLOR%"=="" goto plain
set "USE_COLOR=0"
if defined FORCE_COLOR if not "%FORCE_COLOR%"=="" set "USE_COLOR=1"
if "%USE_COLOR%"=="0" (
  REM TTY-heuristiek: geen CI-achtige env → kleur aan op lokale console.
  if defined CI goto plain
  if defined GITHUB_ACTIONS goto plain
  set "USE_COLOR=1"
)
if "%USE_COLOR%"=="0" goto plain

for /f "delims=" %%E in ('echo prompt $E^| cmd') do set "ESC=%%E"

if /I "%ROLE%"=="ok" (
  echo %ESC%[32m%MSG%%ESC%[0m
  goto done
)
if /I "%ROLE%"=="work" (
  echo %ESC%[33m%MSG%%ESC%[0m
  goto done
)
if /I "%ROLE%"=="hard" (
  echo %ESC%[1;31m%MSG%%ESC%[0m
  goto done
)
if /I "%ROLE%"=="refuse" (
  echo %ESC%[35m%MSG%%ESC%[0m
  goto done
)
if /I "%ROLE%"=="section" (
  echo %ESC%[1;36m%MSG%%ESC%[0m
  goto done
)
if /I "%ROLE%"=="note" (
  echo %ESC%[2m%MSG%%ESC%[0m
  goto done
)
if /I "%ROLE%"=="info" goto plain
if /I "%ROLE%"=="detail" goto plain

echo ERROR: onbekende _msg-rol: %ROLE% 1>&2
echo Verwacht: section ok work hard refuse note info detail 1>&2
endlocal
exit /b 1

:plain
echo %MSG%
goto done

:usage
echo Gebruik: call scripts\_msg.cmd ^<rol^> "tekst" 1>&2
echo Rollen: section ok work hard refuse note info detail 1>&2
endlocal
exit /b 1

:done
endlocal
exit /b 0
