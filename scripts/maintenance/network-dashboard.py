#!/usr/bin/env python3

import os
import time
import psutil
import socket
import subprocess
from datetime import datetime

from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from rich.text import Text
from rich.progress_bar import ProgressBar

console = Console()

INTERFACES = ["enp9s0", "ens2f0"]

CHANNELS = {
    "ENLACE": {
        "udp_port": 11001,
        "rtsp": "rtsp://127.0.0.1:8554/enlace",
    },
    "EJTV": {
        "udp_port": 11002,
        "rtsp": "rtsp://127.0.0.1:8554/ejtv",
    },
}

PORTS = {
    "RTSP": 8554,
    "RTMP": 1935,
    "HLS": 8888,
    "WebRTC HTTP": 8889,
    "WebRTC ICE": 8189,
    "SRT": 8890,
    "ENLACE UDP": 11001,
    "EJTV UDP": 11002,
}


def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def service_status(name):
    status = run_cmd(f"systemctl is-active {name}")
    return status if status else "unknown"


def get_mediamtx_process():
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "cmdline"]):
        try:
            cmdline = " ".join(proc.info.get("cmdline") or [])
            if "mediamtx" in cmdline:
                return proc
        except Exception:
            pass
    return None


def iface_speed(iface):
    try:
        c1 = psutil.net_io_counters(pernic=True)[iface]
        time.sleep(0.4)
        c2 = psutil.net_io_counters(pernic=True)[iface]

        rx = ((c2.bytes_recv - c1.bytes_recv) * 8) / 0.4 / 1_000_000
        tx = ((c2.bytes_sent - c1.bytes_sent) * 8) / 0.4 / 1_000_000

        return rx, tx
    except Exception:
        return 0, 0


def tcp_clients(port):
    count = 0
    for c in psutil.net_connections(kind="tcp"):
        try:
            if c.laddr and c.laddr.port == port and c.status == "ESTABLISHED":
                count += 1
        except Exception:
            pass
    return count


def udp_open(port):
    for c in psutil.net_connections(kind="udp"):
        try:
            if c.laddr and c.laddr.port == port:
                return True
        except Exception:
            pass
    return False


def port_listening(port):
    for c in psutil.net_connections(kind="inet"):
        try:
            if c.laddr and c.laddr.port == port:
                return True
        except Exception:
            pass
    return False


def check_rtsp(url):
    cmd = f'timeout 4s ffprobe -v error -rtsp_transport tcp -i "{url}"'
    result = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def measure_udp_bitrate(port):
    cmd = f'timeout 2s tcpdump -i any -n udp port {port} -w - 2>/dev/null | wc -c'
    out = run_cmd(cmd)

    try:
        bytes_count = int(out)
        mbps = (bytes_count * 8) / 2 / 1_000_000
        return mbps
    except Exception:
        return 0.0


def header_panel():
    text = Text()
    text.append("EJTV NETWORK DASHBOARD\n", style="bold cyan")
    text.append(f"{datetime.now().strftime('%A %d %B %Y - %H:%M:%S')}\n", style="white")
    text.append("Plataforma de distribución ENLACE / EJTV", style="green")

    return Panel(text, border_style="cyan")


def system_panel():
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    load = os.getloadavg()

    table = Table(show_header=False, expand=True)
    table.add_column("Métrica")
    table.add_column("Valor")
    table.add_column("Uso")

    table.add_row("CPU", f"{cpu:.1f} %", ProgressBar(total=100, completed=cpu))
    table.add_row("RAM", f"{mem.used / (1024**3):.1f} / {mem.total / (1024**3):.1f} GiB", ProgressBar(total=100, completed=mem.percent))
    table.add_row("SWAP", f"{swap.used / (1024**3):.1f} / {swap.total / (1024**3):.1f} GiB", ProgressBar(total=100, completed=swap.percent))
    table.add_row("LOAD", f"{load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}", "")

    return Panel(table, title="Sistema", border_style="green")


