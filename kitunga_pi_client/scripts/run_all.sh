#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

load_env
ensure_dirs
run_from_client_dir

PYTHON_BIN="$(python_bin)"
LOG_DIR="${KITUNGA_LOGS_DIR:-${CLIENT_DIR}/logs}"
BASKET_CODE_FILE="${KITUNGA_BASKET_CODE_FILE:-${CLIENT_DIR}/state/basket_code.txt}"
mkdir -p "${LOG_DIR}"

API_BASE_URL="${KITUNGA_API_BASE_URL:-http://127.0.0.1:8000}"
BASKET_CODE="${KITUNGA_BASKET_CODE:-SB-001}"
DEVICE_ID="${KITUNGA_DEVICE_ID:-KITUNGA-PI-001}"

cleanup() {
  echo "[Kitunga AI] Stopping..."
  [[ -n "${DETECTOR_PID:-}" ]] && kill "${DETECTOR_PID}" 2>/dev/null || true
  [[ -n "${SCREEN_PID:-}" ]] && kill "${SCREEN_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[Kitunga AI] Starting detector and screen."
echo "[Kitunga AI] Backend: ${API_BASE_URL} | Basket: ${BASKET_CODE} | Device: ${DEVICE_ID}"
echo "${BASKET_CODE}" > "${BASKET_CODE_FILE}"

"${PYTHON_BIN}" main.py --basket-code-file "${BASKET_CODE_FILE}" >"${LOG_DIR}/detector.log" 2>&1 &
DETECTOR_PID=$!

"${PYTHON_BIN}" tkinter_screen.py \
  --api-base-url "${API_BASE_URL}" \
  --basket-code "${BASKET_CODE}" \
  --basket-code-file "${BASKET_CODE_FILE}" \
  --device-id "${DEVICE_ID}" \
  --fullscreen >"${LOG_DIR}/screen.log" 2>&1 &
SCREEN_PID=$!

wait -n "${DETECTOR_PID}" "${SCREEN_PID}"
