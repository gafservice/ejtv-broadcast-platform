# Engineering Standard (EDS-002)

**Código del estándar:** EDS-002

**Nombre:**
Engineering Standard

**Proyecto:**
EJTV Broadcast Platform

**Subproyecto:**
EJTV Control Center

**Versión:**
1.0

**Estado:**
Vigente

**Autor:**
Gerardo Araya Fallas

---

# 1. Introducción

El presente documento establece el estándar oficial de ingeniería utilizado durante el desarrollo del proyecto EJTV Broadcast Platform y del EJTV Control Center.

Su propósito consiste en definir una metodología uniforme para analizar problemas, diseñar soluciones, implementar capacidades, realizar pruebas y preservar el conocimiento generado durante el desarrollo del proyecto.

Este documento no describe un lenguaje de programación, un framework o un sistema operativo.

Describe la forma de pensar y trabajar dentro del proyecto.

---

# 2. Propósito

Todo proyecto de ingeniería necesita reglas claras.

Cuando cada desarrollador trabaja de una manera diferente, el proyecto pierde consistencia, aumenta su complejidad y se vuelve difícil de mantener.

El propósito de este estándar es garantizar que cada nueva capacidad desarrollada siga exactamente el mismo proceso de ingeniería.

De esta manera el proyecto podrá crecer durante años sin perder orden ni calidad.

---

# 3. Filosofía del Proyecto

El proyecto EJTV no busca únicamente desarrollar software.

Su objetivo principal consiste en construir una plataforma profesional cuya arquitectura, funcionamiento y evolución puedan comprenderse completamente.

Por esta razón cada línea de código debe estar respaldada por una decisión técnica claramente documentada.

En este proyecto no existen desarrollos improvisados.

Toda implementación responde a un diseño previamente analizado.

---

# 4. Principios Fundamentales

El desarrollo del proyecto se rige por los siguientes principios.

## 4.1 Comprender antes de programar

Ninguna implementación inicia sin haber comprendido completamente el problema.

Primero se analiza.

Luego se diseña.

Finalmente se implementa.

---

## 4.2 La arquitectura gobierna al código

El código nunca define la arquitectura.

Es la arquitectura quien determina cómo debe escribirse el código.

Cuando ambas entran en conflicto, siempre prevalece la arquitectura.

---

## 4.3 Cada módulo posee una única responsabilidad

Todo módulo debe resolver un único problema.

No deben existir módulos que realicen múltiples tareas no relacionadas.

Este principio facilita el mantenimiento y la evolución futura.

---

## 4.4 Las dependencias siempre apuntan hacia el dominio

El dominio representa el conocimiento del negocio.

Por esta razón ninguna tecnología externa debe contaminar el dominio.

Frameworks, sistemas operativos, bases de datos o librerías externas permanecen aislados mediante adaptadores.

---

## 4.5 Las capacidades son permanentes

Cada Sprint incorpora una nueva capacidad al sistema.

Las capacidades nunca deben eliminar funcionalidades previamente validadas.

El proyecto evoluciona de forma acumulativa.

---

# 5. Ciclo de Vida de una Misión

Toda misión sigue el mismo ciclo de ingeniería.

```text
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

Cierre
```

Ninguna etapa puede omitirse.

---

# 6. Definición de Sprint

Un Sprint representa un conjunto de actividades cuyo objetivo consiste en incorporar una nueva capacidad completamente funcional al sistema.

Un Sprint no finaliza cuando el código compila.

Finaliza únicamente cuando:

- el código funciona;
- las pruebas son satisfactorias;
- la documentación está completa;
- el baseline ha sido generado;
- el repositorio puede ser comprendido por otro ingeniero.

---

# 7. Definición de Capacidad

Una capacidad representa una funcionalidad permanente del sistema.

Ejemplos de capacidades son:

- Obtener información del sistema operativo.
- Administrar MediaMTX.
- Administrar FFmpeg.
- Administrar usuarios.
- Supervisar la red.
- Gestionar canales.
- Gestionar clientes.

Cada misión incorpora exactamente una nueva capacidad.

---

# 8. Definición de Baseline

Un Baseline constituye una fotografía técnica del proyecto al finalizar una misión.

Describe el estado exacto alcanzado.

Permite reconstruir históricamente la evolución del sistema.

Todo Sprint debe finalizar con su correspondiente Baseline.

---

# 9. Gestión de Cambios

Ninguna modificación importante debe realizarse directamente sobre el código.

Toda modificación sigue el siguiente proceso:

Identificación del problema.

↓

Análisis.

↓

Diseño.

↓

Implementación.

↓

Pruebas.

↓

Documentación.

↓

Actualización del CHANGELOG.

↓

Actualización del ROADMAP.

---

# 10. Gestión del Conocimiento

El conocimiento generado durante el proyecto constituye uno de sus principales activos.

Por esta razón todo descubrimiento técnico debe documentarse.

La experiencia obtenida durante una misión no debe perderse.

Cada misión incorpora una sección denominada:

Lecciones Aprendidas.

---

# 11. Calidad

La calidad no se evalúa únicamente mediante pruebas automáticas.

Una implementación de calidad cumple simultáneamente los siguientes criterios:

- Arquitectura consistente.
- Código legible.
- Documentación clara.
- Pruebas reproducibles.
- Evidencias verificables.
- Trazabilidad completa.

---

# 12. Organización del Trabajo

El desarrollo del proyecto sigue una estructura incremental.

Cada nueva capacidad reutiliza la arquitectura previamente validada.

Nunca se reinventa una solución ya implementada.

La reutilización constituye un objetivo permanente.

---

# 13. Relación entre Código y Documentación

Código y documentación poseen el mismo nivel de importancia.

El código implementa capacidades.

La documentación explica:

- por qué existen;
- cómo funcionan;
- cómo evolucionaron.

Ambos productos forman parte del mismo proceso de ingeniería.

---

# 14. Criterio de Finalización

Una misión se considera oficialmente terminada únicamente cuando se cumplen todas las siguientes condiciones.

✓ Código implementado.

✓ Arquitectura validada.

✓ Pruebas satisfactorias.

✓ Documentación completa.

✓ Evidencias incorporadas.

✓ Baseline generado.

✓ CHANGELOG actualizado.

✓ ROADMAP actualizado.

✓ Commit realizado.

---

# 15. Visión del Proyecto

El proyecto EJTV Broadcast Platform busca convertirse en una plataforma abierta para la administración profesional de infraestructura multimedia.

Cada nueva misión deberá acercar el proyecto a esta visión.

Las funcionalidades individuales no representan el objetivo final.

Constituyen pasos sucesivos hacia una plataforma integral.

---

# 16. Filosofía Institucional

La ingeniería desarrollada dentro del proyecto se resume mediante las siguientes expresiones.

> Donde hay orden, está Dios.

> Comprender antes de programar.

> La arquitectura gobierna al código.

> No estamos desarrollando funciones; estamos construyendo capacidades.

> Administrar infraestructura multimedia profesional desde una plataforma unificada.

> Toda misión deja una capacidad.

> Toda misión deja conocimiento.

> Todo Sprint deja un legado.

---

# 17. Conclusión

El presente estándar establece la metodología oficial de ingeniería del proyecto EJTV Broadcast Platform.

Todos los desarrollos futuros deberán respetar los principios aquí definidos.

La finalidad no consiste únicamente en construir software funcional.

La finalidad consiste en construir una plataforma sólida, escalable, mantenible y completamente documentada, capaz de preservar el conocimiento generado durante toda su evolución.
