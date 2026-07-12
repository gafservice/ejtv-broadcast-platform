# EJTV Control Center

# API REST

**Versión:** 1.0

**Estado:** Diseño

**Misión:** MISSION-017

---

# 1. Introducción

El presente documento define la especificación funcional de la API REST del EJTV Control Center.

La API constituye el único mecanismo autorizado para la comunicación entre el Frontend y el Backend de la plataforma.

Ningún componente del Frontend accederá directamente a MediaMTX, FFmpeg, Linux o cualquier otro servicio de infraestructura.

Toda operación será realizada mediante la API del Control Center.

---

# 2. Filosofía

La API representa el contrato público del sistema.

Su propósito consiste en abstraer la complejidad de la infraestructura y ofrecer una interfaz consistente para todas las operaciones administrativas.

Los cambios internos de la plataforma no deberán afectar la interfaz pública de la API.

---

# 3. Principios de Diseño

La API deberá cumplir los siguientes principios:

• RESTful

• Stateless

• Versionada

• Documentada

• Segura

• Consistente

• Predecible

• Extensible

---

# 4. URL Base

Todas las solicitudes utilizarán una versión explícita.

Ejemplo

/api/v1/

Esto permitirá evolucionar la API sin afectar clientes existentes.

---

# 5. Formato

Todas las solicitudes y respuestas utilizarán JSON.

Ejemplo

Content-Type:

application/json

---

# 6. Autenticación

Todas las operaciones protegidas requerirán autenticación.

La autenticación será administrada por el módulo Security.

Las futuras versiones podrán incorporar:

• JWT

• OAuth2

• OpenID Connect

• LDAP

---

# 7. Recursos Principales

La API administrará inicialmente los siguientes recursos.

Dashboard

Channels

Clients

Users

Roles

Permissions

Services

Protocols

Nodes

Interfaces

Monitoring

Metrics

Alarms

Events

Logs

Reports

Configuration

Sessions

Authentication

Health

System

---

# 8. Dashboard

GET

/api/v1/dashboard

Obtiene el estado general de la plataforma.

---

GET

/api/v1/dashboard/summary

Resumen ejecutivo.

---

GET

/api/v1/dashboard/statistics

Indicadores generales.

---

# 9. Channels

GET

/api/v1/channels

Lista de canales.

---

POST

/api/v1/channels

Crear canal.

---

GET

/api/v1/channels/{id}

Consultar canal.

---

PUT

/api/v1/channels/{id}

Modificar canal.

---

DELETE

/api/v1/channels/{id}

Eliminar canal.

---

POST

/api/v1/channels/{id}/start

Iniciar canal.

---

POST

/api/v1/channels/{id}/stop

Detener canal.

---

POST

/api/v1/channels/{id}/restart

Reiniciar canal.

---

GET

/api/v1/channels/{id}/metrics

Consultar métricas.

---

GET

/api/v1/channels/{id}/events

Consultar eventos.

---

GET

/api/v1/channels/{id}/alarms

Consultar alarmas.

---

# 10. Clients

GET

/api/v1/clients

POST

/api/v1/clients

GET

/api/v1/clients/{id}

PUT

/api/v1/clients/{id}

DELETE

/api/v1/clients/{id}

GET

/api/v1/clients/{id}/channels

GET

/api/v1/clients/{id}/sessions

GET

/api/v1/clients/{id}/metrics

---

# 11. Users

GET

/api/v1/users

POST

/api/v1/users

GET

/api/v1/users/{id}

PUT

/api/v1/users/{id}

DELETE

/api/v1/users/{id}

POST

/api/v1/users/{id}/disable

POST

/api/v1/users/{id}/enable

POST

/api/v1/users/{id}/reset-password

---

# 12. Roles

GET

/api/v1/roles

POST

/api/v1/roles

PUT

/api/v1/roles/{id}

DELETE

/api/v1/roles/{id}

---

# 13. Permissions

GET

/api/v1/permissions

GET

/api/v1/roles/{id}/permissions

PUT

/api/v1/roles/{id}/permissions

---

# 14. Services

GET

/api/v1/services

GET

/api/v1/services/{id}

POST

/api/v1/services/{id}/start

POST

/api/v1/services/{id}/stop

POST

/api/v1/services/{id}/restart

GET

/api/v1/services/{id}/logs

---

# 15. Monitoring

GET

/api/v1/monitoring

GET

/api/v1/monitoring/system

GET

/api/v1/monitoring/network

GET

/api/v1/monitoring/storage

GET

/api/v1/monitoring/processes

GET

/api/v1/monitoring/metrics

---

# 16. Alarms

GET

/api/v1/alarms

GET

/api/v1/alarms/{id}

POST

/api/v1/alarms/{id}/acknowledge

POST

/api/v1/alarms/{id}/close

---

# 17. Events

GET

/api/v1/events

GET

/api/v1/events/{id}

---

# 18. Reports

GET

/api/v1/reports

POST

/api/v1/reports

GET

/api/v1/reports/{id}

DELETE

/api/v1/reports/{id}

---

# 19. Configuration

GET

/api/v1/configuration

PUT

/api/v1/configuration

GET

/api/v1/configuration/history

POST

/api/v1/configuration/restore

---

# 20. Authentication

POST

/api/v1/auth/login

POST

/api/v1/auth/logout

POST

/api/v1/auth/refresh

GET

/api/v1/auth/me

---

# 21. Health

GET

/api/v1/health

Estado general de la API.

---

GET

/api/v1/system

Información general del sistema.

---

# 22. Respuestas

Todas las respuestas utilizarán una estructura uniforme.

Ejemplo

{
    "success": true,
    "data": {},
    "message": "",
    "timestamp": "",
    "request_id": ""
}

---

# 23. Manejo de Errores

La API utilizará códigos HTTP estándar.

200 OK

201 Created

204 No Content

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Unprocessable Entity

500 Internal Server Error

---

# 24. Auditoría

Toda operación que modifique el estado del sistema deberá generar automáticamente un Evento de Auditoría.

---

# 25. Versionado

Toda modificación incompatible generará una nueva versión de la API.

Ejemplo

/api/v2/

La versión anterior permanecerá disponible durante el período de transición.

---

# 26. Escalabilidad

La incorporación de nuevos recursos no requerirá modificar la estructura general de la API.

Cada módulo podrá registrar nuevos endpoints respetando las convenciones definidas en este documento.

---

# 27. Conclusión

La API REST constituye el contrato oficial entre el Frontend y el Backend del EJTV Control Center.

Toda comunicación entre los componentes de la plataforma deberá realizarse mediante esta interfaz, garantizando una arquitectura desacoplada, consistente y preparada para evolucionar en futuras versiones.