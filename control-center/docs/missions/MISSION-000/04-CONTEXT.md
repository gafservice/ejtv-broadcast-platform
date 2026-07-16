# MISSION-000

# Engineering Foundation

## 04 - CONTEXT

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

Todo proyecto de ingeniería nace dentro de un contexto específico.

Las decisiones técnicas no aparecen por casualidad, sino como respuesta
a las necesidades, limitaciones y objetivos existentes en un momento
determinado.

Comprender ese contexto permite interpretar correctamente la arquitectura,
la metodología y la organización adoptadas durante el desarrollo del
proyecto.

Este documento describe el escenario en el cual comenzó el
**EJTV Broadcast Platform** y explica las circunstancias que dieron
origen a la construcción del **EJTV Control Center**.

---

# Una visión de largo plazo

Desde el inicio se tuvo claro que el objetivo del proyecto no consistía
únicamente en instalar un servidor de streaming.

El propósito era mucho más amplio.

Se buscaba construir una plataforma profesional capaz de evolucionar
durante muchos años, incorporando nuevas capacidades sin perder orden,
estabilidad ni calidad técnica.

Esta visión influyó directamente en todas las decisiones tomadas durante
las primeras etapas del desarrollo.

---

# Los primeros pasos

El proyecto comenzó estudiando cada uno de los componentes que formarían
parte de la futura plataforma.

En lugar de utilizar herramientas como una "caja negra", se decidió
comprender cómo funcionaban internamente.

Cada servicio fue instalado, configurado, probado y documentado de forma
independiente.

Entre las tecnologías estudiadas se encuentran:

- Ubuntu Server.
- MediaMTX.
- FFmpeg.
- RTMP.
- SRT.
- HLS.
- WebRTC.
- UDP.
- Multicast.
- Cockpit.
- SSH.

Cada una de estas tecnologías fue validada mediante misiones técnicas
específicas, generando evidencia y documentación para futuras
referencias.

---

# El conocimiento como activo principal

Durante estas primeras etapas quedó claro que el recurso más valioso del
proyecto no era el código desarrollado.

El verdadero valor estaba en el conocimiento adquirido.

Comprender el funcionamiento de cada componente permitió tomar decisiones
basadas en fundamentos técnicos y no únicamente en recomendaciones de
terceros.

Esta filosofía continúa siendo uno de los pilares del proyecto.

---

# El crecimiento del servidor

Conforme aumentó la cantidad de servicios instalados, también aumentó la
complejidad para administrarlos.

Cada componente disponía de sus propios archivos de configuración,
registros, comandos y mecanismos de supervisión.

Aunque todas las herramientas funcionaban correctamente de forma
individual, administrarlas como un conjunto comenzaba a ser cada vez más
difícil.

Se hizo evidente que el crecimiento futuro requeriría una solución más
organizada.

---

# El nacimiento del Control Center

Como respuesta a esa necesidad surgió la idea de desarrollar una
plataforma de administración propia.

No se pretendía reemplazar las herramientas existentes.

El objetivo consistía en integrarlas bajo una arquitectura común,
utilizando una única interfaz y una metodología consistente.

Así nació el **EJTV Control Center**, concebido como el centro de
administración del EJTV Broadcast Platform.

Su misión sería facilitar la supervisión, configuración y operación de
todos los servicios que conforman la infraestructura multimedia.

---

# Una decisión fundamental

Antes de escribir las primeras líneas de código del Control Center se
tomó una decisión que marcaría el rumbo del proyecto.

Primero se construiría la ingeniería.

Después se construiría el software.

Esta decisión dio origen a:

- un modelo de gobierno;
- un Manual de Ingeniería;
- una arquitectura base;
- estándares de desarrollo;
- una metodología de trabajo;
- una estructura documental.

Solo después de completar estos elementos comenzó el desarrollo de las
primeras capacidades funcionales.

---

# Una filosofía de trabajo

Desde ese momento todas las actividades del proyecto comenzaron a seguir
la misma secuencia.

1. Comprender el problema.
2. Diseñar la solución.
3. Implementar.
4. Validar.
5. Documentar.
6. Generar evidencias.
7. Integrar al proyecto.

Este proceso garantiza que el conocimiento permanezca disponible y que
cada nueva capacidad pueda desarrollarse sobre una base estable.

---

# Resultado

El contexto descrito en este documento explica por qué el
**EJTV Broadcast Platform** fue concebido como una plataforma de
ingeniería y no únicamente como un conjunto de aplicaciones para
streaming.

La prioridad siempre ha sido construir un sistema capaz de crecer de
forma organizada, manteniendo la calidad técnica y preservando el
conocimiento generado durante su desarrollo.

---

# Relación con el proyecto

El contexto presentado en este documento constituye el punto de partida
para comprender todas las decisiones descritas en los documentos
posteriores.

La arquitectura, los estándares y el modelo de gobierno encuentran aquí
su justificación.

---

# Documento siguiente

El siguiente documento corresponde al **05-GOVERNANCE.md**.

En él se describe el modelo de gobierno adoptado para dirigir el
desarrollo del proyecto y garantizar que todas las decisiones técnicas
se mantengan alineadas con los principios establecidos durante la etapa
fundacional.

---