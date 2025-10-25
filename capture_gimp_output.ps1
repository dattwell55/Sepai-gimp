# PowerShell script to capture GIMP debug output to file
$gimpExe = "C:\Users\atwel\AppData\Local\Programs\GIMP 3\bin\gimp-3.0.exe"
$outputFile = "C:\Users\atwel\OneDrive\Documents\-SepAI-gimp-main\gimp_debug_output.txt"

Write-Host "Launching GIMP with debug output..." -ForegroundColor Cyan
Write-Host "Output will be saved to: $outputFile" -ForegroundColor Yellow
Write-Host ""
Write-Host "GIMP is starting... Please wait for it to fully load," -ForegroundColor Green
Write-Host "then CLOSE GIMP to complete the capture." -ForegroundColor Green
Write-Host ""

# Run GIMP and capture all output
& $gimpExe --verbose --console-messages 2>&1 | Tee-Object -FilePath $outputFile

Write-Host ""
Write-Host "GIMP closed. Output saved to:" -ForegroundColor Green
Write-Host "  $outputFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "Searching for AI Separation plugin messages..." -ForegroundColor Yellow

# Search for relevant lines
$aiLines = Select-String -Path $outputFile -Pattern "ai-separation|AI Separation" -Context 2,2
$errorLines = Select-String -Path $outputFile -Pattern "error|Error|ERROR|warning|Warning|WARNING" -Context 1,1 | Select-Object -First 20

if ($aiLines) {
    Write-Host ""
    Write-Host "=== AI SEPARATION PLUGIN MESSAGES ===" -ForegroundColor Cyan
    $aiLines | ForEach-Object { Write-Host $_.Line }
} else {
    Write-Host "No AI Separation messages found!" -ForegroundColor Red
}

if ($errorLines) {
    Write-Host ""
    Write-Host "=== ERRORS/WARNINGS (first 20) ===" -ForegroundColor Yellow
    $errorLines | ForEach-Object { Write-Host $_.Line }
}

Write-Host ""
Write-Host "Full output saved to: $outputFile" -ForegroundColor Green
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
