@echo off
setlocal EnableExtensions
REM Voeg @toon (uit titel/pad) en optioneel @tempo 130 toe aan .mvsa.
REM Standaard dry-run. Schrijven: --apply. Tempo meekrijgen: --tempo.
REM
REM Bibliotheek:
REM   cd /d C:\Git\orthodox-ronl\bibliotheek
REM   C:\Git\orthodox-ronl\VSA-tooling\scripts\migrate-metadata.cmd content-source --apply
REM
REM Tooling-voorbeelden:
REM   cd /d C:\Git\orthodox-ronl\VSA-tooling
REM   scripts\migrate-metadata.cmd examples\mvsa --apply
REM
REM Zonder map-argument: huidige map (recursief *.mvsa).

cd /d "%~dp0.."
python scripts\migrate_metadata_toon_tempo.py %*
exit /b %ERRORLEVEL%
