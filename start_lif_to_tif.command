#!/bin/zsh
APP_DIR="${0:A:h}"
cd "$APP_DIR" || exit 1

if command -v xattr >/dev/null 2>&1; then
  echo "Preparing app folder for macOS first launch ..."
  xattr -dr com.apple.quarantine "$APP_DIR" 2>/dev/null || true
fi

if [ ! -d "vendor/readlif" ]; then
  echo "Local dependency folder is missing. Installing into ./vendor ..."
  python3 -m pip install --target vendor -r requirements_lif_to_tif.txt
fi

python3 lif_to_tif_app.py
