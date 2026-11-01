# Valve Finder - automatic upload
# Watches the songs folder this script sits in (its parent folder) and adds every new MIDI,
# MusicXML or Tony .csv file to the songs folder of github.com/lordfran28/Valve-Finder,
# which is what the website shows. It only ever adds or updates: deleting or renaming a file
# on this computer never deletes anything from the website.
param([switch]$Once)

$ErrorActionPreference = "Stop"
try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch {}

$Api   = if ($env:VF_API) { $env:VF_API } else { "https://api.github.com/repos/lordfran28/Valve-Finder" }
$Data  = if ($env:VF_DATA) { $env:VF_DATA } else { Join-Path $env:LOCALAPPDATA "ValveFinder" }
$Tool  = $PSScriptRoot
$Drop  = Split-Path -Parent $Tool
$Log   = Join-Path $Tool "Upload log.txt"
$StateFile = Join-Path $Data "uploaded.tsv"
$KeyFile = Join-Path $Data "key.txt"
$Exts  = @(".mid", ".midi", ".musicxml", ".xml", ".mxl", ".csv")

function Write-Log([string]$text) {
  $line = (Get-Date).ToString("yyyy-MM-dd HH:mm") + "  " + $text
  try {
    $old = @(); if (Test-Path -LiteralPath $Log) { $old = @(Get-Content -LiteralPath $Log -Encoding UTF8) }
    $all = @($old + $line); if ($all.Count -gt 300) { $all = $all[($all.Count - 300)..($all.Count - 1)] }
    Set-Content -LiteralPath $Log -Value $all -Encoding UTF8
  } catch {}
}
function Show-Note([string]$text) {
  try { (New-Object -ComObject WScript.Shell).Popup($text, 0, "Valve Finder", 48) | Out-Null } catch {}
}
function Get-Key {
  if ($env:VF_KEY) { return $env:VF_KEY }
  $secure = (Get-Content -LiteralPath $KeyFile -Raw).Trim() | ConvertTo-SecureString
  return [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
}
function Invoke-GitHub([string]$Method, [string]$Path, $Body) {
  $p = @{ Uri = $Api + $Path; Method = $Method; UseBasicParsing = $true; UserAgent = "ValveFinderUpload";
          Headers = @{ Authorization = "Bearer " + $script:Token; Accept = "application/vnd.github+json" } }
  if ($Body) { $p.Body = [Text.Encoding]::UTF8.GetBytes(($Body | ConvertTo-Json -Compress)); $p.ContentType = "application/json; charset=utf-8" }
  try {
    $r = Invoke-WebRequest @p
    $c = $r.Content; if ($c -is [byte[]]) { $c = [Text.Encoding]::UTF8.GetString($c) }
    return @{ Status = [int]$r.StatusCode; Json = $(if ($c) { $c | ConvertFrom-Json } else { $null }) }
  } catch {
    $resp = $_.Exception.Response
    if ($resp) { return @{ Status = [int]$resp.StatusCode; Json = $null } }
    return @{ Status = 0; Json = $null }
  }
}
function Get-RepoPath([string]$rel) { return "/contents/" + (((("songs/" + $rel) -split "/") | ForEach-Object { [Uri]::EscapeDataString($_) }) -join "/") }
function Read-State {
  $s = @{}
  if (Test-Path -LiteralPath $StateFile) {
    foreach ($l in Get-Content -LiteralPath $StateFile -Encoding UTF8) {
      $f = $l -split "`t"; if ($f.Count -ge 5) { $s[$f[0]] = @{ Size = [long]$f[1]; Ticks = [long]$f[2]; Sha = $f[3]; Remote = $f[4] } }
    }
  }
  return $s
}
function Save-State($s) {
  $lines = foreach ($k in $s.Keys) { $v = $s[$k]; "$k`t$($v.Size)`t$($v.Ticks)`t$($v.Sha)`t$($v.Remote)" }
  New-Item -ItemType Directory -Force -Path $Data | Out-Null
  $tmp = $StateFile + ".tmp"
  Set-Content -LiteralPath $tmp -Value @($lines) -Encoding UTF8
  Move-Item -LiteralPath $tmp -Destination $StateFile -Force
}

# What the website already has, by content, so the same song is never added twice under another name.
function Get-SiteHashes {
  $r = Invoke-GitHub "GET" "/contents/songs/index.json" $null
  $h = @{}
  if ($r.Status -eq 200 -and $r.Json.content) {
    $text = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($r.Json.content -replace "\s", "")))
    $list = $text | ConvertFrom-Json
    foreach ($s in $list.songs) { if ($s.sha1) { $h[[string]$s.sha1] = $(if ($s.removed) { "removed:" } else { "" }) + [string]$s.file } }
    # songs deleted from the website stay deleted: a copy left in this folder isn't sent again
    foreach ($x in $list.removed) { if ($x.sha1 -and -not $h.ContainsKey([string]$x.sha1)) { $h[[string]$x.sha1] = "removed:" + [string]$x.file } }
  } elseif ($r.Status -eq 401 -or $r.Status -eq 403) { throw "key:" + $r.Status }
  return $h
}

