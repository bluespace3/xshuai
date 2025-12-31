# Add Ollama to Windows Startup
# This script creates a shortcut in the Startup folder

$scriptPath = "D:\code\py\xxzhou\utils\start-ollama.bat"
$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "Start-Ollama.lnk"

# Create WScript.Shell object
$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)

# Configure shortcut properties
$shortcut.TargetPath = $scriptPath
$shortcut.WorkingDirectory = "D:\code\py\xxzhou\utils"
$shortcut.Description = "Start Ollama service automatically"
$shortcut.Save()

Write-Host "Ollama has been added to Windows startup!"
Write-Host "Startup shortcut created at: $shortcutPath"