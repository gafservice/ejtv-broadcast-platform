# 6. Node

## Introducción

El **Node** constituye el agregado raíz del modelo de dominio definido por la **Node Contract Specification (NCS)**.

Representa una unidad lógica y operacional de la plataforma Broadcast capaz de ejecutar una responsabilidad específica y de publicar su estado al **Network Operations Center (NOC)** mediante un contrato común.

El Node no representa una ejecución concreta, un proceso, un contenedor ni una máquina física. Representa la identidad lógica y la definición funcional de un componente dentro de la **Node-Oriented Architecture (NOA)**.

---

# Propósito

El propósito del Node es proporcionar una representación canónica de un componente de la plataforma.

Un Node permite al NOC comprender:

* qué componente existe;
* cuál es su identidad lógica;
* qué función desempeña;
* cuántas instancias lo ejecutan;
* cuál es el estado operacional de cada instancia.

El Node agrupa los elementos fundamentales del dominio y actúa como punto de consistencia para todas las entidades relacionadas.

---

# Definición

Un **Node** es una entidad lógica estable que representa una capacidad funcional dentro de la plataforma y que puede poseer una o más instancias de ejecución.

Todo Node DEBE estar definido por:

* un `NodeId`;
* un `NodeType`;
* cero o más `NodeInstance`.

La existencia lógica del Node es independiente de la disponibilidad temporal de sus instancias.

---

# Agregado Raíz

Dentro del modelo de dominio, Node actúa como **Aggregate Root**.

Esto significa que:

* todas las instancias pertenecen a un Node;
* toda modificación del conjunto de instancias debe preservar la consistencia del Node;
* las relaciones externas deben referenciar al Node mediante su identidad canónica;
* el Node controla las invariantes principales del agregado.

El NOC DEBE tratar al Node como la unidad lógica principal del inventario operacional.

---

# Estructura Conceptual

```text
Node
│
├── NodeId
├── NodeType
└── NodeInstance [0..N]
```

Cada Node posee exactamente una identidad y un tipo funcional.

Puede no tener instancias activas o puede tener múltiples instancias ejecutándose simultáneamente.

---

# NodeId

El `NodeId` representa la identidad lógica permanente del Node.

Permite distinguirlo de cualquier otro componente registrado en la plataforma.

El NodeId:

* DEBE ser único;
* DEBE permanecer estable;
* NO DEBE depender de infraestructura;
* NO DEBE cambiar al reiniciar una instancia;
* NO DEBE cambiar cuando el Node sea migrado a otro servidor.

---

# NodeType

El `NodeType` clasifica funcionalmente al Node.

Describe qué responsabilidad cumple dentro de la plataforma.

Ejemplos:

* Identity;
* Streaming;
* Metrics;
* Alarm;
* Automation;
* Transcoding;
* Storage;
* Database.

Un Node DEBE poseer exactamente un NodeType.

El NodeType NO DEBE cambiar durante la vida lógica del Node.

---

# NodeInstance

Una `NodeInstance` representa una ejecución concreta del Node.

Un Node puede tener:

* ninguna instancia activa;
* una instancia;
* múltiples instancias simultáneas.

Cada instancia mantiene su propio:

* entorno de ejecución;
* estado;
* salud;
* capacidad;
* métricas;
* eventos;
* alarmas;
* heartbeat;
* snapshot.

Las instancias comparten la identidad lógica y el tipo del Node, pero poseen identidad operacional propia.

---

# Diferencia entre Node y NodeInstance

La distinción entre Node y NodeInstance es fundamental.

El Node responde:

> ¿Qué componente es?

La NodeInstance responde:

> ¿Dónde y cómo está ejecutándose ahora?

Ejemplo:

```text
Node
└── Streaming

NodeInstances
├── streaming-primary-san-jose
├── streaming-secondary-miami
└── streaming-edge-panama
```

Las tres instancias representan ejecuciones distintas del mismo Node lógico.

---

# Invariantes del Agregado

Toda implementación compatible DEBE preservar las siguientes invariantes:

1. Todo Node posee exactamente un NodeId.
2. Todo Node posee exactamente un NodeType.
3. Toda NodeInstance pertenece exactamente a un Node.
4. Ninguna NodeInstance puede pertenecer simultáneamente a varios Nodes.
5. El NodeId permanece estable durante toda la vida lógica del Node.
6. El NodeType permanece estable durante toda la vida lógica del Node.
7. Dos Nodes distintos NO DEBEN compartir el mismo NodeId.
8. Dos instancias activas del mismo Node NO DEBEN compartir el mismo identificador de instancia.
9. La eliminación de una instancia NO elimina necesariamente el Node lógico.
10. La ausencia de instancias activas NO invalida la existencia del Node.

---

# Ciclo de Vida del Node

El ciclo de vida lógico del Node es independiente del ciclo de vida de sus instancias.

