#!/usr/bin/env bash

IN_IF="enp9s0"
OUT_IF="ens2f0"

IN_ENLACE_PORT="11001"
IN_EJTV_PORT="11002"

RTSP_PORT="8554"
SRT_PORT="8890"
HLS_PORT="8888"
WEBRTC_HTTP_PORT="8889"
WEBRTC_ICE_PORT="8189"

INTERVAL=3

clear
echo "============================================================"
echo "              EJTV NETWORK STATUS"
echo "============================================================"
echo "Fecha: $(date)"
echo

echo "===== SISTEMA ====="
uptime
echo

echo "===== CPU / RAM ====="
echo "CPU:"
top -bn1 | grep "Cpu(s)"
echo
echo "RAM:"
free -h
echo

echo "===== MEDIAMTX ====="
systemctl is-active mediamtx
ps -o pid,%cpu,%mem,rss,vsz,cmd -C mediamtx
echo

echo "===== PUERTOS STREAMING ====="
sudo ss -tulpn | egrep '11001|11002|8554|8890|8888|8889|8189|1935' || echo "No hay puertos visibles"
echo

echo "===== BITRATE POR INTERFAZ ====="
rx1_in=$(cat /sys/class/net/$IN_IF/statistics/rx_bytes)
tx1_in=$(cat /sys/class/net/$IN_IF/statistics/tx_bytes)
rx1_out=$(cat /sys/class/net/$OUT_IF/statistics/rx_bytes)
tx1_out=$(cat /sys/class/net/$OUT_IF/statistics/tx_bytes)

sleep $INTERVAL

rx2_in=$(cat /sys/class/net/$IN_IF/statistics/rx_bytes)
tx2_in=$(cat /sys/class/net/$IN_IF/statistics/tx_bytes)
rx2_out=$(cat /sys/class/net/$OUT_IF/statistics/rx_bytes)
tx2_out=$(cat /sys/class/net/$OUT_IF/statistics/tx_bytes)

rx_in_mbps=$(awk "BEGIN {printf \"%.2f\", (($rx2_in-$rx1_in)*8)/($INTERVAL*1000000)}")
tx_in_mbps=$(awk "BEGIN {printf \"%.2f\", (($tx2_in-$tx1_in)*8)/($INTERVAL*1000000)}")
rx_out_mbps=$(awk "BEGIN {printf \"%.2f\", (($rx2_out-$rx1_out)*8)/($INTERVAL*1000000)}")
tx_out_mbps=$(awk "BEGIN {printf \"%.2f\", (($tx2_out-$tx1_out)*8)/($INTERVAL*1000000)}")

echo "$IN_IF  RX: ${rx_in_mbps} Mbps | TX: ${tx_in_mbps} Mbps"
echo "$OUT_IF RX: ${rx_out_mbps} Mbps | TX: ${tx_out_mbps} Mbps"
echo

echo "===== BITRATE ENTRADA POR CANAL ====="
echo "Midiendo ENLACE UDP $IN_ENLACE_PORT..."
sudo timeout 5 tcpdump -ni "$IN_IF" udp port "$IN_ENLACE_PORT" 2>/tmp/ejtv_11001_tcpdump.txt >/dev/null
pkts_11001=$(grep "packets captured" /tmp/ejtv_11001_tcpdump.txt | awk '{print $1}')
mbps_11001=$(awk "BEGIN {printf \"%.2f\", ($pkts_11001*1316*8)/(5*1000000)}")
echo "ENLACE 11001: ${mbps_11001} Mbps aprox."

echo "Midiendo EJTV UDP $IN_EJTV_PORT..."
sudo timeout 5 tcpdump -ni "$IN_IF" udp port "$IN_EJTV_PORT" 2>/tmp/ejtv_11002_tcpdump.txt >/dev/null
pkts_11002=$(grep "packets captured" /tmp/ejtv_11002_tcpdump.txt | awk '{print $1}')
mbps_11002=$(awk "BEGIN {printf \"%.2f\", ($pkts_11002*1316*8)/(5*1000000)}")
echo "EJTV   11002: ${mbps_11002} Mbps aprox."
echo

echo "===== CLIENTES ACTIVOS ====="
rtsp_clients=$(sudo ss -tn state established "( sport = :$RTSP_PORT )" | tail -n +2 | wc -l)
srt_clients=$(sudo ss -un | grep ":$SRT_PORT" | wc -l)
hls_clients=$(sudo ss -tn state established "( sport = :$HLS_PORT )" | tail -n +2 | wc -l)
webrtc_http_clients=$(sudo ss -tn state established "( sport = :$WEBRTC_HTTP_PORT )" | tail -n +2 | wc -l)
webrtc_udp_clients=$(sudo ss -un | grep ":$WEBRTC_ICE_PORT" | wc -l)

echo "RTSP clientes       : $rtsp_clients"
echo "SRT conexiones UDP  : $srt_clients"
echo "HLS clientes        : $hls_clients"
echo "WebRTC HTTP         : $webrtc_http_clients"
echo "WebRTC ICE UDP      : $webrtc_udp_clients"
echo

echo "===== CANALES RTSP ====="
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height \
-of default=noprint_wrappers=1 rtsp://127.0.0.1:8554/enlace >/tmp/enlace_status.txt 2>&1

if grep -q "codec_name" /tmp/enlace_status.txt; then
    echo "ENLACE: ACTIVO"
else
    echo "ENLACE: ERROR"
fi

ffprobe -v error -show_entries stream=codec_type,codec_name,width,height \
-of default=noprint_wrappers=1 rtsp://127.0.0.1:8554/ejtv >/tmp/ejtv_status.txt 2>&1

if grep -q "codec_name" /tmp/ejtv_status.txt; then
    echo "EJTV  : ACTIVO"
else
    echo "EJTV  : ERROR"
fi

echo
echo "============================================================"
echo "FIN NETWORK STATUS"
echo "============================================================"
