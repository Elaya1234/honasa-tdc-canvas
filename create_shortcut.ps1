$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path -Path $DesktopPath -ChildPath "PDP & Image Downloader.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "C:\Users\elaya.n\Documents\HONASA TDC\Launch_PDP_Downloader.bat"
$Shortcut.WorkingDirectory = "C:\Users\elaya.n\Documents\HONASA TDC"
$Shortcut.Description = "1-Click Honasa PDP & Image Intelligence Downloader"
$Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,278"
$Shortcut.Save()
Write-Output "Shortcut created at $ShortcutPath"
