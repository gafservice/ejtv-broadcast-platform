# WebRTC

## Servicio

WebRTC (Web Real-Time Communication)

---

# Objetivo

Proporcionar distribución de contenido audiovisual en tiempo real con
latencia ultrabaja directamente hacia navegadores compatibles, utilizando
MediaMTX como servidor de señalización y transporte multimedia.

Dentro de la plataforma EJTV Broadcast Platform, WebRTC constituye el
protocolo de menor latencia disponible para la distribución de contenido,
complementando los servicios RTSP, RTMP, SRT y HLS previamente
implementados.

---

# Características

La implementación WebRTC de la plataforma proporciona:

- Distribución multimedia con latencia ultrabaja.
- Reproducción directa desde navegadores compatibles.
- Conversión automática RTSP → WebRTC mediante MediaMTX.
- Video codificado en H.264.
- Audio codificado en Opus.
- Negociación ICE automática.
- Compatibilidad con clientes dentro de la red LAN.
- Integración transparente con el resto de los servicios multimedia de la plataforma.

---

# Arquitectura

```
                FFmpeg
                   │
                   │ RTSP
                   ▼
              MediaMTX
             ┌───────────────┐
             │               │
             │    WebRTC     │
             │               │
             └──────┬────────┘
                    │
         HTTP :8889 │
          ICE :8189 │
                    ▼
          Navegador Web
```

---

# Componentes

| Componente | Función |
|------------|---------|
| MediaMTX | Servidor WebRTC |
| FFmpeg | Publicador RTSP |
| Navegador | Cliente WebRTC |
| ICE | Negociación de conectividad |
| UDP | Transporte multimedia |

---

# Configuración

Parámetros principales utilizados durante la implementación.

```yaml
webrtc: true

webrtcAddress: :8889

webrtcEncryption: false

webrtcAllowOrigins:
  - "*"

webrtcLocalUDPAddress: :8189

webrtcIPsFromInterfaces: true

webrtcAdditionalHosts:
  - 192.168.33.239
```

---

# Puertos utilizados

| Puerto | Protocolo | Uso |
|---------|-----------|-----|
| 8889 | TCP | HTTP / WebRTC |
| 8189 | UDP | ICE |
| 8554 | TCP | RTSP (Publicación) |

---

# Endpoints

Durante la validación se utilizaron los siguientes endpoints.

| Servicio | Endpoint |
|----------|----------|
| RTSP | rtsp://localhost:8554/live/webrtc-test |
| WebRTC | http://192.168.33.239:8889/live/webrtc-test/ |
| HLS | http://192.168.33.239:8888/live/webrtc-test/ |

---

# Flujo de operación

El servicio WebRTC implementado en la plataforma EJTV Broadcast Platform
utiliza MediaMTX como servidor de distribución multimedia en tiempo real.

Durante la operación normal, un publicador genera un flujo RTSP utilizando
FFmpeg. Dicho flujo es recibido por MediaMTX, el cual realiza la adaptación
del protocolo y lo pone a disposición de clientes WebRTC mediante una
negociación ICE y el establecimiento de una conexión Peer-to-Peer.

Una vez establecida la sesión WebRTC, el navegador recibe el contenido
audiovisual codificado en H.264 para video y Opus para audio,
permitiendo una reproducción con latencia significativamente menor que
otros protocolos de distribución.

El flujo operativo implementado es el siguiente.

```
FFmpeg
    │
    │ RTSP
    ▼
MediaMTX
    │
    ├── Negociación ICE
    │
    ▼
WebRTC
    │
    ▼
Navegador
```

---

# Publicación de prueba

La validación del servicio se realizó utilizando FFmpeg como publicador de
referencia.

Durante las pruebas se generó un patrón de video sintético junto con un
tono de audio continuo, permitiendo verificar simultáneamente la
transmisión de video y audio mediante WebRTC.

```bash
ffmpeg -re \
-f lavfi -i testsrc2=size=640x360:rate=25 \
-f lavfi -i sine=frequency=1000:sample_rate=48000 \
-c:v libx264 \
-profile:v baseline \
-level 3.1 \
-preset ultrafast \
-tune zerolatency \
-pix_fmt yuv420p \
-g 25 \
-keyint_min 25 \
-sc_threshold 0 \
-b:v 800k \
-maxrate 800k \
-bufsize 1600k \
-c:a libopus \
-b:a 96k \
-ar 48000 \
-ac 2 \
-f rtsp \
rtsp://localhost:8554/live/webrtc-test
```

---

# Acceso desde navegador

Una vez publicado el flujo RTSP, MediaMTX genera automáticamente el
endpoint WebRTC correspondiente.

```
http://SERVIDOR:8889/live/webrtc-test/
```

Ejemplo utilizado durante la validación.

```
http://192.168.33.239:8889/live/webrtc-test/
```

---

# Verificación del servicio

El funcionamiento del servicio puede verificarse mediante las siguientes
herramientas de administración.

- scripts/maintenance/webrtc-status.sh
- systemctl status mediamtx
- journalctl -u mediamtx
- ss -lntup
- tcpdump

---

# Validación realizada

Durante la MISSION-015 se verificó satisfactoriamente:

