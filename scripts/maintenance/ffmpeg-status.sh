#!/bin/bash

###############################################################################
# EJTV Broadcast Platform
# Script.....: ffmpeg-status.sh
# Objetivo...: Diagnóstico completo de FFmpeg
###############################################################################

clear

echo "=========================================================="
echo " EJTV Broadcast Platform"
echo " FFmpeg Status"
echo "=========================================================="

echo
echo "Fecha:"
date

echo
echo "Hostname:"
hostnamectl --static

echo
echo "=========================================================="
echo "1. Binarios"
echo "=========================================================="

command -v ffmpeg  || echo "FFmpeg: NO instalado"
command -v ffprobe || echo "FFprobe: NO instalado"
command -v ffplay  || echo "FFplay: NO instalado"

echo
echo "=========================================================="
echo "2. Version FFmpeg"
echo "=========================================================="

ffmpeg -version 2>/dev/null | head -5

echo
echo "=========================================================="
echo "3. Version FFprobe"
echo "=========================================================="

ffprobe -version 2>/dev/null | head -5

echo
echo "=========================================================="
echo "4. Version FFplay"
echo "=========================================================="

ffplay -version 2>/dev/null | head -5

echo
echo "=========================================================="
echo "5. Paquetes instalados"
echo "=========================================================="

dpkg -l | grep -i ffmpeg || echo "No hay paquetes FFmpeg registrados."

echo
echo "=========================================================="
echo "6. Protocolos principales"
echo "=========================================================="

ffmpeg -protocols 2>/dev/null | grep -Ei "rtmp|rtsp|http|https|tcp|udp|srt|srtp" || true

echo
echo "=========================================================="
echo "7. Codecs principales"
echo "=========================================================="

ffmpeg -codecs 2>/dev/null | grep -Ei "h264|hevc|aac|opus" || true

echo
echo "=========================================================="
echo "8. Encoders principales"
echo "=========================================================="

ffmpeg -encoders 2>/dev/null | grep -Ei "libx264|libx265|aac|opus" || true

echo
echo "=========================================================="
echo "9. Formatos principales"
echo "=========================================================="

ffmpeg -formats 2>/dev/null | grep -Ei "flv|mpegts|mp4|matroska|hls|rtsp" || true

echo
echo "=========================================================="
echo "10. Dependencias"
echo "=========================================================="

ldd "$(command -v ffmpeg)" 2>/dev/null || echo "No se pudieron listar dependencias."

echo
echo "=========================================================="
echo "11. Auditoria DPKG"
echo "=========================================================="

sudo dpkg --audit || true

echo
echo "=========================================================="
echo "12. Estado MediaMTX"
echo "=========================================================="

systemctl status mediamtx --no-pager | head -15 || true

echo
echo "=========================================================="
echo "13. Puertos multimedia"
echo "=========================================================="

ss -tuln | grep -E "1935|8554|8888|8889|8890|8892|8000|8001|8189" || echo "No se detectaron puertos multimedia abiertos."

echo
echo "=========================================================="
echo "14. Procesos activos"
echo "=========================================================="

ps -ef | grep -E "ffmpeg|ffplay|ffprobe" | grep -v grep || echo "No hay procesos FFmpeg/FFplay/FFprobe activos."

echo
echo "=========================================================="
echo "15. Recursos"
echo "=========================================================="

free -h
df -h /

echo
echo "=========================================================="
echo " FIN DEL DIAGNOSTICO"
echo "=========================================================="
