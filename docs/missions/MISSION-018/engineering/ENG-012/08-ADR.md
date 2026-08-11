# ENG-012 — Architecture Decision Record (ADR)

---

# Objetivo

Este documento registra las principales decisiones de arquitectura
tomadas durante el desarrollo del subsistema **Identity Application Layer
(IAM)**.

Su propósito es preservar el razonamiento técnico que motivó cada
decisión, facilitando el mantenimiento, la evolución y la incorporación
de nuevos ingenieros al proyecto.

Las decisiones aquí documentadas representan el estado aprobado al
finalizar ENG-012.

---

# Filosofía

Toda decisión de arquitectura implica compromisos.

En lugar de documentar únicamente el resultado, este documento explica:

- el problema identificado;
- las alternativas consideradas;
- la decisión adoptada;
- la justificación técnica;
- las consecuencias para la plataforma.

Este enfoque permite comprender el contexto de diseño incluso varios
años después de la implementación.

---

# ADR-001

## El IAM será un subsistema independiente

### Problema

Cada módulo de la plataforma necesita autenticación y autorización.

Implementar estos mecanismos de forma independiente provocaría
duplicación de código, inconsistencias y mayores costos de
mantenimiento.

### Decisión

Construir un subsistema Identity completamente independiente del resto
de la plataforma.

### Justificación

Centralizar la gestión de identidad garantiza un único punto de verdad
para usuarios, roles, permisos y autenticación.

### Consecuencias

Todos los módulos deberán consumir Identity.

Ningún módulo implementará autenticación propia.

---

# ADR-002

## Adopción de Clean Architecture

### Problema

La lógica del negocio no debe depender de frameworks ni tecnologías
específicas.

### Decisión

Organizar el software en las capas:

- API;
- Application;
- Domain;
- Infrastructure.

### Justificación

Permite reemplazar tecnologías sin modificar las reglas del negocio.

### Consecuencias

El dominio permanece completamente independiente de FastAPI,
SQLAlchemy, JWT y SQLite.

---

# ADR-003

## Uso de Protocols para desacoplar la persistencia

### Problema

El dominio necesita acceder a datos sin conocer su implementación.

### Decisión

Definir contratos mediante Protocols e implementar los repositorios en
la infraestructura.

### Justificación

El dominio sólo depende de interfaces.

### Consecuencias

La persistencia puede migrarse a otra tecnología sin modificar el
modelo de negocio.

---

# ADR-004

## Catálogo canónico de roles y permisos

### Problema

La definición de roles distribuida en múltiples lugares puede producir
inconsistencias.

### Decisión

Mantener un único catálogo oficial dentro del dominio.

### Justificación

Existe una única definición autorizada para roles y permisos.

### Consecuencias

Todas las instalaciones de la plataforma utilizan exactamente el mismo
modelo de autorización.

---

# ADR-005

## Bootstrap automático

### Problema

La preparación manual del subsistema aumenta el riesgo operativo.

### Decisión

Ejecutar automáticamente el bootstrap durante el arranque de la
aplicación.

### Justificación

Reduce errores de instalación y garantiza consistencia.

### Consecuencias

Identity siempre inicia desde un estado conocido.

---

# ADR-006

## Sincronización automática del catálogo

### Problema

El catálogo persistido puede quedar desactualizado respecto al dominio.

### Decisión

Sincronizar automáticamente el catálogo durante el bootstrap.

### Justificación

Mantiene alineada la base de datos con la definición oficial del
sistema.

### Consecuencias

La actualización del catálogo deja de depender de operaciones
manuales.

---

# ADR-007

## Verificación obligatoria de integridad

### Problema

La plataforma no debe operar con un modelo de seguridad inconsistente.

### Decisión

Validar la integridad del catálogo antes de aceptar solicitudes HTTP.

### Justificación

Detecta alteraciones o instalaciones incompletas.

### Consecuencias

Si la verificación falla, el proceso de arranque se detiene.

---

# ADR-008

## Política de contraseñas en el dominio

### Problema

Las reglas de contraseña no deben duplicarse en distintos módulos.

### Decisión

Implementar una política única dentro del dominio.

### Justificación

Garantiza un comportamiento uniforme en toda la plataforma.

### Consecuencias

Toda creación o modificación de contraseñas utiliza las mismas reglas.

---

# ADR-009

## Autorización basada en permisos

### Problema

Controlar acceso mediante roles limita la flexibilidad del sistema.

### Decisión

Autorizar operaciones utilizando permisos.

### Justificación

Los roles pueden evolucionar sin modificar los endpoints.

### Consecuencias

Las rutas protegidas verifican permisos y no nombres de roles.

---

# ADR-010

## Protección del último administrador

### Problema

La plataforma nunca debe quedar sin capacidad administrativa.

### Decisión

Impedir eliminar, bloquear o deshabilitar al último administrador
activo.

### Justificación

Garantiza la continuidad operativa del sistema.

### Consecuencias

Siempre existirá al menos un administrador con capacidad de gestión.

---

# ADR-011

## Auditoría integrada

### Problema

Las operaciones críticas deben ser trazables.

### Decisión

Registrar eventos de seguridad y administración en un repositorio de
auditoría.

### Justificación

Facilita investigaciones, soporte y cumplimiento de políticas internas.

### Consecuencias

Todas las acciones relevantes generan evidencia persistente.

---

# ADR-012

## Estrategia de pruebas multinivel

### Problema

Las pruebas de un único nivel no ofrecen suficiente confianza.

### Decisión

Adoptar una pirámide de pruebas:

```text
Dominio

↓

Servicios

↓

Persistencia

↓

API

↓

Integración

↓

End-to-End
```

### Justificación

Cada nivel valida responsabilidades diferentes.

### Consecuencias

La calidad del subsistema queda respaldada por evidencia objetiva.

---

# Resumen de decisiones

| ADR | Decisión |
|------|----------|
| ADR-001 | IAM independiente |
| ADR-002 | Clean Architecture |
| ADR-003 | Protocols y repositorios |
| ADR-004 | Catálogo canónico |
| ADR-005 | Bootstrap automático |
| ADR-006 | Sincronización del catálogo |
| ADR-007 | Verificación de integridad |
| ADR-008 | Política de contraseñas en el dominio |
| ADR-009 | Autorización basada en permisos |
| ADR-010 | Protección del último administrador |
| ADR-011 | Auditoría integrada |
| ADR-012 | Estrategia de pruebas multinivel |

---

# Impacto en la plataforma

Las decisiones adoptadas durante ENG-012 trascienden el subsistema
Identity.

Constituyen lineamientos arquitectónicos que servirán como referencia
para el diseño de los futuros componentes de la plataforma, incluyendo:

- NOC;
- Streaming;
- Alarmas;
- Automatización;
- Nodos especializados;
- Transcodificación;
- Monitoreo distribuido.

De esta forma, ENG-012 establece no sólo un subsistema funcional, sino
también un conjunto de principios de ingeniería que podrán aplicarse de
forma consistente al crecimiento de toda la plataforma.

---

# Conclusión

Las decisiones documentadas en este ADR representan el conocimiento
arquitectónico adquirido durante el desarrollo de ENG-012.

Preservar estas decisiones evita que futuras modificaciones rompan los
principios fundamentales del sistema y proporciona una base sólida para
la evolución controlada del subsistema Identity y del resto de la
plataforma.