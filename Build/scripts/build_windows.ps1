<#
  4R022 Heart - Windows build.  NO Python installation required.
  Copyright (c) 2026 4R022 / Kaan Kross - 4R022 Heart License

  What it does automatically:
    1. Downloads "uv" (one small standalone tool, no admin rights) into Build\.tools
    2. uv downloads a private Python 3.12 and creates Build\.venv
    3. Installs PySide6 + PyInstaller into that private environment
    4. Builds the app (folder build = instant start-up) with audio, fonts and plugins bundled
    5. Self-tests the result and packs Release\4R022-Heart-vX.Y.Z-windows-x64.zip

  Options:  -OneFile  single exe (slower start)   -SkipTest   -CleanEnv   -KeepWork   -NoPause
#>
param([switch]$OneFile, [switch]$SkipTest, [switch]$CleanEnv, [switch]$KeepWork, [switch]$NoPause)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root    = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Build   = Join-Path $Root 'Build'
$Tools   = Join-Path $Build '.tools'
$Venv    = Join-Path $Build '.venv'
$Work    = Join-Path $Build 'work'
$Dist    = Join-Path $Build 'dist'
$Release = Join-Path $Root 'Release'

function Say([string]$m)  { Write-Host "[4R022] $m" -ForegroundColor Magenta }
function Fail([string]$m) { Write-Host "[4R022][ERROR] $m" -ForegroundColor Red; exit 1 }
function Run([string]$exe, [string[]]$a) {
    & $exe @a
    if ($LASTEXITCODE -ne 0) { Fail "Command failed ($LASTEXITCODE): $exe $($a -join ' ')" }
}

try {
    $ver = [regex]::Match((Get-Content (Join-Path $Root 'Main\Main.py') -Raw), '__version__\s*=\s*"([^"]+)"').Groups[1].Value
    if (-not $ver) { Fail 'Could not read the version from Main\Main.py' }
    if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { $arch = 'arm64'; $triple = 'aarch64-pc-windows-msvc' }
    else                                          { $arch = 'x64';   $triple = 'x86_64-pc-windows-msvc' }

    Write-Host ('=' * 64)
    Write-Host "  4R022 Heart v$ver  |  Windows $arch  |  automatic build"
    Write-Host ('=' * 64)

    # 1 - bootstrap uv
    $cmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($cmd) { $uv = $cmd.Source }
    else {
        $uv = Join-Path $Tools 'uv.exe'
        if (-not (Test-Path $uv)) {
            Say 'Downloading the uv bootstrapper (no admin rights needed)...'
            New-Item -ItemType Directory -Force -Path $Tools | Out-Null
            $zip = Join-Path $Tools 'uv.zip'
            $tmp = Join-Path $Tools 'uv-extract'
            Invoke-WebRequest -Uri "https://github.com/astral-sh/uv/releases/latest/download/uv-$triple.zip" -OutFile $zip -UseBasicParsing
            Expand-Archive -Path $zip -DestinationPath $tmp -Force
            $found = Get-ChildItem -Path $tmp -Recurse -Filter 'uv.exe' | Select-Object -First 1
            if (-not $found) { Fail 'uv.exe was not found in the downloaded archive.' }
            Copy-Item $found.FullName $uv -Force
            Remove-Item $tmp, $zip -Recurse -Force
        }
    }
    $env:UV_CACHE_DIR          = Join-Path $Build '.cache\uv'
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $Tools 'python'
    $env:UV_PYTHON_PREFERENCE  = 'only-managed'
    $env:UV_LINK_MODE          = 'copy'

    # 2 - private Python + venv
    if ($CleanEnv -and (Test-Path $Venv)) { Remove-Item $Venv -Recurse -Force }
    $py = Join-Path $Venv 'Scripts\python.exe'
    if (-not (Test-Path $py)) {
        Say 'Creating a private Python 3.12 environment (downloaded automatically)...'
        Run $uv @('venv', $Venv, '--python', '3.12')
    }

    # 3 - dependencies
    Say 'Installing dependencies (PySide6, PyInstaller)...'
    Run $uv @('pip', 'install', '--python', $py, '-r', (Join-Path $Build 'requirements.txt'), '-r', (Join-Path $Build 'requirements-build.txt'))

    # 4 - build
    Remove-Item $Work, $Dist -Recurse -Force -ErrorAction SilentlyContinue
    $env:HEART_ONEFILE = $(if ($OneFile) { '1' } else { '0' })
    Say 'Building the application (a few minutes)...'
    Run $py @('-m', 'PyInstaller', '--noconfirm', '--clean', '--distpath', $Dist, '--workpath', $Work, (Join-Path $Build '4R022-Heart.spec'))

    if ($OneFile) { $exe = Join-Path $Dist '4R022-Heart.exe' } else { $exe = Join-Path $Dist '4R022-Heart\4R022-Heart.exe' }
    if (-not (Test-Path $exe)) { Fail "Built executable not found: $exe" }

    # 5 - self-test
    if (-not $SkipTest) {
        Say 'Running the built-in self-test...'
        New-Item -ItemType Directory -Force -Path $Work | Out-Null
        $log = Join-Path $Work 'selftest.log'
        $old = $env:QT_QPA_PLATFORM
        $env:QT_QPA_PLATFORM = 'offscreen'
        $p = Start-Process -FilePath $exe -ArgumentList @('--selftest', '--log', ('"{0}"' -f $log)) -PassThru
        if (-not $p.WaitForExit(240000)) { $p.Kill(); Fail 'Self-test timed out.' }
        $env:QT_QPA_PLATFORM = $old
        if (Test-Path $log) { Get-Content $log | ForEach-Object { Write-Host "   $_" } }
        if ($p.ExitCode -ne 0) { Fail "Self-test failed (exit code $($p.ExitCode)). Use -SkipTest to package anyway." }
    }

    # 6 - package
    $base  = "4R022-Heart-v$ver-windows-$arch"
    $stage = Join-Path $Release $base
    Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $stage | Out-Null
    if ($OneFile) { Copy-Item $exe $stage; $appDir = $stage }
    else { $appDir = Join-Path $stage '4R022-Heart'; Copy-Item (Join-Path $Dist '4R022-Heart') $appDir -Recurse }
    Copy-Item (Join-Path $Root 'Assets\Config\4R022-Heart.settings.json') $appDir
    Copy-Item (Join-Path $Root 'LICENSE') $stage
    Copy-Item (Join-Path $Root 'README.md') $stage
    Copy-Item (Join-Path $Root 'Docs\NOTICE.md') $stage
    $zipOut = Join-Path $Release "$base.zip"
    Remove-Item $zipOut -Force -ErrorAction SilentlyContinue
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::CreateFromDirectory($stage, $zipOut, [IO.Compression.CompressionLevel]::Optimal, $true)
    Remove-Item $stage -Recurse -Force
    if (-not $KeepWork) { Remove-Item $Work, $Dist -Recurse -Force -ErrorAction SilentlyContinue }

    $mb = [math]::Round((Get-Item $zipOut).Length / 1MB, 1)
    Write-Host ''
    Say "DONE  ->  $zipOut  ($mb MB)"
    exit 0
}
catch {
    Fail $_.Exception.Message
}
