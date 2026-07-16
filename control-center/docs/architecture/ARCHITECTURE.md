# EJTV Control Center

## Arquitectura del Sistema

**Versión:** 1.0

**Estado:** Diseño Arquitectónico

**Misión:** MISSION-017

---

# 1. Introducción

El EJTV Control Center constituye la capa de administración de la EJTV Broadcast Platform.

Su propósito es proporcionar una consola centralizada para la operación, supervisión, configuración y administración de todos los servicios que conforman la plataforma.

El operador no interactúa directamente con Linux, MediaMTX o FFmpeg.

Toda interacción se realiza a través del Control Center.

---

# 2. Objetivos

El Control Center permitirá administrar desde una única interfaz:

- Canales
- Clientes
- Usuarios
- Servicios
- Protocolos
- Alarmas
- Configuración
- Seguridad
- Reportes
- Logs
- Estado general de la plataforma

---

# 3. Filosofía del Proyecto

La infraestructura debe ser invisible para el operador.

Linux continúa siendo el sistema operativo.

MediaMTX continúa siendo el motor multimedia.

FFmpeg continúa siendo el motor de procesamiento.

Sin embargo, todas las operaciones habituales deberán realizarse desde el Control Center.

La terminal Linux quedará reservada para:

- instalación
- mantenimiento avanzado
- recuperación ante fallos
- desarrollo

---

# 4. Arquitectura General

```
                    EJTV Control Center

                     Web Interface

────────────────────────────────────────────

 Dashboard

 Channels

 Clients

 Services

 Monitoring

 Reports

 Security

 Configuration

 Users

 Logs

────────────────────────────────────────────

 REST API

────────────────────────────────────────────

 Backend

────────────────────────────────────────────

 MediaMTX

 FFmpeg

 Linux

 Firewall

 Cockpit

 NTP

────────────────────────────────────────────

 Hardware
```

---

# 5. Arquitectura Backend

El backend será desarrollado utilizando Python y FastAPI.

Su responsabilidad será:

- exponer la API REST
- administrar autenticación
- controlar permisos
- ejecutar tareas del sistema
- consultar MediaMTX
- consultar FFmpeg
- administrar usuarios
- generar auditoría
- administrar configuraciones

Estructura:

```
backend/

api/

auth/

audit/

monitoring/

services/

system/
```

---

# 6. Arquitectura Frontend

El frontend será una aplicación web modular.

Cada módulo representará una función operativa independiente.

```
frontend/

dashboard/

channels/

clients/

services/

monitoring/

users/

configuration/

reports/

security/

logs/
```

Cada módulo tendrá su propia interfaz y utilizará exclusivamente la API del backend.

---

# 7. Modelo Operativo

El operador administrará entidades funcionales.

No administrará procesos Linux.

Por ejemplo:

Canal ENLACE

↓

Iniciar

Detener

Reiniciar

Editar

Ver estadísticas

El backend será responsable de traducir dichas acciones hacia los servicios correspondientes del sistema operativo.

---

# 8. Principios de Desarrollo

El Control Center seguirá los siguientes principios:

• Arquitectura modular.

• Separación entre frontend y backend.

• API REST como único mecanismo de comunicación.

• Seguridad desde el diseño.

• Escalabilidad horizontal.

• Documentación obligatoria.

• Pruebas de validación para cada módulo.

---

# 9. Escalabilidad

La arquitectura deberá soportar el crecimiento de la plataforma sin modificaciones estructurales.

Ejemplos:

2 canales

↓

20 canales

↓

100 canales

o

5 clientes

↓

500 clientes

sin necesidad de rediseñar el sistema.

---

# 10. Seguridad

Todas las operaciones deberán quedar registradas mediante auditoría.

Se implementarán niveles de acceso basados en roles.

El operador únicamente visualizará las funciones autorizadas para su perfil.

---

# 11. Futuras Integraciones

La arquitectura contempla la incorporación de nuevos componentes sin afectar la operación existente.

Entre ellos:

- Docker
- Kubernetes
- PostgreSQL
- LDAP
- Active Directory
- Prometheus
- Grafana
- SNMP
- Sistemas de notificación

---

# 12. Estado de Implementación

| Módulo | Estado |
|---------|--------|
| Arquitectura | ✅ |
| Backend | ⏳ |
| Frontend | ⏳ |
| API REST | ⏳ |
| Dashboard | ⏳ |
| Usuarios | ⏳ |
| Canales | ⏳ |
| Servicios | ⏳ |
| Monitoreo | ⏳ |
| Reportes | ⏳ |

---

# 13. Próximas Misiones

MISSION-018

Backend FastAPI

MISSION-019

Frontend Web

MISSION-020

Integración con la plataforma multimedia