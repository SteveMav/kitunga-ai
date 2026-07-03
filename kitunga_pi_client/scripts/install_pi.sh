#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

run_from_client_dir
ensure_dirs

echo "[Kitunga AI] Installing Raspberry Pi system packages..."
sudo apt-get update
sudo apt-get install -y \
  curl \
  git \
  python3 \
  python3-venv \
  python3-pip \
  python3-tk \
  libgl1 \
  libglib2.0-0

echo "[Kitunga AI] Creating Python virtual environment..."
python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip wheel setuptools
"${VENV_DIR}/bin/python" -m pip install -r requirements.txt

if [[ ! -f "${ENV_FILE}" ]]; then
  cp .env.example .env
  echo "[Kitunga AI] Created .env from .env.example. Edit KITUNGA_API_BASE_URL before running."
fi

if [[ ! -f "models/best.pt" ]]; then
  echo "[Kitunga AI] WARNING: models/best.pt is missing. Copy your YOLO model there before detection."
fi

echo "[Kitunga AI] Install complete."
