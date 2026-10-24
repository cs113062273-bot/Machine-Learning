$ErrorActionPreference='Stop'
$docxPath='C:\Users\chinh\Desktop\Machine Learning\HW1_final_report_simple_113062273.docx'
$qaPdfPath='C:\Users\chinh\Desktop\Machine Learning\tmp\docx\simple-word-render.pdf'
$wordInstance=$null
$ourDocument=$null
$ownsInstance=$false
try {
    $wordInstance=New-Object -ComObject Word.Application
    $ownsInstance=($wordInstance.Documents.Count -eq 0)
    if ($ownsInstance) {
        $wordInstance.Visible=$false
        $wordInstance.DisplayAlerts=0
    }
    $ourDocument=$wordInstance.Documents.Open($docxPath,$false,$true,$false)
    $ourDocument.Repaginate()
    Write-Output ('Rendered page count: '+$ourDocument.ComputeStatistics(2))
    $ourDocument.ExportAsFixedFormat($qaPdfPath,17)
    $ourDocument.Close(0)
    $ourDocument=$null
} finally {
    if ($null -ne $ourDocument) { $ourDocument.Close(0) }
    if ($null -ne $wordInstance) {
        if ($ownsInstance -and $wordInstance.Documents.Count -eq 0) { $wordInstance.Quit() }
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($wordInstance) | Out-Null
    }
}
