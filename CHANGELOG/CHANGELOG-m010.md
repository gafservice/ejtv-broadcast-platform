# Changelog

Todos los cambios relevantes realizados sobre la plataforma **EJTV Broadcast Platform** serán registrados en este documento.

El formato utilizado está basado en **Keep a Changelog**, adaptado a las necesidades del proyecto.

---

## [2026-06-26]

### Added

#### Documentación

* Se incorporó la documentación de la **MISSION-007**, correspondiente a la instalación y validación de Cockpit.
* Se incorporó la documentación de la **MISSION-008**, correspondiente a la implementación del firewall UFW.
* Se creó el documento técnico `docs/network/firewall.md`.
* Se creó el documento técnico `docs/network/ports.md`.
* Se actualizó `docs/security/hardening.md`.
* Se actualizó `docs/services/cockpit.md`.
* Se actualizó `BL-004.md` con la línea base oficial de seguridad de red.
* Se actualizó `BL-005.md` incorporando Cockpit como servicio base del servidor.

### Infrastructure

* Se instaló Cockpit como plataforma oficial de administración web.
* Se habilitó el acceso HTTPS mediante el puerto TCP 9090.
* Se verificó la integración de Cockpit con systemd mediante Socket Activation.
* Se validó el acceso administrativo utilizando autenticación PAM y elevación de privilegios mediante sudo.

### Security

* Se implementó UFW como firewall oficial de la plataforma.
* Se adoptó una política **Default Deny** para conexiones entrantes.
* Se configuró la política **Allow Outgoing** para tráfico saliente.
* Se restringió el reenvío de paquetes (Forward Policy: DENY).
* Se autorizó únicamente el acceso a los servicios SSH (22/TCP) y Cockpit (9090/TCP).
* Se verificó la correcta integración de UFW con Netfilter.

### Validation

Se verificó satisfactoriamente:

* Instalación de Cockpit.
* Estado del servicio mediante systemd.
* Activación del socket `cockpit.socket`.
* Acceso HTTPS al puerto 9090.
* Configuración efectiva del firewall.
* Reglas IPv4 e IPv6.
* Disponibilidad de SSH después de la activación del firewall.
* Disponibilidad de Cockpit después de la activación del firewall.

### Notes

Durante la implementación se detectó un incidente relacionado con el controlador **Broadcom BCM4322**, el cual quedó documentado en `INC-001.md`. Dado que la plataforma operará mediante interfaces Ethernet, se decidió conservar el hardware inalámbrico instalado y posponer su reparación para una etapa posterior, sin afectar la operación del servidor.


## [2026-06-29]

### Added

#### Infraestructura

* Se validó el servicio de sincronización horaria del servidor.
* Se adoptó **systemd-timesyncd** como servicio oficial de sincronización NTP.
* Se documentó el servicio de sincronización horaria.
* Se actualizó la línea base del sistema con la configuración oficial de NTP.

### Validation

* Se verificó la correcta sincronización del reloj del sistema.
* Se validó la integración con systemd.
* Se confirmó el uso de los servidores oficiales `ntp.ubuntu.com`.
* Se verificó el estado de sincronización y la zona horaria configurada.

### Decisions

* Se evaluó la migración hacia Chrony.
* Se decidió mantener la implementación nativa de Ubuntu mediante **systemd-timesyncd**, al cumplir plenamente los requisitos técnicos de la plataforma y evitar complejidad innecesaria.



# CHANGELOG

Todos los cambios importantes realizados sobre la plataforma **EJTV Broadcast Platform** se registran en este documento siguiendo un criterio cronológico.

---

# 2026-06-29

## MISSION-010 — Implementación del servidor MediaMTX

### Estado

**Completada**

---

### Nuevas funcionalidades

* Se incorporó **MediaMTX v1.19.0** como servidor multimedia oficial de la plataforma.
* Se adoptó una instalación nativa utilizando el binario oficial para Linux AMD64.
* Se estableció una estructura permanente de instalación bajo:

```text
/opt/ejtv/mediamtx
```

* Se separaron los directorios para:

  * binarios;
  * configuración;
  * registros;
  * grabaciones;
  * respaldos;
  * versiones descargadas;
  * scripts;
  * pruebas.

---

### Seguridad

* Se verificó la integridad del software mediante SHA256.
* Se registró el hash oficial del binario instalado.
* Se documentó el procedimiento de validación de integridad.

---

### Configuración

* Se instaló el archivo oficial:

```text
config/mediamtx.yml
```

* Se mantuvo la configuración distribuida por el proyecto MediaMTX sin modificaciones funcionales.

---

### Gestión de versiones

Se implementó el archivo:

```text
releases/installed_versions.log
```

El registro almacena:

* fecha de instalación;
* componente;
* versión;
* arquitectura;
* SHA256;
* método de instalación;
* misión responsable;
* estado operativo.

---

### Servicio del sistema

Se creó el servicio:

```text
/etc/systemd/system/mediamtx.service
```

Características implementadas:

* inicio automático durante el arranque;
* ejecución mediante el usuario `ejtv`;
* reinicio automático ante fallos (`Restart=on-failure`);
* integración con `systemd`;
* registro de eventos mediante `journalctl`.

---

### Protocolos habilitados

Durante la instalación quedaron disponibles los siguientes protocolos:

* RTSP
* RTMP
* HLS
* WebRTC
* SRT
* MoQ

---

### Puertos habilitados

| Puerto | Servicio |
| ------ | -------- |
| 8554   | RTSP     |
| 8000   | RTP      |
| 8001   | RTCP     |
| 1935   | RTMP     |
| 8888   | HLS      |
| 8889   | WebRTC   |
| 8189   | ICE      |
| 8890   | SRT      |
| 8892   | MoQ      |

---

### Validaciones realizadas

Se verificó correctamente:

* descarga del software;
* autenticidad mediante SHA256;
* extracción del paquete;
* instalación del binario;
* instalación del archivo de configuración;
* ejecución manual del servidor;
* funcionamiento de todos los protocolos;
* creación del servicio `systemd`;
* habilitación para inicio automático;
* apertura de puertos;
* funcionamiento estable del servicio;
* registro de la versión instalada.

---

### Documentación generada

Se incorporó la siguiente documentación al repositorio:

* `docs/services/mediamtx.md`
* `docs/missions/MISSION-010.md`
* actualización de `docs/baseline/BL-005.md`
* actualización de `docs/network/ports.md`
* actualización de `docs/network/firewall.md`

---

### Scripts incorporados

Se incorporó: script de mantenimiento:

```text
scripts/maintenance/mediamtx-status.sh
```

como herramienta oficial para diagnóstico del servicio.

---

### Resultado

MediaMTX quedó completamente integrado dentro de la plataforma EJTV Broadcast Platform, funcionando como servidor multimedia principal y preparado para las siguientes etapas de desarrollo relacionadas con transmisión, grabación y distribución de contenidos audiovisuales.
