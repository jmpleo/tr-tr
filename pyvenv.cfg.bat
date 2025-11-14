@echo off
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "HOME_DIR="
for /f "delims=" %%D in ('dir /b /ad "%SCRIPT_DIR%\python-*" 2^>nul') do (
  set "HOME_DIR=%SCRIPT_DIR%\%%D"
  goto :found
)
set "HOME_DIR=%SCRIPT_DIR%"
:found

set "HOME_DIR=%HOME_DIR:"=%"

set "IMPLEMENTATION=CPython"
set "VERSION_INFO=3.11.0.final.0"
set "VIRTUALENV=20.35.4"
set "INCLUDE_SYSTEM_SITE_PACKAGES=false"
set "BASE_PREFIX=%HOME_DIR%"
set "BASE_EXEC_PREFIX=%HOME_DIR%"
set "BASE_EXECUTABLE=%HOME_DIR%\python.exe"
set "PROMPT=tr-tr"

set "PYVENVCFG_FILE=%SCRIPT_DIR%\venv\pyvenv.cfg"

(
  echo home = %BASE_PREFIX%
  echo implementation = %IMPLEMENTATION%
  echo version_info = %VERSION_INFO%
  echo virtualenv = %VIRTUALENV%
  echo include-system-site-packages = %INCLUDE_SYSTEM_SITE_PACKAGES%
  echo base-prefix = %BASE_PREFIX%
  echo base-exec-prefix = %BASE_EXEC_PREFIX%
  echo base-executable = %BASE_EXECUTABLE%
  echo prompt = %PROMPT%
) > "%PYVENVCFG_FILE%"

echo update "%PYVENVCFG_FILE%"
