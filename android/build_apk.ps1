<#
.SYNOPSIS
    Build the Amphoreus phone app into android/dist/Amphoreus.apk.

.DESCRIPTION
    No Gradle, no Android Studio — just the pieces the build actually needs:

      aapt2      compiles resources and links the manifest into an APK skeleton
      javac      compiles the one Activity against the platform's android.jar
      d8         turns those classes into classes.dex
      zipalign   aligns the archive so the platform can map it
      apksigner  signs it with a local key

    The SDK parts are downloaded once into android/.sdk (gitignored) from
    dl.google.com and mirror hosts; the sources are the three files next to this
    script. A clean machine with a JDK 17+ needs nothing else.

.PARAMETER Clean
    Throw away build/ before building (not the SDK download).

.PARAMETER SkipSdk
    Fail instead of downloading if the SDK is incomplete.

.EXAMPLE
    pwsh -File android/build_apk.ps1
    pwsh -File android/build_apk.ps1 -Clean
#>
[CmdletBinding()]
param(
    [switch]$Clean,
    [switch]$SkipSdk
)

$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$sdk = Join-Path $here '.sdk'
$raw = Join-Path $sdk '_raw'
$zips = Join-Path $sdk '_zips'
$build = Join-Path $here 'build'
$dist = Join-Path $here 'dist'
$keys = Join-Path $here '.keys'

$packages = @(
    @{ name = 'platform-tools'; key = 'platform-tools';
       url = 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' },
    # build-tools 36.1 ships R8/D8 9.x. The 34.x D8 (R8 8.2) cannot read a class
    # file from a JDK 24 javac — it NPEs on any anonymous inner class, which every
    # WebViewClient subclass needs. Pin the newer one rather than pinning an old JDK.
    @{ name = 'build-tools'; key = 'build-tools';
       url = 'https://dl.google.com/android/repository/build-tools_r36.1_windows.zip' },
    @{ name = 'platform'; key = 'platform';
       url = 'https://dl.google.com/android/repository/platform-34-ext7_r01.zip' }
)

function Write-Step($text) { Write-Host "`n== $text" -ForegroundColor Cyan }
function Write-Ok($text)   { Write-Host "   $text" -ForegroundColor DarkGray }

# ----------------------------------------------------------------- JDK

$javaHome = $env:JAVA_HOME
if (-not $javaHome -or -not (Test-Path (Join-Path $javaHome 'bin\javac.exe'))) {
    $javac = Get-Command javac -ErrorAction SilentlyContinue
    if (-not $javac) { throw 'No JDK found. Install JDK 17+ and set JAVA_HOME.' }
    $javaHome = Split-Path (Split-Path $javac.Source -Parent) -Parent
}
$javacExe = Join-Path $javaHome 'bin\javac.exe'
$jarExe = Join-Path $javaHome 'bin\jar.exe'
$keytool = Join-Path $javaHome 'bin\keytool.exe'
Write-Step "JDK $(& $javacExe -version 2>&1)"
$env:JAVA_HOME = $javaHome

# ----------------------------------------------------------------- SDK

Write-Step 'Android SDK pieces'
New-Item -ItemType Directory -Force -Path $raw, $zips, $build, $dist | Out-Null
if ($Clean -and (Test-Path $build)) { Remove-Item $build -Recurse -Force; New-Item -ItemType Directory $build | Out-Null }

foreach ($p in $packages) {
    $extracted = Join-Path $raw $p.key
    if (Test-Path $extracted) { Write-Ok "$($p.name): present"; continue }
    $zip = Join-Path $zips "$($p.name).zip"
    if (-not (Test-Path $zip)) {
        if ($SkipSdk) { throw "missing $($p.name) and -SkipSdk was given" }
        Write-Ok "downloading $($p.name)…"
        & curl.exe -L --fail --retry 3 --retry-delay 2 --max-time 1800 --silent --show-error -o $zip $p.url
        if ($LASTEXITCODE -ne 0) { throw "download failed: $($p.url)" }
    }
    Expand-Archive -LiteralPath $zip -DestinationPath $extracted -Force
    Write-Ok "$($p.name): unpacked"
}

function Find-In($root, $pattern, $what) {
    $hit = Get-ChildItem -Path $root -Recurse -Filter $pattern -File -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $hit) { throw "could not find $what ($pattern) under $root" }
    return $hit
}

$aapt2     = Find-In (Join-Path $raw 'build-tools') 'aapt2.exe'     'aapt2'
$zipalign  = Find-In (Join-Path $raw 'build-tools') 'zipalign.exe'  'zipalign'
$d8        = Find-In (Join-Path $raw 'build-tools') 'd8.bat'        'd8'
$apksigner = Find-In (Join-Path $raw 'build-tools') 'apksigner.bat' 'apksigner'
$androidJar = Find-In (Join-Path $raw 'platform') 'android.jar'     'android.jar'
Write-Ok "aapt2    $($aapt2.FullName)"
Write-Ok "d8       $($d8.FullName)"
Write-Ok "android  $($androidJar.FullName)"

