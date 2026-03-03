$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = Split-Path -Parent $PSScriptRoot
$zipName = "seven_control_tower_gemini_demo.zip"
$outPath = Join-Path $root $zipName

$excludeSegments = @(
  ".git",
  ".venv",
  "venv",
  "__pycache__",
  ".pytest_cache",
  ".mypy_cache",
  ".ruff_cache",
  ".nox",
  ".tox",
  "build",
  "dist",
  "evidence",
  "logs",
  ".idea",
  ".vscode"
)

$excludeLeafPatterns = @(
  "*.pyc",
  "*.pyo",
  "*.pyd",
  "*.log",
  "*.zip",
  ".env",
  "secrets.toml",
  "secrets.toml.offline-test"
)

function ShouldExclude([string]$relativePath) {
  $normalized = $relativePath -replace "\\", "/"
  $parts = $normalized.Split("/")
  foreach ($part in $parts) {
    if ($excludeSegments -contains $part) {
      return $true
    }
    foreach ($pattern in $excludeLeafPatterns) {
      if ($part -like $pattern) {
        return $true
      }
    }
  }
  return $false
}

if (Test-Path $outPath) {
  Remove-Item $outPath -Force
}

$files = Get-ChildItem -Path $root -Recurse -File | Where-Object {
  $relative = $_.FullName.Substring($root.Length + 1)
  -not (ShouldExclude $relative)
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::Open($outPath, 'Create')
foreach ($file in $files) {
  $entryName = $file.FullName.Substring($root.Length + 1).Replace("\", "/")
  [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $file.FullName, $entryName) | Out-Null
}
$zip.Dispose()

$sizeKb = [math]::Round((Get-Item $outPath).Length / 1KB, 1)
Write-Host "[package] Built $zipName ($sizeKb KB, $($files.Count) files)"
