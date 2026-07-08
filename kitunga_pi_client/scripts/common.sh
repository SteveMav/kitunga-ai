#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${CLIENT_DIR}/.venv"
ENV_FILE="${CLIENT_DIR}/.env"

load_env() {
  if [[ -f "${ENV_FILE}" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "${ENV_FILE}"
    set +a
  fi
}

ensure_dirs() {
  mkdir -p "${CLIENT_DIR}/captures" "${CLIENT_DIR}/logs" "${CLIENT_DIR}/models" "${CLIENT_DIR}/state"
}

python_bin() {
  if [[ -x "${VENV_DIR}/bin/python" ]]; then
    echo "${VENV_DIR}/bin/python"
  else
    echo "python3"
  fi
}

run_from_client_dir() {
  cd "${CLIENT_DIR}"
}
