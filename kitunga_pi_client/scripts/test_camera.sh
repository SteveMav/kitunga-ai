#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

load_env
ensure_dirs
run_from_client_dir

PYTHON_BIN="$(python_bin)"

echo "[Kitunga AI] Capturing one frame without sending to backend..."
exec "${PYTHON_BIN}" main.py --once --no-send "$@"
