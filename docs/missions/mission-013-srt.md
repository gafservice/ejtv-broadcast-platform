# Acceptance Test
# MISSION-013 — SRT

**Proyecto:** EJTV Broadcast Platform

---

# Objetivo

Verificar la correcta implementación del protocolo Secure Reliable Transport (SRT) dentro de la plataforma EJTV Broadcast Platform.

La prueba valida:

- configuración del servicio
- disponibilidad del listener
- publicación de un flujo
- lectura del flujo
- integración con MediaMTX
- reglas de firewall
- soporte de FFmpeg

---

# Prerrequisitos

Debe existir:

- Ubuntu Server operativo
- MediaMTX iniciado
- FFmpeg con soporte SRT
- Firewall habilitado
- Puerto UDP 8890 permitido

---

# Prueba 1 — Servicio

Comando

```bash
systemctl is-active mediamtx
```

Resultado esperado

```text
active
```

PASS

El servicio responde **active**.

---

# Prueba 2 — Listener

Comando

```bash
ss -lunpt | grep 8890
```

Resultado esperado

Debe aparecer:

```text
*:8890
```

PASS

MediaMTX escucha en UDP 8890.

---

# Prueba 3 — Firewall

Comando

```bash
sudo ufw status numbered
```

Resultado esperado

Debe existir:

```text
8890/udp
```

PASS

La regla está presente.

---

# Prueba 4 — Configuración

Comando

```bash
grep -nE "srt|srtAddress" \
/opt/ejtv/mediamtx/config/mediamtx.yml
```

Resultado esperado

```yaml
srt: true

srtAddress: :8890
```

PASS

La configuración coincide.

---

# Prueba 5 — Publicación

Ejecutar

```bash
ffmpeg \
-re \
-f lavfi -i testsrc=size=1280x720:rate=30 \
-f lavfi -i sine=frequency=1000 \
-c:v libx264 \
-c:a aac \
-f mpegts \
"srt://127.0.0.1:8890?streamid=publish:live/test"
```

Resultado esperado

MediaMTX registra:

```text
is publishing
```

PASS

El flujo es aceptado.

---

# Prueba 6 — Lectura

Mientras la prueba anterior continúa ejecutándose:

```bash
ffprobe \
"srt://127.0.0.1:8890?streamid=read:live/test"
```

Resultado esperado

Debe detectarse:

- Video H264

- Audio AAC

PASS

El flujo puede leerse correctamente.

---

# Prueba 7 — Logs

Comando

```bash
journalctl -u mediamtx -n 50 --no-pager
```

Resultado esperado

Debe observarse:

```text
[SRT]

opened

is publishing

is reading
```

PASS

Los eventos aparecen sin errores.

---

# Prueba 8 — Script de mantenimiento

Comando

```bash
scripts/maintenance/srt-status.sh
```

Resultado esperado

El script debe mostrar:

- Servicio activo
- Listener UDP
- Firewall
- Configuración
- Logs recientes
- Soporte SRT de FFmpeg

PASS

La ejecución finaliza sin errores.

---

# Resultado esperado

Todas las pruebas deben completarse satisfactoriamente.

---

# Criterio de aceptación

La misión se considera aprobada únicamente cuando:

- MediaMTX escucha en UDP 8890.
- FFmpeg publica correctamente.
- MediaMTX crea el stream.
- El flujo puede leerse mediante SRT.
- El firewall permite UDP 8890.
- El script de mantenimiento ejecuta sin errores.
- No aparecen errores en los logs de MediaMTX.

---

# Evidencias obtenidas durante la MISSION-013

✔ Listener SRT iniciado.

✔ Publicación SRT validada.

✔ Lectura SRT validada.

✔ FFmpeg con soporte `--enable-libsrt`.

✔ Firewall configurado para UDP 8890.

✔ Script `scripts/maintenance/srt-status.sh` validado.

---

# Estado

**PASS**