# ----------------------------------------------------------------- build

Write-Step 'Compile resources'
& $aapt2.FullName compile --dir (Join-Path $here 'app\res') -o (Join-Path $build 'res.zip')
if ($LASTEXITCODE -ne 0) { throw 'aapt2 compile failed' }

Write-Step 'Link manifest into an APK skeleton'
& $aapt2.FullName link `
    -o (Join-Path $build 'base.apk') `
    -I $androidJar.FullName `
    --manifest (Join-Path $here 'app\AndroidManifest.xml') `
    -R (Join-Path $build 'res.zip') `
    --java (Join-Path $build 'gen') `
    --auto-add-overlay
if ($LASTEXITCODE -ne 0) { throw 'aapt2 link failed' }

Write-Step 'Compile the Activity'
$classes = Join-Path $build 'classes'
New-Item -ItemType Directory -Force -Path $classes | Out-Null
$sources = @(Get-ChildItem -Path (Join-Path $here 'app\src') -Recurse -Filter *.java | ForEach-Object { $_.FullName })
$sources += @(Get-ChildItem -Path (Join-Path $build 'gen') -Recurse -Filter *.java | ForEach-Object { $_.FullName })
& $javacExe -encoding UTF-8 -source 17 -target 17 -Xlint:-options `
    -classpath $androidJar.FullName -d $classes @sources
if ($LASTEXITCODE -ne 0) { throw 'javac failed' }

Write-Step 'Dex it'
& $jarExe cf (Join-Path $build 'classes.jar') -C $classes .
$dexOut = Join-Path $build 'dex'
New-Item -ItemType Directory -Force -Path $dexOut | Out-Null
& $d8.FullName --lib $androidJar.FullName --min-api 24 --output $dexOut (Join-Path $build 'classes.jar')
if ($LASTEXITCODE -ne 0) { throw 'd8 failed' }
Write-Ok ((Get-Item (Join-Path $dexOut 'classes.dex')).Length.ToString() + ' bytes of dex')

Write-Step 'Package'
$apk = Join-Path $build 'unsigned.apk'
Copy-Item (Join-Path $build 'base.apk') $apk -Force
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zipFile = [System.IO.Compression.ZipFile]::Open($apk, 'Update')
try {
    $entry = $zipFile.CreateEntry('classes.dex', [System.IO.Compression.CompressionLevel]::Optimal)
    $stream = $entry.Open()
    try {
        $bytes = [System.IO.File]::ReadAllBytes((Join-Path $dexOut 'classes.dex'))
        $stream.Write($bytes, 0, $bytes.Length)
    } finally { $stream.Dispose() }
} finally { $zipFile.Dispose() }

Write-Step 'Align'
$aligned = Join-Path $build 'aligned.apk'
& $zipalign.FullName -f -p 4 $apk $aligned
if ($LASTEXITCODE -ne 0) { throw 'zipalign failed' }

Write-Step 'Sign'
New-Item -ItemType Directory -Force -Path $keys | Out-Null
$ks = Join-Path $keys 'amphoreus.keystore'
if (-not (Test-Path $ks)) {
    Write-Ok 'creating a local signing key (android/.keys/amphoreus.keystore)'
    & $keytool -genkeypair -v -keystore $ks -alias amphoreus -keyalg RSA -keysize 2048 `
        -validity 10000 -storepass amphoreus -keypass amphoreus `
        -dname 'CN=Project Amphoreus, OU=Sanctuary, O=Amphoreus, L=Okhema, C=AM' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'keytool failed' }
}
$outApk = Join-Path $dist 'Amphoreus.apk'
& $apksigner.FullName sign --ks $ks --ks-pass pass:amphoreus --key-pass pass:amphoreus `
    --out $outApk $aligned
if ($LASTEXITCODE -ne 0) { throw 'apksigner failed' }

Write-Step 'Verify'
& $apksigner.FullName verify --verbose $outApk | Select-Object -First 6 | ForEach-Object { Write-Ok $_ }

$size = [math]::Round((Get-Item $outApk).Length / 1KB, 1)
Write-Host "`nBuilt $outApk  ($size KB)" -ForegroundColor Green
Write-Host 'Install:  adb install -r android\dist\Amphoreus.apk' -ForegroundColor DarkGray
Write-Host 'Or copy dist\Amphoreus.apk to the phone and open it (allow unknown sources).' -ForegroundColor DarkGray
