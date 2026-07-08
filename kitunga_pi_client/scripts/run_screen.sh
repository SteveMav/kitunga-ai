#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

load_env
ensure_dirs
run_from_client_dir

PYTHON_BIN="$(python_bin)"
LOG_FILE="${KITUNGA_LOGS_DIR:-${CLIENT_DIR}/logs}/screen.log"
BASKET_CODE_FILE="${KITUNGA_BASKET_CODE_FILE:-${CLIENT_DIR}/state/basket_code.txt}"
mkdir -p "$(dirname "${LOG_FILE}")"

API_BASE_URL="${KITUNGA_API_BASE_URL:-http://127.0.0.1:8000}"
BASKET_CODE="${KITUNGA_BASKET_CODE:-SB-001}"
DEVICE_ID="${KITUNGA_DEVICE_ID:-KITUNGA-PI-001}"

echo "[Kitunga AI] Starting Tkinter screen. Logs: ${LOG_FILE}"
exec "${PYTHON_BIN}" tkinter_screen.py \
  --api-base-url "${API_BASE_URL}" \
  --basket-code "${BASKET_CODE}" \
  --basket-code-file "${BASKET_CODE_FILE}" \
  --device-id "${DEVICE_ID}" \
  --fullscreen \
  "$@" 2>&1 | tee -a "${LOG_FILE}"
