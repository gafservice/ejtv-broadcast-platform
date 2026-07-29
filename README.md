# Broadcast Platform

> *"Toda plataforma nace para resolver un problema.
> Las plataformas que perduran son aquellas capaces de evolucionar sin perder
> sus principios."*

---

# Bienvenido

Toda plataforma tiene una historia.

Algunas nacen para responder a una necesidad inmediata. Otras aparecen como
resultado de años de experiencia acumulada y del deseo de construir una
solución diferente.

Broadcast Platform pertenece a este segundo grupo.

Durante muchos años la distribución profesional de contenido audiovisual estuvo
ligada principalmente a enlaces satelitales y a soluciones propietarias de alto
costo. Este modelo permitió construir redes confiables y de gran cobertura,
pero también generó una fuerte dependencia de infraestructura especializada,
licenciamientos y plataformas cerradas.

Paralelamente, las redes IP comenzaron a demostrar que podían transportar
contenido audiovisual con niveles de estabilidad cada vez mayores. La evolución
de Internet, el incremento del ancho de banda y la aparición de nuevos
protocolos hicieron posible imaginar una alternativa diferente para la
distribución profesional de televisión.

Entre estos protocolos surgió **SRT (Secure Reliable Transport)**, diseñado para
transportar audio y video con baja latencia, recuperación ante pérdida de
paquetes y mecanismos de seguridad integrados.

Su aparición abrió una nueva posibilidad.

¿Era realmente necesario depender de soluciones propietarias para construir una
infraestructura profesional de distribución de contenido?

Esa pregunta marcó el inicio de este proyecto.

Broadcast Platform nació con un objetivo muy claro:

> **Demostrar que es posible construir una plataforma profesional de recepción,
> administración y distribución de contenido audiovisual utilizando tecnologías
> abiertas, completamente documentadas y sustentadas sobre principios sólidos de
> ingeniería.**

Desde el primer día quedó claro que el propósito del proyecto iba mucho más
allá de instalar un servidor Linux o aprender a utilizar determinadas
herramientas.

Nuestro objetivo consiste en comprender cada componente, justificar cada
decisión y documentar todo el proceso de construcción de la plataforma.

Queremos que cualquier persona pueda recorrer esta documentación y entender no
solamente cómo funciona el sistema, sino también por qué fue diseñado de esta
manera, cuáles alternativas fueron consideradas y qué principios guiaron cada
decisión de arquitectura.

Por esa razón este repositorio no documenta únicamente una instalación.

Documenta la evolución completa de una plataforma de ingeniería.

Desde las primeras ideas hasta su crecimiento hacia un sistema profesional de
operación, monitoreo y administración de infraestructuras Broadcast IP.

---

# ¿Qué es Broadcast Platform?

Broadcast Platform es una plataforma abierta para la recepción, administración,
monitoreo y distribución de contenido audiovisual sobre redes IP.

Su responsabilidad principal consiste en recibir señales previamente
codificadas por equipos especializados y redistribuirlas de forma confiable
hacia diferentes destinos utilizando protocolos modernos de transporte.

Durante las primeras etapas del proyecto la plataforma se concentró en la
recepción y distribución de flujos Broadcast IP utilizando tecnologías abiertas
como **FFmpeg** y **MediaMTX**, construyendo una arquitectura modular, estable y
completamente documentada.

Desde el inicio se tomó una decisión de ingeniería que continúa vigente.

La plataforma **no realizará procesos de transcodificación de video**.

La codificación y compresión del contenido permanecerán bajo la responsabilidad
de equipos especializados, como codificadores profesionales, dispositivos
Magewell u otras soluciones dedicadas.

Esta decisión reduce considerablemente la complejidad del servidor, disminuye
el consumo de recursos y permite concentrar todos los esfuerzos en garantizar
la estabilidad, la administración y la distribución eficiente del contenido.

En otras palabras, la plataforma asume únicamente tres responsabilidades
fundamentales:

- Recibir.
- Administrar.
- Distribuir.

Todo aquello que no pertenezca a estas responsabilidades deberá implementarse
como servicios independientes, preservando la modularidad y facilitando la
evolución futura del sistema.

Esta filosofía ha acompañado al proyecto desde sus primeras versiones y
continúa siendo uno de los pilares sobre los que se construye toda la
arquitectura.

---

# Nuestra filosofía

Existe una diferencia importante entre instalar un servidor y construir una
plataforma.

