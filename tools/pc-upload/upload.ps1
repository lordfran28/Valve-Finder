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
  $secure = Get-Content -LiteralPath $KeyFile -Raw | ConvertTo-SecureString
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
  Set-Content -LiteralPath $StateFile -Value @($lines) -Encoding UTF8
}

# What the website already has, by content, so the same song is never added twice under another name.
function Get-SiteHashes {
  $r = Invoke-GitHub "GET" "/contents/songs/index.json" $null
  $h = @{}
  if ($r.Status -eq 200 -and $r.Json.content) {
    $text = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($r.Json.content -replace "\s", "")))
    foreach ($s in ($text | ConvertFrom-Json).songs) { if ($s.sha1) { $h[[string]$s.sha1] = [string]$s.file } }
  } elseif ($r.Status -eq 401 -or $r.Status -eq 403) { throw "key:" + $r.Status }
  return $h
}

function Invoke-Pass {
  # One pass at a time, even if "Upload now" runs while the background copy is working.
  New-Item -ItemType Directory -Force -Path $Data | Out-Null
  try { $lock = [IO.File]::Open((Join-Path $Data "upload.lock"), "OpenOrCreate", "ReadWrite", "None") } catch { return }
  try { Invoke-PassLocked } finally { $lock.Close() }
}
function Invoke-PassLocked {
  $state = Read-State; $changed = $false; $site = $null
  $files = Get-ChildItem -LiteralPath $Drop -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
    ($Exts -contains $_.Extension.ToLower()) -and -not $_.FullName.StartsWith($Tool + [IO.Path]::DirectorySeparatorChar) -and -not $_.Name.StartsWith(".") -and -not $_.Name.StartsWith("~")
  }
  foreach ($f in $files) {
    $rel = $f.FullName.Substring($Drop.Length).TrimStart("\", "/") -replace "\\", "/"
    $ticks = $f.LastWriteTimeUtc.Ticks
    $known = $state[$rel]
    if ($known -and $known.Size -eq $f.Length -and $known.Ticks -eq $ticks) { continue }
    if (((Get-Date).ToUniversalTime() - $f.LastWriteTimeUtc).TotalSeconds -lt 10) { continue }   # still being copied
    $sha = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA1).Hash.ToLower()
    if ($known -and $known.Sha -eq $sha) { $known.Size = $f.Length; $known.Ticks = $ticks; $changed = $true; continue }
    if ($null -eq $site) { $site = Get-SiteHashes }
    if ($site.ContainsKey($sha)) {
      $state[$rel] = @{ Size = $f.Length; Ticks = $ticks; Sha = $sha; Remote = $site[$sha] }; $changed = $true
      Write-Log ("Already on the website: " + $f.Name); continue
    }
    # Where it goes: the same place as before if this computer added it, otherwise a free name.
    $target = if ($known) { $known.Remote.Substring(6) } else { $rel }
    $remote = Invoke-GitHub "GET" (Get-RepoPath $target) $null
    if ($remote.Status -eq 401 -or $remote.Status -eq 403) { throw "key:" + $remote.Status }
    $remoteSha = $null
    if ($remote.Status -eq 200) {
      if ($known) { $remoteSha = $remote.Json.sha }
      else {
        $base = [IO.Path]::GetFileNameWithoutExtension($rel); $dir = [IO.Path]::GetDirectoryName($rel) -replace "\\", "/"
        $n = 2
        do {
          $target = $(if ($dir) { "$dir/" } else { "" }) + "$base $n" + $f.Extension; $n++
          $probe = Invoke-GitHub "GET" (Get-RepoPath $target) $null
        } while ($probe.Status -eq 200 -and $n -lt 50)
      }
    }
    $body = @{ message = $(if ($remoteSha) { "Update " } else { "Add " }) + [IO.Path]::GetFileName($target) + " from PC"
               content = [Convert]::ToBase64String([IO.File]::ReadAllBytes($f.FullName)); branch = "main" }
    if ($remoteSha) { $body.sha = $remoteSha }
    $put = Invoke-GitHub "PUT" (Get-RepoPath $target) $body
    if ($put.Status -eq 200 -or $put.Status -eq 201) {
      $state[$rel] = @{ Size = $f.Length; Ticks = $ticks; Sha = $sha; Remote = "songs/" + $target }; $changed = $true
      Write-Log ($(if ($remoteSha) { "Updated on the website: " } else { "Added to the website: " }) + [IO.Path]::GetFileName($target))
    } elseif ($put.Status -eq 401 -or $put.Status -eq 403 -or $put.Status -eq 404) { throw "key:" + $put.Status }
    elseif ($put.Status -ne 0) { Write-Log ("GitHub refused " + $f.Name + " (error " + $put.Status + "). It will be tried again.") }
  }
  if ($changed) { Save-State $state }
}

try { $script:Token = Get-Key } catch { Write-Log "No GitHub key on this computer yet. Run 'Set up automatic upload' in this folder."; exit 1 }
do {
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
