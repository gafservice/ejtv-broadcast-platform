# 15. NodeCapacity

## Introducción

El **NodeCapacity** representa la capacidad operacional de una **NodeInstance**.

Describe los recursos cuantificables que la instancia puede proporcionar para ejecutar su función dentro de la plataforma Broadcast.

A diferencia de una métrica instantánea, la capacidad representa el potencial operativo de la instancia.

La Node Contract Specification modela la capacidad como una colección de recursos independientes denominados **CapacityResource**.

---

# Propósito

El propósito del NodeCapacity es proporcionar una representación uniforme y extensible de la capacidad operacional de una NodeInstance.

Esta información permite al **Network Operations Center (NOC)**:

* planificar capacidad;
* distribuir carga;
* estimar crecimiento;
* soportar orquestación automática;
* optimizar la utilización de recursos.

---

# Responsabilidad

NodeCapacity posee una única responsabilidad:

> Representar la capacidad cuantificable de una NodeInstance.

No representa:

* estado operacional;
* salud;
* disponibilidad;
* utilización instantánea;
* funcionalidades.

Estas dimensiones pertenecen a otras entidades del modelo.

---

# Modelo del Dominio

NodeCapacity no representa un único recurso.

Representa una colección de recursos de capacidad.

```text
NodeCapacity
│
├── CapacityResource
├── CapacityResource
├── CapacityResource
└── ...
```

Cada CapacityResource describe un recurso independiente.

---

# CapacityResource

Un **CapacityResource** representa un recurso cuantificable administrado por una NodeInstance.

Ejemplos:

* canales;
* sesiones;
* trabajos;
* ancho de banda;
* GPU;
* memoria;
* almacenamiento.

Todos los recursos utilizan la misma estructura conceptual.

---

# Atributos de CapacityResource

Todo CapacityResource posee los siguientes atributos.

## resource

Nombre canónico del recurso.

Ejemplos:

```text
Streaming Channels
```

```text
GPU Encoding Jobs
```

```text
Bandwidth
```

---

## maximum

Capacidad máxima instalada.

Ejemplo:

```text
16
```

---

## allocated

Capacidad actualmente asignada.

Ejemplo:

```text
10
```

---

## reserved

Capacidad reservada para políticas operacionales.

Ejemplo:

```text
2
```

---

## available

Capacidad disponible para nuevas asignaciones.

Ejemplo:

```text
4
```

---

## unit

Unidad de medida.

Ejemplos:

```text
channels
```

```text
jobs
```

```text
Mbps
```

```text
GB
```

---

# Ejemplo de CapacityResource

```text
CapacityResource

resource: Streaming Channels

maximum: 16

allocated: 10

reserved: 2

available: 4

unit: channels
```

---

# Colección de Recursos

Una NodeInstance puede publicar múltiples recursos.

Ejemplo:

```text
NodeCapacity

├── Streaming Channels
├── Network Bandwidth
├── Storage
├── RAM
└── GPU Encoding Jobs
```

Cada recurso es completamente independiente.

---

# Relación con NodeCapability

NodeCapability responde:

> ¿Qué puede hacer la instancia?

NodeCapacity responde:

> ¿Cuánto puede hacer?

Ejemplo:

```text
Capability

GPU Encoding
```

```text
Capacity

8 trabajos simultáneos
```

La capacidad cuantifica una funcionalidad.

No la reemplaza.

---

# Relación con NodeMetric

NodeCapacity representa el límite operativo.

NodeMetric representa el comportamiento observado.

Ejemplo:

```text
Capacity

Streaming Channels

Maximum: 16
```

```text
Metric

Active Channels

12
```

La utilización nunca modifica la definición de capacidad.

---

# Relación con NodeAvailability

NodeAvailability responde:

> ¿Puede aceptar nuevas tareas?

La disponibilidad constituye una decisión operacional.

La capacidad representa un recurso físico o lógico.

Ejemplo:

```text
Capacity

4 canales disponibles
```

```text
Availability

UNAVAILABLE
```

La instancia posee capacidad libre, pero la política operacional impide utilizarla.

---

# Recursos Canónicos

La primera versión de la especificación define las siguientes categorías.

## Streaming

* Streaming Channels
* Active Sessions
* Bitrate
* Network Bandwidth

---

## Transcoding

* GPU Encoding Jobs
* GPU Decoding Jobs
* CPU Encoding Jobs
* Video Memory

---

## Identity

* Authentication Requests
* Active Sessions
* Token Generation

---

## Storage

* Disk Capacity
* Object Capacity
* Archive Capacity

---

## Network

* Connections
* Throughput
* Interfaces

---

## System

* CPU Cores
* Memory
* Threads

---

# Agregación

Algunos recursos pueden agregarse entre múltiples NodeInstances.

Ejemplo:

```text
Instance A

Streaming Channels

Maximum: 8
```

```text
Instance B

Streaming Channels

Maximum: 12
```

```text
Node

Streaming Channels

Maximum: 20
```

La política de agregación será responsabilidad del NOC Core.

No todos los recursos son agregables.

---

# Actualización

Los CapacityResources pueden cambiar durante la vida de una NodeInstance.

Ejemplos:

* incorporación de GPU;
* ampliación de memoria;
* instalación de discos;
* actualización de licencias;
* incorporación de hardware especializado.

Cuando esto ocurra, la NodeInstance deberá publicar la nueva información.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* publicar NodeCapacity como una colección de CapacityResource;
* utilizar nombres canónicos para los recursos;
* mantener coherencia entre NodeCapability y NodeCapacity;
* utilizar unidades consistentes.

---

**NO DEBE**

* utilizar NodeCapacity para representar utilización instantánea;
* utilizar NodeCapacity para representar estado;
* utilizar NodeCapacity para representar disponibilidad;
* mezclar diferentes recursos dentro de un mismo CapacityResource.

---

**PUEDE**

* publicar uno o múltiples CapacityResources;
* incorporar nuevos recursos compatibles con la especificación;
* actualizar dinámicamente los recursos publicados.

---

# Ejemplo Conceptual

```text
NodeInstance

NodeCapacity

├── Streaming Channels
│       maximum: 16
│       allocated: 12
│       reserved: 2
│       available: 2
│
├── Network Bandwidth
│       maximum: 10 Gbps
│       allocated: 6 Gbps
│       available: 4 Gbps
│
└── Storage
        maximum: 2 TB
        allocated: 1.2 TB
        available: 0.8 TB
```

---

# Relación con el NOC

El Network Operations Center utilizará NodeCapacity para:

* planificación de capacidad;
* distribución inteligente de carga;
* predicción de crecimiento;
* automatización;
* balanceo;
* dimensionamiento de infraestructura.

Las decisiones operacionales podrán combinar NodeCapacity con NodeHealth y NodeAvailability para seleccionar la instancia más adecuada para una nueva carga de trabajo.

---

# Consideraciones de Evolución

La estructura de NodeCapacity permanecerá estable en futuras versiones de la Node Contract Specification.

La incorporación de nuevos recursos requerirá únicamente la definición de nuevos nombres canónicos de CapacityResource.

No será necesario modificar la estructura del contrato.

---

# Conclusión

NodeCapacity representa la capacidad cuantificable de una NodeInstance mediante una colección de **CapacityResource**.

Este modelo permite describir de forma uniforme cualquier tipo de recurso, independientemente del NodeType o de la tecnología utilizada.

La separación entre capacidad, funcionalidad, disponibilidad y métricas convierte a NodeCapacity en uno de los pilares fundamentales para la planificación, la orquestación y la escalabilidad de la plataforma Broadcast.
