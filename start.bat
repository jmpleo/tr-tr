@echo off

set "SCRIPT_DIR=%~dp0"
call %SCRIPT_DIR%\pyvenv.cfg.bat
call "%SCRIPT_DIR%\venv\Scripts\activate.bat"
"%SCRIPT_DIR%\venv\Scripts\python.exe" "%SCRIPT_DIR%\main.py"
exit /b 0