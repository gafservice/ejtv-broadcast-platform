# ENG-011 — IAM Architecture

> Estado: estructura inicial creada. Contenido pendiente de desarrollo.

# ENG-011 — Architecture

---

# Introducción

Identity & Access Management (IAM) constituye el subsistema encargado de garantizar la identidad, autenticación, autorización y trazabilidad de todas las operaciones realizadas dentro de la plataforma Broadcast.

A diferencia de otros módulos de ingeniería, IAM no implementa funcionalidades propias del negocio de distribución multimedia. Su responsabilidad consiste en proporcionar servicios transversales de seguridad que serán consumidos por todos los componentes del sistema.

Por esta razón, IAM debe permanecer completamente desacoplado de la lógica de negocio y del framework utilizado por la aplicación.

---

# Objetivos arquitectónicos

La arquitectura del módulo busca cumplir los siguientes objetivos:

- Independencia del framework.
- Alta cohesión.
- Bajo acoplamiento.
- Escalabilidad.
- Reutilización.
- Facilidad para realizar pruebas.
- Seguridad.
- Evolución incremental.

---

# Principios

El diseño sigue los principios de Clean Architecture.

Las reglas principales son:

- El dominio nunca depende de FastAPI.
- El dominio nunca depende de JWT.
- El dominio nunca depende de bases de datos.
- El dominio nunca depende de librerías criptográficas.
- El dominio únicamente conoce reglas de negocio.

Todas las dependencias apuntan hacia el dominio.

---

# Arquitectura general

```text
                    +---------------------------+
                    |      NOC Web UI           |
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    |        REST API           |
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    |    Authentication Layer   |
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    |     Authorization Layer   |
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    |    Application Services   |
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    |     Identity Domain       |
                    +-------------+-------------+
                                  |
                    +------+------+------+
                    |             |       |
                    v             v       v
             Repository      Token      Audit
             Interface     Interface   Interface
```

---

# Capas

## Domain

Contendrá únicamente reglas de negocio.

Ejemplos:

- User
- Role
- Permission
- AuthenticatedIdentity

El dominio no conoce infraestructura.

---

## Application

Orquesta los casos de uso.

Ejemplos:

- AuthenticateUser
- ChangePassword
- ValidatePermission
- CreateUser

---

## Infrastructure

Implementa las interfaces definidas por el dominio.

Ejemplos:

- PostgreSQL Repository
- JWT Provider
- Argon2 Password Hasher
- FastAPI Security
- Audit Repository

---

## Presentation

Corresponde a:

- REST API
- NOC Web
- Login
- Formularios
- Middleware

---

# Flujo de autenticación

```text
Usuario
   │
   ▼
Login
   │
   ▼
Authentication Service
   │
   ▼
User Repository
   │
   ▼
Password Hasher
   │
   ▼
Authenticated Identity
   │
   ▼
Token Provider
   │
   ▼
JWT
```

---

# Flujo de autorización

```text
Petición HTTP
        │
        ▼
JWT válido
        │
        ▼
Identity
        │
        ▼
Role
        │
        ▼
Permissions
        │
        ▼
Acceso permitido
```

---

# Flujo de auditoría

```text
Usuario
      │
      ▼
Acción
      │
      ▼
Evento
      │
      ▼
Audit Service
      │
      ▼
Persistencia
```

Cada operación relevante generará un evento auditable.

---

# Integración con otros módulos

IAM será utilizado por todos los módulos de ingeniería.

```text
                IAM
                 │
 ┌───────────────┼────────────────┐
 │               │                │
 ▼               ▼                ▼
System      Streaming        Diagnostics
 │               │                │
 └───────────────┼────────────────┘
                 ▼
          Alarm Management
                 │
                 ▼
          Event Management
                 │
                 ▼
            Reporting
                 │
                 ▼
            Automation
                 │
                 ▼
           AI Operations
```

Ningún módulo implementará autenticación propia.

---

# Responsabilidades

IAM será responsable de:

- Identificar usuarios.
- Validar credenciales.
- Administrar sesiones.
- Gestionar permisos.
- Autorizar operaciones.
- Registrar eventos.
- Proteger la API.
- Proteger el NOC Web.

No será responsable de:

- Administración de streaming.
- Diagnósticos.
- Alarmas.
- Reportes.
- Automatización.

---

# Dependencias permitidas

## Dominio

No puede depender de ninguna librería externa.

## Aplicación

Puede depender únicamente del dominio.

## Infraestructura

Puede depender del dominio y de la aplicación.

## Presentación

Puede depender de todas las capas inferiores.

---

# Estrategia de pruebas

Las pruebas se desarrollarán por capas.

- Unitarias para el dominio.
- Integración para repositorios.
- Integración para autenticación.
- API para autorización.
- End-to-End para el NOC Web.

---

# Evolución prevista

La arquitectura ha sido diseñada para permitir la incorporación futura de:

- Multi-Factor Authentication (MFA)
- OAuth2
- OpenID Connect
- LDAP
- Active Directory
- Single Sign-On (SSO)
- API Keys
- Tokens de Servicio
- Organizaciones (Multi-Tenant)
- Federaciones de identidad

sin modificar el núcleo del dominio.

---

# Conclusión

IAM constituye el punto central de seguridad de la plataforma Broadcast.

Toda operación administrativa, toda interacción con el NOC y todo acceso a la API deberá atravesar este subsistema, garantizando autenticación, autorización y trazabilidad mediante una arquitectura desacoplada, mantenible y preparada para la evolución futura.
