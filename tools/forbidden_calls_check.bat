@echo off
REM Check src for subprocess use outside the runner/streaming wrappers and git argv
REM
REM Usage from cmd.exe: tools\forbidden_calls_check.bat

python tools\check_forbidden_calls.py %*
exit /b %ERRORLEVEL%
