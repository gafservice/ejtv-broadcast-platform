# MISSION-010

## Implementación del Servidor de Streaming MediaMTX

**Misión:** MISSION-010

**Estado:** Completada

**Fecha:** 2026-06-29

**Responsable:** Gerardo Araya Fallas

**Plataforma:** EJTV Broadcast Platform

---

# 1. Objetivo

Implementar el servidor de streaming **MediaMTX** como plataforma central de distribución multimedia de la arquitectura EJTV, utilizando una instalación nativa sobre Ubuntu Server, integrándolo con **systemd**, verificando la autenticidad del software mediante SHA256 y documentando completamente el procedimiento de instalación, validación y mantenimiento.

---

# 2. Alcance

La presente misión comprendió la instalación completa del servidor **MediaMTX v1.19.0** utilizando el binario oficial distribuido por el proyecto.

La implementación incluyó:

* Diagnóstico del entorno de ejecución.
* Diseño de la estructura de directorios.
* Descarga del software desde el repositorio oficial.
* Verificación de integridad mediante SHA256.
* Extracción del binario.
* Instalación en la estructura definitiva de la plataforma EJTV.
* Registro de la versión instalada.
* Configuración inicial.
* Creación del servicio `systemd`.
* Validación funcional.
* Registro documental completo.

No se realizaron modificaciones al código fuente de MediaMTX ni a su configuración por defecto durante esta misión.

---

# 3. Diagnóstico inicial

Antes de iniciar la instalación se verificó el estado general del servidor.

## Sistema operativo

```
Ubuntu Server 24.04.4 LTS
```

## Kernel

```
Linux 6.17.0-35-generic
```

## Arquitectura

```
x86_64
```

## Hardware

```
Apple MacPro5,1

Intel Xeon W3530

7.7 GB RAM
```

## Espacio disponible

```
422 GB libres
```

## Estado inicial

Durante el diagnóstico se verificó que:

* MediaMTX no se encontraba instalado.
* No existía ningún servicio systemd asociado.
* No existían procesos ejecutándose.
* No existían conflictos de puertos.
* Docker no estaba instalado.
* Podman no estaba instalado.

El entorno fue considerado apto para iniciar la instalación.

---

# 4. Decisiones de ingeniería

Durante la planificación de la misión se adoptaron las siguientes decisiones.

## Instalación nativa

Se descartó la utilización de Docker debido a que el objetivo principal del proyecto es construir una plataforma administrable directamente desde Ubuntu.

La instalación nativa facilita:

* facilitar el mantenimiento del sistema;
* simplificar las tareas de diagnóstico;
* reducir dependencias externas;
* minimizar el consumo de recursos;
* mantener un mayor control sobre las actualizaciones del servicio.

## Estructura de directorios

Se decidió separar claramente el software instalado, la configuración, los registros y las futuras grabaciones utilizando la siguiente estructura:

```
/opt/ejtv/mediamtx/

├── backup/
├── bin/
├── config/
├── logs/
├── recordings/
├── releases/
├── scripts/
└── tests/
```

Esta organización permite mantener una arquitectura ordenada, facilita la actualización del software y evita modificar directamente los archivos originales descargados.

## Conservación de versiones

Cada versión descargada permanece almacenada dentro del directorio:

```
/opt/ejtv/mediamtx/releases
```

Esto permite realizar procedimientos de actualización o recuperación sin necesidad de descargar nuevamente el software.

## Integración con systemd

MediaMTX fue integrado mediante un servicio nativo de **systemd** para garantizar:

* inicio automático durante el arranque del sistema;
* supervisión permanente del proceso;
* reinicio automático ante fallos;
* integración con el registro del sistema mediante `journalctl`;
* administración unificada junto con el resto de servicios de Ubuntu.

---

# 5. Implementación

La implementación se desarrolló en varias etapas.

## 5.1 Creación de la estructura base

Se creó previamente la estructura definitiva de la plataforma.

Comandos ejecutados:

```bash
sudo mkdir -p /opt/ejtv/mediamtx
sudo mkdir -p /opt/ejtv/mediamtx/bin
sudo mkdir -p /opt/ejtv/mediamtx/config
sudo mkdir -p /opt/ejtv/mediamtx/releases
sudo mkdir -p /opt/ejtv/mediamtx/logs
sudo mkdir -p /opt/ejtv/mediamtx/recordings
sudo mkdir -p /opt/ejtv/mediamtx/backup
sudo mkdir -p /opt/ejtv/mediamtx/scripts
sudo mkdir -p /opt/ejtv/mediamtx/tests

sudo chown -R ejtv:ejtv /opt/ejtv
```

Posteriormente se verificó la estructura mediante:

```bash
tree -L 3 /opt/ejtv
```

---

## 5.2 Descarga del software

La descarga se realizó exclusivamente desde el repositorio oficial del proyecto.

Comandos utilizados:

