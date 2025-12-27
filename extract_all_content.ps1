# Extract ALL content from origin/main that's not in local main
$files = git diff b8d582c..origin/main --name-only

foreach ($file in $files) {
    $safeName = $file -replace '[\\/:*?"<>|]', '_'
    $outputPath = "forensic_analysis/extracted_$safeName"
    
    # Create directory if needed
    $dir = Split-Path $outputPath -Parent
    if ($dir) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    
    # Get full content from origin/main
    git show "origin/main:$file" > $outputPath 2>&1
    
    Write-Output "Extracted: $file -> $outputPath"
}

Write-Output "`n=== EXTRACTION COMPLETE ==="
Write-Output "Total files: $($files.Count)"
