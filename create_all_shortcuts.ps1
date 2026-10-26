$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$BaseDir = "C:\Users\elaya.n\Documents\HONASA TDC"

Write-Host "Creating Desktop Shortcuts for HONASA Intelligence Suite..." -ForegroundColor Cyan

# 1. Product Data & Media Downloader
$sc1 = $WshShell.CreateShortcut((Join-Path $DesktopPath "Product Data & Media Downloader.lnk"))
$sc1.TargetPath = (Join-Path $BaseDir "Launch_Product_Data_Media_Downloader.bat")
$sc1.WorkingDirectory = $BaseDir
$sc1.Description = "Product Data & Media Downloader"
$sc1.IconLocation = "$env:SystemRoot\System32\shell32.dll,278"
$sc1.Save()
Write-Host "[OK] Created: Product Data & Media Downloader.lnk" -ForegroundColor Green

# 2. Exact SKU Marketplace Link Finder
$sc2 = $WshShell.CreateShortcut((Join-Path $DesktopPath "Exact SKU Marketplace Link Finder.lnk"))
$sc2.TargetPath = (Join-Path $BaseDir "Launch_Exact_SKU_Marketplace_Link_Finder.bat")
$sc2.WorkingDirectory = (Join-Path $BaseDir "skuscout")
$sc2.Description = "Exact SKU Marketplace Link Finder"
$sc2.IconLocation = "$env:SystemRoot\System32\shell32.dll,23"
$sc2.Save()
Write-Host "[OK] Created: Exact SKU Marketplace Link Finder.lnk" -ForegroundColor Green

# 3. Instagram Reel Intelligence Analyzer
$sc3 = $WshShell.CreateShortcut((Join-Path $DesktopPath "Instagram Reel Intelligence Analyzer.lnk"))
$sc3.TargetPath = (Join-Path $BaseDir "Launch_Instagram_Reel_Intelligence_Analyzer.bat")
$sc3.WorkingDirectory = (Join-Path $BaseDir "ig_reel_collector")
$sc3.Description = "Instagram Reel Intelligence Analyzer"
$sc3.IconLocation = "$env:SystemRoot\System32\shell32.dll,138"
$sc3.Save()
Write-Host "[OK] Created: Instagram Reel Intelligence Analyzer.lnk" -ForegroundColor Green

# 4. Product Page Competitive Comparison
$sc4 = $WshShell.CreateShortcut((Join-Path $DesktopPath "Product Page Competitive Comparison.lnk"))
$sc4.TargetPath = (Join-Path $BaseDir "Launch_Product_Page_Competitive_Comparison.bat")
$sc4.WorkingDirectory = $BaseDir
$sc4.Description = "Product Page Competitive Comparison"
$sc4.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$sc4.Save()
Write-Host "[OK] Created: Product Page Competitive Comparison.lnk" -ForegroundColor Green

# 5. Marketplace Link Auto-Filler
$sc5 = $WshShell.CreateShortcut((Join-Path $DesktopPath "Marketplace Link Auto-Filler.lnk"))
$sc5.TargetPath = (Join-Path $BaseDir "Run_Marketplace_Link_Auto_Filler.bat")
$sc5.WorkingDirectory = $BaseDir
$sc5.Description = "Marketplace Link Auto-Filler"
$sc5.IconLocation = "$env:SystemRoot\System32\shell32.dll,165"
$sc5.Save()
Write-Host "[OK] Created: Marketplace Link Auto-Filler.lnk" -ForegroundColor Green

# 6. Product Page Intelligence Extractor
$sc6 = $WshShell.CreateShortcut((Join-Path $DesktopPath "Product Page Intelligence Extractor.lnk"))
$sc6.TargetPath = (Join-Path $BaseDir "Run_Product_Page_Intelligence_Extractor.bat")
$sc6.WorkingDirectory = $BaseDir
$sc6.Description = "Product Page Intelligence Extractor"
$sc6.IconLocation = "$env:SystemRoot\System32\shell32.dll,22"
$sc6.Save()
Write-Host "[OK] Created: Product Page Intelligence Extractor.lnk" -ForegroundColor Green

# 7. TDC - IM Performance Tracking Agent
$sc7 = $WshShell.CreateShortcut((Join-Path $DesktopPath "TDC - IM Performance Tracking Agent.lnk"))
$sc7.TargetPath = (Join-Path $BaseDir "Launch_TDC_IM_Agent.bat")
$sc7.WorkingDirectory = $BaseDir
$sc7.Description = "The Derma Co - IM Performance Tracking Agent"
$sc7.IconLocation = "$env:SystemRoot\System32\shell32.dll,246"
$sc7.Save()
Write-Host "[OK] Created: TDC - IM Performance Tracking Agent.lnk" -ForegroundColor Green

# Master Suite Menu
$scMenu = $WshShell.CreateShortcut((Join-Path $DesktopPath "HONASA Tools Suite.lnk"))
$scMenu.TargetPath = (Join-Path $BaseDir "LAUNCH_ALL_HONASA_TOOLS.bat")
$scMenu.WorkingDirectory = $BaseDir
$scMenu.Description = "HONASA Intelligence & E-Commerce Suite"
$scMenu.IconLocation = "$env:SystemRoot\System32\shell32.dll,15"
$scMenu.Save()
Write-Host "[OK] Created: HONASA Tools Suite.lnk" -ForegroundColor Green

Write-Host "`nAll 7 tool shortcuts created successfully on Desktop!" -ForegroundColor Yellow
