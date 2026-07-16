# EJTV Control Center

# Roles y Permisos

**Versión:** 1.0

**Estado:** Diseño

**Misión:** MISSION-017

---

# 1. Introducción

El presente documento define el modelo inicial de roles y permisos del EJTV Control Center.

Su propósito consiste en establecer mecanismos claros de autorización para garantizar que cada usuario pueda acceder únicamente a las funciones necesarias para cumplir sus responsabilidades.

La autenticación determina quién es el usuario.

La autorización determina qué acciones puede ejecutar.

La auditoría registra lo que realizó.

Estos tres elementos deberán aplicarse de forma conjunta en toda la plataforma.

---

# 2. Objetivos

El modelo de permisos deberá permitir:

- proteger operaciones críticas;
- reducir el riesgo de error humano;
- separar responsabilidades;
- aplicar el principio de mínimo privilegio;
- controlar el acceso a información sensible;
- registrar todas las acciones administrativas;
- facilitar la incorporación de nuevos roles;
- mantener consistencia entre Backend y Frontend.

---

# 3. Principios de Seguridad

## 3.1 Mínimo privilegio

Cada usuario recibirá únicamente los permisos indispensables para cumplir su función.

## 3.2 Denegación por defecto

Toda acción estará denegada salvo que exista un permiso explícito que la autorice.

## 3.3 Separación de responsabilidades

Las funciones críticas podrán requerir diferentes niveles de autorización.

Un operador no deberá administrar usuarios ni modificar configuraciones globales.

## 3.4 Trazabilidad

Toda acción sensible deberá registrar:

- usuario;
- fecha;
- hora;
- dirección IP;
- recurso;
- acción;
- resultado;
- motivo cuando corresponda.

## 3.5 Autorización en el Backend

El Frontend podrá ocultar botones o funciones no autorizadas, pero la validación definitiva siempre será realizada por el Backend.

Nunca se considerará al Frontend como mecanismo de seguridad.

---

# 4. Modelo de Permisos

Los permisos utilizarán una nomenclatura uniforme:

```text
recurso.acción
```

Ejemplos:

```text
dashboard.read
channels.create
channels.start
channels.stop
channels.restart
services.read
services.restart
users.manage
configuration.apply
logs.read
reports.export
```

Cuando sea necesario podrá utilizarse una tercera parte:

```text
recurso.subrecurso.acción
```

Ejemplo:

```text
channels.protocols.update
clients.credentials.rotate
configuration.security.apply
```

---

# 5. Tipos de Acciones

Las acciones iniciales serán:

- `read`
- `create`
- `update`
- `delete`
- `start`
- `stop`
- `restart`
- `enable`
- `disable`
- `acknowledge`
- `close`
- `apply`
- `restore`
- `export`
- `manage`

La acción `manage` representa control completo sobre un recurso y deberá utilizarse únicamente en roles administrativos.

---

# 6. Roles Iniciales

## 6.1 Administrador General

### Propósito

Posee control completo sobre el Control Center y la plataforma.

### Responsabilidades

- administrar usuarios;
- administrar roles y permisos;
- administrar configuración global;
- administrar canales;
- administrar clientes;
- administrar servicios;
- consultar y cerrar alarmas;
- generar reportes;
- revisar auditoría;
- gestionar seguridad.

### Restricciones

No posee restricciones funcionales dentro de la primera versión.

Toda acción deberá quedar auditada.

---

## 6.2 Administrador Técnico

### Propósito

Administra la infraestructura y la operación técnica sin controlar la administración general de usuarios.

### Responsabilidades

- administrar canales;
- administrar servicios;
- consultar monitoreo;
- modificar configuración técnica;
- consultar logs;
- gestionar alarmas;
- ejecutar mantenimiento;
- administrar nodos e interfaces.

### Restricciones

No puede:

- eliminar al Administrador General;
- modificar políticas maestras de seguridad;
- administrar permisos del Administrador General;
- eliminar registros de auditoría.

---

## 6.3 Operador NOC

### Propósito

Supervisa la operación diaria y ejecuta acciones operativas controladas.

### Responsabilidades

- consultar Dashboard;
- consultar canales;
- iniciar, detener o reiniciar canales autorizados;
- consultar servicios;
- reiniciar servicios operativos autorizados;
- consultar monitoreo;
- reconocer alarmas;
- consultar logs operativos;
- generar reportes operativos.

### Restricciones

No puede:

