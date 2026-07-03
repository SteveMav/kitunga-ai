#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

load_env
ensure_dirs
run_from_client_dir

PYTHON_BIN="$(python_bin)"
LOG_FILE="${KITUNGA_LOGS_DIR:-${CLIENT_DIR}/logs}/detector.log"
BASKET_CODE_FILE="${KITUNGA_BASKET_CODE_FILE:-${CLIENT_DIR}/state/basket_code.txt}"
mkdir -p "$(dirname "${LOG_FILE}")"

echo "[Kitunga AI] Starting detector. Logs: ${LOG_FILE}"
exec "${PYTHON_BIN}" main.py --basket-code-file "${BASKET_CODE_FILE}" "$@" 2>&1 | tee -a "${LOG_FILE}"
