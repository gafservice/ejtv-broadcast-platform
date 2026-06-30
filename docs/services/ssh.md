# Secure Reliable Transport (SRT)

**Proyecto:** EJTV Broadcast Platform

**Misión:** MISSION-013 — SRT

---

# 1. Objetivo

Este documento describe la implementación del protocolo **Secure Reliable Transport (SRT)** dentro de la plataforma **EJTV Broadcast Platform**, incluyendo su arquitectura, configuración, validación, operación y procedimientos de mantenimiento.

La implementación permite utilizar SRT como protocolo de contribución ("ingest") de baja latencia y alta confiabilidad hacia MediaMTX.

---

# 2. Descripción

SRT (Secure Reliable Transport) es un protocolo de transporte desarrollado para la distribución de audio y video sobre redes IP.

Su diseño incorpora mecanismos de:

- recuperación de paquetes perdidos
- retransmisión selectiva
- control de congestión
- baja latencia configurable
- cifrado AES opcional

A diferencia de RTMP, SRT utiliza UDP como protocolo de transporte.

---

# 3. Arquitectura

```
                 +-------------------+
                 |   Encoder/FFmpeg  |
                 +---------+---------+
                           |
                      SRT / UDP
                           |
                      Puerto 8890
                           |
                    +--------------+
                    |   MediaMTX   |
                    +--------------+
                           |
        +------------------+------------------+
        |                  |                  |
      RTSP               HLS             WebRTC
```

MediaMTX actúa como servidor SRT y redistribuye posteriormente el flujo hacia los demás protocolos soportados.

---

# 4. Configuración

Archivo:

```text
/opt/ejtv/mediamtx/config/mediamtx.yml
```

Configuración utilizada:

```yaml
srt: true

srtAddress: :8890
```

La configuración por defecto mantiene deshabilitado el uso de contraseñas.

Campos disponibles:

```yaml
srtReadPassphrase:

srtPublishPassphrase:
```

Estos parámetros permanecen vacíos durante la fase actual del proyecto.

---

# 5. Puerto utilizado

| Protocolo | Puerto |
|-----------|---------|
| UDP | 8890 |

Firewall UFW:

```
8890/udp
```

---

# 6. Publicación

Ejemplo de publicación mediante FFmpeg:

```bash
ffmpeg \
-re \
-f lavfi -i testsrc=size=1280x720:rate=30 \
-f lavfi -i sine=frequency=1000 \
-c:v libx264 \
-c:a aac \
-f mpegts \
"srt://SERVIDOR:8890?streamid=publish:live/test"
```

Ejemplo local:

```text
srt://127.0.0.1:8890?streamid=publish:live/test
```

---

# 7. Lectura

Ejemplo:

```bash
ffprobe \
"srt://SERVIDOR:8890?streamid=read:live/test"
```

Ejemplo local:

```text
srt://127.0.0.1:8890?streamid=read:live/test
```

---

# 8. Validación

Durante MISSION-013 se verificó correctamente:

- apertura del listener SRT
- publicación desde FFmpeg
- creación del stream
- lectura mediante SRT
- detección automática del flujo por MediaMTX
- publicación de audio AAC
- publicación de video H264

Mensajes observados:

```
[SRT] opened

is publishing

is reading

stream is available and online
```

---

# 9. Verificación del servicio

Estado:

```bash
systemctl status mediamtx
```

Listener:

```bash
ss -lunpt
```

Configuración:

```bash
grep srt /opt/ejtv/mediamtx/config/mediamtx.yml
```

Logs:

```bash
journalctl -u mediamtx
```

---

# 10. Script de mantenimiento

La plataforma incorpora:

```
scripts/maintenance/srt-status.sh
```

El script verifica:

- estado del servicio
- configuración
- listener UDP
- firewall
- soporte SRT en FFmpeg
- eventos recientes del log

---

# 11. Seguridad

Actualmente la plataforma opera sin autenticación SRT.

MediaMTX permite incorporar posteriormente:

- Publish Passphrase
- Read Passphrase

sin modificar la arquitectura existente.

---

# 12. Integración con EJTV

Actualmente SRT se utiliza como protocolo de contribución.

MediaMTX recibe el flujo mediante SRT y puede redistribuirlo simultáneamente mediante:

- RTSP
- RTMP
- HLS
- WebRTC
- MoQ

sin necesidad de recodificación.

---

# 13. Estado de implementación

| Característica | Estado |
|----------------|--------|
| Listener SRT | Implementado |
| Firewall | Configurado |
| Publicación | Validada |
| Lectura | Validada |
| Script de mantenimiento | Disponible |
| Acceptance Test | Pendiente de incorporación |
| Passphrase | Disponible, no utilizada |

---

# 14. Troubleshooting
Agregar una sección "Troubleshooting", donde documentemos problemas típicos (puerto cerrado, streamid incorrecto, ffprobe sin flujo, etc.).


# 15. Acceptance Criteria
Agregar una sección "Acceptance Criteria", que enumere explícitamente los criterios que debe cumplir una instalación para considerarse conforme. Esto hace que la documentación quede alineada con la metodología de misiones y acceptance tests del proyecto.


# 16. Referencias

- MediaMTX Documentation
- FFmpeg Documentation
- Haivision SRT Protocol Specification