- crear o eliminar usuarios;
- modificar roles;
- modificar configuración global;
- eliminar canales;
- modificar políticas de seguridad;
- eliminar clientes;
- acceder a secretos o credenciales.

---

## 6.4 Supervisor

### Propósito

Supervisa la operación y valida decisiones sin ejecutar cambios técnicos críticos.

### Responsabilidades

- consultar Dashboard;
- consultar canales;
- consultar clientes;
- consultar servicios;
- consultar métricas;
- consultar alarmas;
- cerrar alarmas resueltas;
- generar reportes;
- consultar auditoría operativa.

### Restricciones

No puede:

- iniciar o detener servicios;
- modificar configuraciones;
- administrar usuarios;
- administrar credenciales;
- ejecutar cambios críticos.

---

## 6.5 Auditor

### Propósito

Consulta información histórica, seguridad y trazabilidad.

### Responsabilidades

- consultar logs;
- consultar eventos;
- consultar auditoría;
- consultar usuarios y roles;
- consultar cambios de configuración;
- generar reportes de auditoría;
- exportar evidencia.

### Restricciones

Acceso de solo lectura.

No puede modificar el estado del sistema.

---

## 6.6 Usuario de Consulta

### Propósito

Permite visualizar información básica de la plataforma.

### Responsabilidades

- consultar Dashboard;
- consultar estado de canales;
- consultar métricas generales;
- consultar reportes autorizados.

### Restricciones

No puede ejecutar acciones operativas ni administrativas.

---

# 7. Matriz General de Acceso

| Recurso | Administrador General | Administrador Técnico | Operador NOC | Supervisor | Auditor | Consulta |
|---|---:|---:|---:|---:|---:|---:|
| Dashboard | Total | Total | Lectura | Lectura | Lectura | Lectura |
| Channels | Total | Total | Operación | Lectura | Lectura | Lectura |
| Clients | Total | Lectura/Edición | Lectura | Lectura | Lectura | No |
| Services | Total | Total | Operación limitada | Lectura | Lectura | No |
| Monitoring | Total | Total | Lectura | Lectura | Lectura | Resumen |
| Users | Total | Lectura | No | No | Lectura | No |
| Roles | Total | No | No | No | Lectura | No |
| Security | Total | Técnico | No | Lectura | Lectura | No |
| Reports | Total | Total | Operativos | Total | Auditoría | Lectura |
| Configuration | Total | Técnica | No | No | Lectura | No |
| Logs | Total | Total | Operativos | Lectura | Total | No |
| Alarms | Total | Total | Reconocer | Cerrar | Lectura | No |
| Nodes | Total | Total | Lectura | Lectura | Lectura | No |

---

# 8. Permisos por Módulo

## 8.1 Dashboard

```text
dashboard.read
dashboard.read_sensitive
```

`dashboard.read_sensitive` permitirá visualizar información restringida como direcciones IP, errores internos o datos de seguridad.

---

## 8.2 Channels

```text
channels.read
channels.create
channels.update
channels.delete
channels.start
channels.stop
channels.restart
channels.duplicate
channels.maintenance
channels.metrics.read
channels.logs.read
channels.protocols.update
channels.sources.update
```

La eliminación de un canal deberá requerir confirmación reforzada.

---

## 8.3 Clients

```text
clients.read
clients.create
clients.update
clients.suspend
clients.enable
clients.delete
clients.channels.assign
clients.protocols.assign
clients.addresses.manage
clients.credentials.manage
clients.metrics.read
clients.sessions.read
```

Las credenciales no podrán mostrarse en texto plano.

---

## 8.4 Services

```text
services.read
services.start
services.stop
services.restart
services.maintenance
services.logs.read
services.metrics.read
services.dependencies.read
services.configuration.update
```

Servicios críticos como SSH, Firewall o el propio Control Center podrán requerir permisos adicionales.

---

## 8.5 Monitoring

```text
monitoring.read
monitoring.system.read
monitoring.network.read
monitoring.storage.read
monitoring.processes.read
monitoring.metrics.read
monitoring.thresholds.update
```

---

## 8.6 Users

```text
users.read
users.create
users.update
users.disable
users.enable
users.delete
users.password.reset
users.sessions.read
users.sessions.revoke
users.roles.assign
users.permissions.assign
```

No se permitirá eliminar al último Administrador General activo.

---

## 8.7 Roles y Permisos

```text
roles.read
roles.create
roles.update
roles.delete
roles.permissions.assign
permissions.read
permissions.manage
```

