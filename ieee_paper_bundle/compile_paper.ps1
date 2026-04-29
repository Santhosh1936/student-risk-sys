param(
    [string]$MainFile = "sars_paper.tex"
)

$ErrorActionPreference = "Stop"
$bundleRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $bundleRoot

if (-not (Test-Path $MainFile)) {
    Write-Error "Main LaTeX file '$MainFile' was not found in $bundleRoot."
}

if (Get-Command latexmk -ErrorAction SilentlyContinue) {
    latexmk -pdf -interaction=nonstopmode -halt-on-error $MainFile
    exit $LASTEXITCODE
}

if (Get-Command pdflatex -ErrorAction SilentlyContinue) {
    pdflatex -interaction=nonstopmode -halt-on-error $MainFile
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    pdflatex -interaction=nonstopmode -halt-on-error $MainFile
    exit $LASTEXITCODE
}

Write-Host "No LaTeX compiler was found." -ForegroundColor Yellow
Write-Host "Install TeX Live or MiKTeX, then rerun .\\compile_paper.ps1 from this folder." -ForegroundColor Yellow
exit 1
