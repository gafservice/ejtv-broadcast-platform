# SPRINT-001 — Design

> Estado: estructura inicial creada. Contenido pendiente de desarrollo.

# SPRINT-001 — Design

---

# Introducción

Este documento describe el diseño del dominio de Identity & Access Management (IAM) correspondiente al Sprint-001.

El propósito de este sprint no es implementar mecanismos de autenticación, autorización o persistencia, sino definir el modelo conceptual que servirá como fundamento para todas las funcionalidades de seguridad de la plataforma.

El diseño presentado en este documento sigue los principios de Clean Architecture y Domain-Driven Design (DDD), garantizando que el dominio permanezca independiente de cualquier tecnología de infraestructura.

---

# Objetivos del diseño

El diseño del dominio persigue los siguientes objetivos:

- Representar correctamente el concepto de identidad dentro de la plataforma.
- Separar responsabilidades entre entidades, objetos de valor e interfaces.
- Evitar dependencias con frameworks o bases de datos.
- Facilitar la implementación de pruebas unitarias.
- Permitir la evolución futura del sistema sin modificar el dominio.

---

# Alcance

Este documento cubre únicamente el diseño del dominio.

Incluye:

- Modelo conceptual.
- Entidades.
- Objetos de valor.
- Interfaces (Protocols).
- Reglas del dominio.
- Relaciones entre componentes.

No incluye:

- FastAPI.
- JWT.
- PostgreSQL.
- SQLAlchemy.
- Redis.
- HTTP.
- Interfaces gráficas.
- Persistencia.
---

# Modelo Conceptual

El dominio IAM está compuesto por un conjunto reducido de conceptos fundamentales.

Cada uno representa una responsabilidad específica dentro del sistema.

Durante este sprint únicamente se modelarán los conceptos necesarios para soportar la autenticación y autorización futuras.

Los conceptos iniciales son:

- User
- Role
- Permission
- AuthenticatedIdentity

Los siguientes componentes serán incorporados en sprints posteriores:

- Session
- AuditEvent
- RefreshToken
- APIKey
- Organization

## User

### Descripción

Representa una identidad permanente registrada dentro de la plataforma.

Un User describe a una persona o sistema autorizado para utilizar los recursos del Broadcast Platform.

Un User no representa:

- una sesión;
- un token;
- una conexión HTTP;
- una petición REST.

El usuario existe independientemente de que se encuentre autenticado o no.

### Responsabilidades

- Mantener su identidad.
- Conservar sus roles.
- Conservar su estado.
- Permitir cambios controlados sobre su información.

### No es responsable de

- Autenticarse.
- Generar tokens.
- Validar contraseñas.
- Administrar sesiones.
