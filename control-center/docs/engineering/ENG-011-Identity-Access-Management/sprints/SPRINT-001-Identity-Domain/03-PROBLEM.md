# SPRINT-001 — Problem

> Estado: estructura inicial creada. Contenido pendiente de desarrollo.

# SPRINT-001 — Problem

---

# Introducción

La plataforma Broadcast ha evolucionado incorporando múltiples módulos de ingeniería para la administración del sistema, la red, el streaming, los diagnósticos, las alarmas y la automatización.

Hasta este punto del proyecto, la mayoría de los servicios pueden ser utilizados sin un mecanismo centralizado que identifique a los usuarios, controle sus permisos o registre de manera uniforme las acciones realizadas.

A medida que la plataforma crece y comienza a incorporar interfaces administrativas, API públicas y un NOC Web, esta ausencia representa un riesgo tanto para la seguridad como para la mantenibilidad del sistema.

---

# Situación actual

Actualmente:

- No existe un modelo de identidad.
- No existe una representación formal de usuarios.
- No existen roles.
- No existe un modelo de permisos.
- No existe autenticación.
- No existe autorización.
- No existe un registro uniforme de auditoría.

Cada nuevo módulo tendría que implementar estas capacidades de forma independiente.

---

# Problema principal

La ausencia de un dominio de identidad genera múltiples inconvenientes.

## Duplicación de lógica

Cada componente podría implementar sus propios mecanismos para validar usuarios y permisos.

Esto produciría:

- Código repetido.
- Inconsistencias.
- Mayor mantenimiento.
- Mayor probabilidad de errores.

---

## Alto acoplamiento

Si la autenticación se implementara directamente dentro de FastAPI o del NOC Web, el dominio dependería de tecnologías específicas.

Esto dificultaría:

- Las pruebas.
- La reutilización.
- La evolución tecnológica.

---

## Falta de trazabilidad

Sin un modelo común de identidad resulta imposible responder preguntas como:

- ¿Quién reinició un servicio?
- ¿Quién confirmó una alarma?
- ¿Quién modificó una configuración?
- ¿Quién creó un nuevo usuario?

Estas operaciones deben quedar registradas de manera uniforme.

---

## Escalabilidad limitada

En las primeras etapas del proyecto puede existir un único administrador.

Sin embargo, la plataforma está diseñada para evolucionar hacia un entorno con múltiples perfiles de usuario.

Por ejemplo:

- Administradores.
- Operadores del NOC.
- Clientes.
- Integradores mediante API.
- Organizaciones independientes.

Sin un dominio de identidad esta evolución obligaría a rediseñar gran parte del sistema.

---

# Impacto sobre la arquitectura

La ausencia de IAM afecta transversalmente a todos los módulos de ingeniería.

Entre ellos:

- System Engineering.
- Network Engineering.
- Streaming Engineering.
- Diagnostics.
- Alarm Management.
- Reporting.
- Automation.
- AI Operations.

Todos requieren conocer quién ejecuta una operación y si posee autorización para realizarla.

---

# Justificación del Sprint-001

Antes de implementar autenticación, JWT o protección de endpoints es necesario definir el lenguaje del dominio.

Este sprint tiene como propósito construir ese lenguaje.

Se establecerán:

- Entidades.
- Objetos de valor.
- Interfaces.
- Reglas de negocio.
- Relaciones entre conceptos.

Todo ello sin depender de tecnologías concretas.

---

# Restricciones

Durante este sprint no se resolverán problemas relacionados con:

- Persistencia.
- Protocolos HTTP.
- Seguridad criptográfica.
- Tokens.
- Interfaces gráficas.
- Integración con FastAPI.

Estas responsabilidades corresponden a los sprints posteriores.

---

# Resultado esperado

Al finalizar este sprint la plataforma dispondrá de un dominio de identidad completamente definido.

Este dominio constituirá la base sobre la cual se implementarán:

- Authentication.
- Authorization.
- Audit.
- NOC Web Login.
- Gestión de usuarios.
- Protección de la API.

---

# Conclusión

El problema que resuelve el Sprint-001 no consiste en permitir que un usuario inicie sesión.

Su verdadero propósito es proporcionar un modelo de identidad sólido, independiente y reutilizable que permita construir todas las funcionalidades de seguridad de la plataforma sin comprometer la arquitectura ni duplicar responsabilidades.