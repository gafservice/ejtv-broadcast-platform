# Servicio de Sincronización Horaria (NTP)

## Descripción

La plataforma EJTV Broadcast Platform utiliza el servicio **systemd-timesyncd** como mecanismo oficial para la sincronización horaria del sistema operativo.

Este servicio mantiene sincronizado el reloj del servidor utilizando el protocolo **Network Time Protocol (NTP)** y los servidores oficiales de Ubuntu.

---

# Objetivo

Garantizar que:

* los registros del sistema posean marcas de tiempo coherentes;
* los servicios de streaming utilicen una referencia temporal consistente;
* las operaciones administrativas dispongan de una hora confiable;
* futuras implementaciones de certificados TLS y auditorías funcionen correctamente.

---

# Servicio utilizado

Servicio:

```
systemd-timesyncd
```

Administrador:

```
systemd
```

Estado:

Activo y habilitado.

---

# Configuración actual

Servidor utilizado:

```
ntp.ubuntu.com
```

Zona horaria:

```
America/Costa_Rica
```

UTC:

Sí.

RTC:

UTC.

---

# Razones para utilizar systemd-timesyncd

Después de evaluar Chrony y ntpd se decidió mantener la implementación nativa de Ubuntu debido a:

* menor complejidad;
* integración con systemd;
* mantenimiento reducido;
* sincronización suficiente para los requerimientos de la plataforma;
* ausencia de infraestructura NTP propia.

# Referencia temporal de la plataforma

La plataforma **EJTV Broadcast Platform** utiliza como referencia temporal única el reloj del sistema operativo (System Clock) mantenido por Linux y sincronizado mediante el servicio nativo **systemd-timesyncd**.

Todos los componentes del sistema utilizan esta misma referencia temporal, incluyendo:

- MediaMTX;
- FFmpeg;
- servicios administrados por systemd;
- scripts de mantenimiento;
- registros del sistema (logs);
- futuras aplicaciones que formen parte de la plataforma.

Por esta razón, no fue necesario desarrollar ni incorporar un mecanismo propio para la administración del tiempo o la sincronización horaria, aprovechando la infraestructura nativa proporcionada por Ubuntu Server.

Esta decisión reduce la complejidad de la plataforma, facilita el mantenimiento y garantiza que todos los componentes compartan una referencia temporal única y consistente.


# Validación

Consultar estado

```bash
timedatectl
```

Estado detallado

```bash
timedatectl status
```

Información del servidor

```bash
timedatectl show-timesync
```

Estado del servicio

```bash
systemctl status systemd-timesyncd
```

---

# Criterios de operación

El servicio deberá mantenerse:

* activo;
* habilitado;
* sincronizado;
* utilizando servidores NTP confiables.

---

# Buenas prácticas

* No instalar múltiples servicios NTP simultáneamente.
* Mantener una única fuente oficial de sincronización.
* Verificar el estado del servicio después de actualizaciones importantes.
* Documentar cualquier modificación de servidores NTP.

---

# Documentos relacionados

* MISSION-009.md
* BL-003.md
* docs/security/hardening.md
* CHANGELOG.md
