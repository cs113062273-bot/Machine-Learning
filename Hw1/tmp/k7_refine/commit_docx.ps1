$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName Microsoft.VisualBasic
$reportTaskPath = 'C:\Users\chinh\Desktop\Machine Learning\HW1_final_report_reviewed_113062273.docx'
$reportTaskCandidate = 'C:\Users\chinh\Desktop\Machine Learning\tmp\k7_refine\HW1_final_report_reviewed_113062273.docx'
$reportTaskAudit = Get-Content -LiteralPath 'C:\Users\chinh\Desktop\Machine Learning\tmp\k7_refine\docx_scope_audit.json' -Raw | ConvertFrom-Json
$reportTaskDoc = [Microsoft.VisualBasic.Interaction]::GetObject($reportTaskPath)
if (-not $reportTaskDoc.Saved) { throw 'The document has unsaved changes; preserve them before applying the patch.' }
function Get-ReportSharedHash([string]$reportHashPath) {
    $reportHashStream = [System.IO.File]::Open($reportHashPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    $reportHashAlgorithm = [System.Security.Cryptography.SHA256]::Create()
    try { return ([System.BitConverter]::ToString($reportHashAlgorithm.ComputeHash($reportHashStream))).Replace('-', '').ToLowerInvariant() }
    finally { $reportHashStream.Dispose(); $reportHashAlgorithm.Dispose() }
}
$reportTaskHash = Get-ReportSharedHash $reportTaskPath
if ($reportTaskHash -ne $reportTaskAudit.original_sha256) { throw 'The source document changed after the scope audit.' }
$reportTaskApp = $reportTaskDoc.Application
$reportTaskDoc.Close(0)
try {
    Copy-Item -LiteralPath $reportTaskCandidate -Destination $reportTaskPath -Force
    $reportTaskFinalHash = (Get-FileHash -LiteralPath $reportTaskPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($reportTaskFinalHash -ne $reportTaskAudit.candidate_sha256) { throw 'Final file does not match the reviewed candidate.' }
} finally {
    $reportTaskReopened = $reportTaskApp.Documents.Open($reportTaskPath)
    $reportTaskReopened.Activate()
}
Write-Output 'Replaced the original DOCX and reopened it in the same Word application.'
Write-Output "Final SHA256: $reportTaskFinalHash"
