#!/bin/zsh
cd "$(dirname "$0")"

if [ ! -d "vendor/readlif" ]; then
  echo "Local dependency folder is missing. Installing into ./vendor ..."
  python3 -m pip install --target vendor -r requirements_lif_to_tif.txt
fi

python3 lif_to_tif_app.py