```bash
cd /opt/ejtv/mediamtx/releases

MEDIAMTX_VERSION="v1.19.0"

MEDIAMTX_FILE="mediamtx_${MEDIAMTX_VERSION}_linux_amd64.tar.gz"

wget "https://github.com/bluenviron/mediamtx/releases/download/${MEDIAMTX_VERSION}/${MEDIAMTX_FILE}"

wget "https://github.com/bluenviron/mediamtx/releases/download/${MEDIAMTX_VERSION}/checksums.sha256"
```

Una vez completada la descarga se verificó la presencia de ambos archivos mediante:

```bash
ls -lah
```

---

## 5.3 Verificación de integridad

Antes de instalar el software se verificó la autenticidad del archivo descargado.

Inicialmente se revisó el contenido del archivo de firmas:

```bash
cat checksums.sha256
```

Posteriormente se validó únicamente el archivo correspondiente a la arquitectura instalada:

```bash
grep "mediamtx_v1.19.0_linux_amd64.tar.gz" checksums.sha256 | sha256sum -c -
```

Resultado esperado:

```
mediamtx_v1.19.0_linux_amd64.tar.gz: OK
```

Finalmente se verificó manualmente el hash obtenido:

```bash
sha256sum mediamtx_v1.19.0_linux_amd64.tar.gz
```

Checksum registrado:

```
ee900a73d78919a44f995e04d65588f1cea10ddb43ebf1c740f2c6c4fa0c29b0
```

La coincidencia entre ambos valores confirmó la integridad del binario descargado.

---

## 5.4 Extracción

El paquete fue extraído dentro del directorio de versiones.

Comandos utilizados:

```bash
mkdir -p v1.19.0

tar -xzf mediamtx_v1.19.0_linux_amd64.tar.gz -C v1.19.0
```

Posteriormente se verificó el contenido:

```bash
ls -lah v1.19.0
```

Y la arquitectura del ejecutable:

```bash
file v1.19.0/mediamtx
```

Resultado:

```
ELF 64-bit
x86_64
Statically linked
```

Lo anterior confirmó que el binario correspondía exactamente a la arquitectura del servidor Ubuntu utilizado por la plataforma EJTV.

*## 5.5 Instalación del software

Una vez verificada la integridad del binario y completada la extracción del paquete, se procedió a instalar MediaMTX dentro de la estructura definitiva de la plataforma EJTV.

El ejecutable fue copiado al directorio destinado para los binarios de producción y se asignaron los permisos de ejecución correspondientes.

Asimismo, el archivo de configuración por defecto fue ubicado dentro del directorio de configuración, manteniendo separadas las áreas destinadas al software, configuración y versiones descargadas.

Comandos ejecutados:

```bash
cd /opt/ejtv/mediamtx

cp releases/v1.19.0/mediamtx bin/mediamtx

chmod 755 bin/mediamtx

cp releases/v1.19.0/mediamtx.yml config/mediamtx.yml
```

Posteriormente se verificó la estructura completa del directorio mediante:

```bash
tree -L 3 /opt/ejtv/mediamtx
```

La organización adoptada permite actualizar futuras versiones sin sobrescribir las anteriores y facilita la recuperación ante cualquier eventualidad.

---

## 5.6 Registro de la versión instalada

Como parte de la política de trazabilidad de la plataforma EJTV se implementó un registro permanente de las versiones instaladas.

Este registro se almacena en:

```
/opt/ejtv/mediamtx/releases/installed_versions.log
```

El archivo contiene la siguiente información:

- Fecha de instalación.
- Componente instalado.
- Versión.
- Arquitectura.
- Hash SHA256.
- Método de instalación.
- Misión responsable de la instalación.
- Estado operativo.

El contenido registrado fue:

```text
2026-06-29
Component: MediaMTX
Version: v1.19.0
Architecture: linux_amd64
SHA256: ee900a73d78919a44f995e04d65588f1cea10ddb43ebf1c740f2c6c4fa0c29b0
Install method: official binary release
Installed by: MISSION-010
Status: installed
```

Este mecanismo facilitará futuras auditorías, procesos de actualización y procedimientos de recuperación.

---

## 5.7 Prueba manual del servidor

Antes de integrar MediaMTX como un servicio permanente del sistema se realizó una ejecución manual con el objetivo de verificar el correcto funcionamiento del binario y de la configuración instalada.

Comando utilizado:

```bash
cd /opt/ejtv/mediamtx

./bin/mediamtx config/mediamtx.yml
```

Durante la ejecución se verificó que el servidor cargara correctamente el archivo de configuración y habilitara todos los protocolos soportados.

Los mensajes observados indicaron la activación de los siguientes servicios:

- RTSP
- RTMP
- HLS
- WebRTC
- SRT
- MoQ

Asimismo, se verificó la apertura de los puertos asociados a cada protocolo y la ausencia de errores durante la inicialización.