Los permisos asignados directamente a usuarios deberán utilizarse de manera excepcional.

---

## 8.8 Security

```text
security.read
security.events.read
security.policies.read
security.policies.update
security.certificates.read
security.certificates.manage
security.sessions.read
security.sessions.revoke
security.audit.read
```

La visualización de secretos privados estará prohibida incluso para administradores.

---

## 8.9 Reports

```text
reports.read
reports.create
reports.delete
reports.export
reports.schedule
reports.templates.manage
```

---

## 8.10 Configuration

```text
configuration.read
configuration.create
configuration.validate
configuration.apply
configuration.restore
configuration.export
configuration.import
configuration.history.read
```

La aplicación y restauración deberán registrarse obligatoriamente.

---

## 8.11 Logs

```text
logs.read
logs.export
logs.archive
logs.retention.manage
```

Los registros de auditoría no podrán eliminarse desde la interfaz normal.

---

## 8.12 Alarms

```text
alarms.read
alarms.acknowledge
alarms.investigate
alarms.resolve
alarms.close
alarms.suppress
alarms.rules.manage
```

---

## 8.13 Nodes

```text
nodes.read
nodes.create
nodes.update
nodes.disable
nodes.maintenance
nodes.interfaces.read
nodes.interfaces.update
```

---

# 9. Acciones Críticas

Las siguientes acciones se consideran críticas:

- eliminar un canal;
- detener MediaMTX;
- detener el Control Center;
- modificar Firewall;
- modificar red;
- restaurar configuración;
- eliminar un usuario administrativo;
- modificar roles administrativos;
- revocar certificados;
- deshabilitar autenticación;
- eliminar un cliente;
- detener múltiples canales.

Estas acciones deberán requerir:

1. permiso específico;
2. confirmación explícita;
3. registro de motivo;
4. auditoría;
5. respuesta clara del sistema.

En futuras versiones podrán requerir doble aprobación.

---

# 10. Permisos Contextuales

Algunas autorizaciones dependerán del recurso específico.

Ejemplo:

Un Operador NOC puede reiniciar el canal ENLACE, pero no otros canales.

Esto podrá representarse mediante alcance:

```text
permission: channels.restart
scope: channel:enlace
```

Otros alcances posibles:

```text
node:ejtv-01
client:cliente-a
service:ejtv-enlace
module:monitoring
```

---

# 11. Acciones Permitidas por la API

La API podrá incluir el campo:

```json
{
  "allowed_actions": [
    "read",
    "restart",
    "view_logs"
  ]
}
```

El Frontend utilizará este campo para mostrar únicamente las acciones disponibles.

Sin embargo, el Backend validará nuevamente cada solicitud.

---

# 12. Sesiones

Los permisos de una sesión deberán recalcularse cuando:

- el usuario cambie de rol;
- el rol cambie de permisos;
- el usuario sea suspendido;
- la sesión sea revocada;
- se modifique una política crítica.

Las sesiones activas podrán cerrarse de forma administrativa.

---

# 13. Herencia y Conflictos

Los permisos podrán obtenerse mediante:

- roles;
- asignaciones directas;
- alcance contextual.

Cuando exista conflicto, prevalecerá la regla más restrictiva.

Una denegación explícita tendrá prioridad sobre una autorización.

---

# 14. Auditoría

Deberán auditarse como mínimo:

- autenticaciones;
- cambios de permisos;
- asignaciones de roles;
- acciones críticas;
- reinicios de servicios;
- cambios de configuración;
- creación y suspensión de clientes;
- creación y eliminación de canales;
- exportación de información sensible.

---

# 15. Evolución

En futuras versiones podrán incorporarse:

- aprobación por dos personas;
- permisos temporales;
- delegación;
- políticas por horario;
- políticas por ubicación;
- autenticación multifactor;
- integración LDAP;
- Active Directory;
- OAuth2;
- OpenID Connect;
- roles por organización;
- permisos por sede o nodo.

Estas capacidades deberán respetar el principio de mínimo privilegio.

---

# 16. Conclusión

El modelo de roles y permisos constituye la base de seguridad operacional del EJTV Control Center.

Su finalidad no consiste únicamente en restringir accesos.

También permite organizar responsabilidades, reducir riesgos, mantener trazabilidad y proteger la estabilidad de la plataforma.

Toda funcionalidad futura deberá declarar explícitamente los permisos requeridos antes de ser implementada.