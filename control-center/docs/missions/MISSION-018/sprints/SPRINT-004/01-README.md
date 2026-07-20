# SPRINT-004

# Monitoreo de Servicios del Sistema

---

# Estado

**Completado**

---

# Versión

**1.0**

---

# Fecha

Julio 2026

---

# Introducción

El cuarto sprint de la MISSION-018 incorpora la primera capacidad de
monitoreo operativo del Control Center.

Hasta el Sprint-003 la plataforma era capaz de consultar información del
servidor, como identidad, utilización de CPU, memoria, disco y tiempo de
funcionamiento.

Con este sprint el sistema evoluciona hacia un centro de administración,
permitiendo conocer el estado de los servicios críticos que soportan la
plataforma de distribución multimedia.

La información obtenida proviene tanto de servicios administrados por
systemd como de procesos ejecutados directamente por el sistema
operativo.

---

# Objetivo del Sprint

Incorporar una arquitectura de monitoreo de servicios que permita
consultar el estado operativo de los componentes principales del
servidor mediante una interfaz uniforme expuesta por la API REST.

---

# Alcance

Durante este sprint se implementó:

- Modelo de dominio para servicios monitoreados.
- Modelo para instancias de procesos.
- Modelo para capturas de monitoreo.
- Estados normalizados de operación.
- Adaptador Linux para consultar servicios systemd.
- Adaptador Linux para detectar procesos activos.
- Integración con la capa de servicios.
- Nuevo endpoint REST para monitoreo.
- Pruebas unitarias.
- Validación sobre el servidor real.

---

# Funcionalidad incorporada

El Control Center ahora puede consultar el estado de:

- MediaMTX
- FFmpeg
- Control Center Backend (Uvicorn)

Para cada servicio se obtiene información como:

- Estado operativo.
- PID.
- Uso instantáneo de CPU.
- Memoria utilizada.
- Tiempo de ejecución.
- Cantidad de instancias activas.

---

# Endpoint incorporado

```
GET /api/v1/system/services
```

La respuesta se entrega utilizando el formato estándar definido por la
API del proyecto.

---

# Resultado obtenido

El monitoreo fue validado utilizando el servidor real del proyecto.

Las consultas realizadas confirmaron la correcta detección de:

- Servicios administrados por systemd.
- Procesos de usuario.
- Servicios activos.
- Servicios detenidos.
- Información de múltiples instancias.

---

# Validación

Durante este sprint se ejecutó la totalidad de la batería de pruebas del
backend.

Resultado final:

```
60 passed
```

No se detectaron regresiones sobre funcionalidades implementadas en
sprints anteriores.

---

# Componentes implementados

| Componente | Estado |
|------------|:------:|
| Dominio | ✅ |
| Adaptador Linux | ✅ |
| Servicios | ✅ |
| API REST | ✅ |
| Pruebas | ✅ |
| Validación real | ✅ |

---

# Relación con la misión

Este sprint representa el primer paso hacia el monitoreo integral de la
infraestructura del servidor.

La información obtenida servirá como base para los siguientes módulos del
Control Center, incluyendo monitoreo de canales, clientes, procesos de
transcodificación, alarmas y paneles operativos.

---

# Documento siguiente

**02-OBJECTIVE.md**