# MISSION-000

# Engineering Foundation

## 03 - PROBLEM

---

# Estado

**Completada**

---

# Versión

1.0

---

# Fecha

Julio 2026

---

# Introducción

Todo proyecto de ingeniería nace como respuesta a una necesidad.

Antes de desarrollar una solución es necesario comprender el problema que se desea resolver, ya que las decisiones de diseño, arquitectura e implementación dependerán directamente de dicha comprensión.

El presente documento describe el problema que motivó la creación del **EJTV Broadcast Platform** y explica por qué fue necesario desarrollar una plataforma propia para la administración de infraestructura multimedia.

---

# Situación inicial

La distribución profesional de contenido multimedia involucra múltiples componentes que deben trabajar de forma coordinada.

Un servidor moderno puede ejecutar simultáneamente diversos servicios especializados, entre ellos:

- MediaMTX.
- FFmpeg.
- Servidores Web.
- Servicios de red.
- Firewalls.
- Docker.
- Sistemas de monitoreo.
- Bases de datos.
- Herramientas de administración remota.

Cada uno de estos componentes posee mecanismos propios de configuración, supervisión y mantenimiento.

Aunque todos cumplen una función específica, normalmente operan de manera independiente.

---

# Problema identificado

La administración de una plataforma multimedia suele realizarse utilizando múltiples herramientas diferentes.

Por ejemplo, el administrador debe acceder a la terminal para revisar procesos, utilizar archivos de configuración para modificar servicios, consultar registros del sistema para diagnosticar fallos y emplear distintas aplicaciones para verificar el estado de la red o del servidor.

Esta fragmentación provoca diversos inconvenientes:

- La información se encuentra distribuida en múltiples lugares.
- El diagnóstico de problemas requiere utilizar diferentes herramientas.
- La curva de aprendizaje aumenta considerablemente.
- El conocimiento depende de la experiencia del administrador.
- La documentación suele quedar desactualizada.
- La incorporación de nuevas capacidades resulta compleja.

Como consecuencia, el mantenimiento de la plataforma se vuelve más difícil conforme el sistema crece.

---

# Necesidad detectada

Durante el desarrollo del proyecto se identificó la necesidad de disponer de una plataforma capaz de centralizar la administración de todos los componentes involucrados en la distribución multimedia.

Más que desarrollar una aplicación adicional, se buscó construir un entorno que permitiera visualizar, supervisar y administrar la infraestructura desde un único punto de acceso.

Esta plataforma debía facilitar tanto la operación diaria como el crecimiento futuro del sistema.

---

# Limitaciones de las soluciones existentes

Existen diversas herramientas que permiten administrar componentes específicos de un servidor.

Algunas ofrecen monitoreo del sistema operativo.

Otras permiten controlar contenedores, visualizar registros o administrar determinados servicios multimedia.

Sin embargo, la mayoría de estas soluciones fueron diseñadas para resolver problemas particulares y no para integrarse dentro de una plataforma unificada orientada al flujo de trabajo del proyecto EJTV.

Adicionalmente, muchas de ellas requieren configuraciones independientes, utilizan interfaces diferentes o no permiten incorporar fácilmente nuevas capacidades desarrolladas por el propio equipo.

---

# Problema de ingeniería

El verdadero problema no consistía únicamente en administrar un servidor Linux.

Tampoco consistía únicamente en controlar MediaMTX o FFmpeg.

El desafío era construir una plataforma capaz de integrar todos esos componentes bajo una misma arquitectura, utilizando una metodología uniforme y preservando la independencia entre las distintas capas del sistema.

Desde esta perspectiva, el problema debía abordarse como un problema de arquitectura de software y no únicamente como un problema de programación.

---

# Decisión adoptada

Como respuesta a esta necesidad se decidió desarrollar el **EJTV Control Center**, un sistema diseñado específicamente para administrar la infraestructura del EJTV Broadcast Platform.

Su desarrollo se fundamenta en principios de ingeniería de software, arquitectura limpia y documentación continua.

Cada nueva capacidad incorporada deberá integrarse respetando estos principios, garantizando que la plataforma pueda evolucionar de manera ordenada y sostenible.

---

# Resultado esperado

La solución propuesta permitirá administrar progresivamente todos los componentes del servidor mediante una interfaz unificada, reduciendo la complejidad operativa y facilitando el mantenimiento del sistema.

La plataforma será capaz de crecer mediante la incorporación de nuevas capacidades sin comprometer la estabilidad de las funcionalidades ya existentes.

---

# Relación con el proyecto

El problema descrito en este documento constituye la razón de ser del EJTV Broadcast Platform.

Todas las decisiones de arquitectura, diseño e implementación adoptadas durante el proyecto buscan responder de manera progresiva a las necesidades aquí identificadas.

---

# Documento siguiente

El siguiente documento corresponde al **04-CONTEXT.md**, donde se describe el contexto en el cual nació el proyecto, las condiciones existentes al momento de iniciar el desarrollo y los principios que guiaron las primeras decisiones de ingeniería.

---