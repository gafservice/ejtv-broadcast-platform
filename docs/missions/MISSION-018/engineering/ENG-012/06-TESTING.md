# ENG-012 — Estrategia de Pruebas y Certificación

---

# Objetivo

Este documento describe la estrategia de validación utilizada durante el
desarrollo del subsistema **Identity Application Layer (IAM)**.

Su propósito es demostrar que las funcionalidades implementadas fueron
verificadas de manera sistemática mediante pruebas automatizadas en
diferentes niveles de la arquitectura.

La estrategia adoptada busca garantizar la calidad del software,
preservar el comportamiento esperado del dominio y detectar regresiones
durante la evolución futura de la plataforma.

---

# Filosofía de pruebas

El proceso de pruebas se diseñó bajo los siguientes principios.

## Automatización

Toda funcionalidad crítica debe estar protegida por pruebas
automatizadas.

---

## Repetibilidad

Las pruebas deben producir el mismo resultado independientemente del
entorno donde se ejecuten.

---

## Independencia

Cada prueba debe validar una responsabilidad específica sin depender del
resultado de otras pruebas.

---

## Evidencia objetiva

La calidad del sistema debe demostrarse mediante evidencia ejecutable y
no únicamente mediante revisión manual.

---

# Pirámide de pruebas

El subsistema IAM utiliza una estrategia escalonada de validación.

```text
                    End-to-End
                         ▲
                         │
                 Integración
                         ▲
                         │
                       API
                         ▲
                         │
                    Servicios
                         ▲
                         │
                      Dominio
```

Cada nivel verifica responsabilidades diferentes.

---

# Pruebas del Dominio

Las pruebas de dominio validan las reglas fundamentales del modelo de
negocio.

Entre ellas:

- entidades;
- value objects;
- enumeraciones;
- catálogo de roles;
- catálogo de permisos;
- política de contraseñas;
- excepciones;
- reglas de integridad.

Estas pruebas no dependen de:

- FastAPI;
- SQLAlchemy;
- SQLite;
- JWT;
- infraestructura.

Su ejecución es rápida y completamente determinística.

---

# Pruebas de Servicios

Los servicios de aplicación fueron validados mediante repositorios
simulados (Fake Repositories).

Se verificaron, entre otras capacidades:

## AuthenticationService

- autenticación exitosa;
- credenciales inválidas;
- usuarios bloqueados;
- usuarios deshabilitados.

---

## AuthorizationService

- permisos válidos;
- permisos insuficientes;
- construcción de AuthenticatedIdentity.

---

## IdentityAdministrationService

- creación de usuarios;
- consulta de usuarios;
- listado;
- cambio de estado;
- cambio de contraseña;
- asignación de roles;
- revocación de roles;
- protección del último administrador.

---

## IdentityBootstrapService

- sincronización del catálogo;
- bootstrap idempotente;
- creación del administrador inicial;
- verificación de integridad.

---

# Pruebas de Persistencia

Los adaptadores SQLAlchemy fueron verificados mediante una base de datos
temporal.

Entre ellos:

- UserRepository;
- AuditRepository;
- IdentityCatalogRepository.

Las pruebas comprobaron:

- inserción;
- consulta;
- actualización;
- persistencia de relaciones;
- sincronización del catálogo.

---

# Pruebas de API

Los endpoints REST fueron validados utilizando FastAPI TestClient.

Se verificaron:

- códigos HTTP;
- validación de solicitudes;
- autenticación;
- autorización;
- serialización;
- manejo de errores;
- respuestas JSON.

Las pruebas garantizan que la interfaz pública del IAM permanezca
estable.

---

# Pruebas de Integración

Las pruebas de integración validan la cooperación entre múltiples
componentes del sistema.

Entre ellas:

- servicios;
- persistencia;
- autenticación;
- autorización;
- auditoría.

Estas pruebas utilizan implementaciones reales siempre que resulta
conveniente.

---

# Pruebas End-to-End

La certificación End-to-End representa el nivel más alto de validación.

Las pruebas ejecutan el sistema prácticamente en las mismas condiciones
utilizadas durante la operación real.

Se utilizan componentes reales:

- FastAPI;
- lifespan;
- bootstrap;
- SQLite temporal;
- SQLAlchemy;
- bcrypt;
- JWT;
- auditoría.

---

# Escenario certificado

La primera certificación End-to-End valida el flujo completo del
subsistema.

```text
Inicio de la aplicación
            │
            ▼
Bootstrap automático
            │
            ▼
Sincronización del catálogo
            │
            ▼
Verificación de integridad
            │
            ▼
Login del administrador
            │
            ▼
Emisión del JWT
            │
            ▼
Bearer Authentication
            │
            ▼
Consulta de /auth/me
            │
            ▼
Validación de roles
            │
            ▼
Validación de permisos
            │
            ▼
Persistencia de auditoría
```

Este flujo constituye la evidencia de que el subsistema opera de manera
integral.

---

# Protección contra regresiones

Cada nueva funcionalidad incorpora pruebas antes de considerarse
completada.

Esta estrategia permite detectar automáticamente modificaciones que
afecten el comportamiento esperado del sistema.

El objetivo es preservar la estabilidad del IAM durante toda la vida del
proyecto.

---

# Cobertura funcional

Las pruebas cubren, entre otros aspectos:

- autenticación;
- autorización;
- bootstrap;
- catálogo;
- política de contraseñas;
- administración de usuarios;
- administración de roles;
- persistencia;
- auditoría;
- validación de permisos;
- respuestas HTTP;
- protección del último administrador;
- integridad del catálogo.

---

# Entorno de pruebas

El entorno automatizado utiliza:

- pytest;
- FastAPI TestClient;
- SQLite temporal;
- SQLAlchemy;
- bcrypt;
- JWT;
- repositorios simulados;
- repositorios reales.

Esta combinación permite equilibrar velocidad de ejecución y fidelidad
respecto al entorno de producción.

---

# Resultados

Al finalizar ENG-012 se obtuvo una suite completamente automatizada.

Estado de la certificación:

```text
Total de pruebas ejecutadas

944

Resultado

944 aprobadas

0 fallidas

0 errores

Estado

CERTIFICADO
```

La ejecución completa de la suite constituye la evidencia objetiva de
que el subsistema cumple las especificaciones funcionales definidas para
ENG-012.

---

# Beneficios

La estrategia implementada proporciona:

- detección temprana de errores;
- prevención de regresiones;
- confianza durante el refactor;
- documentación ejecutable;
- despliegues más seguros;
- mantenimiento simplificado.

Cada prueba representa una especificación verificable del comportamiento
esperado del sistema.

---

# Relación con la arquitectura

La estrategia de pruebas sigue la misma organización de la arquitectura
del subsistema.

```text
Dominio
        │
        ▼
Servicios
        │
        ▼
Persistencia
        │
        ▼
API
        │
        ▼
Integración
        │
        ▼
End-to-End
```

Esta correspondencia facilita localizar errores y mantener una cobertura
uniforme en todas las capas del sistema.

---

# Conclusión

La estrategia de pruebas implementada durante ENG-012 permitió validar
el comportamiento del subsistema Identity desde las reglas más básicas
del dominio hasta la operación completa de la aplicación mediante
escenarios End-to-End.

La existencia de una suite automatizada, amplia y reproducible convierte
las pruebas en una parte integral de la arquitectura y proporciona una
base sólida para la evolución futura de la plataforma.

El IAM queda certificado no sólo por su implementación, sino por la
evidencia objetiva aportada por sus pruebas automatizadas.