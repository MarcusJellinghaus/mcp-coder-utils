@echo off
REM Run tach module dependency check
REM Configuration is in tach.toml
REM
REM Usage from Git Bash: ./tools/tach_check.sh
REM Usage from cmd.exe:  tools\tach_check.bat

where tach >nul 2>&1
if errorlevel 1 (
    echo ERROR: tach not found. Install with: uv pip install tach
    exit /b 1
)

echo Running tach module dependency check...
tach check %*
exit /b %ERRORLEVEL%
