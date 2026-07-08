#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

load_env

API_BASE_URL="${KITUNGA_API_BASE_URL:-http://127.0.0.1:8000}"
BASKET_CODE="${KITUNGA_BASKET_CODE:-SB-001}"

echo "[Kitunga AI] Testing backend: ${API_BASE_URL}"
curl -fsS "${API_BASE_URL}/api/baskets/${BASKET_CODE}/" | python3 -m json.tool
