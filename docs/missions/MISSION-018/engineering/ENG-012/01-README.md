# ENG-012 — Identity Application Layer

## 1. Identificación

| Campo | Valor |
|---|---|
| Misión | `MISSION-018` |
| Ingeniería | `ENG-012` |
| Nombre | Identity Application Layer |
| Subsistema | Identity and Access Management — IAM |
| Estado técnico | Implementado y validado |
| Estado documental | Cierre formal en progreso |
| Rama de desarrollo | `feature/eng-012-identity-application` |
| Último hito técnico | `ENG-012F.6-complete` |
| Commit del último hito | `39a57ae` |

---

## 2. Propósito

`ENG-012` implementa el subsistema de identidad, autenticación,
autorización y administración de acceso de la plataforma Broadcast.

Su propósito es ofrecer una base única y reutilizable para que los
módulos actuales y futuros puedan proteger sus operaciones sin volver
a implementar mecanismos propios de:

- autenticación;
- emisión y validación de tokens;
- autorización;
- administración de usuarios;
- gestión de roles;
- gestión de permisos;
- almacenamiento seguro de contraseñas;
- auditoría;
- bootstrap;
- verificación de integridad.

El subsistema IAM se diseña como una capacidad transversal de la
plataforma. No pertenece exclusivamente al NOC Web ni a un servicio de
streaming específico.

Todos los componentes protegidos deberán consumir los contratos y
dependencias definidos por Identity.

---

## 3. Objetivo de ingeniería

El objetivo principal de `ENG-012` fue transformar una necesidad
inicial de acceso administrativo básico en un subsistema completo,
desacoplado y verificable.

La implementación debía garantizar:

1. autenticación centralizada;
2. autorización basada en permisos;
3. independencia entre dominio, aplicación, API e infraestructura;
4. persistencia desacoplada mediante contratos;
5. roles y permisos canónicos;
6. bootstrap seguro e idempotente;
7. trazabilidad de las operaciones;
8. protección contra la pérdida del último administrador activo;
9. política de contraseñas uniforme;
10. capacidad de ser consumido por todos los módulos futuros.

---

## 4. Alcance implementado

### 4.1 Autenticación

El subsistema permite:

- autenticar usuarios mediante nombre de usuario y contraseña;
- verificar contraseñas mediante bcrypt;
- emitir tokens JWT firmados;
- validar tokens Bearer;
- recuperar la identidad autenticada;
- rechazar credenciales inválidas;
- rechazar usuarios deshabilitados;
- rechazar usuarios bloqueados;
- registrar autenticaciones exitosas en auditoría.

Endpoints principales:

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me

# ENG-012 — Identity Application Layer

---

# Estado

| Campo | Valor |
|-------|--------|
| Misión | MISSION-018 |
| Ingeniería | ENG-012 |
| Nombre | Identity Application Layer |
| Subsistema | Identity and Access Management (IAM) |
| Estado | Implementado y certificado técnicamente |
| Documentación | En proceso de cierre formal (ENG-012G) |

---

# ¿Qué es ENG-012?

ENG-012 corresponde al desarrollo del subsistema de **Identity and Access
Management (IAM)** de la plataforma Broadcast.

Este subsistema proporciona una infraestructura unificada para la
autenticación, autorización y administración de identidades utilizada por
todos los componentes actuales y futuros de la plataforma.

Identity constituye uno de los pilares fundamentales de la arquitectura,
ya que centraliza las responsabilidades relacionadas con el acceso seguro
a los servicios y evita que cada módulo implemente sus propios mecanismos
de autenticación o control de permisos.

A partir de este subsistema, cualquier componente de la plataforma puede
proteger sus recursos utilizando los contratos públicos definidos por
Identity.

---

# Objetivo

El objetivo de ENG-012 fue diseñar e implementar un sistema de identidad
robusto, desacoplado y reutilizable que cumpliera con los siguientes
principios de ingeniería:

