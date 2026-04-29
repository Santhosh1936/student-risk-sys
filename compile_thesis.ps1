$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$pdflatex = Get-Command pdflatex -ErrorAction SilentlyContinue
if (-not $pdflatex) {
    Write-Host "pdflatex was not found in PATH." -ForegroundColor Yellow
    Write-Host "Install a LaTeX distribution such as MiKTeX or TeX Live, then run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Compiling sars_thesis_report.tex..." -ForegroundColor Cyan
& $pdflatex.Source -interaction=nonstopmode -halt-on-error sars_thesis_report.tex
& $pdflatex.Source -interaction=nonstopmode -halt-on-error sars_thesis_report.tex

Write-Host "Compilation finished. Output file: sars_thesis_report.pdf" -ForegroundColor Green
