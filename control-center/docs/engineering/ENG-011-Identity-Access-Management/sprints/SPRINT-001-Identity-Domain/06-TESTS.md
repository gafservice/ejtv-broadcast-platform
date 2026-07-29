# SPRINT-001 — Tests

> Estado: estructura inicial creada. Contenido pendiente de desarrollo.

# SPRINT-001 — Tests

---

# Introducción

Este documento define el plan de pruebas correspondiente al Sprint-001 del módulo Identity & Access Management (IAM).

El objetivo es verificar que el dominio de identidad se comporte correctamente antes de incorporar cualquier componente de infraestructura.

Todas las pruebas de este sprint serán pruebas unitarias.

---

# Objetivos

Las pruebas deberán garantizar que:

- El dominio sea consistente.
- Las reglas de negocio sean correctas.
- Las entidades mantengan sus invariantes.
- Los Value Objects validen correctamente sus datos.
- No existan dependencias externas.

---

# Alcance

Este sprint probará únicamente:

- Enumeraciones.
- Excepciones.
- Value Objects.
- Entidades.
- Protocols.

No se probarán:

- FastAPI.
- JWT.
- PostgreSQL.
- Redis.
- HTTP.
- SQLAlchemy.
- Interfaces Web.

---

# Estrategia

Cada componente será probado inmediatamente después de su implementación.

El desarrollo seguirá el siguiente orden:

1. Enumeraciones
2. Excepciones
3. Value Objects
4. Entidades
5. Protocols

No se avanzará al siguiente componente mientras existan pruebas pendientes.

---

# Casos de prueba

## Enumeraciones

Se verificará:

- Valores válidos.
- Comparaciones.
- Estados permitidos.

---

## Excepciones

Se verificará:

- Creación.
- Herencia.
- Mensajes.
- Lanzamiento correcto.

---

## Value Objects

Para cada objeto se validará:

- Construcción válida.
- Construcción inválida.
- Igualdad.
- Inmutabilidad.
- Representación.

---

## Entidades

Para cada entidad se comprobará:

- Creación.
- Estado inicial.
- Reglas de negocio.
- Invariantes.
- Métodos públicos.

---

## Protocols

Se verificará:

- Existencia.
- Métodos requeridos.
- Firmas.
- Compatibilidad con tipado.

---

# Requisitos de ejecución

Las pruebas deberán ejecutarse:

- Sin base de datos.
- Sin red.
- Sin servicios externos.
- Sin dependencias de infraestructura.

---

# Cobertura esperada

| Componente | Cobertura mínima |
|------------|-----------------:|
| Enumeraciones | 100 % |
| Excepciones | 100 % |
| Value Objects | 100 % |
| Entidades | 100 % |
| Protocols | 100 % |

Cobertura total esperada del dominio:

**100 %.**

---

# Herramientas

Las pruebas utilizarán:

- Pytest
- pytest-cov

No se utilizarán mocks salvo que resulten estrictamente necesarios.

---

# Criterios de aceptación

El Sprint-001 únicamente podrá cerrarse cuando:

- Todas las pruebas pasen correctamente.
- No existan errores.
- No existan advertencias relevantes.
- Se mantenga la cobertura objetivo.
- El dominio permanezca desacoplado de la infraestructura.

---

# Resultado esperado

El dominio deberá quedar completamente validado mediante pruebas unitarias, proporcionando una base sólida para el Sprint-002 (Authentication).