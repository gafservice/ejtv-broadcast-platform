# ENG-012 — Arquitectura

---

# Objetivo

Este documento describe la arquitectura técnica del subsistema
**Identity Application Layer (IAM)** implementado durante ENG-012.

Su propósito es explicar la organización del software, las
responsabilidades de cada capa y la interacción entre los diferentes
componentes del sistema.

No constituye un manual de implementación, sino una descripción de la
arquitectura utilizada para garantizar mantenibilidad, escalabilidad y
desacoplamiento.

---

# Principios de diseño

El diseño del subsistema Identity se basa en los siguientes principios.

## Clean Architecture

Las reglas del negocio permanecen independientes de:

- FastAPI;
- SQLAlchemy;
- JWT;
- bcrypt;
- SQLite;
- PostgreSQL;
- HTTP.

---

## Inversión de dependencias

El dominio depende únicamente de contratos (Protocols).

Las implementaciones concretas pertenecen a la infraestructura.

---

## Alta cohesión

Cada componente posee una única responsabilidad claramente definida.

---

## Bajo acoplamiento

Las capas superiores desconocen los detalles internos de las inferiores.

---

## Sustitución de infraestructura

La infraestructura puede reemplazarse sin modificar el dominio.

---

# Arquitectura por capas

El subsistema se encuentra dividido en cuatro capas principales.

```text
                  CLIENTE HTTP
                        │
                        ▼
               FastAPI REST API
                        │
                        ▼
          Application Services Layer
                        │
                        ▼
               Identity Domain Layer
                        │
                        ▼
            Infrastructure Layer
                        │
                        ▼
                 Base de Datos
```

Cada capa tiene responsabilidades específicas.

---

# API

La capa API representa el punto de entrada del sistema.

Responsabilidades:

- exponer endpoints REST;
- validar solicitudes;
- serializar respuestas;
- autenticar usuarios;
- verificar permisos;
- convertir excepciones de dominio en respuestas HTTP.

Componentes principales:

```text
api/
```

Entre ellos:

- auth.py
- identity.py
- dependencies.py
- security.py

---

# Application Layer

La capa de aplicación implementa los casos de uso.

No contiene reglas de infraestructura.

Servicios principales:

```text
AuthenticationService

AuthorizationService

IdentityAdministrationService

IdentityBootstrapService
```

Cada servicio coordina:

- entidades;
- value objects;
- protocolos;
- auditoría;
- persistencia.

---

# Domain Layer

El dominio representa el núcleo del sistema.

Aquí viven todas las reglas del negocio.

Componentes:

```text
Entities

Value Objects

Catalog

Protocols

Password Policy

Exceptions

Enums
```

El dominio desconoce completamente:

- HTTP;
- SQLAlchemy;
- JWT;
- FastAPI;
- SQLite.

---

# Infrastructure Layer

La infraestructura implementa los contratos definidos por el dominio.

Ejemplos:

```text
SQLAlchemyUserRepository

SQLAlchemyAuditRepository

SQLAlchemyIdentityCatalogRepository

JWTTokenProvider

BcryptPasswordHasher
```

Estos componentes pueden cambiar sin afectar el dominio.

---

# Flujo de autenticación

La autenticación sigue la siguiente secuencia.

```text
Cliente

↓

POST /auth/login

↓

AuthenticationService

↓

PasswordHasher

↓

UserRepository

↓

JWTTokenProvider

↓

Token JWT

↓

Cliente
```

---

# Flujo de autorización

La autorización ocurre antes de ejecutar cada endpoint protegido.

```text
Solicitud

↓

Bearer Token

↓

JWT Validation

↓

AuthenticatedIdentity

↓

Permission Verification

↓

Endpoint
```

Las rutas no verifican usuarios directamente.

Verifican permisos.

---

# Flujo de Bootstrap

Durante el arranque de la aplicación se ejecuta el proceso de bootstrap.

```text
Inicializar Base de Datos

↓

Sincronizar Catálogo

↓

Verificar Integridad

↓

Administrador Inicial

↓

Aplicación Lista
```

Este proceso garantiza que el sistema siempre inicie en un estado
consistente.

---

# Persistencia

La persistencia utiliza SQLAlchemy como implementación de los
repositorios definidos mediante Protocols.

```text
Application

↓

Protocol

↓

SQLAlchemy Repository

↓

SQLite / PostgreSQL
```

Este desacoplamiento permite migrar a otro motor de persistencia sin
modificar las reglas del dominio.

---

# Relaciones entre componentes

```text
FastAPI

↓

Authentication Service

↓

Authorization Service

↓

Identity Administration

↓

Repositories

↓

SQLAlchemy

↓

Database
```

Todos los accesos a datos pasan por los contratos definidos en el
dominio.

---

# Beneficios de la arquitectura

La arquitectura implementada proporciona:

- independencia tecnológica;
- facilidad para realizar pruebas;
- separación clara de responsabilidades;
- reutilización de componentes;
- escalabilidad;
- facilidad de mantenimiento;
- sustitución controlada de infraestructura;
- alta capacidad de evolución.

---

# Preparación para el futuro

La arquitectura fue diseñada para servir como base a los módulos
posteriores de la plataforma.

Entre ellos:

- NOC Web;
- Dashboard;
- Alarmas;
- Streaming;
- Transcodificación;
- Automatización;
- Administración de nodos.

Todos estos módulos consumirán Identity mediante contratos públicos,
evitando duplicar mecanismos de autenticación y autorización.

---

# Conclusión

La arquitectura implementada durante ENG-012 establece un subsistema
desacoplado, verificable y preparado para evolucionar junto con la
plataforma.

La separación entre API, aplicación, dominio e infraestructura permite
que el crecimiento futuro del sistema se realice sin comprometer las
reglas fundamentales del modelo de identidad.