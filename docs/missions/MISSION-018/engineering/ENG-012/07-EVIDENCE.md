# ENG-012 — Evidencias Técnicas

---

# Objetivo

Este documento reúne las principales evidencias generadas durante el
desarrollo de **ENG-012 — Identity Application Layer**.

Su propósito es demostrar objetivamente que el subsistema fue diseñado,
implementado, probado, versionado y certificado siguiendo el proceso de
ingeniería definido para la plataforma Broadcast.

Las evidencias aquí presentadas permiten reconstruir la evolución del
subsistema y verificar su estado final.

---

# Evidencias de implementación

Durante ENG-012 se desarrollaron los componentes fundamentales del
subsistema Identity.

Entre ellos:

- Authentication Service.
- Authorization Service.
- Identity Administration Service.
- Identity Bootstrap Service.
- Password Policy.
- Catálogo canónico de roles.
- Catálogo canónico de permisos.
- Repositorios SQLAlchemy.
- Auditoría.
- Bootstrap automático.
- Verificación de integridad.

---

# Evidencias de arquitectura

La implementación sigue la arquitectura definida para la plataforma.

Capas implementadas:

```text
API

↓

Application

↓

Domain

↓

Infrastructure
```

El dominio permanece completamente desacoplado de FastAPI,
SQLAlchemy y la infraestructura de persistencia.

---

# Evidencias del modelo de dominio

El dominio implementa:

## Entidades

```text
User

Role

Permission

AuthenticatedIdentity
```

---

## Value Objects

```text
UserId

Username

Email

PasswordHash

RoleName

PermissionName
```

---

## Enumeraciones

```text
UserStatus
```

---

## Protocols

```text
UserRepository

AuditRepository

IdentityCatalogRepository

PasswordHasher

TokenProvider
```

---

# Evidencias de seguridad

Se implementaron las siguientes capacidades.

- JWT.
- Bearer Authentication.
- bcrypt.
- Password Policy.
- Roles.
- Permisos.
- Auditoría.
- Protección del último administrador.
- Bootstrap seguro.
- Verificación de integridad.

---

# Evidencias de Bootstrap

El bootstrap implementa:

- inicialización automática;
- sincronización del catálogo;
- creación idempotente del administrador;
- validación de integridad;
- registro de auditoría.

---

# Evidencias de persistencia

Repositorios implementados:

```text
SQLAlchemyUserRepository

SQLAlchemyAuditRepository

SQLAlchemyIdentityCatalogRepository
```

La persistencia fue validada mediante pruebas automatizadas utilizando
SQLite temporal.

---

# Evidencias de API

Endpoints implementados.

## Authentication

```text
POST /api/v1/auth/login

GET /api/v1/auth/me
```

---

## Identity

```text
GET /identity/users

POST /identity/users

PATCH /identity/users/{id}/status

POST /identity/users/{id}/password

GET /identity/roles

POST /identity/users/{id}/roles

DELETE /identity/users/{id}/roles/{role}
```

Todos los endpoints se encuentran protegidos mediante autorización
basada en permisos.

---

# Evidencias de pruebas

La certificación del subsistema incluye pruebas de:

```text
Dominio

Servicios

Persistencia

API

Integración

End-to-End
```

Resultado final:

```text
944 pruebas ejecutadas

944 aprobadas

0 errores

0 fallos
```

---

# Evidencias End-to-End

El escenario certificado valida:

```text
Bootstrap

↓

Administrador inicial

↓

Login

↓

JWT

↓

Bearer Authentication

↓

/auth/me

↓

Roles

↓

Permisos

↓

Auditoría
```

La prueba utiliza componentes reales del sistema.

---

# Evidencias de auditoría

Las siguientes operaciones generan registros persistentes.

```text
identity.login.succeeded

identity.user.created

identity.user.password_changed

identity.user.status_changed

identity.user.role_assigned

identity.user.role_removed

identity.bootstrap.catalog_synchronized

identity.bootstrap.integrity_verified

identity.bootstrap.administrator_created
```

---

# Evidencias de calidad

Durante el desarrollo se aplicaron las siguientes prácticas.

- Clean Architecture.
- Domain-Driven Design.
- Protocols.
- Dependency Injection.
- Repository Pattern.
- Value Objects.
- Entidades inmutables.
- Catálogo canónico.
- Bootstrap idempotente.
- Automatización de pruebas.

---

# Evidencias de versionado

Principales hitos del desarrollo.

| Hito | Descripción |
|------|-------------|
| ENG-012F.1 | Administración inicial de usuarios |
| ENG-012F.2 | Estados y contraseñas |
| ENG-012F.3 | Administración de roles |
| ENG-012F.4 | Catálogo canónico de permisos |
| ENG-012F.5 | Bootstrap e integridad |
| ENG-012F.6 | Hardening y certificación End-to-End |

---

# Evidencias de Git

Commits principales.

```text
39a57ae

c853b2f

9e6c21e

7571aac

4c00eac
```

Tags principales.

```text
ENG-012F.1-complete

ENG-012F.2-complete

ENG-012F.3-complete

ENG-012F.4-complete

ENG-012F.5-complete

ENG-012F.6-complete
```

---

# Evidencias documentales

Durante ENG-012 se generó documentación técnica correspondiente a:

- arquitectura;
- dominio;
- bootstrap;
- seguridad;
- pruebas;
- decisiones de arquitectura;
- checklist;
- cierre formal.

Toda la documentación forma parte del expediente técnico del
subsistema.

---

# Resultado de la certificación

Estado de implementación.

```text
Arquitectura
✔

Dominio
✔

Persistencia
✔

API
✔

Seguridad
✔

Bootstrap
✔

Auditoría
✔

Pruebas
✔

End-to-End
✔

Documentación
✔
```

---

# Conclusión

Las evidencias reunidas durante ENG-012 demuestran que el subsistema
Identity fue desarrollado siguiendo un proceso de ingeniería completo.

La existencia de commits, versionado, pruebas automatizadas,
certificación End-to-End y documentación técnica proporciona evidencia
objetiva de que el IAM constituye un componente estable, verificable y
preparado para ser utilizado por el resto de la plataforma Broadcast.

ENG-012 queda respaldado no únicamente por su código fuente, sino por un
conjunto de evidencias técnicas que permiten verificar su calidad y
trazabilidad.