# SPRINT-003

# CHANGELOG

---

# Versión

1.0

---

# Fecha

2026-07-16

---

# Estado

Completado

---

# Objetivo

Registrar los cambios incorporados durante el Sprint-003 de la
MISSION-018 correspondiente a la capacidad **System Resources**.

---

# Nuevas capacidades

## Dominio

Se incorporaron los modelos del dominio:

- CPUInfo
- MemoryInfo
- DiskInfo
- UptimeInfo
- SystemResources

---

## Contrato del adaptador

Se amplió el contrato **SystemAdapter** con los métodos:

- cpu_info()
- memory_info()
- disk_info()
- uptime_info()

---

## Adaptador Linux

Se implementó la obtención de información real utilizando **psutil**.

Información disponible:

- uso del procesador;
- núcleos físicos;
- núcleos lógicos;
- frecuencia actual;
- memoria;
- almacenamiento;
- uptime.

---

## Servicio

Se incorporó:

```text
SystemService.get_system_resources()
```

El servicio consolida la información del adaptador y construye
el objeto de dominio **SystemResources**.

---

## API REST

Nuevo endpoint:

```text
GET /api/v1/system/resources
```

El endpoint publica información real del servidor mediante
la respuesta estándar de la API.

---

## Dependencias

Se agregó:

```text
psutil
```

como dependencia oficial del backend.

---

## Pruebas

Se incorporaron nuevas pruebas para:

- dominio;
- adaptador Linux;
- servicio;
- endpoint REST.

Resultado final:

```text
46 pruebas aprobadas

0 fallos

1 advertencia no bloqueante
```

---

# Validación

La implementación fue validada mediante:

- pruebas automatizadas;
- pruebas de integración;
- consultas reales utilizando curl.

---

# Compatibilidad

No se introdujeron cambios incompatibles.

El endpoint:

```text
GET /api/v1/system/info
```

continúa funcionando sin modificaciones.

---

# Resultado

El Sprint-003 deja incorporada la capacidad permanente
**System Resources**, constituyendo el segundo bloque funcional
del EJTV Control Center.

---

# Responsable

Proyecto EJTV Broadcast Platform

MISSION-018

EJTV Control Center

---