Finalmente, el servidor fue detenido manualmente mediante:

```
CTRL + C
```

confirmándose un cierre ordenado de todos los servicios activos.

---

## 5.8 Integración con systemd

Con el objetivo de administrar MediaMTX como un servicio nativo del sistema operativo, se creó la unidad correspondiente para **systemd**.

Archivo creado:

```
/etc/systemd/system/mediamtx.service
```

Contenido:

```ini
[Unit]
Description=MediaMTX streaming server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ejtv
Group=ejtv
WorkingDirectory=/opt/ejtv/mediamtx
ExecStart=/opt/ejtv/mediamtx/bin/mediamtx /opt/ejtv/mediamtx/config/mediamtx.yml
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Posteriormente se ejecutaron los siguientes comandos:

```bash
sudo systemctl daemon-reload

sudo systemctl enable mediamtx

sudo systemctl start mediamtx
```

Con ello MediaMTX quedó integrado al proceso de arranque del sistema operativo.

---

# 6. Resultados obtenidos

La implementación concluyó satisfactoriamente.

Los principales resultados fueron los siguientes:

| Elemento | Estado |
|----------|--------|
| Descarga del software | Correcta |
| Verificación SHA256 | Correcta |
| Extracción del paquete | Correcta |
| Instalación | Correcta |
| Configuración inicial | Correcta |
| Servicio systemd | Operativo |
| Inicio automático | Habilitado |
| Validación funcional | Correcta |

Durante toda la implementación no se registraron fallos que comprometieran la instalación del servicio.

---

# 7. Evidencias

Las evidencias obtenidas durante la misión permitieron confirmar que:

- MediaMTX inició correctamente.
- El archivo de configuración fue cargado sin errores.
- El servicio quedó registrado dentro de systemd.
- El proceso permaneció estable durante las pruebas.
- El inicio automático quedó habilitado.
- Todos los protocolos principales fueron inicializados correctamente.

Los puertos habilitados por defecto fueron:

| Servicio | Puerto |
|----------|---------|
| RTSP | 8554 |
| RTP | 8000 |
| RTCP | 8001 |
| RTMP | 1935 |
| HLS | 8888 |
| WebRTC | 8889 |
| WebRTC ICE | 8189 |
| SRT | 8890 |
| MoQ | 8892 |

---

# 8. Validación

La validación del servicio se realizó mediante las herramientas propias del sistema operativo.

Comandos utilizados:

```bash
systemctl status mediamtx

systemctl is-enabled mediamtx

ps -ef | grep mediamtx

ss -tuln

journalctl -u mediamtx

tree -L 3 /opt/ejtv/mediamtx

cat /opt/ejtv/mediamtx/releases/installed_versions.log
```

Las verificaciones confirmaron:

- Servicio activo.
- Inicio automático habilitado.
- Proceso ejecutándose.
- Puertos abiertos correctamente.
- Configuración cargada.
- Registro de versión creado.

---

# 9. Lecciones aprendidas

La implementación permitió establecer varios lineamientos que serán adoptados para futuras instalaciones dentro de la plataforma EJTV.

Entre los aspectos más relevantes destacan:

- Toda instalación deberá validar previamente la integridad del software mediante SHA256.
- Se conservarán todas las versiones descargadas para facilitar procesos de actualización y recuperación.
- Los binarios, archivos de configuración y registros permanecerán separados en directorios independientes.
- Todos los servicios deberán integrarse mediante systemd.
- Cada misión deberá documentar completamente el procedimiento realizado para garantizar la reproducibilidad del sistema.

---

# 10. Pendientes

Durante la presente misión quedaron identificadas las siguientes actividades para etapas posteriores:

- Personalizar el archivo `mediamtx.yml` de acuerdo con la arquitectura definitiva de la plataforma.
- Definir la política de puertos para producción.
- Integrar OBS Studio como fuente de transmisión.
- Implementar pruebas utilizando FFmpeg.
- Configurar políticas definitivas del firewall.
- Implementar scripts automáticos de monitoreo y diagnóstico.
- Evaluar futuras actualizaciones del servidor MediaMTX.

---

# 11. Conclusiones

La misión permitió integrar exitosamente **MediaMTX v1.19.0** dentro de la plataforma EJTV Broadcast Platform utilizando una instalación nativa sobre Ubuntu Server.

El servidor quedó completamente funcional, integrado con **systemd**, preparado para iniciar automáticamente durante el arranque del sistema y documentado de manera que cualquier administrador pueda reproducir el procedimiento completo de instalación, validación y mantenimiento.

Esta implementación constituye la base de la infraestructura de transmisión multimedia del proyecto y habilita el desarrollo de las siguientes etapas relacionadas con la distribución de contenidos mediante RTSP, RTMP, HLS, WebRTC, SRT y otros protocolos soportados por MediaMTX.


