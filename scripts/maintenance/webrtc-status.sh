#!/usr/bin/env bash

# ============================================================
# EJTV Broadcast Platform
# MISSION-015 — WebRTC Status
# ============================================================

set -u

SERVICE_NAME="mediamtx"
CONFIG_FILE="/opt/ejtv/mediamtx/config/mediamtx.yml"
MEDIAMTX_BIN="/opt/ejtv/mediamtx/bin/mediamtx"

WEBRTC_HTTP_PORT="8889"
WEBRTC_ICE_PORT="8189"
WEBRTC_TEST_PATH="live/webrtc-test"

OK=0
WARN=0
FAIL=0

print_header() {
    echo "============================================================"
    echo " EJTV Broadcast Platform — WebRTC Status"
    echo " MISSION-015"
    echo "============================================================"
    echo "Fecha: $(date)"
    echo
}

check_pass() {
    echo "PASS  - $1"
    OK=$((OK + 1))
}

check_warn() {
    echo "WARN  - $1"
    WARN=$((WARN + 1))
}

check_fail() {
    echo "FAIL  - $1"
    FAIL=$((FAIL + 1))
}

section() {
    echo
    echo "------------------------------------------------------------"
    echo "$1"
    echo "------------------------------------------------------------"
}

print_header

# ============================================================
# Servicio
# ============================================================

section "1. Servicio MediaMTX"

if systemctl is-active --quiet "$SERVICE_NAME"; then
    check_pass "MediaMTX está activo"
else
    check_fail "MediaMTX no está activo"
fi

if systemctl is-enabled --quiet "$SERVICE_NAME"; then
    check_pass "MediaMTX está habilitado al arranque"
else
    check_warn "MediaMTX no está habilitado al arranque"
fi

echo
systemctl status "$SERVICE_NAME" --no-pager -l | sed -n '1,12p'

# ============================================================
# Versión
# ============================================================

section "2. Versión MediaMTX"

if [ -x "$MEDIAMTX_BIN" ]; then
    VERSION="$($MEDIAMTX_BIN --version 2>/dev/null || true)"
    echo "Versión detectada: $VERSION"

    if echo "$VERSION" | grep -q "v1.19.2"; then
        check_pass "Versión validada para WebRTC: v1.19.2"
    else
        check_warn "La versión no coincide con la línea base M015 esperada: v1.19.2"
    fi
else
    check_fail "No se encontró el binario $MEDIAMTX_BIN"
fi

# ============================================================
# Configuración
# ============================================================

section "3. Configuración WebRTC"

if [ -f "$CONFIG_FILE" ]; then
    check_pass "Archivo de configuración encontrado: $CONFIG_FILE"
    echo
    grep -nE "webrtc:|webrtcAddress|webrtcEncryption|webrtcAllowOrigins|webrtcLocalUDPAddress|webrtcAdditionalHosts|webrtcIPsFromInterfaces" "$CONFIG_FILE" || true

    if grep -q "^webrtc: true" "$CONFIG_FILE"; then
        check_pass "WebRTC habilitado"
    else
        check_fail "WebRTC no aparece habilitado"
    fi

    if grep -q "webrtcAddress: :$WEBRTC_HTTP_PORT" "$CONFIG_FILE"; then
        check_pass "Puerto HTTP WebRTC configurado en :$WEBRTC_HTTP_PORT"
    else
        check_warn "No se encontró webrtcAddress esperado en :$WEBRTC_HTTP_PORT"
    fi

    if grep -q "webrtcLocalUDPAddress: :$WEBRTC_ICE_PORT" "$CONFIG_FILE"; then
        check_pass "Puerto ICE UDP configurado en :$WEBRTC_ICE_PORT"
    else
        check_warn "No se encontró webrtcLocalUDPAddress esperado en :$WEBRTC_ICE_PORT"
    fi

    if grep -A2 "webrtcAdditionalHosts" "$CONFIG_FILE" | grep -qE "192\.168\."; then
        check_pass "webrtcAdditionalHosts contiene una IP LAN"
    else
        check_warn "webrtcAdditionalHosts no contiene una IP LAN explícita"
    fi
else
    check_fail "No se encontró el archivo de configuración $CONFIG_FILE"
fi

# ============================================================
# Puertos
# ============================================================

section "4. Listeners WebRTC"