def mediamtx_panel():
    proc = get_mediamtx_process()
    status = service_status("mediamtx")

    table = Table(show_header=False, expand=True)
    table.add_column("Campo")
    table.add_column("Valor")

    if proc:
        proc.cpu_percent(interval=None)
        table.add_row("Estado", f"[green]{status}[/green]" if status == "active" else f"[red]{status}[/red]")
        table.add_row("PID", str(proc.pid))
        table.add_row("CPU", f"{proc.cpu_percent(interval=0.1):.1f} %")
        table.add_row("RAM", f"{proc.memory_percent():.1f} %")
    else:
        table.add_row("Estado", "[red]No detectado[/red]")
        table.add_row("PID", "-")
        table.add_row("CPU", "-")
        table.add_row("RAM", "-")

    return Panel(table, title="MediaMTX", border_style="magenta")


def interfaces_panel():
    table = Table(expand=True)
    table.add_column("Interfaz")
    table.add_column("RX Mbps", justify="right")
    table.add_column("TX Mbps", justify="right")

    for iface in INTERFACES:
        rx, tx = iface_speed(iface)
        table.add_row(iface, f"{rx:.2f}", f"{tx:.2f}")

    return Panel(table, title="Bitrate por interfaz", border_style="blue")


def channels_panel():
    table = Table(expand=True)
    table.add_column("Canal")
    table.add_column("UDP")
    table.add_column("Bitrate entrada")
    table.add_column("RTSP")

    for name, data in CHANNELS.items():
        udp_port = data["udp_port"]
        bitrate = measure_udp_bitrate(udp_port)
        rtsp_ok = check_rtsp(data["rtsp"])

        table.add_row(
            name,
            str(udp_port),
            f"{bitrate:.2f} Mbps",
            "[green]ACTIVO[/green]" if rtsp_ok else "[red]INACTIVO[/red]",
        )

    return Panel(table, title="Canales", border_style="yellow")


def clients_panel():
    rtsp = tcp_clients(8554)
    hls = tcp_clients(8888)
    webrtc_http = tcp_clients(8889)

    srt = "ABIERTO" if udp_open(8890) else "CERRADO"
    ice = "ABIERTO" if udp_open(8189) else "CERRADO"

    table = Table(show_header=False, expand=True)
    table.add_column("Servicio")
    table.add_column("Estado / Clientes")

    table.add_row("RTSP clientes", str(rtsp))
    table.add_row("HLS clientes", str(hls))
    table.add_row("WebRTC HTTP", str(webrtc_http))
    table.add_row("SRT UDP", srt)
    table.add_row("WebRTC ICE UDP", ice)

    return Panel(table, title="Clientes activos", border_style="red")


def ports_panel():
    table = Table(expand=True)
    table.add_column("Servicio")
    table.add_column("Puerto")
    table.add_column("Estado")

    for name, port in PORTS.items():
        ok = port_listening(port)
        table.add_row(
            name,
            str(port),
            "[green]ABIERTO[/green]" if ok else "[red]CERRADO[/red]",
        )

    return Panel(table, title="Puertos streaming", border_style="cyan")


def build_dashboard():
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=5),
        Layout(name="body"),
    )

    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )

    layout["left"].split_column(
        Layout(name="system"),
        Layout(name="interfaces"),
        Layout(name="channels"),
    )

    layout["right"].split_column(
        Layout(name="mediamtx"),
        Layout(name="clients"),
        Layout(name="ports"),
    )

    layout["header"].update(header_panel())
    layout["system"].update(system_panel())
    layout["interfaces"].update(interfaces_panel())
    layout["channels"].update(channels_panel())
    layout["mediamtx"].update(mediamtx_panel())
    layout["clients"].update(clients_panel())
    layout["ports"].update(ports_panel())

    return layout


def main():
    with Live(build_dashboard(), refresh_per_second=1, screen=True) as live:
        while True:
            live.update(build_dashboard())
            time.sleep(5)


if __name__ == "__main__":
    main()

