@echo off
REM TEv2 preprocess only (staging → mrg-import → tools → TermRef-check → MRG-copy).
REM Preferred install: npm install  (pins in package.json)
setlocal
cd /d "%~dp0.."
call scripts\_ensure.cmd --node --npm-install --pip-r requirements-docs.txt --import mkdocs
if errorlevel 1 exit /b 1
set NO_MKDOCS_2_WARNING=1

if exist "%APPDATA%\npm" set "PATH=%APPDATA%\npm;%PATH%"
if exist "node_modules\.bin" set "PATH=%CD%\node_modules\.bin;%PATH%"
set "MRGT=mrgt"
set "HRGT=hrgt"
set "TRRT=trrt"
set "MRG_IMPORT=mrg-import"
if exist "%APPDATA%\npm\mrgt.cmd" set "MRGT=%APPDATA%\npm\mrgt.cmd"
if exist "%APPDATA%\npm\hrgt.cmd" set "HRGT=%APPDATA%\npm\hrgt.cmd"
if exist "%APPDATA%\npm\trrt.cmd" set "TRRT=%APPDATA%\npm\trrt.cmd"
if exist "%APPDATA%\npm\mrg-import.cmd" set "MRG_IMPORT=%APPDATA%\npm\mrg-import.cmd"
if exist "%CD%\node_modules\.bin\mrgt.cmd" set "MRGT=%CD%\node_modules\.bin\mrgt.cmd"
if exist "%CD%\node_modules\.bin\hrgt.cmd" set "HRGT=%CD%\node_modules\.bin\hrgt.cmd"
if exist "%CD%\node_modules\.bin\trrt.cmd" set "TRRT=%CD%\node_modules\.bin\trrt.cmd"
if exist "%CD%\node_modules\.bin\mrg-import.cmd" set "MRG_IMPORT=%CD%\node_modules\.bin\mrg-import.cmd"

if not exist "%MRGT%" where mrgt >nul 2>nul
if errorlevel 1 if not exist "%MRGT%" (
  echo ERROR: mrgt was not found on PATH.
  echo Install with: npm install
  exit /b 1
)

if not exist "%HRGT%" where hrgt >nul 2>nul
if errorlevel 1 if not exist "%HRGT%" (
  echo ERROR: hrgt was not found on PATH.
  echo Install with: npm install
  exit /b 1
)

if not exist "%TRRT%" where trrt >nul 2>nul
if errorlevel 1 if not exist "%TRRT%" (
  echo ERROR: trrt was not found on PATH.
  echo Install with: npm install
  exit /b 1
)

echo [1/5] Prepare TEv2 docs staging tree
python scripts\prepare-tev2-docs.py
if errorlevel 1 exit /b 1

echo [2/5] mrg-import
if not exist "%MRG_IMPORT%" where mrg-import >nul 2>nul
if errorlevel 1 if not exist "%MRG_IMPORT%" (
  echo ERROR: mrg-import was not found on PATH.
  echo Install with: npm install
  exit /b 1
)
pushd generated\docs
call "%MRG_IMPORT%" -c tev2-config.yaml
if errorlevel 1 (
  popd
  exit /b 1
)
popd

echo [3/5] mrgt + hrgt
pushd generated\docs
call "%MRGT%" -c tev2-config.yaml
if errorlevel 1 (
  popd
  exit /b 1
)

call "%HRGT%" -f -c tev2-config.yaml
if errorlevel 1 (
  popd
  exit /b 1
)

python ..\..\scripts\sort-glossary-table.py glossary.md
if errorlevel 1 (
  popd
  exit /b 1
)

python ..\..\scripts\inject-glossary-termrefs.py glossary.md
if errorlevel 1 (
  popd
  exit /b 1
)

echo [4/5] trrt + TermRef check
call "%TRRT%" -f -c tev2-config.yaml
if errorlevel 1 (
  popd
  exit /b 1
)
popd

python scripts\check-tev2-termrefs.py generated\docs
if errorlevel 1 exit /b 1

if not exist docs\mrgs mkdir docs\mrgs
copy /Y generated\docs\mrgs\mrg.vsa-tooling*.yaml docs\mrgs\ >nul
python scripts\prepare-tev2-docs.py --normalize-mrg-scopes
if errorlevel 1 exit /b 1

exit /b 0
