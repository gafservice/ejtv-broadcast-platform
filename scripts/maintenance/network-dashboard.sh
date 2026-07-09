#!/usr/bin/env bash

clear

echo "============================================================"
echo "                    EJTV NETWORK DASHBOARD"
echo "============================================================"
echo "Fecha: $(date)"
echo

echo "===== SISTEMA ====="
uptime
echo

echo "===== CPU / RAM ====="
echo "CPU:"
top -bn1 | grep "%Cpu"
echo
echo "RAM:"
free -h
echo

echo "===== MEDIAMTX ====="
systemctl is-active mediamtx
ps -C mediamtx -o pid,%cpu,%mem,rss,vsz,cmd
echo

echo "===== PUERTOS STREAMING ====="
ss -tunlp | grep -E '11001|11002|8554|8890|8189|8888|8889|1935' || echo "Sin puertos encontrados"
echo

echo "===== BITRATE POR INTERFAZ ====="

measure_iface() {
    IFACE="$1"

    RX1=$(cat /sys/class/net/$IFACE/statistics/rx_bytes 2>/dev/null)
    TX1=$(cat /sys/class/net/$IFACE/statistics/tx_bytes 2>/dev/null)

    sleep 1

    RX2=$(cat /sys/class/net/$IFACE/statistics/rx_bytes 2>/dev/null)
    TX2=$(cat /sys/class/net/$IFACE/statistics/tx_bytes 2>/dev/null)

    if [ -n "$RX1" ] && [ -n "$RX2" ]; then
        RX_MBPS=$(awk "BEGIN {printf \"%.2f\", (($RX2-$RX1)*8)/1000000}")
        TX_MBPS=$(awk "BEGIN {printf \"%.2f\", (($TX2-$TX1)*8)/1000000}")
        echo "$IFACE RX: ${RX_MBPS} Mbps | TX: ${TX_MBPS} Mbps"
    else
        echo "$IFACE no disponible"
    fi
}

measure_iface enp9s0
measure_iface ens2f0
echo

echo "===== BITRATE ENTRADA POR CANAL ====="

measure_udp_port() {
    NAME="$1"
    PORT="$2"

    echo "Midiendo $NAME UDP $PORT..."

    BYTES=$(timeout 3s tcpdump -i any -n udp port "$PORT" -w - 2>/dev/null | wc -c)

    MBPS=$(awk "BEGIN {printf \"%.2f\", ($BYTES*8)/3/1000000}")

    echo "$NAME $PORT: ${MBPS} Mbps aprox."
}

measure_udp_port "ENLACE" 11001
measure_udp_port "EJTV  " 11002
echo

echo "===== CLIENTES ACTIVOS ====="

RTSP_CLIENTS=$(ss -tnp | grep ':8554' | grep ESTAB | wc -l)
SRT_CLIENTS=$(ss -unp | grep ':8890' | wc -l)
HLS_CLIENTS=$(ss -tnp | grep ':8888' | grep ESTAB | wc -l)
WEBRTC_HTTP=$(ss -tnp | grep ':8889' | grep ESTAB | wc -l)
WEBRTC_ICE=$(ss -unp | grep ':8189' | wc -l)

echo "RTSP clientes       : $RTSP_CLIENTS"
echo "SRT conexiones UDP  : $SRT_CLIENTS"
echo "HLS clientes        : $HLS_CLIENTS"
echo "WebRTC HTTP         : $WEBRTC_HTTP"
echo "WebRTC ICE UDP      : $WEBRTC_ICE"
echo

echo "===== CANALES RTSP ====="

check_channel() {
    NAME="$1"
    URL="$2"

    timeout 5s ffprobe -v error -rtsp_transport tcp -i "$URL" >/dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "$NAME: ACTIVO"
    else
        echo "$NAME: INACTIVO"
    fi
}

check_channel "ENLACE" "rtsp://127.0.0.1:8554/enlace"
check_channel "EJTV  " "rtsp://127.0.0.1:8554/ejtv"

echo
echo "============================================================"
echo "FIN NETWORK DASHBOARD"
echo "============================================================"
