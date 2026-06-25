# Arquitectura de la Plataforma

> *"Una buena arquitectura no depende de las herramientas que utiliza.
> Depende de la claridad con que define las responsabilidades de cada componente."*

---

# Introducción

Toda plataforma tecnológica necesita una arquitectura.

La arquitectura define la organización general del sistema, establece la
responsabilidad de cada componente y describe la forma en que la información
circula desde su origen hasta el usuario final.

Antes de seleccionar un sistema operativo, instalar servicios o escribir una
sola línea de configuración, es necesario comprender cómo debe funcionar la
plataforma en su conjunto.

Este documento presenta la arquitectura conceptual de **EJTV Broadcast
Platform**.

Su propósito no consiste en explicar la instalación de herramientas
específicas.

Su objetivo es definir la estructura general que servirá como guía para todas
las decisiones técnicas que se tomarán durante el desarrollo del proyecto.

---

# El problema que buscamos resolver

Durante muchos años la distribución de contenido audiovisual hacia operadores
de televisión se realizó principalmente mediante enlaces satelitales.

Este modelo permitió ofrecer un servicio confiable durante décadas.

Sin embargo, también implicó altos costos de operación, dependencia de
infraestructura especializada y poca flexibilidad para incorporar nuevas
tecnologías.

La evolución de las redes IP abrió una nueva posibilidad.

Hoy es posible distribuir contenido audiovisual utilizando protocolos
especializados capaces de ofrecer altos niveles de confiabilidad sobre redes de
datos convencionales.

Esta evolución tecnológica permitió plantear una nueva arquitectura de
distribución.

Una arquitectura basada en servidores estándar, software abierto y protocolos
modernos de transporte.

---

# Nuestra visión de la arquitectura

La arquitectura de **EJTV Broadcast Platform** se basa en una idea muy simple.

Cada componente debe cumplir una única responsabilidad.

Cuando un componente realiza únicamente la función para la cual fue diseñado,
el sistema completo resulta más fácil de comprender, mantener y ampliar.

Por el contrario, cuando un mismo componente acumula múltiples funciones,
aparecen dependencias innecesarias, aumenta la complejidad y el mantenimiento
se vuelve más difícil.

Por esta razón toda la plataforma ha sido organizada alrededor de
responsabilidades claramente definidas y no alrededor de aplicaciones
específicas.

---

# Arquitectura funcional

Desde un punto de vista funcional, la plataforma se divide en seis grandes
bloques.

## 1. Recepción del contenido

Representa el punto de ingreso de las señales audiovisuales.

Durante la primera etapa del proyecto estas señales serán entregadas por
equipos externos especializados en codificación.

La plataforma no realizará procesos de codificación ni transcodificación.

Su responsabilidad comienza cuando el flujo audiovisual llega al servidor.

---

## 2. Administración de flujos

Una vez recibido el contenido, la plataforma administra los diferentes flujos
de distribución.

En esta etapa se controlan aspectos relacionados con la organización de los
canales, la disponibilidad del servicio y la gestión interna de la plataforma.

Este bloque constituye el núcleo operativo del sistema.

---

## 3. Distribución

El bloque de distribución entrega los diferentes flujos hacia los clientes
autorizados.

Durante la primera versión de la plataforma esta distribución se realizará
utilizando el protocolo **SRT (Secure Reliable Transport)**.

La incorporación futura de nuevos protocolos no modificará la arquitectura
general del sistema.

Únicamente ampliará las capacidades del bloque de distribución.

---

## 4. Seguridad

Toda plataforma conectada a una red requiere mecanismos que protejan tanto el
servidor como los servicios que ofrece.

La seguridad forma parte de la arquitectura desde el inicio del proyecto.

Su función consiste en controlar el acceso, proteger los servicios y garantizar
que únicamente usuarios autorizados puedan utilizar la plataforma.

---

## 5. Monitoreo

Una plataforma profesional debe ser capaz de informar permanentemente su estado
de operación.

El monitoreo permitirá conocer el comportamiento del sistema, detectar fallas,
registrar eventos importantes y facilitar el mantenimiento preventivo.

El objetivo no consiste únicamente en detectar problemas.

También busca comprender el comportamiento de la plataforma a lo largo del
tiempo.

---

## 6. Administración

Toda plataforma necesita mecanismos que permitan administrar su configuración,
realizar tareas de mantenimiento y supervisar el funcionamiento de los
distintos servicios.

Este bloque reúne las herramientas necesarias para operar la plataforma durante
su vida útil.

---

# Flujo general del servicio

Desde una perspectiva funcional, el recorrido del contenido puede resumirse en
las siguientes etapas.

```text
Recepción
      │
      ▼
Administración de flujos
      │
      ▼
Control de acceso
      │
      ▼
Distribución
      │
      ▼
Clientes autorizados
```

Aunque posteriormente se incorporarán nuevos servicios, este flujo constituye
la base sobre la cual se desarrollará toda la plataforma.

---

# Principios arquitectónicos

Toda decisión relacionada con la arquitectura deberá respetar los siguientes
principios.

## Modularidad

Cada componente tendrá una única responsabilidad claramente definida.

---

## Independencia

Los diferentes servicios podrán evolucionar o sustituirse sin afectar el resto
de la plataforma.

---

## Escalabilidad

La arquitectura permitirá incorporar nuevos canales, protocolos y servicios sin
requerir modificaciones profundas en su diseño.

---

## Estabilidad

La incorporación de nuevas funcionalidades nunca comprometerá la estabilidad de
los servicios existentes.

---

## Seguridad

La seguridad será considerada desde las primeras etapas del diseño y no como un
componente agregado posteriormente.

---

## Documentación

Toda modificación arquitectónica deberá quedar registrada y justificada dentro
del repositorio del proyecto.

---

# Una arquitectura preparada para crecer

Durante la primera etapa del proyecto la plataforma se concentrará
exclusivamente en la distribución de contenido mediante el protocolo SRT.

Sin embargo, la arquitectura ha sido diseñada para facilitar la incorporación
de nuevas tecnologías conforme evolucionen las necesidades de EJTV.

Esta evolución podrá incluir nuevos protocolos de distribución, herramientas
de monitoreo, mecanismos avanzados de seguridad y plataformas de administración
sin alterar la estructura general del sistema.

---

# Conclusión

La arquitectura de **EJTV Broadcast Platform** no gira alrededor de un sistema
operativo ni de una aplicación específica.

Su verdadero fundamento consiste en definir claramente las responsabilidades de
cada componente y establecer una estructura capaz de evolucionar durante muchos
años.

Las herramientas podrán cambiar.

Las versiones del software también cambiarán.

La arquitectura deberá permanecer.

Ese será el principio que guiará todas las decisiones técnicas de este
proyecto.
