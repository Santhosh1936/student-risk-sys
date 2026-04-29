# IEEE Paper Bundle

This folder contains a self-contained package for the IEEE paper.

## Files

- `sars_paper.tex`: main IEEE paper source
- `assets/`: only the figures used by the paper
- `compile_paper.ps1`: simple Windows compile helper

## How to compile

Open PowerShell in this folder and run:

```powershell
.\compile_paper.ps1
```

If `latexmk` is installed, the script uses it automatically.
If not, it falls back to `pdflatex` and runs it twice.

## Requirements

- A LaTeX distribution such as MiKTeX or TeX Live
- The `IEEEtran` class available in that distribution

## Output

The generated PDF will appear in this folder as `sars_paper.pdf`.
