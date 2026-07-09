#!/usr/bin/env python3
import os, time, psutil, requests
from datetime import datetime
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.progress_bar import ProgressBar

API_URL = "http://127.0.0.1:9997/v3/paths/list"
CHANNELS = ["enlace", "ejtv"]
INTERFACES = ["enp9s0", "ens2f0"]
PORTS = {
    "RTSP": 8554, "RTMP": 1935, "HLS": 8888,
    "WebRTC": 8889, "SRT": 8890,
    "ENLACE IN": 11001, "EJTV IN": 11002,
    "API": 9997, "Metrics": 9998,
}
last = {}

def api_paths():
    try:
        r = requests.get(API_URL, timeout=2)
        r.raise_for_status()
        return r.json().get("items", [])
    except Exception:
        return []

def mbps(key, value):
    now = time.time()
    old = last.get(key)
    last[key] = (value, now)
    if not old:
        return 0.0
    old_val, old_time = old
    dt = now - old_time
    if dt <= 0 or value < old_val:
        return 0.0
    return ((value - old_val) * 8) / dt / 1_000_000

def iface_rate(iface):
    try:
        a = psutil.net_io_counters(pernic=True)[iface]
        time.sleep(0.1)
        b = psutil.net_io_counters(pernic=True)[iface]
        rx = ((b.bytes_recv - a.bytes_recv) * 8) / 0.1 / 1_000_000
        tx = ((b.bytes_sent - a.bytes_sent) * 8) / 0.1 / 1_000_000
        return rx, tx
    except Exception:
        return 0.0, 0.0

def port_open(port):
    for c in psutil.net_connections(kind="inet"):
        try:
            if c.laddr and c.laddr.port == port:
                return True
        except Exception:
            pass
    return False

def mediamtx_alive():
    for p in psutil.process_iter(["cmdline"]):
        try:
            if "mediamtx" in " ".join(p.info.get("cmdline") or []):
                return True
        except Exception:
            pass
    return False

def header():
    t = Table.grid(expand=True)
    t.add_column(justify="left")
    t.add_column(justify="right")
    t.add_row("[bold cyan]EJTV CONTROL CENTER / NOC[/bold cyan]",
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    t.add_row("[green]MediaMTX API[/green]", "[white]ENLACE / EJTV[/white]")
    return Panel(t, border_style="cyan")

def server_panel():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    load = os.getloadavg()
    t = Table(show_header=False, expand=True)
    t.add_column("Métrica"); t.add_column("Valor"); t.add_column("Uso")
    t.add_row("CPU", f"{cpu:.1f} %", ProgressBar(100, completed=cpu))
    t.add_row("RAM", f"{mem.percent:.1f} %", ProgressBar(100, completed=mem.percent))
    t.add_row("SWAP", f"{swap.percent:.1f} %", ProgressBar(100, completed=swap.percent))
    t.add_row("LOAD", f"{load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}", "")
    return Panel(t, title="Servidor", border_style="green")

def channel_panel(item, name):
    ready = item.get("ready", False)
    readers = item.get("readers", [])
    srt = sum(1 for r in readers if r.get("type") == "srtConn")
    rtsp = sum(1 for r in readers if r.get("type") == "rtspSession")
    rtmp = sum(1 for r in readers if r.get("type") == "rtmpConn")
    webrtc = sum(1 for r in readers if r.get("type") == "webrtcSession")
    hls = sum(1 for r in readers if r.get("type") == "hlsMuxer")

    video, audio = "-", "-"
    for tr in item.get("tracks2", []):
        codec = tr.get("codec", "-")
        props = tr.get("codecProps", {})
        if "width" in props:
            video = f"{codec} {props.get('width')}x{props.get('height')}"
        if "sampleRate" in props:
            audio = f"{codec} {props.get('sampleRate')} Hz"

    inb = item.get("inboundBytes", item.get("bytesReceived", 0))
    outb = item.get("outboundBytes", item.get("bytesSent", 0))
    inm = mbps(name + "_in", inb)
    outm = mbps(name + "_out", outb)
    errors = item.get("inboundFramesInError", 0)

    t = Table(show_header=False, expand=True)
    t.add_column("Campo"); t.add_column("Valor")
    t.add_row("Estado", "[green]ON AIR[/green]" if ready else "[red]FUERA DE AIRE[/red]")
    t.add_row("Entrada", f"{inm:.2f} Mbps")
    t.add_row("Salida", f"{outm:.2f} Mbps")
    t.add_row("Video", video)
    t.add_row("Audio", audio)
    t.add_row("RTSP", str(rtsp))
    t.add_row("RTMP", str(rtmp))
    t.add_row("SRT", str(srt))
    t.add_row("HLS", str(hls))
    t.add_row("WebRTC", str(webrtc))
    t.add_row("Errores", str(errors))
    return Panel(t, title=name.upper(), border_style="green" if ready else "red")

def channels(items):
    found = {i.get("name"): i for i in items}
    l = Layout()
    l.split_row(Layout(name="enlace"), Layout(name="ejtv"))
    for ch in CHANNELS:
        if ch in found:
            l[ch].update(channel_panel(found[ch], ch))
        else:
            l[ch].update(Panel("[red]Canal no encontrado[/red]", title=ch.upper(), border_style="red"))
    return l

def interfaces_panel():
    t = Table(expand=True)
    t.add_column("Interfaz"); t.add_column("RX Mbps", justify="right"); t.add_column("TX Mbps", justify="right")
    for i in INTERFACES:
        rx, tx = iface_rate(i)
        t.add_row(i, f"{rx:.2f}", f"{tx:.2f}")
    return Panel(t, title="Interfaces", border_style="blue")

def ports_panel():
    t = Table(expand=True)
    t.add_column("Servicio"); t.add_column("Puerto"); t.add_column("Estado")
    for name, port in PORTS.items():
        t.add_row(name, str(port), "[green]OK[/green]" if port_open(port) else "[red]CERRADO[/red]")
    return Panel(t, title="Puertos", border_style="cyan")

def alarms_panel(items):
    alarms = []
    if not mediamtx_alive():
        alarms.append("[red]MediaMTX caído[/red]")
    found = {i.get("name"): i for i in items}
    for ch in CHANNELS:
        if ch not in found:
            alarms.append(f"[red]{ch.upper()} no existe[/red]")
        elif not found[ch].get("ready", False):
            alarms.append(f"[red]{ch.upper()} fuera de aire[/red]")
    if psutil.cpu_percent() > 85:
        alarms.append("[yellow]CPU alta[/yellow]")
    if psutil.virtual_memory().percent > 85:
        alarms.append("[yellow]RAM alta[/yellow]")
    return Panel("\n".join(alarms) if alarms else "[green]Sin alarmas críticas[/green]",
                 title="Alarmas", border_style="red")

def build():
    items = api_paths()
    l = Layout()
    l.split_column(Layout(name="h", size=4), Layout(name="c", size=15), Layout(name="b"))
    l["b"].split_row(Layout(name="srv"), Layout(name="if"), Layout(name="ports"), Layout(name="al"))
    l["h"].update(header())
    l["c"].update(channels(items))
    l["srv"].update(server_panel())
    l["if"].update(interfaces_panel())
    l["ports"].update(ports_panel())
    l["al"].update(alarms_panel(items))
    return l

def main():
    with Live(build(), refresh_per_second=1, screen=True) as live:
        while True:
            live.update(build())
            time.sleep(5)

if __name__ == "__main__":
    main()
