# SPRINT-005

# MediaMTX Path Monitoring

---

# Estado

**En desarrollo**

---

# Versión

**1.0**

---

# Fecha

Julio 2026

---

# Misión

**MISSION-018 — Control Center**

---

# Introducción

El Sprint-005 incorpora el monitoreo interno de MediaMTX dentro del
Control Center.

Hasta el Sprint-004, la plataforma podía determinar si el servicio
MediaMTX se encontraba activo en el sistema operativo, así como consultar
información básica del proceso, entre ella:

- PID;
- utilización de CPU;
- memoria utilizada;
- tiempo de ejecución;
- estado del servicio.

Sin embargo, conocer que MediaMTX está ejecutándose no permite determinar
si los canales administrados por el servidor multimedia están realmente
operativos.

Este sprint amplía el alcance del monitoreo para consultar directamente
la API de MediaMTX y obtener información sobre los `paths`, productores,
lectores y conexiones activas.

---

# Contexto

MediaMTX organiza los flujos multimedia mediante `paths`.

Cada `path` representa un punto lógico de publicación y distribución de
contenido.

Ejemplos:

```text
enlace
canal-principal
canal-backup
iglesia
municipalidad
cliente-01