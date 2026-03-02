# PowerShell: create a clean distributable ZIP of the demo
# Usage: .\scripts\package_zip.ps1
# Output: seven_control_tower_gemini_demo.zip (in workspace root)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = Split-Path -Parent $PSScriptRoot
$zipName = "seven_control_tower_gemini_demo.zip"
$outPath = Join-Path $root $zipName

Write-Host "[package] Building $zipName from $root"

# Remove old zip if present
if (Test-Path $outPath) { Remove-Item $outPath -Force }

# Exclusion patterns
$excludeDirs = @(".venv", "__pycache__", ".git", "evidence", ".idea", ".vscode")
$excludeFiles = @("*.pyc", "*.log", ".env", "secrets.toml", $zipName)

function ShouldExclude($path) {
    $name = Split-Path -Leaf $path
    foreach ($d in $excludeDirs) {
        if ($name -eq $d) { return $true }
    }
    foreach ($p in $excludeFiles) {
        if ($name -like $p) { return $true }
    }
    return $false
}

# Collect files
$files = Get-ChildItem -Recurse -File -Path $root | Where-Object {
    $item = $_
    $rel = $item.FullName.Substring($root.Length + 1)
    $parts = $rel -split [regex]::Escape([IO.Path]::DirectorySeparatorChar)
    $exclude = $false
    foreach ($part in $parts) {
        if (ShouldExclude $part) { $exclude = $true; break }
    }
    -not $exclude
}

# Create zip
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open($outPath, 'Create')
foreach ($file in $files) {
    $entryName = $file.FullName.Substring($root.Length + 1).Replace('\', '/')
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $file.FullName, $entryName) | Out-Null
}
$zip.Dispose()

$size = [math]::Round((Get-Item $outPath).Length / 1KB, 1)
Write-Host "[package] Done: $outPath ($size KB, $($files.Count) files)"