if ss -lntup 2>/dev/null | grep -q ":$WEBRTC_HTTP_PORT"; then
    check_pass "Listener TCP WebRTC activo en :$WEBRTC_HTTP_PORT"
else
    check_fail "No se detecta listener TCP en :$WEBRTC_HTTP_PORT"
fi

if ss -lunp 2>/dev/null | grep -q ":$WEBRTC_ICE_PORT"; then
    check_pass "Listener UDP ICE activo en :$WEBRTC_ICE_PORT"
else
    check_fail "No se detecta listener UDP en :$WEBRTC_ICE_PORT"
fi

echo
ss -lntup 2>/dev/null | grep -E "$WEBRTC_HTTP_PORT|$WEBRTC_ICE_PORT|8554|1935|8890|8888" || true

# ============================================================
# Firewall
# ============================================================

section "5. Firewall UFW"

if command -v ufw >/dev/null 2>&1; then
    sudo ufw status numbered | grep -E "$WEBRTC_HTTP_PORT|$WEBRTC_ICE_PORT" || true

    if sudo ufw status | grep -q "$WEBRTC_HTTP_PORT/tcp"; then
        check_pass "UFW permite TCP $WEBRTC_HTTP_PORT"
    else
        check_warn "No se encontró regla UFW para TCP $WEBRTC_HTTP_PORT"
    fi

    if sudo ufw status | grep -q "$WEBRTC_ICE_PORT/udp"; then
        check_pass "UFW permite UDP $WEBRTC_ICE_PORT"
    else
        check_warn "No se encontró regla UFW para UDP $WEBRTC_ICE_PORT"
    fi
else
    check_warn "UFW no está instalado o no está disponible"
fi

# ============================================================
# FFmpeg
# ============================================================

section "6. FFmpeg"

if command -v ffmpeg >/dev/null 2>&1; then
    check_pass "FFmpeg disponible"
    ffmpeg -version | head -n 1

    if ffmpeg -encoders 2>/dev/null | grep -q "libx264"; then
        check_pass "Encoder libx264 disponible"
    else
        check_warn "Encoder libx264 no detectado"
    fi

    if ffmpeg -encoders 2>/dev/null | grep -q "libopus"; then
        check_pass "Encoder libopus disponible"
    else
        check_warn "Encoder libopus no detectado"
    fi
else
    check_fail "FFmpeg no está disponible"
fi

# ============================================================
# Logs WebRTC
# ============================================================

section "7. Logs recientes WebRTC"

journalctl -u "$SERVICE_NAME" -n 80 --no-pager -l 2>/dev/null | grep -Ei "WebRTC|ICE|$WEBRTC_TEST_PATH|peer connection|deadline|is reading|closed|stream is available" || true

echo
if journalctl -u "$SERVICE_NAME" -n 300 --no-pager -l 2>/dev/null | grep -q "peer connection established"; then
    check_pass "Se encontró evidencia reciente de Peer Connection establecida"
else
    check_warn "No se encontró evidencia reciente de Peer Connection establecida"
fi

if journalctl -u "$SERVICE_NAME" -n 300 --no-pager -l 2>/dev/null | grep -q "is reading from path '$WEBRTC_TEST_PATH'"; then
    check_pass "Se encontró lectura WebRTC reciente desde $WEBRTC_TEST_PATH"
else
    check_warn "No se encontró lectura WebRTC reciente desde $WEBRTC_TEST_PATH"
fi

# ============================================================
# URL de prueba
# ============================================================

section "8. URLs de prueba"

HOST_IP="$(hostname -I | awk '{print $1}')"

echo "WebRTC:"
echo "  http://${HOST_IP}:${WEBRTC_HTTP_PORT}/${WEBRTC_TEST_PATH}/"
echo
echo "HLS de referencia:"
echo "  http://${HOST_IP}:8888/${WEBRTC_TEST_PATH}/"
echo
echo "Publicación RTSP de prueba:"
echo "  rtsp://localhost:8554/${WEBRTC_TEST_PATH}"

# ============================================================
# Resumen
# ============================================================

section "9. Resumen"

echo "PASS : $OK"
echo "WARN : $WARN"
echo "FAIL : $FAIL"

echo
if [ "$FAIL" -eq 0 ]; then
    echo "Estado general: OPERATIVO"
    exit 0
else
    echo "Estado general: REVISAR"
    exit 1
fi