- Inicio correcto del servicio MediaMTX.
- Activación del listener HTTP para WebRTC.
- Activación del listener ICE sobre UDP.
- Publicación RTSP mediante FFmpeg.
- Conversión automática RTSP hacia WebRTC.
- Negociación ICE.
- Establecimiento de Peer Connection.
- Recepción de video H.264.
- Recepción de audio Opus.
- Reproducción desde navegador compatible.
- Ejecución satisfactoria del script `scripts/maintenance/webrtc-status.sh`.

---

# Evidencia técnica

Los registros del servidor confirmaron el establecimiento correcto de la
sesión WebRTC.

```
peer connection established

local candidate:
host/udp/127.0.0.1/8189

remote candidate:
prflx/udp/192.168.33.239/45075

is reading from path 'live/webrtc-test'

2 tracks (H264, Opus)
```

Estos mensajes confirman que:

- la negociación ICE fue completada correctamente;
- la conexión Peer-to-Peer fue establecida;
- MediaMTX inició la transmisión del flujo multimedia;
- el navegador comenzó la recepción del contenido audiovisual.

---

# Validación de red

Como parte del proceso de validación se verificó el correcto funcionamiento
de la infraestructura de red mediante las siguientes pruebas.

- Verificación del listener HTTP sobre el puerto 8889.
- Verificación del listener ICE sobre UDP en el puerto 8189.
- Captura de tráfico mediante tcpdump.
- Confirmación del intercambio bidireccional de paquetes ICE.
- Confirmación del establecimiento de la Peer Connection.
- Validación del flujo multimedia utilizando HLS como mecanismo de referencia.

Estas pruebas permitieron descartar problemas de conectividad,
configuración del firewall o publicación del flujo multimedia.

---

# Compatibilidad

La implementación es compatible con navegadores que soportan WebRTC.

- Google Chrome
- Microsoft Edge
- Mozilla Firefox

---

# Dependencias

La implementación requiere.

- Ubuntu Server 24.04.4 LTS
- MediaMTX v1.19.2
- FFmpeg 6.1.1

---

# Historial de ingeniería

## Implementación inicial

La implementación comenzó utilizando MediaMTX v1.19.0 manteniendo la
arquitectura previamente validada para los servicios RTSP, RTMP, SRT y HLS.

El servicio iniciaba correctamente y aceptaba conexiones WebRTC; sin
embargo, todas las sesiones finalizaban durante la negociación ICE.

Los registros mostraban repetidamente.

```
closed: deadline exceeded while waiting connection
```

## Proceso de diagnóstico

Con el objetivo de identificar la causa del problema se realizaron las
siguientes verificaciones.

- Configuración WebRTC.
- Publicación RTSP mediante FFmpeg.
- Compatibilidad de codecs.
- Conversión del audio hacia Opus.
- Funcionamiento del servicio HLS.
- Captura de tráfico ICE mediante tcpdump.
- Verificación de puertos utilizando ss.
- Revisión de registros mediante journalctl.
- Validación del firewall UFW.

Las pruebas permitieron comprobar que:

- el flujo multimedia era válido;
- la infraestructura de red operaba correctamente;
- la negociación ICE intercambiaba tráfico entre cliente y servidor;
- el problema no correspondía a la configuración implementada.

## Decisión de ingeniería

Una vez descartadas las posibles causas relacionadas con la red,
configuración y publicación multimedia, se decidió actualizar MediaMTX
desde la versión 1.19.0 hacia la versión 1.19.2 manteniendo exactamente la
misma configuración del servidor.

Antes de realizar la actualización se generaron respaldos completos tanto
del binario como del archivo de configuración, garantizando la posibilidad
de revertir el cambio en caso necesario.

## Resultado

Después de actualizar MediaMTX a la versión 1.19.2 se obtuvo
correctamente el establecimiento de la conexión WebRTC.

Los registros confirmaron.

```
peer connection established

is reading from path 'live/webrtc-test'

2 tracks (H264, Opus)
```

Con ello quedó validado oficialmente el servicio WebRTC dentro de la
infraestructura de la EJTV Broadcast Platform.

## Lecciones aprendidas

La implementación permitió establecer las siguientes conclusiones.

- HLS constituye un mecanismo útil para validar previamente el flujo multimedia antes de depurar WebRTC.
- tcpdump permitió confirmar el intercambio correcto de paquetes ICE.
- La actualización a MediaMTX v1.19.2 resolvió el problema de interoperabilidad observado durante las pruebas iniciales.
- Mantener respaldos completos antes de cada actualización permitió realizar el proceso de forma segura y completamente reversible.

---

# Troubleshooting

## Pantalla negra

Verificar.

- existencia de un publicador RTSP activo;
- utilización de H.264 y Opus;
- puertos 8889 y 8189 disponibles;
- configuración de `webrtcAdditionalHosts`.

## Deadline exceeded while waiting connection

Generalmente asociado a:

- problemas durante la negociación ICE;
- incompatibilidades de versión de MediaMTX;
- configuración incorrecta de interfaces de red.

## No stream is available

Indica que no existe un publicador RTSP activo sobre el path solicitado.

---

# Estado del servicio

Estado: **IMPLEMENTADO**

Validación: **COMPLETA**

Pruebas: **SUPERADAS**

Versión validada:

**MediaMTX v1.19.2**

**MISSION-015 COMPLETADA**