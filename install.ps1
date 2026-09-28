param([switch]$BuildExe)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $project
py -3 -m pip install -r requirements.txt
if ($BuildExe) {
  py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --collect-all rapidocr_onnxruntime --name QiangMa main.py
  Write-Host "EXE 已生成：$project\dist\QiangMa.exe"
}