- autenticación centralizada;
- autorización basada en permisos;
- administración segura de usuarios;
- catálogo canónico de roles y permisos;
- auditoría completa de operaciones;
- bootstrap automático del sistema;
- verificación de integridad del catálogo;
- independencia entre dominio e infraestructura;
- alta capacidad de mantenimiento y evolución.

Más que resolver el problema del inicio de sesión, el objetivo fue crear
una base permanente sobre la cual construir el resto de la plataforma.

---

# ¿Qué se implementó?

Durante ENG-012 se desarrollaron las capacidades principales del
subsistema IAM.

Entre ellas destacan:

## Autenticación

- inicio de sesión mediante usuario y contraseña;
- emisión de tokens JWT;
- autenticación Bearer;
- recuperación de la identidad autenticada.

---

## Autorización

- permisos canónicos;
- roles predefinidos;
- protección declarativa de endpoints;
- validación automática de permisos.

---

## Administración de usuarios

- creación de usuarios;
- consulta individual;
- listado;
- cambio de estado;
- cambio administrativo de contraseña;
- asignación y revocación de roles.

---

## Seguridad

- contraseñas protegidas mediante bcrypt;
- política centralizada de contraseñas;
- protección del último administrador activo;
- validaciones de integridad.

---

## Bootstrap

- inicialización automática del subsistema;
- sincronización del catálogo canónico;
- creación idempotente del administrador inicial;
- verificación del estado del sistema durante el arranque.

---

## Auditoría

Todas las operaciones relevantes generan registros persistentes de
auditoría que permiten mantener la trazabilidad del sistema.

---

## Persistencia

El subsistema implementa una arquitectura desacoplada basada en
Protocols y repositorios SQLAlchemy, permitiendo sustituir la
infraestructura sin modificar el dominio.

---

## Pruebas

El desarrollo fue acompañado por pruebas de:

- dominio;
- servicios;
- persistencia;
- API;
- integración;
- End-to-End.

---

# Resultado

Al finalizar ENG-012 se obtuvo un subsistema de Identity completamente
funcional y preparado para ser utilizado por toda la plataforma.

Entre los principales resultados alcanzados destacan:

- arquitectura desacoplada siguiendo Clean Architecture;
- modelo de dominio estable;
- catálogo canónico de roles y permisos;
- bootstrap automático;
- verificación de integridad;
- auditoría integrada;
- protección de operaciones críticas;
- infraestructura de pruebas End-to-End;
- validación completa mediante la suite automatizada del proyecto.

El resultado no consiste únicamente en un mecanismo de autenticación,
sino en un subsistema completo de gestión de identidad listo para
convertirse en uno de los pilares de la plataforma Broadcast.

---

# Documentación del cierre

El cierre de ENG-012 está organizado en los siguientes documentos.

| Documento | Descripción |
|-----------|-------------|
| **01-README.md** | Visión general del subsistema |
| **02-ARCHITECTURE.md** | Arquitectura técnica |
| **03-DOMAIN.md** | Modelo de dominio |
| **04-BOOTSTRAP.md** | Inicialización y recuperación |
| **05-SECURITY.md** | Seguridad y políticas |
| **06-TESTING.md** | Estrategia y resultados de pruebas |
| **07-EVIDENCE.md** | Evidencias técnicas y versionado |
| **08-ADR.md** | Decisiones de arquitectura |
| **09-CHECKLIST.md** | Criterios de aceptación |
| **10-CLOSURE.md** | Cierre formal de ENG-012 |

---

# Estado del proyecto

ENG-012 representa la consolidación del subsistema de identidad de la
plataforma Broadcast.

A partir de este punto, los módulos futuros consumirán los servicios de
Identity sin necesidad de desarrollar mecanismos propios de
autenticación, autorización o administración de usuarios.

Con la finalización de ENG-012, el proyecto dispone de una base sólida
sobre la cual continuar el desarrollo del NOC, los nodos especializados
y los demás componentes de la plataforma.