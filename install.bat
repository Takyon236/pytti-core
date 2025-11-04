@echo off
REM PyTTI Installation Script for Windows

echo ================================================================
echo            PyTTI Modern - Installation Script
echo ================================================================
echo.

REM Check if we're in a git repository
if not exist ".git" (
    echo Error: Not in a git repository
    echo Please run this script from the pytti-core directory
    exit /b 1
)

echo Step 1: Initializing git submodules...
echo ----------------------------------------------------------------
git submodule update --init --recursive
if errorlevel 1 (
    echo Failed to initialize submodules
    exit /b 1
)
echo Submodules initialized
echo.

echo Step 2: Installing vendor dependencies...
echo ----------------------------------------------------------------

REM Install AdaBins
if exist "vendor\AdaBins" (
    echo Installing AdaBins...
    pip install .\vendor\AdaBins
    echo AdaBins installed
) else (
    echo AdaBins directory not found, skipping...
)

REM Install CLIP
if exist "vendor\CLIP" (
    echo Installing CLIP...
    pip install .\vendor\CLIP
    echo CLIP installed
) else (
    echo CLIP directory not found, skipping...
)

REM Install GMA
if exist "vendor\GMA" (
    echo Installing GMA...
    pip install .\vendor\GMA
    echo GMA installed
) else (
    echo GMA directory not found, skipping...
)

REM Install taming-transformers
if exist "vendor\taming-transformers" (
    echo Installing taming-transformers...
    pip install .\vendor\taming-transformers
    echo taming-transformers installed
) else (
    echo taming-transformers directory not found, skipping...
)

echo.
echo Step 3: Installing PyTTI core...
echo ----------------------------------------------------------------

REM Detect installation option
if "%1"=="all" (
    echo Installing PyTTI with ALL features ^(modern + webui^)...
    echo Using version constraints for stable, tested dependencies...
    pip install -c constraints.txt -e .[all]
) else if "%1"=="modern" (
    echo Installing PyTTI with modern AI models...
    echo Using version constraints for stable, tested dependencies...
    pip install -c constraints.txt -e .[modern]
) else if "%1"=="webui" (
    echo Installing PyTTI with Web UI...
    echo Using version constraints for stable, tested dependencies...
    pip install -c constraints.txt -e .[webui]
) else (
    echo Installing PyTTI core only...
    echo ^(Use 'install.bat all' for all features^)
    echo Using version constraints for stable, tested dependencies...
    pip install -c constraints.txt -e .
)

echo PyTTI installed
echo.

echo Step 4: Validating installation...
echo ----------------------------------------------------------------
where pytti-validate >nul 2>&1
if errorlevel 1 (
    echo pytti-validate not found, skipping validation...
) else (
    pytti-validate
)

echo.
echo ================================================================
echo               Installation Complete!
echo ================================================================
echo.

if "%1"=="all" (
    echo Launch Web UI with: pytti-webui
    echo.
) else if "%1"=="webui" (
    echo Launch Web UI with: pytti-webui
    echo.
)

echo Documentation:
echo   - Quick Start: QUICK_START.md
echo   - Web UI Guide: WEBUI_GUIDE.md
echo   - Examples: MODERN_USAGE_EXAMPLES.md
echo.
echo Happy creating!
