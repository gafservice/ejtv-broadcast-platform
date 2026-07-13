#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
TEMP_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "${TEMP_DIR}"
}

trap cleanup EXIT

check_endpoint() {
    local path="$1"
    local output_file="${TEMP_DIR}/response.json"
    local status_code

    status_code="$(
        curl \
            --silent \
            --show-error \
            --output "${output_file}" \
            --write-out "%{http_code}" \
            "${BASE_URL}${path}"
    )"

    if [[ "${status_code}" != "200" ]]; then
        echo "ERROR: ${path} respondió HTTP ${status_code}"
        cat "${output_file}"
        exit 1
    fi

    echo "OK: ${path} respondió HTTP 200"
}

check_endpoint "/"
check_endpoint "/api/v1/health"
check_endpoint "/api/v1/system/info"
check_endpoint "/openapi.json"
check_endpoint "/docs"

system_payload="$(
    curl --silent --show-error \
        "${BASE_URL}/api/v1/system/info"
)"

echo "${system_payload}" |
    jq -e '
        .success == true and
        (.data.hostname | length > 0) and
        (.data.operating_system | length > 0) and
        (.data.kernel | length > 0) and
        (.request_id | length > 0)
    ' >/dev/null

echo "OK: la información real del sistema es válida."
echo "Sprint 2 — prueba de humo completada correctamente."
