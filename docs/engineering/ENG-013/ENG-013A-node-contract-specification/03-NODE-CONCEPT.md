# 3. Node Concept

## Introducción

La **Node-Oriented Architecture (NOA)** establece que todo componente operativo de la plataforma Broadcast será representado mediante un **Node**.

El Node constituye la unidad lógica fundamental de la plataforma y representa la capacidad funcional que el **Network Operations Center (NOC)** administra, supervisa y coordina.

Toda interacción entre el NOC y los componentes de la plataforma se realiza exclusivamente mediante la **Node Contract Specification (NCS)**.

---

# Definición

Un **Node** representa una capacidad funcional estable dentro de la plataforma.

No constituye una ejecución concreta del software, sino la representación lógica de un servicio que puede disponer de una o más instancias operativas.

Cada Node:

* posee una identidad estable;
* representa una única responsabilidad funcional;
* agrupa todas las instancias que ejecutan dicha responsabilidad;
* constituye el Aggregate Root del modelo de dominio definido por la Node Contract Specification.

---

# Node y NodeInstance

Es importante distinguir claramente ambos conceptos.

## Node

Representa la entidad lógica.

Responde a la pregunta:

> **¿Qué servicio existe dentro de la plataforma?**

Ejemplos:

* Identity
* Streaming
* Metrics
* Alarm
* Automation
* Transcoding
* Storage

Un Node permanece estable durante toda su existencia.

---

## NodeInstance

Representa una ejecución concreta de un Node.

Responde a la pregunta:

> **¿Dónde y cómo se está ejecutando actualmente ese servicio?**

Ejemplos:

* Streaming Node ejecutándose en el servidor principal.
* Streaming Node ejecutándose en un servidor remoto.
* Múltiples nodos de transcodificación distribuidos geográficamente.

Cada Node puede poseer cero, una o múltiples NodeInstances.

---

# Modelo Conceptual

```text
Node
│
├── NodeId
├── NodeType
└── NodeInstance [0..N]
```

Cada NodeInstance mantiene su propio estado operacional.

---

# Naturaleza

Un Node representa una entidad lógica.

No representa:

* una clase;
* un objeto del lenguaje de programación;
* un proceso del sistema operativo;
* un contenedor;
* una máquina virtual;
* una instancia de ejecución.

Aunque una NodeInstance pueda ejecutarse sobre cualquiera de estos elementos, el Node continúa siendo una abstracción lógica dentro de la arquitectura.

---

# Responsabilidad

Todo Node posee una única responsabilidad funcional.

Ejemplos:

* administrar identidad;
* distribuir contenido multimedia;
* calcular métricas;
* gestionar alarmas;
* ejecutar automatizaciones;
* realizar transcodificación;
* administrar almacenamiento.

La implementación concreta pertenece exclusivamente a sus NodeInstances.

El NOC nunca participa en dicha ejecución.

---

# Autonomía

Cada Node mantiene autonomía funcional.

Las NodeInstances administran:

* su configuración;
* sus procesos internos;
* sus recursos;
* su estado operacional;
* sus métricas;
* sus eventos;
* sus alarmas.

La Node Contract Specification únicamente define cómo publicar dicha información.

No impone cómo obtenerla.

---

# Identidad

Todo Node posee una identidad lógica única dentro de la plataforma.

Esta identidad será utilizada por el NOC para:

* registrar Nodes;
* construir inventarios;
* identificar servicios;
* agrupar NodeInstances;
* correlacionar información operacional.

La identidad lógica permanece estable durante toda la vida del Node.

---

# Comunicación

El Node no necesita conocer la implementación del NOC.

Su única responsabilidad consiste en garantizar que todas sus NodeInstances publiquen información conforme a la Node Contract Specification.

El mecanismo de transporte utilizado para dicha publicación no forma parte del concepto de Node.

---

# Ciclo de Vida

El ciclo de vida del Node es independiente del ciclo de vida de sus instancias.

Conceptualmente comprende:

```text
Creación
    │
    ▼
Registro
    │
    ▼
Operación
    │
    ▼
Actualización
    │
    ▼
Retiro
```

Durante este ciclo el Node puede crear o eliminar NodeInstances sin alterar su identidad lógica.

---

# Node e Implementación

La implementación interna de un Node es completamente libre.

Las NodeInstances podrán desarrollarse utilizando:

* Python;
* Go;
* Rust;
* Java;
* C++;
* cualquier otro lenguaje.

Asimismo podrán ejecutarse como:

* servicios del sistema;
* contenedores;
* procesos independientes;
* microservicios;
* aplicaciones embebidas;
* servicios en la nube.

La interoperabilidad depende exclusivamente del cumplimiento de la Node Contract Specification.

---

# NodeType

El NodeType define la naturaleza funcional del Node.

Ejemplos:

* Identity
* Streaming
* Metrics
* Alarm
* Automation
* Database
* Storage
* Transcoding

Dos NodeInstances distintas pueden compartir exactamente el mismo NodeType al pertenecer al mismo Node.

---

# Relación con el NOC

El Network Operations Center administra Nodes e Instances de forma diferenciada.

El Node representa el servicio lógico.

La NodeInstance representa la ejecución concreta.

Esta separación permite:

* múltiples instancias por servicio;
* alta disponibilidad;
* balanceo de carga;
* escalabilidad horizontal;
* despliegues híbridos;
* operación distribuida.

---

# Independencia

Los Nodes son independientes entre sí.

Un Node:

* NO DEBE depender del conocimiento interno de otros Nodes;
* NO DEBE asumir tecnologías específicas;
* NO DEBE acceder directamente al estado interno de otros Nodes.

Toda interacción operacional deberá realizarse utilizando mecanismos definidos por la arquitectura de la plataforma.

---

# Escalabilidad

La incorporación de nuevas NodeInstances no modifica el modelo de dominio.

Ejemplo:

```text
Streaming Node

├── Instance A
├── Instance B
├── Instance C
└── Instance D
```

Cada instancia publica su propio estado operacional utilizando exactamente el mismo contrato.

---

# Principios Fundamentales

Todo Node compatible con la plataforma cumple los siguientes principios:

* posee identidad lógica estable;
* representa una única responsabilidad funcional;
* agrupa una o más NodeInstances;
* mantiene autonomía funcional;
* publica información mediante la Node Contract Specification;
* evoluciona independientemente del resto del sistema.

Estos principios constituyen la definición oficial del concepto de Node dentro de la Node-Oriented Architecture.

---

# Conclusión

El Node representa la unidad lógica fundamental de la plataforma Broadcast.

La separación entre **Node** y **NodeInstance** permite construir una arquitectura distribuida donde múltiples ejecuciones concretas pueden coexistir bajo una misma identidad lógica, preservando la interoperabilidad, la escalabilidad y el desacoplamiento definidos por la Node Contract Specification.

Toda capacidad futura de la plataforma deberá integrarse mediante Nodes compatibles con la NCS, respetando los principios establecidos por la Node-Oriented Architecture.
