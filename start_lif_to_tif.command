#!/bin/zsh
APP_DIR="${0:A:h}"
cd "$APP_DIR" || exit 1

if command -v xattr >/dev/null 2>&1; then
  echo "Preparing app folder for macOS first launch ..."
  xattr -dr com.apple.quarantine "$APP_DIR" 2>/dev/null || true
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. Please install Python 3 and run this launcher again."
  read "?Press Return to close..."
  exit 1
fi

NEEDS_INSTALL=0
python3 - <<'PY' || NEEDS_INSTALL=1
import sys
sys.path.insert(0, "vendor")
required_modules = ("readlif", "numpy", "PIL", "bs4", "soupsieve", "imageio", "imageio_ffmpeg")
missing = []
for module_name in required_modules:
    try:
        __import__(module_name)
    except Exception:
        missing.append(module_name)
if missing:
    print("Missing local Python dependencies:", ", ".join(missing))
    raise SystemExit(1)
PY

if [ "$NEEDS_INSTALL" -ne 0 ]; then
  echo "Installing or updating local dependencies into ./vendor ..."
  python3 -m pip install --upgrade --target vendor -r requirements_lif_to_tif.txt || {
    echo "Dependency installation failed. Please check your internet connection and Python installation."
    read "?Press Return to close..."
    exit 1
  }
fi

python3 lif_to_tif_app.py
