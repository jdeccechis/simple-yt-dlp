@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 setup.py
set "setup_result=%errorlevel%"
goto finished
:use_python
python setup.py
set "setup_result=%errorlevel%"
:finished
if not "%setup_result%"=="0" echo Setup did not finish. Read the error above.
pause
exit /b %setup_result%
