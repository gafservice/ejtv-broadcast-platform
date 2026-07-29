# ENG-011 — Roles and Permissions

> Estado: estructura inicial creada. Contenido pendiente de desarrollo.

# ENG-011 — Roles & Permissions

---

# Introducción

Este documento define el modelo de autorización de la plataforma Broadcast.

El objetivo es establecer una estructura uniforme para controlar el acceso a los distintos recursos del sistema, garantizando que cada usuario únicamente pueda ejecutar las operaciones autorizadas para su rol.

La autorización se implementará mediante un modelo RBAC (Role-Based Access Control).

---

# Objetivos

El modelo de permisos debe cumplir los siguientes principios:

- Simplicidad.
- Escalabilidad.
- Fácil administración.
- Bajo acoplamiento.
- Compatibilidad con futuras organizaciones (Multi-Tenant).
- Compatibilidad con auditoría.

---

# Modelo RBAC

Cada usuario posee uno o más roles.

Cada rol agrupa un conjunto de permisos.

Los permisos representan acciones específicas sobre recursos del sistema.

```text
Usuario
    │
    ▼
Roles
    │
    ▼
Permisos
    │
    ▼
Recursos
```

---

# Roles iniciales

Durante las primeras versiones del proyecto se utilizarán cinco roles principales.

| Rol | Descripción |
|------|-------------|
| Super Administrator | Control total de la plataforma. |
| Administrator | Administración general del sistema. |
| Operator | Operación diaria del NOC. |
| Observer | Monitoreo únicamente. |
| API Client | Acceso programático mediante API. |

---

# Super Administrator

Tiene acceso completo.

Puede:

- Administrar usuarios.
- Administrar roles.
- Administrar permisos.
- Reiniciar servicios.
- Configurar infraestructura.
- Modificar configuraciones.
- Gestionar alarmas.
- Consultar auditoría.
- Crear administradores.
- Eliminar usuarios.

No posee restricciones funcionales.

---

# Administrator

Puede administrar la plataforma, pero no modificar la estructura de seguridad principal.

Puede:

- Gestionar operadores.
- Gestionar configuraciones.
- Reiniciar procesos.
- Administrar dashboards.
- Resolver alarmas.
- Consultar reportes.
- Gestionar sesiones.

No puede:

- Crear Super Administrators.
- Modificar permisos base.
- Cambiar políticas globales de seguridad.

---

# Operator

Corresponde al personal del NOC.

Puede:

- Acceder al Dashboard.
- Consultar estado de servicios.
- Confirmar alarmas.
- Reiniciar servicios autorizados.
- Ejecutar diagnósticos.
- Consultar eventos.

No puede:

- Crear usuarios.
- Cambiar configuraciones críticas.
- Modificar roles.
- Alterar permisos.

---

# Observer

Acceso de solo lectura.

Puede:

- Consultar dashboards.
- Consultar métricas.
- Consultar alarmas.
- Consultar reportes.

No puede ejecutar operaciones administrativas.

---

# API Client

Representa aplicaciones externas.

Su acceso dependerá de los permisos asignados al token utilizado.

Podrá:

- Consultar información.
- Ejecutar acciones autorizadas.
- Integrarse mediante API REST.

No tendrá acceso al NOC Web.

---

# Recursos protegidos

Inicialmente se protegerán los siguientes recursos.

## System

- Información del sistema.
- Estado del servidor.
- Configuración.

---

## Streaming

- Paths.
- Publicadores.
- Lectores.
- Estadísticas.
- Reinicios.

---

## Diagnostics

- Health.
- Verificaciones.
- Diagnósticos.

---

## Alarm Management

- Alarmas activas.
- Confirmación.
- Resolución.

---

## Reporting

- Reportes.
- Exportaciones.
- Históricos.

---

## Automation

- Automatizaciones.
- Programaciones.
- Ejecuciones.

---

## AI Operations

- Asistentes.
- Recomendaciones.
- Automatización inteligente.

---

# Permisos

Los permisos seguirán una nomenclatura uniforme.

Ejemplos:

```text
system.read
system.write

streaming.read
streaming.restart
streaming.publish

diagnostics.execute

alarm.read
alarm.acknowledge
alarm.resolve

report.read
report.export

automation.execute

ai.execute

users.read
users.create
users.update
users.delete

roles.read
roles.update

audit.read
```

---

# Matriz de permisos

| Permiso | Super Admin | Admin | Operator | Observer | API Client |
|-----------|:----------:|:-----:|:--------:|:--------:|:----------:|
| Dashboard | ✔ | ✔ | ✔ | ✔ | ✖ |
| Usuarios | ✔ | ✔ | ✖ | ✖ | ✖ |
| Roles | ✔ | ✖ | ✖ | ✖ | ✖ |
| Configuración | ✔ | ✔ | ✖ | ✖ | ✖ |
| Streaming | ✔ | ✔ | ✔ | Lectura | Según Token |
| Alarmas | ✔ | ✔ | ✔ | Lectura | Según Token |
| Diagnósticos | ✔ | ✔ | ✔ | Lectura | Según Token |
| Reportes | ✔ | ✔ | ✔ | Lectura | Según Token |
| Auditoría | ✔ | ✔ | Lectura | ✖ | ✖ |

---

# Principio de mínimo privilegio

Todos los usuarios deberán iniciar con el menor conjunto posible de permisos.

Los privilegios adicionales deberán asignarse explícitamente.

Este principio reduce la superficie de ataque y minimiza el impacto de errores operativos.

---

# Evolución futura

El modelo permitirá incorporar posteriormente:

- Organizaciones (Multi-Tenant).
- Equipos.
- Grupos.
- Permisos temporales.
- Delegación de funciones.
- Herencia de roles.
- Políticas dinámicas.
- Acceso basado en atributos (ABAC).

La arquitectura actual ha sido diseñada para permitir esta evolución sin modificar el dominio principal.

---

# Conclusión

El modelo RBAC definido en este documento establece una base sólida para proteger todos los recursos de la plataforma Broadcast.

La combinación de roles, permisos y auditoría permitirá mantener un entorno seguro, trazable y preparado para el crecimiento futuro del sistema.