# TEST-OBS

## Objetivo

Validar OBS Studio como fuente de publicación RTMP.

---

## Configuración utilizada

Resolución:

1920x1080

FPS:

30

Codec:

H264 Main

Audio:

AAC

Bitrate:

2500 kbps

---

## Resultados

RTMP

✅ Correcto

RTSP

⚠ Correcto localmente.

Pendiente habilitar 8554/TCP en UFW para acceso remoto.

HLS

✅ Audio y video correctos.

WebRTC

⚠ Video correcto.

Audio pendiente.

SRT

✅ Audio y video correctos.

---

## Conclusión

OBS Studio puede utilizarse como codificador oficial de la plataforma EJTV Broadcast Platform.