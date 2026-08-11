# 29. Reference Examples

## Introducción

Los **Reference Examples** proporcionan implementaciones conceptuales de referencia para las entidades definidas por la **Node Contract Specification (NCS)**.

Su objetivo es ilustrar la aplicación correcta del contrato mediante perfiles representativos de distintos tipos de Node.

Estos ejemplos tienen carácter normativo únicamente en cuanto al uso del contrato. Los valores utilizados son ilustrativos.

---

# Propósito

El propósito de los Reference Examples es:

* facilitar la implementación de la NCS;
* reducir ambigüedades;
* promover la interoperabilidad;
* proporcionar modelos reutilizables;
* servir como referencia para SDKs, pruebas y documentación.

---

# Principios

Todo ejemplo de referencia deberá:

* respetar íntegramente el contrato definido por la NCS;
* utilizar nombres canónicos;
* preservar la semántica de las entidades;
* representar escenarios realistas.

Los ejemplos ilustran el uso del contrato, no una implementación específica.

---

# Perfil 1 — Minimal Node

El **Minimal Node** representa la implementación mínima compatible con la NCS.

Debe incluir como mínimo:

```text
Node

├── NodeId
├── NodeType
├── NodeInstance
├── NodeStatus
└── NodeHeartbeat
```

Este perfil está orientado a pruebas, prototipos y nuevos desarrollos.

---

# Perfil 2 — Streaming Node

Ejemplo conceptual de un nodo de distribución de contenido multimedia.

Componentes típicos:

```text
Streaming Node

├── NodeInfo
├── NodeStatus
├── NodeHealth
├── NodeAvailability
├── NodeCapability
├── NodeCapacity
├── NodeMetric
├── NodeAlarm
├── NodeHeartbeat
└── NodeSnapshot
```

Las capacidades pueden incluir:

* recepción SRT;
* distribución RTMP;
* HLS;
* WebRTC;
* monitoreo de sesiones.

---

# Perfil 3 — Identity Node

Nodo responsable de autenticación y autorización.

Ejemplo conceptual:

```text
Identity Node

├── Authentication
├── Authorization
├── Session Metrics
├── Token Metrics
├── NodeHealth
└── NodeSnapshot
```

El contrato utilizado es exactamente el mismo.

---

# Perfil 4 — Transcoding Node

Nodo especializado en procesamiento de audio y video.

Ejemplo conceptual:

```text
Transcoding Node

├── GPU Metrics
├── CPU Metrics
├── Active Jobs
├── Capacity
├── Health
└── Snapshot
```

Las capacidades publicadas difieren de las de un Streaming Node, pero la estructura permanece inalterada.

---

# Perfil 5 — Metrics Node

Nodo dedicado a la recopilación y agregación de métricas.

Ejemplo conceptual:

```text
Metrics Node

├── Metric Samples
├── Aggregation
├── Snapshot
└── Heartbeat
```

---

# Perfil 6 — Alarm Node

Nodo especializado en la gestión de alarmas.

Ejemplo conceptual:

```text
Alarm Node

├── Active Alarms
├── Alarm History
├── Health
└── Snapshot
```

---

# Perfil 7 — Automation Node

Nodo encargado de ejecutar acciones automáticas.

Ejemplo conceptual:

```text
Automation Node

├── Automation Rules
├── Execution Status
├── Events
├── Metrics
└── Snapshot
```

---

# Ejemplo de NodeSnapshot

Todo perfil de referencia puede generar un NodeSnapshot.

Ejemplo conceptual:

```text
NodeSnapshot

Identity
    NodeId
    NodeType
    NodeInstance

Execution
    NodeInfo
    NodeStatus
    NodeHealth
    NodeAvailability

Capability
    NodeCapability
    NodeCapacity

Observability
    NodeMetric
    NodeAlarm
    NodeHeartbeat
```

El Snapshot constituye la representación unificada del estado del Node.

---

# Buenas Prácticas

Toda implementación debería:

* utilizar nombres canónicos;
* publicar únicamente información válida;
* mantener coherencia entre las entidades;
* respetar las reglas de Versioning y Compatibility;
* validar la información antes de publicarla.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* respetar la estructura definida por la NCS;
* utilizar entidades canónicas;
* preservar el significado de los ejemplos de referencia.

---

**NO DEBE**

* modificar la semántica de las entidades presentadas;
* utilizar nombres ambiguos en los perfiles de referencia;
* interpretar estos ejemplos como limitaciones funcionales.

---

**PUEDE**

* extender los perfiles;
* crear nuevos tipos de Node;
* incorporar capacidades específicas del dominio;
* generar ejemplos adicionales compatibles con la especificación.

---

# Relación con el SDK

Los Reference Examples constituyen la base para el desarrollo de:

* SDK oficiales;
* implementaciones de referencia;
* pruebas de conformidad;
* ejemplos de documentación;
* plantillas para nuevos Nodes.

Los ejemplos podrán materializarse posteriormente en formatos como JSON, YAML, Protocol Buffers u otros, manteniendo siempre la estructura lógica definida por la NCS.

---

# Consideraciones de Evolución

La incorporación de nuevos perfiles de referencia no modificará el contrato definido por la Node Contract Specification.

Los perfiles evolucionarán como ejemplos oficiales de implementación, reflejando las capacidades disponibles en cada versión de la NCS.

---

# Conclusión

Los Reference Examples proporcionan una colección de perfiles de implementación que ilustran el uso correcto de la Node Contract Specification.

Estos perfiles constituyen la referencia oficial para desarrolladores, integradores y fabricantes de Nodes, facilitando la interoperabilidad y acelerando la adopción de la NCS.

Al separar claramente el contrato de sus ejemplos de aplicación, la especificación mantiene su independencia tecnológica y proporciona una base sólida para la construcción de SDKs, herramientas de validación e implementaciones de referencia.
