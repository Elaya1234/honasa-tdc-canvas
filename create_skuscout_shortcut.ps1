$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path -Path $DesktopPath -ChildPath "SKUScout - Cross-Marketplace Link Agent.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "C:\Users\elaya.n\Documents\HONASA TDC\Launch_SKUScout.bat"
$Shortcut.WorkingDirectory = "C:\Users\elaya.n\Documents\HONASA TDC"
$Shortcut.Description = "1-Click SKUScout Autonomous Cross-Marketplace Exact Variant Link Finder"
$Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,23"
$Shortcut.Save()
Write-Output "Shortcut created at $ShortcutPath"
