# 5. Domain Model

## Introducción

El presente documento define el **modelo de dominio oficial** de la **Node Contract Specification (NCS)**.

Este modelo representa la estructura conceptual utilizada por todos los nodos compatibles con la plataforma Broadcast para describir su identidad, su estado operacional y la información publicada al **Network Operations Center (NOC)**.

El Domain Model constituye la referencia arquitectónica para el desarrollo del **SDK oficial**, del **NOC Core** y de cualquier implementación compatible con la Node Contract Specification.

---

# Objetivo

El objetivo del modelo de dominio consiste en establecer una representación uniforme de todos los conceptos fundamentales definidos por la NCS.

Esta representación permite que todas las implementaciones compartan exactamente el mismo lenguaje, independientemente de la tecnología utilizada.

---

# Aggregate Root

El modelo se organiza alrededor de un único **Aggregate Root**:

```text
Node
```

El **Node** representa una capacidad funcional estable dentro de la plataforma.

Todas las demás entidades pertenecen al agregado del Node y describen sus diferentes dimensiones operacionales.

---

# Modelo General del Dominio

```text
Node
│
├── NodeId
├── NodeType
└── NodeInstance [0..N]
        │
        ├── NodeInfo
        ├── NodeStatus
        ├── NodeHealth
        ├── NodeAvailability
        ├── NodeCapability
        ├── NodeCapacity
        ├── NodeMetric
        ├── NodeEvent
        ├── NodeAlarm
        ├── NodeHeartbeat
        └── NodeSnapshot
```

Este modelo constituye la representación oficial del dominio utilizada por toda implementación compatible con la Node Contract Specification.

---

# Nivel 1 — Identidad

La primera dimensión del modelo describe la identidad lógica del servicio.

Está compuesta por:

* Node
* NodeId
* NodeType

Estos elementos permanecen estables durante toda la vida del Node.

---

## Node

Representa la entidad lógica que agrupa todas las instancias responsables de una misma capacidad funcional.

El Node constituye el Aggregate Root del dominio.

---

## NodeId

Identificador lógico único del Node.

Permanece estable durante toda la vida del servicio.

---

## NodeType

Clasificación funcional del Node.

Ejemplos:

* Identity
* Streaming
* Metrics
* Alarm
* Automation
* Storage
* Database
* Transcoding

---

# Nivel 2 — Ejecución

La segunda dimensión describe la ejecución concreta del Node.

Está representada mediante:

```text
NodeInstance
```

Cada Node puede poseer:

* cero;
* una;
* múltiples instancias.

Cada NodeInstance mantiene su propio estado operacional.

---

# Nivel 3 — Estado Operacional

Toda NodeInstance publica las siguientes dimensiones operacionales.

## NodeInfo

Describe información descriptiva de la instancia.

Ejemplos:

* hostname;
* versión;
* sistema operativo;
* dirección de red;
* ubicación.

---

## NodeStatus

Describe el estado del ciclo de vida.

Ejemplos:

* STARTING
* RUNNING
* STOPPING
* FAILED

Responde:

> ¿Qué está haciendo la instancia?

---

## NodeHealth

Describe la condición operacional.

Ejemplos:

* HEALTHY
* WARNING
* DEGRADED
* CRITICAL

Responde:

> ¿Qué tan bien funciona?

---

## NodeAvailability

Describe la disponibilidad para aceptar nuevas tareas.

Ejemplos:

* AVAILABLE
* LIMITED
* DRAINING
* UNAVAILABLE

Responde:

> ¿Puede aceptar nuevas tareas?

---

# Nivel 4 — Capacidades

Las capacidades describen las funcionalidades y recursos disponibles.

## NodeCapability

Representa las funcionalidades soportadas por la NodeInstance.

Responde:

> ¿Qué puede hacer?

Ejemplos:

* SRT
* RTMP
* HLS
* WebRTC
* REST API
* GPU Encoding

---

## NodeCapacity

Representa la capacidad cuantificable de la NodeInstance.

Responde:

