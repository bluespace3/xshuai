# Set console encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Get the directory where this script is located
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PY_SCRIPT = Join-Path $SCRIPT_DIR "main.py"

# Change to the script directory
Set-Location $SCRIPT_DIR

if (-not (Test-Path $PY_SCRIPT)) {
    Write-Host "Error: main.py not found at $PY_SCRIPT" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Run Python script with all arguments
python $PY_SCRIPT $args