# The id GitHub gives a file's content, so we can tell whether the website already has these exact bytes.
function Get-BlobSha([byte[]]$bytes) {
  $head = [Text.Encoding]::ASCII.GetBytes("blob " + $bytes.Length + [char]0)
  $all = New-Object byte[] ($head.Length + $bytes.Length)
  [Array]::Copy($head, $all, $head.Length)
  [Array]::Copy($bytes, 0, $all, $head.Length, $bytes.Length)
  $h = [Security.Cryptography.SHA1]::Create()
  return (($h.ComputeHash($all) | ForEach-Object { $_.ToString("x2") }) -join "")
}

# Keeps these scripts the same as the copy in the Valve-Finder repository (tools/pc-upload),
# so fixes reach this computer by themselves. Returns $true when upload.ps1 itself changed.
function Update-Self {
  $restart = $false
  foreach ($name in @("upload.ps1", "setup.ps1", "stop.ps1")) {
    try {
      $local = Join-Path $Tool $name
      $r = Invoke-GitHub "GET" ("/contents/tools/pc-upload/" + $name) $null
      if ($r.Status -ne 200 -or -not $r.Json.content) { continue }
      $bytes = [Convert]::FromBase64String(($r.Json.content -replace "\s", ""))
      $have = if (Test-Path -LiteralPath $local) { Get-BlobSha ([IO.File]::ReadAllBytes($local)) } else { "" }
      if ($have -eq (Get-BlobSha $bytes)) { continue }
      $errs = $null; $tokens = $null
      [void][Management.Automation.Language.Parser]::ParseInput([Text.Encoding]::UTF8.GetString($bytes), [ref]$tokens, [ref]$errs)
      if ($errs -and $errs.Count -gt 0) { continue }
      [IO.File]::WriteAllBytes($local, $bytes)
      Write-Log ("Updated " + $name + " to the latest version.")
      if ($name -eq "upload.ps1") { $restart = $true }
    } catch {}
  }
  return $restart
}

