@echo off
REM PyTTI Modern Installation Script for Windows
REM No legacy dependencies required - uses modern AI models only

echo ================================================================
echo            PyTTI Modern - Installation Script
echo ================================================================
echo.
echo IMPORTANT: Install PyTorch first for your CUDA version!
echo Visit: https://pytorch.org/get-started/locally/
echo.
echo Example for CUDA 12.1:
echo   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
echo.

REM Check if we're in a git repository
if not exist ".git" (
    echo Error: Not in a git repository
    echo Please run this script from the pytti-core directory
    exit /b 1
)

echo Installing PyTTI Modern...
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

echo Validating installation...
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
