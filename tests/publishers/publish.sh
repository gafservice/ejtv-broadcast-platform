#!/usr/bin/env bash
# ============================================================
# EJTV Broadcast Test Lab
# Universal Publisher
# ============================================================

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROFILE_DIR="${ROOT_DIR}/tests/profiles"

if [ $# -ne 1 ]; then
    echo
    echo "Uso:"
    echo "    $0 <PROFILE>"
    echo
    echo "Ejemplo:"
    echo "    $0 TEST-001-H264-360p-25fps"
    echo
    exit 1
fi

PROFILE="${PROFILE_DIR}/${1}.conf"

if [ ! -f "${PROFILE}" ]; then
    echo
    echo "Perfil no encontrado:"
    echo "    ${PROFILE}"
    echo
    exit 1
fi

source "${PROFILE}"

# ------------------------------------------------------------
# Valores por defecto
# ------------------------------------------------------------

VIDEO_FILTER="${VIDEO_FILTER:-null}"

VIDEO_PROFILE="${VIDEO_PROFILE:-baseline}"
VIDEO_LEVEL="${VIDEO_LEVEL:-3.1}"

PRESET="${PRESET:-ultrafast}"
TUNE="${TUNE:-zerolatency}"

GOP_SIZE="${GOP_SIZE:-25}"
KEYINT_MIN="${KEYINT_MIN:-25}"
SC_THRESHOLD="${SC_THRESHOLD:-0}"

VIDEO_MAXRATE="${VIDEO_MAXRATE:-$VIDEO_BITRATE}"
VIDEO_BUFSIZE="${VIDEO_BUFSIZE:-1600k}"

PROTOCOL="${PROTOCOL:-rtsp}"

echo
echo "============================================================"
echo " EJTV Broadcast Test Lab"
echo "============================================================"
echo
echo "Perfil        : ${PROFILE_NAME}"
echo "Descripción   : ${DESCRIPTION}"
echo "Video Codec   : ${VIDEO_CODEC}"
echo "Audio Codec   : ${AUDIO_CODEC}"
echo "Resolución    : ${WIDTH}x${HEIGHT}"
echo "FPS           : ${FPS}"
echo "Video Bitrate : ${VIDEO_BITRATE}"
echo "Audio Bitrate : ${AUDIO_BITRATE}"
echo "Video Filter  : ${VIDEO_FILTER}"
echo "Salida        : ${OUTPUT_PATH}"
echo

exec ffmpeg \
-re \
-f lavfi -i "testsrc2=size=${WIDTH}x${HEIGHT}:rate=${FPS}" \
-f lavfi -i "sine=frequency=1000:sample_rate=${AUDIO_RATE}" \
-vf "${VIDEO_FILTER}" \
-c:v "${VIDEO_CODEC}" \
-profile:v "${VIDEO_PROFILE}" \
-level "${VIDEO_LEVEL}" \
-preset "${PRESET}" \
-tune "${TUNE}" \
-pix_fmt "${PIX_FMT}" \
-g "${GOP_SIZE}" \
-keyint_min "${KEYINT_MIN}" \
-sc_threshold "${SC_THRESHOLD}" \
-b:v "${VIDEO_BITRATE}" \
-maxrate "${VIDEO_MAXRATE}" \
-bufsize "${VIDEO_BUFSIZE}" \
-c:a "${AUDIO_CODEC}" \
-b:a "${AUDIO_BITRATE}" \
-ar "${AUDIO_RATE}" \
-ac "${AUDIO_CHANNELS}" \
-f rtsp \
"rtsp://localhost:8554/${OUTPUT_PATH}"