# MISSION-009

# Validación del servicio de sincronización horaria (NTP)

---

## Objetivo

Verificar el mecanismo de sincronización horaria implementado en el servidor, validar el estado del reloj del sistema y establecer el servicio oficial de sincronización de tiempo para la plataforma EJTV Broadcast Platform.

---

## Fecha

2026-06-29

---

# Estado inicial

Se realizó un diagnóstico del sistema para determinar el servicio encargado de la sincronización horaria.

Se verificó:

* Sistema Operativo Ubuntu Server 24.04.4 LTS.
* Kernel Linux 6.17.0-35-generic.
* Servicio NTP activo.
* Reloj del sistema sincronizado.
* Zona horaria configurada para Costa Rica.

---

# Diagnóstico

El sistema utiliza como mecanismo de sincronización:

**systemd-timesyncd**

Estado del servicio:

* Activo.
* Habilitado.
* Sin errores.

Servidor NTP utilizado:

```
ntp.ubuntu.com
```

Servidor actualmente seleccionado:

```
185.125.190.58
```

Características observadas:

* Stratum 2.
* Sincronización correcta.
* Jitter aproximado de 2.17 ms.
* Intervalo máximo de sincronización de 34 minutos.

---

# Evaluación técnica

Durante esta misión se evaluó la posibilidad de migrar hacia Chrony.

Después del análisis se determinó que la configuración nativa de Ubuntu satisface completamente los requerimientos de la plataforma.

No se identificaron ventajas operativas que justificaran incorporar un servicio adicional de sincronización.

---

# Decisión

Se adopta oficialmente:

**systemd-timesyncd**

como servicio de sincronización horaria de la plataforma.

No se instalará Chrony mientras la arquitectura del proyecto continúe utilizando un único servidor con sincronización mediante servidores públicos NTP.

---

# Validación

Se verificó correctamente:

* Servicio activo.
* Sincronización del reloj.
* Zona horaria.
* Servidor NTP.
* Estado del sistema.
* Integración con systemd.

No fue necesario realizar modificaciones adicionales.

---

# Resultado

MISSION-009 finalizada satisfactoriamente.

El servicio nativo de sincronización horaria de Ubuntu queda incorporado como parte de la línea base oficial de la plataforma.
