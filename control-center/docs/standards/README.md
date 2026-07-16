# Manual de Ingeniería

**Proyecto:**
EJTV Broadcast Platform

**Subproyecto:**
EJTV Control Center

**Versión**
1.0

**Estado**
Vigente

---

# Bienvenido

Antes de escribir una sola línea de código es importante comprender cómo se desarrolla ingeniería dentro del proyecto EJTV.

Este directorio reúne el conjunto de normas oficiales utilizadas durante todo el ciclo de vida del proyecto.

Su finalidad consiste en mantener una metodología uniforme que permita construir una plataforma profesional, escalable, mantenible y completamente documentada.

Los estándares aquí descritos no sustituyen el conocimiento técnico.

Lo organizan.

---

# ¿Por qué existen estos estándares?

A medida que un proyecto crece aumenta su complejidad.

Sin reglas claras aparecen diferencias de estilo, duplicación de soluciones, documentación inconsistente y arquitecturas difíciles de mantener.

Los estándares permiten que todas las decisiones técnicas sigan el mismo criterio independientemente del momento en que fueron desarrolladas o de la persona que las implementó.

En otras palabras, los estándares convierten un conjunto de desarrollos individuales en un proyecto de ingeniería.

---

# Organización del Manual

El Manual de Ingeniería se encuentra dividido en siete estándares principales.

Cada uno aborda un aspecto diferente del desarrollo.

```
EDS-001
Engineering Documentation Standard

↓

EDS-002
Engineering Standard

↓

EDS-003
Coding Standard

↓

EDS-004
Git Workflow Standard

↓

EDS-005
Testing Standard

↓

EDS-006
Architecture Standard

↓

EDS-007
Technical Communication Standard
```

Aunque cada documento puede consultarse de forma independiente, se recomienda leerlos en el orden anterior.

Cada estándar utiliza conceptos definidos en los documentos previos.

---

# Relación entre los estándares

Cada estándar responde una pregunta distinta.

| Estándar | Pregunta que responde |
|----------|-----------------------|
| EDS-001 | ¿Cómo documentamos? |
| EDS-002 | ¿Cómo hacemos ingeniería? |
| EDS-003 | ¿Cómo escribimos código? |
| EDS-004 | ¿Cómo gestionamos la evolución del proyecto? |
| EDS-005 | ¿Cómo validamos las capacidades? |
| EDS-006 | ¿Cómo está organizada la arquitectura? |
| EDS-007 | ¿Cómo comunicamos el conocimiento técnico? |

Juntos conforman una metodología completa de trabajo.

---

# Cómo utilizar este manual

Cuando surja una duda durante el desarrollo, debe consultarse el estándar correspondiente.

Por ejemplo.

Si la duda está relacionada con documentación:

→ EDS-001

Si la duda está relacionada con arquitectura:

→ EDS-006

Si la duda está relacionada con pruebas:

→ EDS-005

Si la duda está relacionada con Git:

→ EDS-004

El objetivo consiste en evitar decisiones improvisadas.

Las reglas ya se encuentran definidas.

---

# Principios Fundamentales del Proyecto

Toda decisión técnica deberá respetar los siguientes principios.

• Comprender antes de programar.

• La arquitectura gobierna al código.

• Toda capacidad debe poder demostrarse.

• Todo Sprint deja una capacidad.

• Toda misión deja conocimiento.

• El código implementa capacidades.

• La documentación preserva conocimiento.

---

# Flujo Oficial de Desarrollo

Todo desarrollo sigue el mismo proceso.

```
Problema

↓

Análisis

↓

Diseño

↓

Implementación

↓

Pruebas

↓

Documentación

↓

Baseline

↓

Commit

↓

Push
```

Ninguna etapa puede omitirse.

---

# El concepto de Capacidad

Dentro del proyecto EJTV no se habla únicamente de funcionalidades.

Se habla de capacidades.

Una capacidad representa una habilidad permanente adquirida por la plataforma.

Por ejemplo.

• Obtener información del sistema.

• Administrar MediaMTX.

• Administrar FFmpeg.

• Supervisar la red.

• Gestionar canales.

Cada Sprint incorpora exactamente una nueva capacidad.

---

# El concepto de Misión

Una misión constituye una unidad completa de ingeniería.

Incluye:

- análisis;
- diseño;
- implementación;
- pruebas;
- documentación;
- evidencias;
- baseline.

Una misión no termina cuando el código funciona.

Termina cuando todo el conocimiento generado ha quedado preservado.

---

# El concepto de Sprint

Un Sprint representa el trabajo necesario para incorporar una nueva capacidad al sistema.

Cada Sprint deja un resultado permanente.

Nunca se realizan desarrollos experimentales directamente sobre la rama principal.

---

# Filosofía del Proyecto

El objetivo del proyecto EJTV no consiste únicamente en construir software.

Su propósito es construir una plataforma profesional cuya evolución pueda comprenderse completamente incluso muchos años después de haber sido desarrollada.

Por esta razón el conocimiento posee el mismo valor que el código.

---

# Nuestra Cultura de Ingeniería

Este proyecto adopta una filosofía de mejora continua.

Cada nuevo Sprint debe dejar el proyecto en mejores condiciones de las que lo encontró.

La calidad no se incorpora al final.

Se construye desde el inicio.

---

# Frases que Definen el Proyecto

La cultura técnica del proyecto puede resumirse mediante las siguientes expresiones.

> Donde hay orden, está Dios.

> Comprender antes de programar.

> La arquitectura gobierna al código.

> No estamos desarrollando funciones; estamos construyendo capacidades.

> Administrar infraestructura multimedia profesional desde una plataforma unificada.

> Toda misión deja una capacidad.

> Toda misión deja conocimiento.

> Todo Sprint deja un legado.

---

# Conclusión

El presente Manual de Ingeniería constituye la referencia principal para el desarrollo del proyecto EJTV Broadcast Platform.

Todo nuevo integrante deberá conocer estos estándares antes de comenzar cualquier implementación.

La finalidad no consiste únicamente en producir software funcional.

La finalidad consiste en construir una plataforma sólida, comprensible y capaz de evolucionar durante muchos años sin perder el conocimiento generado durante su desarrollo.
