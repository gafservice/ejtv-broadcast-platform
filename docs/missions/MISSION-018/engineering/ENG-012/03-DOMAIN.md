# ENG-012 — Modelo de Dominio

---

# Objetivo

Este documento describe el modelo de dominio implementado por el
subsistema **Identity Application Layer (IAM)**.

El dominio representa el núcleo de las reglas de negocio relacionadas
con identidad, autenticación, autorización y administración de acceso.

Su diseño sigue los principios de Domain-Driven Design (DDD) y Clean
Architecture, manteniendo completa independencia respecto a la
infraestructura, el framework web y la tecnología de persistencia.

---

# Principios del dominio

El modelo de dominio fue diseñado siguiendo los siguientes principios.

- Inmutabilidad de las entidades.
- Reglas de negocio centralizadas.
- Independencia tecnológica.
- Consistencia del modelo.
- Expresividad mediante Value Objects.
- Persistencia desacoplada mediante Protocols.

El dominio nunca depende de FastAPI, SQLAlchemy, JWT ni bcrypt.

---

# Componentes principales

El dominio está organizado alrededor de los siguientes elementos.

```text
Identity
│
├── Entities
├── Value Objects
├── Enums
├── Catalog
├── Password Policy
├── Protocols
└── Exceptions
```

Cada uno representa una responsabilidad claramente definida.

---

# Entidades

Las entidades representan objetos con identidad propia dentro del
sistema.

## User

Representa una cuenta autenticable de la plataforma.

Responsabilidades:

- identidad única;
- nombre de usuario;
- correo electrónico;
- contraseña cifrada;
- estado operativo;
- colección de roles.

El usuario constituye la entidad principal del dominio.

---

## Role

Representa un conjunto de permisos agrupados bajo una responsabilidad
funcional.

Ejemplos:

```text
administrator

operator

viewer
```

Los roles simplifican la administración de permisos sin afectar la
granularidad del modelo de autorización.

---

## Permission

Representa una capacidad específica dentro de la plataforma.

Ejemplos:

```text
dashboard.read

dashboard.write

users.manage

streaming.read

alarms.write
```

Los permisos constituyen la unidad mínima utilizada por el sistema de
autorización.

---

## AuthenticatedIdentity

Representa la identidad autenticada utilizada durante una solicitud.

Contiene únicamente la información necesaria para autorizar una
operación.

Su objetivo es evitar exponer la entidad User completa durante el
procesamiento de una petición.

---

# Value Objects

Los Value Objects encapsulan reglas de validación y representan valores
inmutables.

Actualmente el dominio incluye:

```text
UserId

Username

Email

PasswordHash

RoleName

PermissionName
```

Cada uno garantiza que los valores utilizados por el sistema cumplan las
restricciones definidas por el dominio.

---

## UserId

Representa el identificador único del usuario.

Su existencia evita utilizar cadenas de texto arbitrarias como
identificadores.

---

## Username

Representa el nombre de usuario.

Centraliza todas las reglas relacionadas con su validación.

---

## Email

Representa una dirección de correo electrónico válida.

Evita que el resto del sistema procese cadenas sin validar.

---

## PasswordHash

Representa una contraseña cifrada.

El dominio nunca almacena contraseñas en texto plano.

---

## RoleName

Representa el nombre de un rol.

Garantiza consistencia entre el catálogo canónico y la persistencia.

---

## PermissionName

Representa el nombre único de un permiso.

Permite identificar capacidades del sistema sin depender de valores
literales distribuidos por la aplicación.

---

# Enumeraciones

El dominio utiliza enumeraciones para representar estados limitados.

Actualmente se implementa:

```text
UserStatus
```

Valores:

```text
active

disabled

locked
```

El uso de enumeraciones evita estados inválidos y mejora la legibilidad
del código.

---

# Catálogo canónico

Identity mantiene un catálogo oficial de roles y permisos.

Su objetivo es garantizar que toda instalación de la plataforma posea
exactamente la misma definición funcional.

El catálogo define:

- roles;
- permisos;
- relaciones entre ambos.

Durante el bootstrap este catálogo se sincroniza automáticamente con la
base de datos.

Posteriormente se verifica su integridad.

---

# Política de contraseñas

La política de contraseñas constituye una regla del dominio.

No pertenece a la API ni a la infraestructura.

Las reglas implementadas incluyen:

- longitud mínima;
- longitud máxima compatible con bcrypt;
- mayúsculas;
- minúsculas;
- números;
- símbolos;
- eliminación de espacios externos.

Centralizar esta política garantiza un comportamiento uniforme en toda
la plataforma.

---

# Protocols

Los Protocols representan contratos que desacoplan el dominio de la
infraestructura.

Entre ellos:

```text
UserRepository

AuditRepository

IdentityCatalogRepository

PasswordHasher

TokenProvider
```

Los servicios únicamente conocen estos contratos.

Las implementaciones concretas pertenecen a la infraestructura.

---

# Excepciones del dominio

Las excepciones representan reglas de negocio incumplidas.

Ejemplos:

```text
AuthenticationFailed

WeakPassword

UserAlreadyExists

RoleNotFound

PermissionDenied

CannotRemoveLastAdministrator

CannotDisableLastAdministrator
```

Estas excepciones son posteriormente traducidas a respuestas HTTP por la
capa API.

---

# Relaciones entre entidades

```text
User
 │
 ├──────────────► Role
 │                    │
 │                    ▼
 └──────────────► Permission
```

Un usuario posee uno o más roles.

Cada rol contiene uno o más permisos.

La autorización siempre se realiza mediante permisos.

---

# Flujo lógico del dominio

```text
Usuario

↓

Authentication

↓

AuthenticatedIdentity

↓

Authorization

↓

Permission

↓

Operación permitida
```

Las reglas de autorización nunca dependen directamente del nombre del
usuario.

---

# Reglas fundamentales del dominio

El dominio implementa diversas reglas críticas.

Entre ellas:

- un usuario no puede autenticarse si está deshabilitado;
- un usuario bloqueado no puede iniciar sesión;
- las contraseñas deben cumplir la política definida;
- los roles deben pertenecer al catálogo canónico;
- los permisos provienen exclusivamente del catálogo;
- el bootstrap debe ser idempotente;
- el catálogo debe verificarse durante el arranque;
- nunca debe quedar la plataforma sin un administrador activo.

Estas reglas constituyen la base funcional del subsistema IAM.

---

# Independencia del dominio

El dominio fue diseñado para permanecer completamente independiente de
la infraestructura.

No conoce:

- FastAPI;
- SQLAlchemy;
- SQLite;
- PostgreSQL;
- JWT;
- bcrypt;
- HTTP;
- variables de entorno.

Esto permite reutilizar el modelo incluso si la infraestructura cambia
en el futuro.

---

# Beneficios del modelo

El modelo de dominio proporciona:

- alta cohesión;
- bajo acoplamiento;
- facilidad para realizar pruebas;
- mantenimiento simplificado;
- evolución controlada;
- independencia tecnológica;
- consistencia funcional.

---

# Conclusión

El modelo de dominio constituye el núcleo del subsistema Identity.

Todas las reglas críticas relacionadas con usuarios, roles, permisos,
autenticación y autorización residen en esta capa.

Gracias a esta separación, la plataforma puede evolucionar en aspectos
tecnológicos sin comprometer las reglas fundamentales del negocio.