> ¿Cuánto puede hacer?

NodeCapacity se modela como una colección de recursos.

```text
NodeCapacity
│
├── CapacityResource
├── CapacityResource
├── CapacityResource
└── ...
```

Cada **CapacityResource** describe un recurso específico mediante atributos como:

* resource
* maximum
* allocated
* reserved
* available
* unit

---

# Nivel 5 — Observabilidad

Toda NodeInstance publica información operacional mediante entidades especializadas.

## NodeMetric

Publica mediciones instantáneas.

Se compone de uno o más **MetricSample**.

Ejemplos:

* CPU
* Memory
* Network
* Temperature

---

## NodeEvent

Publica sucesos relevantes.

Se compone de uno o más **EventRecord**.

Ejemplos:

* inicio;
* reinicio;
* error;
* recuperación.

---

## NodeAlarm

Publica condiciones que requieren atención.

Se compone de uno o más **AlarmRecord**.

Ejemplos:

* CPU crítica;
* pérdida de señal;
* almacenamiento lleno.

---

## NodeHeartbeat

Confirma periódicamente que la NodeInstance continúa activa.

Permite detectar pérdida de comunicación.

---

## NodeSnapshot

Representa una fotografía consistente del estado completo de la NodeInstance en un instante determinado.

Constituye la unidad principal de intercambio de información con el NOC.

---

# Relaciones del Modelo

Las principales relaciones son:

```text
Node
    │
    ├── posee un NodeId
    ├── posee un NodeType
    └── contiene NodeInstances
```

```text
NodeInstance
    │
    ├── publica NodeInfo
    ├── publica NodeStatus
    ├── publica NodeHealth
    ├── publica NodeAvailability
    ├── publica NodeCapability
    ├── publica NodeCapacity
    ├── publica NodeMetric
    ├── publica NodeEvent
    ├── publica NodeAlarm
    ├── publica NodeHeartbeat
    └── genera NodeSnapshot
```

Todas las entidades dependen conceptualmente de NodeInstance.

---

# Principios del Modelo

El modelo de dominio se fundamenta en los siguientes principios:

* una única identidad lógica por Node;
* múltiples instancias por Node;
* separación entre identidad y ejecución;
* separación entre estado, salud y disponibilidad;
* separación entre capacidades y capacidad instalada;
* observabilidad integrada desde el diseño;
* independencia tecnológica;
* extensibilidad del contrato.

---

# Responsabilidades

Cada entidad posee una responsabilidad única.

| Entidad          | Responsabilidad         |
| ---------------- | ----------------------- |
| Node             | Aggregate Root          |
| NodeId           | Identidad               |
| NodeType         | Clasificación           |
| NodeInstance     | Ejecución               |
| NodeInfo         | Información descriptiva |
| NodeStatus       | Estado                  |
| NodeHealth       | Condición operacional   |
| NodeAvailability | Disponibilidad          |
| NodeCapability   | Funcionalidades         |
| NodeCapacity     | Recursos disponibles    |
| NodeMetric       | Métricas                |
| NodeEvent        | Eventos                 |
| NodeAlarm        | Alarmas                 |
| NodeHeartbeat    | Latido                  |
| NodeSnapshot     | Estado completo         |

---

# Extensibilidad

El modelo ha sido diseñado para evolucionar sin modificar su estructura fundamental.

Las futuras versiones podrán incorporar nuevas entidades derivadas o nuevos atributos especializados manteniendo la compatibilidad con las implementaciones existentes.

---

# Conclusión

El Domain Model constituye la representación oficial del dominio de la Node Contract Specification.

La separación entre **Node** y **NodeInstance**, junto con la especialización de las entidades responsables de la identidad, el estado operacional, las capacidades y la observabilidad, proporciona una arquitectura coherente, desacoplada y preparada para soportar plataformas distribuidas, altamente disponibles y escalables.

Este modelo servirá como referencia única para el desarrollo del SDK oficial, del NOC Core y de todas las implementaciones compatibles con la plataforma Broadcast.
