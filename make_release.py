from pathlib import Path
import hashlib
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "QiangMa.exe"
STAGE = ROOT / "QiangMa_Portable"
ZIP = ROOT / "QiangMa_Portable.zip"

if not EXE.exists():
    raise SystemExit(f"missing {EXE}")
shutil.rmtree(STAGE, ignore_errors=True)
ZIP.unlink(missing_ok=True)
STAGE.mkdir()
shutil.copy2(EXE, STAGE / "QiangMa.exe")
(STAGE / "README.txt").write_text(
    "Valorant room-code OCR tool (portable Windows x64)\n\n"
    "1. Run QiangMa.exe\n"
    "2. Click Select Region and drag around the room code\n"
    "3. Click Recognize Now or enable Auto Recognize\n"
    "4. Click Copy Room Code\n\n"
    "Expected format: 3 uppercase letters + 3 digits, e.g. SDF345.\n"
    "No Python installation is required.\n",
    encoding="utf-8",
)
with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in STAGE.iterdir():
        archive.write(path, path.name)
print(f"exe={EXE} bytes={EXE.stat().st_size}")
print(f"zip={ZIP} bytes={ZIP.stat().st_size}")
print(f"sha256={hashlib.sha256(ZIP.read_bytes()).hexdigest()}")
