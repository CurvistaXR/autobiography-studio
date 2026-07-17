param(
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$skillRoot = (Resolve-Path (Join-Path $repoRoot "autobiography-studio")).Path
$distRoot = Join-Path $repoRoot "dist"
$zipPath = Join-Path $distRoot ("autobiography-studio-{0}.zip" -f $Version)
$checksumPath = "$zipPath.sha256"

if (-not $skillRoot.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Skill path resolved outside the repository."
}
if (-not (Test-Path -LiteralPath (Join-Path $skillRoot "SKILL.md") -PathType Leaf)) {
    throw "SKILL.md is missing from the Skill root."
}

New-Item -ItemType Directory -Force -Path $distRoot | Out-Null

foreach ($target in @($zipPath, $checksumPath)) {
    if (Test-Path -LiteralPath $target) {
        $resolved = (Resolve-Path -LiteralPath $target).Path
        if (-not $resolved.StartsWith($distRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove a build target outside dist: $resolved"
        }
        Remove-Item -LiteralPath $resolved -Force
    }
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$fixedTimestamp = [DateTimeOffset]::new(
    2020, 1, 1, 0, 0, 0, [TimeSpan]::Zero
)
$fileStream = [System.IO.File]::Open(
    $zipPath,
    [System.IO.FileMode]::CreateNew,
    [System.IO.FileAccess]::ReadWrite,
    [System.IO.FileShare]::None
)

try {
    $archive = [System.IO.Compression.ZipArchive]::new(
        $fileStream,
        [System.IO.Compression.ZipArchiveMode]::Create,
        $false,
        [System.Text.Encoding]::UTF8
    )
    try {
        $files = Get-ChildItem -LiteralPath $skillRoot -Recurse -File |
            Where-Object {
                $_.Name -notlike "*.pyc" -and
                $_.Name -notlike "*.tmp" -and
                $_.FullName -notmatch "[\\/]__pycache__[\\/]"
            } |
            Sort-Object FullName

        foreach ($file in $files) {
            $relative = $file.FullName.Substring($skillRoot.Length).TrimStart("\", "/")
            $entryName = $relative.Replace("\", "/")
            $entry = $archive.CreateEntry(
                $entryName,
                [System.IO.Compression.CompressionLevel]::Optimal
            )
            $entry.LastWriteTime = $fixedTimestamp

            $inputStream = [System.IO.File]::OpenRead($file.FullName)
            $entryStream = $entry.Open()
            try {
                $inputStream.CopyTo($entryStream)
            }
            finally {
                $entryStream.Dispose()
                $inputStream.Dispose()
            }
        }
    }
    finally {
        $archive.Dispose()
    }
}
finally {
    $fileStream.Dispose()
}

$zipInfo = Get-Item -LiteralPath $zipPath
$maxBytes = 10MB
if ($zipInfo.Length -gt $maxBytes) {
    Remove-Item -LiteralPath $zipPath -Force
    throw "Release ZIP exceeds SkillHub's 10MB limit."
}

$readArchive = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
try {
    $names = @($readArchive.Entries | ForEach-Object FullName)
    if ($names -notcontains "SKILL.md") {
        throw "Release ZIP does not contain root-level SKILL.md."
    }
    if ($names | Where-Object { $_ -like "autobiography-studio/*" }) {
        throw "Release ZIP contains an unwanted wrapper directory."
    }
}
finally {
    $readArchive.Dispose()
}

$hash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
$checksumLine = "$hash  $([System.IO.Path]::GetFileName($zipPath))`n"
[System.IO.File]::WriteAllText(
    $checksumPath,
    $checksumLine,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Output ("Created {0} ({1} bytes)" -f $zipPath, $zipInfo.Length)
Write-Output ("SHA256 {0}" -f $hash)