```text
Definición
    │
    ▼
Registro
    │
    ▼
Disponibilidad lógica
    │
    ├── Sin instancias activas
    │
    ├── Una instancia activa
    │
    └── Múltiples instancias activas
    │
    ▼
Retiro
```

Reiniciar, reemplazar o migrar una instancia NO crea necesariamente un nuevo Node.

---

# Estado del Node

El Node lógico no publica directamente métricas o información de ejecución.

Estas pertenecen a sus instancias.

El estado agregado del Node puede ser calculado por el NOC a partir del estado de todas sus NodeInstances.

Ejemplos:

* `AVAILABLE`: al menos una instancia puede prestar el servicio;
* `DEGRADED`: algunas instancias presentan problemas;
* `UNAVAILABLE`: ninguna instancia puede prestar el servicio;
* `INACTIVE`: no existen instancias activas;
* `UNKNOWN`: no existe información suficiente.

Estos estados agregados pertenecen al NOC Core y no sustituyen el `NodeStatus` de cada instancia.

---

# Capacidad Agregada

La capacidad global de un Node puede calcularse mediante la consolidación de la capacidad publicada por sus instancias.

Ejemplo:

```text
Transcoding Node
├── Instance A: 4 canales disponibles
├── Instance B: 6 canales disponibles
└── Capacidad agregada: 10 canales
```

La forma exacta de agregación dependerá del tipo de capacidad y deberá respetar su semántica.

El NOC NO DEBE sumar valores que no sean agregables.

---

# Salud Agregada

La salud lógica del Node puede derivarse del estado de salud de todas sus instancias.

Ejemplo:

```text
Instance A: HEALTHY
Instance B: HEALTHY
Instance C: WARNING

Node agregado: DEGRADED
```

La política exacta de agregación será responsabilidad del NOC Core.

La NCS define los datos fuente, pero no impone una única estrategia operacional de consolidación.

---

# Persistencia

La definición lógica del Node DEBERÍA persistir aunque temporalmente no existan instancias activas.

Esto permite preservar:

* inventario;
* trazabilidad;
* configuración;
* historial;
* eventos;
* alarmas;
* relaciones operacionales.

La desaparición temporal de todas las instancias no implica la eliminación automática del Node.

---

# Registro

Todo Node compatible DEBE registrarse ante el NOC antes de publicar información operacional de sus instancias.

El registro deberá incluir como mínimo:

* NodeId;
* NodeType;
* versión del contrato;
* metadatos básicos;
* instancias conocidas, cuando existan.

El mecanismo de registro será definido posteriormente por el NOC Core y por la capa de transporte correspondiente.

---

# Extensibilidad

El modelo permite incorporar nuevas propiedades al Node siempre que se preserve la compatibilidad.

Las extensiones futuras pueden incluir:

* etiquetas;
* relaciones;
* grupos;
* dependencias;
* ubicación lógica;
* políticas;
* propietario operacional.

Estas extensiones NO DEBEN alterar el significado de NodeId, NodeType o NodeInstance.

---

# Ejemplo Conceptual

```text
Node
├── NodeId
│   └── 9f6c6c9a-9d86-4ea5-b5f8-7fd0f0e30c44
├── NodeType
│   └── STREAMING
└── Instances
    ├── streaming-primary
    └── streaming-secondary
```

El Node representa la capacidad lógica de streaming.

Las instancias representan las ejecuciones concretas que prestan esa capacidad.

---

# Relación con NodeSnapshot

Un `NodeSnapshot` representa el estado de una NodeInstance en un momento determinado.

Por lo tanto:

* un Node puede tener múltiples snapshots simultáneos;
* cada snapshot pertenece a una única instancia;
* el NOC puede construir una vista agregada del Node utilizando los snapshots de todas sus instancias.

El NodeSnapshot NO representa directamente al Node lógico.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* representar el Node como entidad lógica;
* separar Node de NodeInstance;
* asociar toda instancia a un único Node;
* preservar las invariantes del agregado;
* mantener estable el NodeId;
* mantener estable el NodeType.

**NO DEBE**

* mezclar identidad lógica con información de ejecución;
* utilizar direcciones IP como NodeId;
* considerar cada reinicio como un nuevo Node;
* publicar métricas directamente desde el Node lógico;
* asociar una instancia a más de un Node.

**PUEDE**

* mantener Nodes sin instancias activas;
* agregar etiquetas y metadatos compatibles;
* calcular vistas agregadas a partir de múltiples instancias.

---

# Conclusión

El Node constituye el agregado raíz del dominio operacional de la plataforma Broadcast.

Su función es representar una capacidad lógica estable, independiente de las ejecuciones concretas que la materializan.

La separación entre Node y NodeInstance permite soportar alta disponibilidad, escalabilidad horizontal, despliegues distribuidos y migraciones de infraestructura sin perder identidad ni trazabilidad.

Esta distinción constituye uno de los fundamentos principales de la Node-Oriented Architecture y de la Node Contract Specification.