function Invoke-Pass {
  # One pass at a time, even if "Upload now" runs while the background copy is working.
  New-Item -ItemType Directory -Force -Path $Data | Out-Null
  try { $lock = [IO.File]::Open((Join-Path $Data "upload.lock"), "OpenOrCreate", "ReadWrite", "None") } catch { return }
  try { Invoke-PassLocked } finally { $lock.Close() }
}
function Invoke-PassLocked {
  $state = Read-State; $script:Site = $null
  $files = Get-ChildItem -LiteralPath $Drop -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    ($Exts -contains $_.Extension.ToLower()) -and -not $_.FullName.StartsWith($Tool + [IO.Path]::DirectorySeparatorChar) -and -not $_.Name.StartsWith(".") -and -not $_.Name.StartsWith("~")
  } | Sort-Object { $_.Name -match "\(\d+\)\.[^.]+$" }, FullName   # "song.mid" before its copy "song (1).mid"
  foreach ($f in $files) {
    # One file that can't be read (still downloading, locked, a cloud placeholder) doesn't stop the others,
    # and what was sent is written down straight away, so nothing is ever sent twice.
    try { if (Send-File $f $state) { Save-State $state } }
    catch {
      if ("$_" -like "key:*") { throw }
      Write-Log ("Couldn't send " + $f.Name + " this time (" + $_.Exception.Message + "). It will be tried again.")
    }
  }
}
function Send-File($f, $state) {
  $found = $null
  $rel = $f.FullName.Substring($Drop.Length).TrimStart("\", "/") -replace "\\", "/"
  $ticks = $f.LastWriteTimeUtc.Ticks
  $known = $state[$rel]
  if ($known -and $known.Size -eq $f.Length -and $known.Ticks -eq $ticks) { return $false }
  if (((Get-Date).ToUniversalTime() - $f.LastWriteTimeUtc).TotalSeconds -lt 10) { return $false }   # still being copied
  $bytes = [IO.File]::ReadAllBytes($f.FullName)
  $sha = (([Security.Cryptography.SHA1]::Create().ComputeHash($bytes)) | ForEach-Object { $_.ToString("x2") }) -join ""
  if ($known -and $known.Sha -eq $sha) { $known.Size = $f.Length; $known.Ticks = $ticks; return $true }
  if ($null -eq $script:Site) { $script:Site = Get-SiteHashes }
  if ($script:Site.ContainsKey($sha)) {
    $state[$rel] = @{ Size = $f.Length; Ticks = $ticks; Sha = $sha; Remote = $script:Site[$sha] }
    if ($script:Site[$sha] -like "removed:*") { Write-Log ("Deleted from the website, so not sent again: " + $f.Name) }
    else { Write-Log ("Already on the website: " + $f.Name) }
    return $true
  }
  $blob = Get-BlobSha $bytes
  # Where it goes: the same place as before if this computer added it, otherwise a free name.
  $mine = $known -and $known.Remote -like "songs/*"
  $target = if ($mine) { $known.Remote.Substring(6) } else { $rel }
  $remote = Invoke-GitHub "GET" (Get-RepoPath $target) $null
  if ($remote.Status -eq 401 -or $remote.Status -eq 403) { throw "key:" + $remote.Status }
  $remoteSha = $null
  if ($remote.Status -eq 200) {
    if ($remote.Json.sha -eq $blob) { $found = $target }
    elseif ($mine) { $remoteSha = $remote.Json.sha }
    else {
      $base = [IO.Path]::GetFileNameWithoutExtension($rel); $dir = [IO.Path]::GetDirectoryName($rel) -replace "\\", "/"
      $n = 2
      do {
        $target = $(if ($dir) { "$dir/" } else { "" }) + "$base $n" + $f.Extension; $n++
        $probe = Invoke-GitHub "GET" (Get-RepoPath $target) $null
        if ($probe.Status -eq 200 -and $probe.Json.sha -eq $blob) { $found = $target; break }
      } while ($probe.Status -eq 200 -and $n -lt 50)
    }
  }
  if ($found) {
    # the very same file is already there (sent a moment ago, before the song list caught up)
    $state[$rel] = @{ Size = $f.Length; Ticks = $ticks; Sha = $sha; Remote = "songs/" + $found }
    $script:Site[$sha] = "songs/" + $found
    Write-Log ("Already on the website: " + $f.Name)
    return $true
  }
  $body = @{ message = $(if ($remoteSha) { "Update " } else { "Add " }) + [IO.Path]::GetFileName($target) + " from PC"
             content = [Convert]::ToBase64String($bytes); branch = "main" }
  if ($remoteSha) { $body.sha = $remoteSha }
  $put = Invoke-GitHub "PUT" (Get-RepoPath $target) $body
  if ($put.Status -eq 200 -or $put.Status -eq 201) {
    $state[$rel] = @{ Size = $f.Length; Ticks = $ticks; Sha = $sha; Remote = "songs/" + $target }
    $script:Site[$sha] = "songs/" + $target   # a second copy of the same file in this folder isn't sent again
    Write-Log ($(if ($remoteSha) { "Updated on the website: " } else { "Added to the website: " }) + [IO.Path]::GetFileName($target))
    return $true
  }
  if ($put.Status -eq 401 -or $put.Status -eq 403 -or $put.Status -eq 404) { throw "key:" + $put.Status }
  if ($put.Status -ne 0) { Write-Log ("GitHub refused " + $f.Name + " (error " + $put.Status + "). It will be tried again.") }
  return $false
}

if (-not $env:VF_KEY -and -not (Test-Path -LiteralPath $KeyFile)) { Write-Log "No GitHub key on this computer yet. Run 'Set up automatic upload' in this folder."; exit 1 }
try { $script:Token = Get-Key } catch { Write-Log ("The GitHub key couldn't be read (" + $_.Exception.Message + "). Run 'Set up automatic upload' again."); exit 1 }
$pass = 0
do {
  if ($pass % 60 -eq 0 -and -not $env:VF_NO_UPDATE) {
    if ((Update-Self) -and -not $Once) {
      # start the new version and let this one go (if it can't be started, this one carries on)
      $args2 = @("-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", "`"" + (Join-Path $Tool "upload.ps1") + "`"")
      $exe = (Get-Process -Id $PID).Path
      $started = $false
      try { Start-Process -FilePath $exe -WindowStyle Hidden -ArgumentList $args2; $started = $true }
      catch { try { Start-Process -FilePath $exe -ArgumentList $args2; $started = $true } catch {} }
      if ($started) { exit 0 }
    }
  }
  $pass++
  try { Invoke-Pass }
  catch {
    if ("$_" -like "key:*") {
      Write-Log "The GitHub key stopped working (it may have expired). Run 'Set up automatic upload' again."
      Show-Note "Valve Finder can't upload new songs: the GitHub key stopped working (it may have expired).`n`nOpen the 'Valve Finder upload' folder inside your songs folder and run 'Set up automatic upload' again."
      exit 2
    }
    Write-Log ("Something went wrong, trying again in a minute: " + $_.Exception.Message)
  }
  if (-not $Once) { Start-Sleep -Seconds 60 }
} while (-not $Once)