Instalar un servidor consiste en ejecutar una secuencia de comandos hasta
obtener un sistema funcionando. Aunque este proceso puede resolver una
necesidad inmediata, rara vez permite comprender las razones que existen detrás
de cada decisión técnica.

Construir una plataforma exige un enfoque diferente.

Significa comprender cada componente, justificar cada decisión de arquitectura,
evaluar distintas alternativas y pensar en el mantenimiento del sistema durante
los próximos años.

Nosotros elegimos este segundo camino.

Desde el inicio decidimos que cada componente incorporado debía tener un motivo
claramente justificado. Ninguna herramienta forma parte del proyecto por ser
popular o por encontrarse de moda.

Cada tecnología utilizada debe responder a una necesidad concreta dentro de la
arquitectura.

Del mismo modo, asumimos que ningún componente es permanente.

Los protocolos evolucionan.

Las aplicaciones cambian.

Los sistemas operativos se actualizan.

Incluso el hardware sobre el que hoy se ejecuta la plataforma será sustituido
algún día.

Sin embargo, los principios de ingeniería permanecerán.

Por esa razón este proyecto no está construido alrededor de programas
específicos.

Está construido alrededor de decisiones de arquitectura.

Si en el futuro FFmpeg, MediaMTX o cualquier otra herramienta son reemplazados
por alternativas superiores, la plataforma deberá ser capaz de evolucionar sin
perder su identidad.

Creemos que una plataforma madura no depende de un producto determinado.

Depende de la calidad de sus principios.

Y esos principios deben quedar tan bien documentados como el propio código.

---

# Principios de ingeniería

Toda decisión tomada durante el desarrollo de esta plataforma deberá respetar
los siguientes principios.

Estos principios constituyen la base sobre la que evolucionará el proyecto y
servirán como referencia para evaluar cualquier cambio futuro.

## Estabilidad

La estabilidad siempre tendrá prioridad sobre la incorporación de nuevas
funcionalidades.

Antes de añadir un nuevo servicio, incorporar un protocolo adicional o
actualizar una versión de software, deberá demostrarse que dicho cambio no
compromete la confiabilidad del sistema.

Una plataforma profesional debe comportarse de forma predecible incluso bajo
condiciones adversas.

## Seguridad

La seguridad forma parte del diseño de la plataforma.

No será considerada como un elemento adicional incorporado al finalizar el
desarrollo.

Cada servicio deberá ejecutarse con los privilegios mínimos necesarios, cada
acceso deberá encontrarse controlado y toda modificación importante deberá
quedar registrada y documentada.

## Modularidad

Cada servicio tendrá una única responsabilidad.

La separación clara de responsabilidades facilita el mantenimiento, simplifica
el diagnóstico de problemas y permite sustituir componentes individuales sin
afectar el resto del sistema.

Una arquitectura modular también favorece el crecimiento progresivo de la
plataforma.

Cada nuevo módulo deberá integrarse sin alterar el funcionamiento de los
componentes existentes.

## Independencia

Todos los componentes deberán poder evolucionar de forma independiente.

La sustitución de un servidor multimedia, un sistema operativo, una base de
datos o una herramienta de monitoreo no deberá obligar a rediseñar toda la
arquitectura.

La plataforma debe adaptarse a la evolución tecnológica sin perder estabilidad.

## Observabilidad

No es posible administrar aquello que no puede observarse.

Desde sus primeras versiones la plataforma registrará información suficiente
para comprender el comportamiento de cada uno de sus componentes.

La observabilidad permitirá identificar problemas antes de que afecten la
operación y proporcionará la base para el desarrollo del Engineering NOC.

## Documentación

La documentación forma parte integral del proyecto.

Cada decisión importante deberá quedar registrada, explicada y justificada
dentro de este repositorio.

Nuestro objetivo no consiste únicamente en construir una plataforma funcional.

Queremos construir una plataforma comprensible.

Una plataforma cuya evolución pueda entenderse incluso muchos años después de
haber sido diseñada.

---

# Nuestra metodología

Toda la documentación de Broadcast Platform ha sido escrita con un enfoque
didáctico y progresivo.

No asumimos que el lector conoce previamente todos los conceptos utilizados
durante el desarrollo del proyecto.

Cada nuevo término será presentado antes de ser utilizado y cada decisión será
explicada antes de ser implementada.

Nuestro propósito no consiste únicamente en mostrar una configuración que
funciona.

Queremos explicar por qué funciona.

