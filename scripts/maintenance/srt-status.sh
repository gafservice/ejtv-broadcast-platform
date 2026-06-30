#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "EJTV Broadcast Platform - SRT Status"
echo "============================================================"
echo "Fecha: $(date)"
echo

echo "[1/6] MediaMTX service"
systemctl is-active mediamtx
systemctl is-enabled mediamtx
echo

echo "[2/6] MediaMTX SRT configuration"
sudo grep -nE '^[[:space:]]*srt:|^[[:space:]]*srtAddress:|srtReadPassphrase|srtPublishPassphrase' \
  /opt/ejtv/mediamtx/config/mediamtx.yml || true
echo

echo "[3/6] UDP listener"
sudo ss -lunpt | grep -E ':8890|mediamtx' || true
echo

echo "[4/6] Firewall rule"
sudo ufw status numbered | grep -E '8890/udp|SRT' || true
echo

echo "[5/6] FFmpeg SRT support"
ffmpeg -hide_banner -protocols 2>/dev/null | grep -E '^[[:space:]]*srt$|^[[:space:]]*srtp$' || true
ffmpeg -hide_banner -buildconf 2>/dev/null | grep -- '--enable-libsrt' || true
echo

echo "[6/6] Recent MediaMTX SRT logs"
sudo journalctl -u mediamtx -n 30 --no-pager | grep -E '\[SRT\]|live/test' || true
echo

echo "============================================================"
echo "SRT status check completed"
echo "============================================================"
