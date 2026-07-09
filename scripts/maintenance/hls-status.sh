#!/usr/bin/env bash

# ============================================================
# EJTV Broadcast Platform
# MISSION-014 — HLS Status Check
# Servicio: MediaMTX / HTTP Live Streaming
# ============================================================

set -u

HLS_URL="${1:-http://127.0.0.1:8888/live/hls-test/index.m3u8}"
SERVICE_NAME="mediamtx"
HLS_PORT="8888"

echo "============================================================"
echo " EJTV Broadcast Platform — HLS Status Check"
echo "============================================================"
echo "Fecha:        $(date)"
echo "Servicio:     ${SERVICE_NAME}"
echo "URL HLS:      ${HLS_URL}"
echo "Puerto HLS:   ${HLS_PORT}/tcp"
echo "------------------------------------------------------------"

echo "[1] Estado del servicio MediaMTX"
if systemctl is-active --quiet "${SERVICE_NAME}"; then
    echo "OK  - MediaMTX está activo"
else
    echo "FAIL - MediaMTX no está activo"
    exit 1
fi

echo
echo "[2] Verificación del puerto HLS"
if ss -lntup | grep -q ":${HLS_PORT}"; then
    echo "OK  - El puerto ${HLS_PORT}/tcp está escuchando"
else
    echo "FAIL - El puerto ${HLS_PORT}/tcp no está escuchando"
    exit 1
fi

echo
echo "[3] Verificación HTTP del master playlist"
HTTP_CODE=$(curl -L -s -o /tmp/ejtv-hls-index.m3u8 -w "%{http_code}" "${HLS_URL}" || true)

if [ "${HTTP_CODE}" = "200" ]; then
    echo "OK  - El servidor HLS respondió HTTP 200"
else
    echo "FAIL - El servidor HLS respondió HTTP ${HTTP_CODE}"
    exit 1
fi

echo
echo "[4] Verificación de contenido HLS"
if grep -q "#EXTM3U" /tmp/ejtv-hls-index.m3u8; then
    echo "OK  - Playlist HLS válida detectada (#EXTM3U)"
else
    echo "FAIL - No se detectó una playlist HLS válida"
    cat /tmp/ejtv-hls-index.m3u8
    exit 1
fi

if grep -q "#EXT-X-STREAM-INF" /tmp/ejtv-hls-index.m3u8; then
    echo "OK  - Master playlist contiene referencia de flujo multimedia"
else
    echo "WARN - No se detectó #EXT-X-STREAM-INF"
fi

echo
echo "[5] Resumen"
echo "OK  - HLS operativo para la URL:"
echo "      ${HLS_URL}"
echo "============================================================"

exit 0
