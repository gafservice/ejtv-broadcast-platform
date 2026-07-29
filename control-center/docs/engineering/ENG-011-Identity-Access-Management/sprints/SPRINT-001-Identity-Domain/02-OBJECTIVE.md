# SPRINT-001 — Objective

> Estado: estructura inicial creada. Contenido pendiente de desarrollo.

# SPRINT-001 — Objective

---

# Objetivo general

Diseñar e implementar el dominio de Identity & Access Management (IAM) como un módulo completamente independiente de la infraestructura, estableciendo las entidades, objetos de valor, interfaces y reglas de negocio que servirán como fundamento para los procesos de autenticación, autorización y auditoría de la plataforma Broadcast.

Este sprint representa la construcción del núcleo del subsistema IAM y no contempla mecanismos de autenticación ni tecnologías específicas de implementación.

---

# Objetivos específicos

Al finalizar este sprint deberán cumplirse los siguientes objetivos.

## 1. Definir el lenguaje del dominio

Establecer un vocabulario único y consistente para todos los componentes relacionados con identidad y control de acceso.

Entre ellos:

- User
- Role
- Permission
- AuthenticatedIdentity
- UserStatus
- PermissionSet
- UserRepository
- AuthenticationProvider

Este lenguaje será utilizado de forma uniforme en:

- Código fuente.
- Documentación.
- API.
- Auditoría.
- NOC Web.

---

## 2. Modelar las entidades principales

Diseñar las entidades que representan el dominio.

Inicialmente deberán existir:

- User
- Role
- Permission
- AuthenticatedIdentity

Cada entidad deberá representar únicamente reglas de negocio.

No contendrá detalles de infraestructura.

---

## 3. Definir Value Objects

Identificar los objetos inmutables necesarios para representar conceptos del dominio.

Ejemplos previstos:

- UserId
- Username
- Email
- PasswordHash
- RoleName
- PermissionName

Estos objetos deberán encapsular validaciones y reglas propias.

---

## 4. Definir contratos del dominio

Diseñar las interfaces que permitirán desacoplar el dominio de cualquier implementación concreta.

Inicialmente se contemplan:

- UserRepository
- PasswordHasher
- TokenProvider
- AuditRepository

Las implementaciones concretas serán desarrolladas en sprints posteriores.

---

## 5. Definir reglas de negocio

Toda lógica relacionada con identidad deberá pertenecer al dominio.

Entre otras:

- Un usuario puede estar activo o inactivo.
- Un usuario bloqueado no puede autenticarse.
- Un rol contiene permisos.
- Un permiso identifica una capacidad específica.
- Una identidad autenticada representa una sesión válida.

---

## 6. Garantizar independencia tecnológica

El dominio no podrá depender de:

- FastAPI.
- SQLAlchemy.
- PostgreSQL.
- JWT.
- Redis.
- Argon2.
- HTTP.
- MediaMTX.

La única dependencia permitida será la biblioteca estándar de Python y los componentes internos del dominio.

---

## 7. Implementar pruebas unitarias

Cada entidad y regla de negocio deberá estar respaldada por pruebas unitarias.

Las pruebas deberán ejecutarse de forma aislada.

No utilizarán:

- Base de datos.
- Red.
- Servicios externos.

---

# Criterios de aceptación

El sprint será considerado completado únicamente cuando se cumplan todas las siguientes condiciones.

- Dominio completamente implementado.
- Todas las entidades definidas.
- Value Objects implementados.
- Protocols definidos.
- Reglas de negocio documentadas.
- Cobertura de pruebas del dominio igual o superior al 100%.
- Sin dependencias de infraestructura.
- Sin referencias a FastAPI.
- Sin referencias a JWT.
- Sin referencias a PostgreSQL.
- Documentación actualizada.

---

# Fuera del alcance

Este sprint no desarrollará:

- Login.
- Logout.
- JWT.
- Bearer Token.
- OAuth2.
- OpenID Connect.
- MFA.
- Recuperación de contraseña.
- API REST.
- Middleware.
- Pantalla de autenticación.
- Administración gráfica de usuarios.

Estas funcionalidades serán abordadas en los siguientes sprints.

---

# Riesgos identificados

Los principales riesgos del sprint son:

- Introducir dependencias hacia infraestructura.
- Modelar entidades con responsabilidades excesivas.
- Duplicar reglas de negocio.
- Definir interfaces demasiado acopladas a una implementación específica.
- Incorporar lógica de autenticación antes de finalizar el dominio.

Estos riesgos deberán evitarse mediante revisiones continuas de arquitectura.

---

# Definición de "Done"

El Sprint-001 será considerado finalizado cuando el dominio IAM pueda ser utilizado como una biblioteca independiente, completamente desacoplada del resto de la plataforma y preparada para soportar la implementación de autenticación, autorización y auditoría en los sprints posteriores.