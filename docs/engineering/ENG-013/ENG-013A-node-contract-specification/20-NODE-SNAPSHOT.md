# 20. NodeSnapshot

## Introducción

El **NodeSnapshot** representa una fotografía completa del estado de una **NodeInstance** en un instante determinado.

A diferencia de las entidades individuales definidas por la Node Contract Specification, el Snapshot constituye un **objeto compuesto** que reúne la información operacional de una instancia bajo una única representación consistente.

El NodeSnapshot constituye el principal mecanismo utilizado por el **Network Operations Center (NOC)** para obtener una visión integral del estado actual de una NodeInstance.

---

# Propósito

El propósito del NodeSnapshot es proporcionar una representación uniforme, consistente y autocontenida del estado completo de una NodeInstance.

El Snapshot permite al NOC:

* visualizar el estado completo de una instancia;
* sincronizar información operacional;
* almacenar fotografías históricas;
* reconstruir el estado de la plataforma;
* intercambiar información entre componentes.

---

# Responsabilidad

NodeSnapshot posee una única responsabilidad:

> Representar el estado completo de una NodeInstance en un instante determinado.

No representa:

* una serie temporal;
* una secuencia de eventos;
* un historial;
* una política operacional.

Estas responsabilidades pertenecen a otras entidades del modelo.

---

# Naturaleza

El Snapshot es una representación instantánea.

Describe cómo se encontraba una NodeInstance en un momento específico.

No describe:

* cómo llegó a ese estado;
* cuánto tiempo permaneció en él;
* qué ocurrirá posteriormente.

---

# Modelo del Dominio

NodeSnapshot constituye un agregado de entidades.

```text
NodeSnapshot
│
├── NodeId
├── NodeType
├── NodeInstance
├── NodeInfo
├── NodeStatus
├── NodeHealth
├── NodeAvailability
├── NodeCapability
├── NodeCapacity
├── NodeMetric
├── NodeAlarm
└── NodeHeartbeat
```

Cada componente mantiene su propia semántica.

El Snapshot únicamente los agrupa.

---

# Componentes

Todo NodeSnapshot puede contener la siguiente información.

## Identidad

* NodeId
* NodeType
* NodeInstance

---

## Ejecución

* NodeInfo
* NodeStatus
* NodeHealth
* NodeAvailability

---

## Capacidades

* NodeCapability
* NodeCapacity

---

## Observabilidad

* NodeMetric
* NodeAlarm
* NodeHeartbeat

---

# Timestamp

Todo Snapshot debe representar un instante perfectamente definido.

Por ello, todo Snapshot deberá incluir un timestamp global que identifique el momento en que la fotografía fue construida.

Ejemplo:

```text
snapshot_timestamp

2026-08-09T21:15:00Z
```

Este timestamp identifica al Snapshot completo.

No reemplaza los timestamps individuales de las entidades internas.

---

# Coherencia

Todas las entidades incluidas en un Snapshot deben corresponder al mismo contexto operacional.

Aunque algunas mediciones puedan haberse obtenido con pequeñas diferencias temporales, la representación debe ser suficientemente consistente para describir una única visión de la NodeInstance.

---

# Construcción

El Snapshot puede generarse mediante diferentes estrategias.

Ejemplos:

* captura periódica;
* captura bajo demanda;
* sincronización completa;
* reconstrucción desde memoria.

La Node Contract Specification no impone un mecanismo específico.

---

# Relación con NodeMetric

NodeMetric representa mediciones individuales.

NodeSnapshot incorpora el conjunto de métricas disponibles en el instante de captura.

---

# Relación con NodeEvent

Los eventos no forman parte del Snapshot.

Los eventos describen la historia de la NodeInstance.

El Snapshot describe únicamente su estado actual.

---

# Relación con NodeAlarm

El Snapshot incorpora las alarmas activas conocidas durante la captura.

No incorpora el historial completo de alarmas.

---

# Relación con NodeHeartbeat

El Snapshot incorpora el último Heartbeat conocido.

No incorpora el historial de Heartbeats.

---

# Persistencia

Los Snapshots pueden almacenarse para:

* auditoría;
* análisis histórico;
* comparación temporal;
* generación de reportes;
* recuperación de estado.

La política de retención será responsabilidad del NOC Core.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* construir el Snapshot utilizando las entidades definidas por la Node Contract Specification;
* incluir un timestamp global;
* preservar la coherencia entre los componentes;
* representar una única NodeInstance.

---

**NO DEBE**

* mezclar información perteneciente a distintas NodeInstances;
* modificar el significado de las entidades incluidas;
* utilizar el Snapshot como sustituto del historial de eventos.

---

**PUEDE**

* omitir componentes no aplicables;
* extender el Snapshot con información compatible;
* generar Snapshots bajo demanda o periódicamente.

---

# Ejemplo Conceptual

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

---

# Relación con el NOC

El Network Operations Center utilizará NodeSnapshot como unidad principal de sincronización entre la NodeInstance y el NOC.

A partir del Snapshot, el NOC podrá:

* actualizar dashboards;
* recalcular estados agregados;
* evaluar disponibilidad;
* alimentar procesos automáticos;
* construir vistas históricas.

NodeSnapshot constituye la representación oficial del estado operacional completo de una NodeInstance.

---

# Consideraciones de Evolución

La estructura de NodeSnapshot evolucionará incorporando nuevas entidades definidas por futuras versiones de la Node Contract Specification.

La incorporación de nuevos componentes no modificará el significado de los ya existentes.

Esto garantiza la compatibilidad hacia adelante de la especificación.

---

# Conclusión

NodeSnapshot representa una fotografía completa, consistente y autocontenida del estado de una NodeInstance.

Su función consiste en integrar las distintas dimensiones definidas por la Node Contract Specification en un único objeto coherente, facilitando la sincronización, la observación y la administración operacional de la plataforma.

NodeSnapshot constituye el punto de integración entre la Node Contract Specification y el Network Operations Center, proporcionando la base para la visualización, la automatización y la toma de decisiones sobre el estado de la infraestructura distribuida.
