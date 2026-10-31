# Valve Finder - one-time setup for automatic upload
$ErrorActionPreference = "Stop"
try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch {}
$Api  = if ($env:VF_API) { $env:VF_API } else { "https://api.github.com/repos/lordfran28/Valve-Finder" }
$Data = if ($env:VF_DATA) { $env:VF_DATA } else { Join-Path $env:LOCALAPPDATA "ValveFinder" }
$Upload = Join-Path $PSScriptRoot "upload.ps1"
$TaskName = "Valve Finder upload"
$KeyUrl = "https://github.com/settings/personal-access-tokens/new?name=Valve%20Finder%20uploads%20from%20PC&description=Adds%20songs%20from%20the%20PC%20to%20Valve%20Finder&target_name=lordfran28&expires_in=366&contents=write"

Write-Host ""
Write-Host "  VALVE FINDER - AUTOMATIC UPLOAD" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Songs you put in this folder will be added to the website by themselves:"
Write-Host "  $(Split-Path -Parent $PSScriptRoot)"
Write-Host ""
Write-Host "  1. A GitHub page is opening. Under 'Repository access' choose"
Write-Host "     'Only select repositories' and pick Valve-Finder."
Write-Host "     (Contents is already set to 'Read and write'.)"
Write-Host "  2. Press 'Generate token' at the bottom, then copy the key it shows."
Write-Host "  3. Come back here, paste it (right-click or Ctrl+V) and press Enter."
Write-Host ""
if (-not $env:VF_KEY) { Start-Process $KeyUrl }

$ok = $false
for ($try = 1; $try -le 3 -and -not $ok; $try++) {
  if ($env:VF_KEY) { $plain = $env:VF_KEY; $secure = ConvertTo-SecureString $plain -AsPlainText -Force }
  else {
    $secure = Read-Host "  Paste the key here" -AsSecureString
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
  }
  $plain = $plain.Trim()
  if (-not $plain) { Write-Host "  Nothing was pasted. Try again." -ForegroundColor Red; continue }
  try {
    $r = Invoke-WebRequest -Uri ($Api + "/contents/songs") -UseBasicParsing -UserAgent "ValveFinderUpload" -Headers @{ Authorization = "Bearer $plain"; Accept = "application/vnd.github+json" }
    $ok = $true
  } catch {
    $code = 0; if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
    if ($code -eq 401) { Write-Host "  GitHub didn't accept that key. Copy it again (the whole thing, starting github_pat_)." -ForegroundColor Red }
    elseif ($code -eq 404 -or $code -eq 403) { Write-Host "  That key can't see Valve-Finder. Make a new one and pick Valve-Finder under Repository access." -ForegroundColor Red }
    else { Write-Host "  Couldn't reach GitHub. Check the internet connection and try again." -ForegroundColor Red }
    if ($env:VF_KEY) { break }
  }
}
if (-not $ok) { Write-Host ""; Write-Host "  Setup didn't finish. Run it again when you're ready."; if (-not $env:VF_KEY) { Read-Host "  Press Enter to close" | Out-Null }; exit 1 }

New-Item -ItemType Directory -Force -Path $Data | Out-Null
ConvertTo-SecureString $plain -AsPlainText -Force | ConvertFrom-SecureString | Set-Content -LiteralPath (Join-Path $Data "key.txt")

# Start with Windows, quietly, and keep running in the background.
$started = $false
try {
  $me = [Security.Principal.WindowsIdentity]::GetCurrent().Name
  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"" + $Upload + "`"")
  $trigger = New-ScheduledTaskTrigger -AtLogOn -User $me
  $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -StartWhenAvailable
  $principal = New-ScheduledTaskPrincipal -UserId $me -LogonType Interactive -RunLevel Limited
  Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
  Start-ScheduledTask -TaskName $TaskName
  $started = $true
} catch {
  # Fallback: a shortcut in the Startup folder does the same at every sign-in.
  try {
    $lnk = Join-Path ([Environment]::GetFolderPath("Startup")) "Valve Finder upload.lnk"
    $sh = New-Object -ComObject WScript.Shell; $s = $sh.CreateShortcut($lnk)
    $s.TargetPath = "powershell.exe"; $s.Arguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Upload`""; $s.WindowStyle = 7; $s.Save()
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @("-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", "`"$Upload`"")
    $started = $true
  } catch {}
}
Write-Host ""
if ($started) {
  Write-Host "  Done. New songs in this folder go to the website within a minute or two." -ForegroundColor Green
  Write-Host "  It starts by itself whenever you sign in to Windows. 'Upload log.txt' shows what it added."
} else {
  Write-Host "  The key is saved, but Windows wouldn't let it start by itself." -ForegroundColor Red
  Write-Host "  Double-click 'Upload now' whenever you add songs."
}
Write-Host ""
if (-not $env:VF_KEY) { Read-Host "  Press Enter to close" | Out-Null }
