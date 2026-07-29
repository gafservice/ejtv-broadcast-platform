# ENG-011 — IAM Roadmap

> Estado: estructura inicial creada. Contenido pendiente de desarrollo.

# ENG-011 — Roadmap

---

# Propósito

El módulo Identity & Access Management (IAM) será desarrollado de forma incremental mediante una serie de sprints orientados a construir un sistema de autenticación y autorización robusto, escalable y completamente integrado con la arquitectura de la plataforma Broadcast.

Cada sprint agrega una capacidad específica sin comprometer la independencia del dominio ni la estabilidad del sistema.

---

# Objetivos generales

Al finalizar ENG-011 la plataforma dispondrá de:

- Gestión centralizada de identidades.
- Autenticación segura.
- Autorización basada en roles.
- Protección de toda la API.
- Auditoría completa.
- Integración con el NOC Web.
- Base para futuras funcionalidades empresariales.

---

# Principios del roadmap

El desarrollo seguirá los siguientes principios:

- Arquitectura antes que implementación.
- Dominio independiente del framework.
- Cambios pequeños y verificables.
- Compatibilidad hacia atrás.
- Cobertura de pruebas desde el primer sprint.
- Evolución incremental.

---

# Sprint 001 — Identity Domain

## Objetivo

Construir el dominio de identidad completamente desacoplado de FastAPI, JWT y cualquier mecanismo de persistencia.

## Alcance

- Entidad User.
- Value Objects.
- Roles.
- Estados de usuario.
- Protocolos del dominio.
- Interfaces.
- Casos de prueba unitarios.

## Entregables

- Dominio completamente funcional.
- Sin dependencias externas.
- Cobertura de pruebas.

---

# Sprint 002 — Authentication

## Objetivo

Implementar el proceso de autenticación.

## Alcance

- PasswordHasher.
- Argon2.
- AuthenticationService.
- UserRepository.
- Usuario administrador inicial.
- Validación de credenciales.

## Entregables

- Login funcional.
- Contraseñas cifradas.
- Pruebas de autenticación.

---

# Sprint 003 — Authorization

## Objetivo

Proteger los recursos de la plataforma.

## Alcance

- JWT.
- Bearer Token.
- FastAPI Security.
- Roles.
- Permisos.
- Protección de endpoints.

## Entregables

- API protegida.
- Validación de permisos.
- Respuestas HTTP 401 y 403.

---

# Sprint 004 — Audit

## Objetivo

Registrar todos los eventos relevantes relacionados con identidad y seguridad.

## Alcance

- Registro de inicios de sesión.
- Intentos fallidos.
- Cambios de contraseña.
- Acciones administrativas.
- Historial de eventos.

## Entregables

- Sistema de auditoría.
- Eventos consultables.
- Base para reportes.

---

# Sprint 005 — NOC Web Integration

## Objetivo

Integrar el módulo IAM con la interfaz web del NOC.

## Alcance

- Pantalla de login.
- Gestión de sesión.
- Protección de vistas.
- Menús según permisos.
- Cierre de sesión.

## Entregables

- Acceso autenticado al NOC.
- Navegación protegida.
- Control de acceso por roles.

---

# Evolución futura

Una vez completado ENG-011 podrán incorporarse nuevas capacidades sin modificar la arquitectura principal.

Entre ellas:

- Multi-Factor Authentication (MFA).
- OAuth2.
- OpenID Connect.
- LDAP.
- Active Directory.
- Single Sign-On (SSO).
- API Keys.
- Tokens de larga duración.
- Delegación de permisos.
- Administración gráfica de usuarios.
- Políticas avanzadas de seguridad.
- Integración con proveedores externos de identidad.

---

# Dependencias

Este módulo será consumido por:

- ENG-001 System Engineering
- ENG-002 Network Engineering
- ENG-003 Streaming Engineering
- ENG-004 Session Engineering
- ENG-005 Diagnostics
- ENG-006 Alarm Management
- ENG-007 Event Management
- ENG-008 Reporting
- ENG-009 Automation
- ENG-010 AI Operations

---

# Estado del roadmap

| Sprint | Estado |
|---------|--------|
| Sprint 001 | Planificado |
| Sprint 002 | Planificado |
| Sprint 003 | Planificado |
| Sprint 004 | Planificado |
| Sprint 005 | Planificado |

---

# Criterio de finalización

ENG-011 será considerado completado cuando:

- Exista autenticación segura.
- Toda la API se encuentre protegida.
- Los permisos sean administrados mediante roles.
- Todas las acciones críticas queden registradas.
- El NOC Web requiera autenticación para su utilización.
- La cobertura de pruebas cumpla los estándares del proyecto.