---

# Organización del repositorio

Este repositorio constituye la fuente oficial de documentación del proyecto.

Todo el conocimiento generado durante el desarrollo de la plataforma deberá
quedar organizado, versionado y disponible para futuras etapas de evolución.

La documentación se estructura en diferentes niveles, cada uno con un propósito
específico.

Los documentos fundacionales describen la visión, la misión y los principios de
ingeniería que orientan el desarrollo de la plataforma.

Los **Architecture Decision Records (ADR)** documentan las decisiones
arquitectónicas más importantes, explicando el contexto en el que fueron
tomadas, las alternativas evaluadas y las razones que justifican la solución
adoptada.

Las **Missions** representan los grandes objetivos funcionales del proyecto,
mientras que los **Sprints** organizan el trabajo incremental necesario para
alcanzarlos.

De esta manera, cualquier persona podrá comprender no solamente el estado
actual de la plataforma, sino también la evolución que la condujo hasta ese
punto.

La documentación crecerá junto con la plataforma.

Nunca será considerada un elemento secundario.

---

# Evolución del proyecto

Las primeras etapas del proyecto estuvieron dedicadas a demostrar que era
posible construir una infraestructura profesional utilizando exclusivamente
tecnologías abiertas.

Cada Mission permitió consolidar un nuevo componente de la arquitectura,
incorporando progresivamente capacidades de recepción, distribución y
administración de flujos Broadcast IP.

Conforme el proyecto fue creciendo apareció una nueva necesidad.

Distribuir correctamente el contenido resolvía solamente una parte del
problema.

Una plataforma profesional también necesita comprender lo que ocurre en su
interior.

Necesita conocer el estado del sistema operativo, los servicios, las interfaces
de red, las sesiones activas, los protocolos de streaming, el consumo de
recursos y el comportamiento de cada componente que participa en la operación.

Esta necesidad dio origen a una nueva etapa del proyecto.

Una etapa orientada no solamente a distribuir contenido, sino también a
observar, diagnosticar y administrar toda la infraestructura desde una única
consola de ingeniería.

Así nació el concepto del **Engineering NOC (Engineering Network Operations
Center)**.

El Engineering NOC no sustituye la plataforma de distribución.

La complementa.

Su propósito consiste en proporcionar observabilidad, facilitar el diagnóstico,
centralizar la administración técnica y preparar la plataforma para futuras
capacidades de resiliencia y alta disponibilidad.

Su desarrollo se realizará de manera incremental mediante nuevas Missions y
Sprints, preservando siempre la compatibilidad con los componentes ya
implementados.

---

# Estado actual del proyecto

Actualmente la plataforma dispone de un núcleo funcional para la recepción y
distribución de contenido Broadcast IP basado en tecnologías abiertas.

La arquitectura continúa evolucionando hacia un sistema integral de ingeniería
capaz de administrar, monitorear y diagnosticar todos los componentes que
participan en la operación del servicio.

Las siguientes etapas estarán orientadas principalmente hacia tres grandes
objetivos.

La **observabilidad**, para comprender el comportamiento de toda la
infraestructura en tiempo real.

La **portabilidad**, para permitir que la plataforma pueda desplegarse sobre
diferentes tipos de hardware y entornos sin modificar su arquitectura.

Y la **resiliencia**, incorporando progresivamente mecanismos de redundancia,
recuperación y continuidad del servicio.

Cada nueva funcionalidad deberá fortalecer al menos uno de estos tres pilares.

---

# Nuestro compromiso

Más que construir un servidor, queremos construir conocimiento.

Esperamos que cualquier persona que recorra esta documentación pueda comprender
cómo nació la plataforma, cuáles fueron los problemas que intentó resolver, por
qué se tomaron determinadas decisiones y cómo continuar su evolución en el
futuro.

Nuestro compromiso no termina cuando una funcionalidad entra en producción.

También incluye documentar cada decisión importante, mantener actualizada la
arquitectura y preservar el conocimiento adquirido durante el desarrollo del
proyecto.

Creemos que una plataforma bien documentada puede mantenerse durante muchos
años, independientemente del hardware, del sistema operativo o de las personas
que participen en su evolución.

Ese continúa siendo el verdadero objetivo de Broadcast Platform.

---

**Versión del documento:** 1.0.0

**Estado del proyecto:** Arquitectura consolidada e inicio de la evolución
hacia el Engineering Network Operations Center (Engineering NOC).