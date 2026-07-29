# ENG-011 — Architectural Decisions

> Estado: estructura inicial creada. Contenido pendiente de desarrollo.

# ENG-011 — Architectural Decisions

---

# Introducción

Este documento registra las decisiones arquitectónicas relevantes tomadas durante el desarrollo del módulo Identity & Access Management (IAM).

Su propósito es preservar el contexto técnico de cada decisión, facilitando el mantenimiento del sistema y evitando que futuras modificaciones pierdan la justificación original del diseño.

Cada decisión recibe un identificador único (ADR – Architecture Decision Record) y permanece como parte permanente de la documentación del proyecto.

---

# ADR-001 — Adoptar Clean Architecture

## Estado

Aceptada.

## Contexto

IAM constituye un servicio transversal que será utilizado por todos los módulos de la plataforma.

La incorporación de dependencias directas hacia FastAPI, JWT o cualquier componente de infraestructura limitaría la reutilización del dominio y dificultaría las pruebas.

## Decisión

Implementar el módulo siguiendo los principios de Clean Architecture.

## Consecuencias

- Dominio independiente.
- Mayor mantenibilidad.
- Alta cobertura de pruebas.
- Facilidad para sustituir tecnologías de infraestructura.

---

# ADR-002 — Separar Autenticación y Autorización

## Estado

Aceptada.

## Contexto

Aunque ambos conceptos están relacionados, representan responsabilidades diferentes.

## Decisión

Implementar Authentication y Authorization como componentes independientes.

## Consecuencias

- Menor acoplamiento.
- Mayor reutilización.
- Evolución independiente.

---

# ADR-003 — Utilizar RBAC

## Estado

Aceptada.

## Contexto

La plataforma requiere un mecanismo sencillo y escalable para controlar el acceso a recursos.

## Decisión

Adoptar un modelo Role-Based Access Control (RBAC).

## Consecuencias

- Administración simplificada.
- Fácil incorporación de nuevos roles.
- Compatibilidad futura con ABAC.

---

# ADR-004 — Auditoría Obligatoria

## Estado

Aceptada.

## Contexto

Toda operación administrativa debe ser trazable.

## Decisión

Registrar todos los eventos relevantes de autenticación, autorización y administración.

## Consecuencias

- Mayor seguridad.
- Trazabilidad completa.
- Base para reportes y análisis.

---

# ADR-005 — Dominio Independiente de la Persistencia

## Estado

Aceptada.

## Contexto

El modelo de identidad no debe depender de una base de datos específica.

## Decisión

Definir repositorios mediante interfaces y delegar la persistencia a la infraestructura.

## Consecuencias

- Flexibilidad tecnológica.
- Mejor capacidad de pruebas.
- Evolución independiente de la base de datos.

---

# Futuras decisiones

Este documento continuará creciendo conforme evolucione el módulo.

Entre las decisiones previstas se encuentran:

- Selección del algoritmo de hash.
- Estrategia de expiración de tokens.
- Gestión de sesiones.
- Integración con proveedores externos.
- Multi-Factor Authentication (MFA).
- Multi-Tenant.

---

# Conclusión

Las decisiones registradas en este documento constituyen la memoria arquitectónica del módulo IAM y deberán mantenerse actualizadas durante toda su evolución.