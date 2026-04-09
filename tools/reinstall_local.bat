@echo off
setlocal enabledelayedexpansion
REM Reinstall mcp-coder-utils package in development mode (editable install)
REM Usage: call tools\reinstall_local.bat  (from project root)
echo =============================================
echo MCP-Coder-Utils Package Reinstallation (Developer)
echo =============================================
echo.
echo NOTE: This installs in editable mode from local source.
echo.

REM Determine project root (parent of tools directory)
set "PROJECT_DIR=%~dp0.."
pushd "!PROJECT_DIR!"
set "PROJECT_DIR=%CD%"
popd

set "VENV_DIR=!PROJECT_DIR!\.venv"
set "VENV_SCRIPTS=!VENV_DIR!\Scripts"
echo [0/6] Checking Python environment...

REM Silently deactivate any active venv
call deactivate 2>nul

REM Check if uv is available
where uv >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [FAIL] uv not found. Install it: pip install uv
    exit /b 1
)
echo [OK] uv found

REM Check if local .venv exists
if not exist "!VENV_SCRIPTS!\activate.bat" (
    echo Local virtual environment not found at !VENV_DIR!
    uv venv .venv
    echo Local virtual environment created at !VENV_DIR!
)
echo [OK] Target environment: !VENV_DIR!
echo.

echo [1/6] Uninstalling existing packages...
uv pip uninstall mcp-coder-utils mcp-coder mcp-tools-py mcp-workspace --python "!VENV_SCRIPTS!\python.exe" 2>nul
echo [OK] Packages uninstalled

echo.
echo [2/6] Installing mcp-coder-utils (this project) in editable mode with dev extras...
pushd "!PROJECT_DIR!"
uv pip install -e ".[dev]" --python "!VENV_SCRIPTS!\python.exe"
if !ERRORLEVEL! NEQ 0 (
    echo [FAIL] Editable installation failed!
    popd
    exit /b 1
)
popd
echo [OK] Package and dev dependencies installed (editable)

echo.
echo [3/6] Overriding sibling deps with GitHub versions...
REM Validate read_github_deps.py succeeds before parsing its output
"!VENV_SCRIPTS!\python.exe" tools\read_github_deps.py > nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo [FAIL] read_github_deps.py failed!
    "!VENV_SCRIPTS!\python.exe" tools\read_github_deps.py
    exit /b 1
)
REM Read GitHub dependency overrides from pyproject.toml
for /f "delims=" %%C in ('"!VENV_SCRIPTS!\python.exe" tools\read_github_deps.py') do (
    echo   %%C
    %%C --python "!VENV_SCRIPTS!\python.exe"
    if !ERRORLEVEL! NEQ 0 (
        echo [FAIL] GitHub dependency override failed!
        exit /b 1
    )
)
echo [OK] GitHub dependencies overridden from pyproject.toml

echo.
echo [4/6] Finalizing editable install of mcp-coder-utils...
REM Re-run to ensure local source is the active install for this project
pushd "!PROJECT_DIR!"
uv pip install -e . --python "!VENV_SCRIPTS!\python.exe"
if !ERRORLEVEL! NEQ 0 (
    echo [FAIL] Final editable install failed!
    popd
    exit /b 1
)
popd
echo [OK] mcp-coder-utils installed (editable)

echo.
echo [5/6] Verifying package import...
"!VENV_SCRIPTS!\python.exe" -c "import mcp_coder_utils; print('mcp_coder_utils OK')"
if !ERRORLEVEL! NEQ 0 (
    echo [FAIL] mcp_coder_utils import failed!
    exit /b 1
)
echo [OK] mcp_coder_utils imports cleanly

echo.
echo =============================================
echo [6/6] Reinstallation completed successfully!
echo.
echo Virtual environment: !VENV_DIR!
echo =============================================
echo.

REM Pass VENV_DIR out of setlocal scope so activation persists to caller
endlocal & set "_REINSTALL_VENV=%VENV_DIR%"

REM Deactivate wrong venv if one is active
if defined VIRTUAL_ENV (
    if not "%VIRTUAL_ENV%"=="%_REINSTALL_VENV%" (
        echo   Deactivating wrong virtual environment: %VIRTUAL_ENV%
        call deactivate 2>nul
    )
)

REM Activate the correct venv (persists to caller's shell)
if not "%VIRTUAL_ENV%"=="%_REINSTALL_VENV%" (
    echo   Activating virtual environment: %_REINSTALL_VENV%
    call "%_REINSTALL_VENV%\Scripts\activate.bat"
)

set "_REINSTALL_VENV="
