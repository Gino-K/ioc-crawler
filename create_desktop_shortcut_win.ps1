# ===================================================================
#  PowerShell-Skript zur Erstellung einer Desktop-Verknuepfung
#  fuer den IOC Webcrawler.
# ===================================================================

$ShortcutName = "IOC Crawler.lnk"

$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path -Path $DesktopPath -ChildPath $ShortcutName
$ProjectRoot = $PSScriptRoot
$PythonExecutable = Join-Path -Path $ProjectRoot -ChildPath "venv\Scripts\python.exe"


Write-Host "Erstelle Verknuepfung fuer IOC Crawler auf dem Desktop..."

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

$Shortcut.TargetPath = $PythonExecutable
$Shortcut.Arguments = "-m ui.gui"
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.IconLocation = "$PythonExecutable,0"
$Shortcut.Description = "Startet den IOC Webcrawler"

$Shortcut.Save()

Write-Host "Verknuepfung '$ShortcutName' erfolgreich auf dem Desktop erstellt."
Write-Host "BITTE BEACHTEN: Du musst die Verknuepfung noch manuell so einstellen, dass sie als Administrator ausgefuehrt wird."
Write-Host "Rechtsklick -> Eigenschaften -> Erweitert... -> 'Als Administrator ausfuehren'"
