# Valve Finder - stop automatic upload and forget the key on this computer
$Data = if ($env:VF_DATA) { $env:VF_DATA } else { Join-Path $env:LOCALAPPDATA "ValveFinder" }
try { Stop-ScheduledTask -TaskName "Valve Finder upload" -ErrorAction SilentlyContinue; Unregister-ScheduledTask -TaskName "Valve Finder upload" -Confirm:$false -ErrorAction SilentlyContinue } catch {}
try { Remove-Item -LiteralPath (Join-Path ([Environment]::GetFolderPath("Startup")) "Valve Finder upload.lnk") -ErrorAction SilentlyContinue } catch {}
# Only this folder's uploader; Fret Finder's keeps running.
$Upload = Join-Path $PSScriptRoot "upload.ps1"
Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($Upload) } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Remove-Item -LiteralPath (Join-Path $Data "key.txt") -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "  Automatic upload is off, and the GitHub key is removed from this computer."
Write-Host "  Your songs on the website are untouched."
Write-Host ""
Read-Host "  Press Enter to close" | Out-Null
