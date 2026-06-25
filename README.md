# EJTV Broadcast Platform

> *"Toda plataforma nace para resolver un problema."*

---

# Bienvenido

Durante muchos años la distribución de contenido televisivo dependió casi exclusivamente de enlaces satelitales.

Este modelo permitió construir redes de gran cobertura y ofrecer servicios confiables durante décadas. Sin embargo, también introdujo una serie de limitaciones relacionadas con los costos de operación, la dependencia de infraestructura especializada y la dificultad para evolucionar hacia nuevas tecnologías basadas en redes IP.

Al mismo tiempo, comenzaron a aparecer protocolos abiertos capaces de transportar contenido audiovisual con altos niveles de confiabilidad sobre Internet y redes privadas.

Entre ellos destaca **SRT (Secure Reliable Transport)**, un protocolo diseñado para transportar audio y video con baja latencia, corrección de errores y mecanismos de recuperación ante pérdidas de paquetes.

En EJTV surgió entonces una pregunta muy sencilla:

> **¿Es posible construir una plataforma profesional para distribuir televisión utilizando herramientas abiertas, completamente documentadas y sin depender de soluciones propietarias?**

Esta pregunta dio origen a **EJTV Broadcast Platform**.

Este proyecto no nace con el objetivo de instalar un servidor Linux.

Tampoco pretende ser únicamente una guía para configurar diferentes programas.

Nuestro propósito es mucho más ambicioso.

Queremos construir una plataforma de ingeniería cuya evolución quede completamente documentada, permitiendo comprender no solamente cómo funciona cada componente, sino también por qué fue seleccionado y cuál es su papel dentro del sistema.

Este repositorio documenta ese recorrido.

Desde la primera decisión de arquitectura hasta la puesta en producción del servidor.

---

# ¿Qué es EJTV Broadcast Platform?

EJTV Broadcast Platform es una plataforma abierta para la recepción, administración y distribución de contenido audiovisual sobre redes IP.

Su objetivo principal consiste en recibir señales previamente codificadas por equipos profesionales y redistribuirlas de forma confiable hacia operadores de televisión por cable utilizando protocolos modernos de transporte.

Durante la primera etapa del proyecto la plataforma estará orientada exclusivamente al protocolo **SRT**.

Esta decisión permite concentrar los esfuerzos en construir una infraestructura estable y altamente confiable antes de incorporar otros protocolos o nuevas funcionalidades.

Desde el inicio se tomó otra decisión importante.

La plataforma **no realizará procesos de transcodificación de video**.

La codificación y compresión del contenido serán realizadas por equipos especializados, como codificadores profesionales y dispositivos Magewell.

Nuestro servidor tendrá una única responsabilidad:

- recibir;
- administrar;
- distribuir.

Nada más.

Reducir las responsabilidades del servidor simplifica la arquitectura, disminuye el consumo de recursos y mejora considerablemente la estabilidad del sistema.

---

# Nuestra filosofía

Existe una diferencia importante entre instalar un servidor y construir una plataforma.

Instalar un servidor consiste en ejecutar una serie de comandos hasta obtener un sistema funcionando.

Construir una plataforma significa comprender cada componente, justificar cada decisión y pensar en el mantenimiento del sistema durante los próximos años.

Nosotros elegimos el segundo camino.

Por esa razón este proyecto está organizado alrededor de principios de ingeniería y no alrededor de programas específicos.

Creemos que una plataforma estable depende tanto de la calidad de sus decisiones técnicas como de la claridad con que estas decisiones quedan documentadas.

Todo componente podrá evolucionar.

Todo componente podrá sustituirse.

Pero los principios de ingeniería permanecerán.

---

# Principios de ingeniería

Toda decisión tomada durante el desarrollo de esta plataforma deberá respetar los siguientes principios.

## Estabilidad

La estabilidad prevalece sobre la incorporación de nuevas funcionalidades.

Antes de instalar un nuevo componente, incorporar un protocolo adicional o actualizar una versión del software, deberá demostrarse que dicho cambio no compromete la confiabilidad de la plataforma.

---

## Seguridad

La seguridad forma parte del diseño del sistema.

No será considerada como un elemento adicional incorporado al finalizar el proyecto.

Cada servicio deberá ejecutarse con los privilegios mínimos necesarios y todo acceso deberá encontrarse controlado y documentado.

---

## Modularidad

Cada servicio tendrá una única responsabilidad.

Esta filosofía facilita el mantenimiento, simplifica el diagnóstico de problemas y permite comprender rápidamente la función de cada componente.

---

## Independencia

Todos los componentes deberán poder evolucionar de manera independiente.

Si en el futuro resulta necesario sustituir un servidor multimedia, un sistema operativo o una herramienta de monitoreo, el resto de la plataforma deberá continuar funcionando con los menores cambios posibles.

---

## Documentación

La documentación forma parte integral del proyecto.

Toda decisión importante será explicada, justificada y registrada dentro de este repositorio.

Nuestro objetivo no consiste únicamente en construir una plataforma funcional.

Queremos construir una plataforma comprensible.

---

# Nuestra metodología

La documentación de EJTV Broadcast Platform ha sido escrita con un enfoque completamente didáctico.

Cada documento responderá siempre las siguientes preguntas:

1. ¿Qué es?
2. ¿Por qué existe?
3. ¿Cómo funciona?
4. ¿Cómo se implementa?
5. ¿Cómo verificamos que funciona correctamente?

De esta forma el lector no solamente podrá reproducir una configuración, sino comprender completamente la lógica detrás de cada decisión.

No asumiremos que el lector conoce previamente todos los conceptos utilizados durante el proyecto.

Cada término nuevo será introducido y explicado antes de ser utilizado.

Creemos que enseñar forma parte del proceso de construir una buena plataforma.

---

# Estado actual del proyecto

Actualmente la plataforma se encuentra en su etapa inicial de diseño.

Durante esta fase se definirán:

- la arquitectura general;
- los principios de ingeniería;
- la organización documental;
- la estrategia de seguridad;
- la estructura de red;
- los procedimientos de instalación;
- los mecanismos de administración y monitoreo.

Posteriormente comenzará la implementación progresiva de cada componente.

---

# Organización del repositorio

Este repositorio constituye la fuente oficial de documentación del proyecto.

Toda la información relacionada con la plataforma se encontrará organizada y versionada mediante Git.

Cada documento tendrá un propósito específico y responderá una pregunta concreta.

La documentación evolucionará junto con la plataforma.

---

# Nuestro compromiso

Más que construir un servidor, queremos construir conocimiento.

Esperamos que cualquier persona que recorra esta documentación pueda comprender cómo nació la plataforma, cuáles fueron los problemas que intentó resolver, por qué se tomaron determinadas decisiones y cómo continuar su evolución en el futuro.

Creemos que una plataforma bien documentada puede mantenerse durante muchos años, independientemente del hardware, del sistema operativo o de las personas que participen en su desarrollo.

Ese es el verdadero objetivo de **EJTV Broadcast Platform**.

---

**Versión del documento:** 0.1.0  
**Estado del proyecto:** Diseño de arquitectura