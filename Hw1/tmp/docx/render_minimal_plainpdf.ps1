$ErrorActionPreference = 'Stop'
$workspacePath = 'C:\Users\chinh\Desktop\Machine Learning'
$docxPath = Join-Path $workspacePath 'HW1_final_report_minimal_113062273.docx'
$qaPdfPath = Join-Path $workspacePath 'tmp\docx\minimal_preview\word-render.pdf'
$wordInstance = $null
$ourDocument = $null
$ownsInstance = $false
try {
    $wordInstance = New-Object -ComObject Word.Application
    $ownsInstance = ($wordInstance.Documents.Count -eq 0)
    if ($ownsInstance) {
        $wordInstance.Visible = $false
        $wordInstance.DisplayAlerts = 0
    }
    $ourDocument = $wordInstance.Documents.Open($docxPath, $false, $true, $false)
    $ourDocument.Repaginate()
    $ourDocument.Fields.Update() | Out-Null
    Write-Output ('Rendered page count: ' + $ourDocument.ComputeStatistics(2))
    $ourDocument.ExportAsFixedFormat($qaPdfPath, 17, $false, 1, 0, 1, 1, 0, $false, $false, 0, $false, $true, $false)
    $ourDocument.Close(0)
    $ourDocument = $null
} finally {
    if ($null -ne $ourDocument) { $ourDocument.Close(0) }
    if ($null -ne $wordInstance) {
        if ($ownsInstance -and $wordInstance.Documents.Count -eq 0) { $wordInstance.Quit() }
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($wordInstance) | Out-Null
    }
}
