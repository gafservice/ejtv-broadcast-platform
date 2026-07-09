# OBS Studio

## Objetivo

Utilizar OBS Studio como codificador de video para publicar señales en la plataforma EJTV Broadcast Platform mediante RTMP.

---

## Configuración

### Stream

Servicio:

Custom

Servidor:

rtmp://192.168.33.239/live

Stream Key:

obs-local

---

## Video

Canvas:

1920x1080

Salida:

1920x1080

FPS:

30

---

## Encoder

Software x264

Rate Control:

CBR

Bitrate:

2500 kbps

Keyframe:

2 segundos

Preset:

veryfast

Profile:

Main

Audio:

AAC
48 kHz
Stereo
160 kbps

---

## Flujo generado

OBS

↓

RTMP

↓

MediaMTX

↓

RTSP
HLS
WebRTC
SRT