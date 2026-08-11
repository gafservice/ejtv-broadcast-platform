# ENG-012 — Seguridad

---

# Objetivo

Este documento describe la estrategia de seguridad implementada por el
subsistema **Identity Application Layer (IAM)**.

Su propósito es definir los mecanismos utilizados para proteger la
identidad de los usuarios, controlar el acceso a los recursos de la
plataforma y garantizar la integridad del modelo de autorización.

Las medidas implementadas constituyen la primera línea de defensa de la
plataforma Broadcast.

---

# Principios de seguridad

El diseño del subsistema Identity se basa en los siguientes principios.

## Autenticación centralizada

Toda autenticación debe realizarse exclusivamente mediante Identity.

Ningún módulo implementa mecanismos propios de autenticación.

---

## Autorización basada en permisos

Las operaciones protegidas verifican permisos específicos y no nombres
de usuario.

Este enfoque desacopla la lógica del negocio de la administración de
usuarios.

---

## Mínimo privilegio

Cada usuario posee únicamente los permisos necesarios para cumplir su
función.

Los permisos adicionales deben asignarse explícitamente.

---

## Defensa en profundidad

La seguridad no depende de un único mecanismo.

El sistema combina:

- autenticación;
- autorización;
- política de contraseñas;
- auditoría;
- catálogo canónico;
- verificación de integridad.

---

# Autenticación

La autenticación verifica la identidad del usuario mediante:

```text
Username

+

Password
```

La contraseña nunca se almacena en texto plano.

El flujo implementado es:

```text
Usuario

↓

AuthenticationService

↓

PasswordHasher

↓

JWT

↓

Cliente autenticado
```

---

# JWT

Una autenticación exitosa produce un token JWT firmado.

El token representa la identidad autenticada durante toda la solicitud.

Las rutas protegidas aceptan únicamente:

```text
Authorization: Bearer <token>
```

El token contiene la información necesaria para reconstruir la
identidad autenticada sin consultar nuevamente las credenciales.

---

# Bearer Authentication

Cada solicitud protegida sigue el siguiente flujo.

```text
Solicitud HTTP

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

Si alguna etapa falla, la operación se rechaza.

---

# Autorización

La autorización se basa exclusivamente en permisos.

Los endpoints no comparan:

- nombres de usuario;
- identificadores;
- roles específicos.

En su lugar utilizan:

```python
Depends(require_permission("permission.name"))
```

Este diseño facilita la evolución del catálogo sin modificar los
controladores HTTP.

---

# Roles

Identity implementa un catálogo canónico de roles.

Actualmente incluye:

```text
administrator

operator

viewer
```

Cada rol representa un conjunto de permisos previamente definido por el
dominio.

---

# Permisos

Los permisos constituyen la unidad mínima de autorización.

Ejemplos:

```text
dashboard.read

dashboard.write

users.manage

streaming.read

alarms.write
```

Las operaciones protegidas siempre verifican permisos.

Nunca verifican roles directamente.

---

# Política de contraseñas

La política de contraseñas es una regla del dominio.

Toda contraseña nueva debe cumplir los siguientes requisitos.

## Longitud mínima

```text
12 caracteres
```

---

## Longitud máxima

```text
72 bytes UTF-8
```

Este límite mantiene compatibilidad con bcrypt.

---

## Complejidad

La contraseña debe contener:

- una letra mayúscula;
- una letra minúscula;
- un número;
- un símbolo.

---

## Espacios

No se permiten espacios al inicio ni al final.

---

# Bcrypt

Las contraseñas nunca se almacenan en texto plano.

El subsistema utiliza bcrypt como algoritmo de hash.

Beneficios:

- algoritmo ampliamente probado;
- resistente a ataques de fuerza bruta;
- configurable mediante factor de costo.

---

# Protección del último administrador

Una regla crítica del dominio impide dejar la plataforma sin un
administrador activo.

No es posible:

- eliminar el rol administrator del último administrador;
- deshabilitarlo;
- bloquearlo.

La operación únicamente se permite cuando existe otro administrador con
estado activo.

Esta protección garantiza la continuidad administrativa del sistema.

---

# Bootstrap seguro

El bootstrap inicializa Identity de forma controlada.

Durante el proceso:

- sincroniza el catálogo;
- verifica la integridad;
- crea el administrador inicial;
- registra auditoría.

El administrador únicamente se crea durante la instalación inicial.

---

# Verificación de integridad

Antes de aceptar tráfico HTTP, Identity valida que la base de datos sea
coherente con el catálogo canónico.

La validación detecta:

- roles faltantes;
- roles inesperados;
- permisos inconsistentes.

Si la verificación falla, la aplicación detiene el arranque.

---

# Auditoría

Las operaciones críticas generan registros persistentes.

Entre ellas:

- login;
- creación de usuarios;
- cambio de estado;
- cambio de contraseña;
- asignación de roles;
- revocación de roles;
- bootstrap;
- sincronización del catálogo.

La auditoría permite reconstruir posteriormente las acciones realizadas
sobre el sistema.

---

# Manejo de errores

El dominio comunica condiciones de seguridad mediante excepciones
específicas.

Ejemplos:

```text
AuthenticationFailed

PermissionDenied

WeakPassword

CannotRemoveLastAdministrator

CannotDisableLastAdministrator
```

La API convierte estas excepciones en respuestas HTTP apropiadas.

---

# Respuestas HTTP

Las respuestas de seguridad utilizan códigos estándar.

| Código | Significado |
|---------|-------------|
| 401 | Usuario no autenticado |
| 403 | Permiso insuficiente |
| 404 | Recurso inexistente |
| 409 | Conflicto con reglas del dominio |
| 422 | Solicitud inválida |

---

# Buenas prácticas implementadas

El subsistema incorpora diversas prácticas recomendadas.

Entre ellas:

- separación entre autenticación y autorización;
- hashing robusto de contraseñas;
- catálogo centralizado;
- políticas únicas de contraseña;
- auditoría persistente;
- bootstrap idempotente;
- verificación automática de integridad;
- protección del último administrador;
- uso de Protocols para desacoplar la infraestructura.

---

# Seguridad por capas

La protección del sistema se construye mediante múltiples niveles.

```text
Usuario

↓

Password Policy

↓

Authentication

↓

JWT

↓

Bearer Validation

↓

Authorization

↓

Permission Verification

↓

Business Operation

↓

Audit Log
```

Cada nivel complementa al anterior.

No existe un único punto responsable de toda la seguridad.

---

# Futuras capacidades

La arquitectura fue diseñada para incorporar posteriormente nuevas
capacidades sin modificar el núcleo del dominio.

Entre ellas:

- autenticación multifactor (MFA);
- recuperación segura de contraseña;
- refresh tokens;
- rotación automática de claves JWT;
- OAuth2;
- OpenID Connect;
- LDAP;
- Active Directory;
- proveedores externos de identidad.

---

# Conclusión

La estrategia de seguridad implementada por ENG-012 proporciona una base
sólida para proteger la plataforma Broadcast.

La combinación de autenticación centralizada, autorización basada en
permisos, políticas de contraseña, auditoría, bootstrap seguro y
verificación de integridad permite que el resto de los módulos confíen
en Identity como autoridad única para el control de acceso.

A partir de este subsistema, toda nueva funcionalidad de la plataforma
deberá integrarse con Identity, evitando la implementación de mecanismos
paralelos de autenticación o autorización.
