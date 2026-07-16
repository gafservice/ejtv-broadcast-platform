# MISSION-000

# Engineering Foundation

## 06 - ARCHITECTURE

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

La arquitectura de software constituye el conjunto de decisiones
fundamentales que definen la organización de un sistema.

Una buena arquitectura permite incorporar nuevas capacidades sin afectar
las ya existentes, facilita el mantenimiento y reduce la dependencia
entre los diferentes componentes del proyecto.

Durante la etapa fundacional del EJTV Broadcast Platform se decidió
adoptar una arquitectura orientada a responsabilidades, donde cada capa
cumple una función claramente definida.

---

# Objetivo de la arquitectura

La arquitectura fue diseñada con los siguientes objetivos.

- Reducir el acoplamiento entre componentes.
- Facilitar la incorporación de nuevas capacidades.
- Mejorar la mantenibilidad del sistema.
- Favorecer las pruebas automatizadas.
- Aislar la infraestructura del negocio.
- Preservar la independencia tecnológica.

Estos objetivos acompañarán al proyecto durante todo su ciclo de vida.

---

# Principio fundamental

El principio más importante adoptado durante el diseño fue el siguiente.

> Las dependencias siempre apuntan hacia el dominio del problema y nunca
> hacia la infraestructura.

En otras palabras, la lógica del negocio nunca debe depender de una
tecnología específica.

Si mañana cambia FastAPI, Linux o MediaMTX, el dominio del proyecto debe
permanecer prácticamente igual.

---

# Arquitectura por capas

La plataforma se organiza en seis capas principales.

```text
Cliente

↓

API

↓

Services

↓

Domain

↓

Adapters

↓

Infrastructure
```

Cada una de estas capas posee responsabilidades específicas.

---

# Cliente

Representa cualquier componente que interactúa con la plataforma.

Puede tratarse de:

- una aplicación web;
- una aplicación móvil;
- un servicio externo;
- una API;
- otro sistema.

El cliente nunca accede directamente a la infraestructura.

Toda comunicación se realiza mediante la API.

---

# API

La API constituye el punto de entrada del sistema.

Sus responsabilidades son:

- recibir solicitudes;
- validar parámetros;
- invocar servicios;
- construir respuestas;
- manejar errores.

La API no implementa reglas de negocio.

---

# Services

La capa de servicios coordina el funcionamiento del sistema.

Su función consiste en organizar el flujo de trabajo entre el dominio y
los adaptadores.

Los servicios conocen el problema que debe resolverse, pero no conocen
cómo se implementa la infraestructura.

---

# Domain

El dominio representa el corazón del proyecto.

Aquí se encuentran los modelos, reglas y conceptos propios del negocio.

El dominio no conoce:

- Linux;
- FastAPI;
- MediaMTX;
- FFmpeg;
- Docker.

Conoce únicamente los conceptos del problema que se desea resolver.

Esta independencia constituye uno de los pilares de la arquitectura.

---

# Adapters

Los adaptadores actúan como traductores entre el dominio y la
infraestructura.

Su función consiste en convertir llamadas específicas de una tecnología
en operaciones comprensibles para el resto del sistema.

Ejemplos de adaptadores son:

- LinuxSystemAdapter.
- MediaMTXAdapter.
- FFmpegAdapter.
- DockerAdapter.
- NetworkAdapter.

Cada adaptador encapsula completamente los detalles de la tecnología que
representa.

---

# Infrastructure

La infraestructura corresponde al nivel más externo de la plataforma.

Aquí residen todos los componentes que dependen directamente del sistema
operativo o de aplicaciones externas.

Entre ellos se encuentran:

- Linux.
- MediaMTX.
- FFmpeg.
- Docker.
- Sistema de archivos.
- Red.
- Base de datos.

La infraestructura nunca debe contener reglas de negocio.

---

# Flujo de dependencias

Las dependencias siguen una única dirección.

```text
Cliente

↓

API

↓

Services

↓

Domain

↓

Adapters

↓

Infrastructure
```

Ninguna capa puede omitir este flujo.

Este principio evita dependencias circulares y facilita el mantenimiento
del sistema.

---

# Beneficios de esta arquitectura

La arquitectura adoptada proporciona múltiples ventajas.

- Reduce el acoplamiento.
- Facilita las pruebas unitarias.
- Permite reemplazar tecnologías.
- Favorece la reutilización del código.
- Simplifica el crecimiento del proyecto.
- Mejora la comprensión del sistema.

---

# Evolución futura

La arquitectura fue diseñada pensando en el crecimiento del proyecto.

En el futuro podrán incorporarse nuevos adaptadores para administrar
otros componentes sin modificar la estructura general de la plataforma.

De esta forma será posible integrar nuevas capacidades manteniendo la
coherencia arquitectónica definida durante la MISSION-000.

---

# Resultado

La arquitectura establecida durante esta misión proporciona una base
estable sobre la cual podrán desarrollarse todas las capacidades futuras
del EJTV Broadcast Platform.

Su principal objetivo consiste en permitir que la plataforma evolucione
de manera ordenada durante los próximos años.

---

# Relación con el proyecto

La arquitectura constituye el fundamento técnico del proyecto.

Todas las decisiones de diseño e implementación deberán respetar los
principios descritos en este documento.

---

# Documento siguiente

El siguiente documento corresponde al **07-DESIGN.md**.

En él se describen los criterios de diseño utilizados para transformar
los principios arquitectónicos en una estructura de proyecto organizada,
escalable y fácil de mantener.

---
