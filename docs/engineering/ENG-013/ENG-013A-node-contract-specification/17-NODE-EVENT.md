# 17. NodeEvent

## Introducción

El **NodeEvent** representa el conjunto de eventos generados por una **NodeInstance** durante su ciclo de vida.

Un evento describe un hecho significativo ocurrido en un instante determinado.

A diferencia de las métricas, que representan observaciones continuas, un evento representa un cambio, una acción o una situación puntual.

La Node Contract Specification modela los eventos como una colección de registros independientes denominados **EventRecord**.

---

# Propósito

El propósito del NodeEvent es proporcionar un registro uniforme, cronológico e inmutable de los hechos relevantes ocurridos en una NodeInstance.

Los eventos permiten al **Network Operations Center (NOC)**:

* reconstruir la historia operacional;
* realizar auditorías;
* correlacionar incidentes;
* alimentar procesos automáticos;
* facilitar el diagnóstico de fallos;
* generar trazabilidad distribuida.

---

# Responsabilidad

NodeEvent posee una única responsabilidad:

> Registrar hechos significativos ocurridos durante la operación de una NodeInstance.

No representa:

* estado actual;
* salud;
* disponibilidad;
* métricas;
* alarmas.

Estas dimensiones pertenecen a otras entidades del modelo.

---

# Modelo del Dominio

NodeEvent representa una colección de registros de eventos.

```text
NodeEvent
│
├── EventRecord
├── EventRecord
├── EventRecord
└── ...
```

Cada EventRecord representa un único hecho ocurrido.

---

# EventRecord

Un **EventRecord** representa un acontecimiento ocurrido en un instante específico.

Una vez publicado, un EventRecord es inmutable.

Los eventos constituyen el historial operacional de una NodeInstance.

---

# Inmutabilidad

Todo EventRecord debe cumplir el principio de inmutabilidad.

Una vez emitido:

* no puede modificarse;
* no puede reutilizarse;
* no puede sobrescribirse.

Si ocurre un nuevo hecho, deberá generarse un nuevo EventRecord.

Este principio garantiza la integridad del historial operacional.

---

# Atributos de EventRecord

Todo EventRecord posee los siguientes atributos.

## event_id

Identificador único del evento.

Ejemplo:

```text
evt-6a0f51d2
```

---

## event_type

Nombre canónico del evento.

Ejemplos:

```text
INSTANCE_STARTED
```

```text
CLIENT_CONNECTED
```

```text
STREAM_CREATED
```

---

## severity

Nivel de importancia del evento.

La versión 1.0 define:

* INFO
* NOTICE
* WARNING
* ERROR
* CRITICAL

La severidad clasifica el evento.

No implica necesariamente la existencia de una alarma.

---

## timestamp

Momento exacto en que ocurrió el evento.

---

## source

Origen del evento.

Generalmente corresponde a la NodeInstance que lo generó.

---

## title

Resumen breve del evento.

Ejemplo:

```text
Streaming service started
```

---

## description

Descripción detallada del evento.

Debe proporcionar suficiente contexto para comprender el hecho registrado.

---

## attributes

Colección opcional de pares clave-valor con información adicional.

Ejemplo:

```text
stream = "Canal-01"
client = "192.168.10.25"
protocol = "SRT"
```

---

## correlation_id

Identificador utilizado para relacionar múltiples eventos pertenecientes a una misma operación.

---

# Catálogo Canónico de Eventos

La versión 1.0 define el siguiente catálogo inicial.

## Ciclo de Vida

* INSTANCE_CREATED
* INSTANCE_INITIALIZED
* INSTANCE_STARTED
* INSTANCE_STOPPED
* INSTANCE_RESTARTED
* INSTANCE_TERMINATED

---

## Configuración

* CONFIGURATION_LOADED
* CONFIGURATION_RELOADED
* CONFIGURATION_UPDATED

---

## Streaming

* STREAM_CREATED
* STREAM_REMOVED
* STREAM_STARTED
* STREAM_STOPPED
* PUBLISHER_CONNECTED
* PUBLISHER_DISCONNECTED
* READER_CONNECTED
* READER_DISCONNECTED

---

## Red

* NETWORK_CONNECTED
* NETWORK_DISCONNECTED
* INTERFACE_UP
* INTERFACE_DOWN

---

## Seguridad

* AUTHENTICATION_SUCCEEDED
* AUTHENTICATION_FAILED
* AUTHORIZATION_GRANTED
* AUTHORIZATION_DENIED

---

## Recursos

* RESOURCE_ALLOCATED
* RESOURCE_RELEASED
* CAPACITY_UPDATED

---

# Correlación

Los eventos relacionados con una misma operación pueden compartir un mismo **correlation_id**.

Ejemplo:

```text
INSTANCE_STARTED
        │
        ▼
CONFIGURATION_LOADED
        │
        ▼
DATABASE_CONNECTED
        │
        ▼
STREAMS_INITIALIZED
        │
        ▼
INSTANCE_READY
```

Todos estos eventos pueden pertenecer a una única secuencia operacional.

---

# Relación con NodeMetric

NodeMetric responde:

> ¿Qué está ocurriendo en este instante?

NodeEvent responde:

> ¿Qué ocurrió?

Ejemplo:

```text
Metric

cpu_usage = 91%
```

```text
Event

GPU_INITIALIZED
```

Una métrica es una observación.

Un evento es un hecho.

---

# Relación con NodeAlarm

Un evento puede originar una alarma.

Ejemplo:

```text
Event

NETWORK_DISCONNECTED
```

↓

```text
Alarm

NETWORK_LOST
```

La existencia de un evento no implica necesariamente una alarma.

Y una alarma puede depender de múltiples eventos.

---

# Persistencia

Los EventRecord deben conservarse para mantener la trazabilidad operacional.

La política de retención dependerá de la organización y del tipo de Node.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* publicar eventos mediante EventRecord;
* utilizar nombres canónicos;
* registrar timestamp;
* garantizar la inmutabilidad de los eventos;
* asignar un event_id único.

---

**NO DEBE**

* modificar un EventRecord ya publicado;
* reutilizar identificadores;
* utilizar nombres ambiguos;
* mezclar múltiples eventos en un mismo EventRecord.

---

**PUEDE**

* incluir atributos adicionales;
* utilizar correlation_id;
* publicar eventos específicos del dominio siempre que respeten la estructura de la especificación.

---

# Ejemplo Conceptual

```text
NodeEvent

├── INSTANCE_STARTED
├── CONFIGURATION_LOADED
├── PUBLISHER_CONNECTED
├── STREAM_CREATED
├── READER_CONNECTED
└── STREAM_STOPPED
```

Cada EventRecord representa un hecho independiente ocurrido durante la vida de la NodeInstance.

---

# Relación con el NOC

El Network Operations Center utilizará NodeEvent para:

* reconstrucción cronológica de incidentes;
* auditoría operacional;
* análisis forense;
* automatización;
* correlación de fallos;
* generación de reportes;
* integración con sistemas externos.

NodeEvent constituye la memoria operacional de la NodeInstance.

---

# Consideraciones de Evolución

La estructura de NodeEvent permanecerá estable.

La incorporación de nuevos tipos de eventos requerirá únicamente ampliar el catálogo canónico.

No será necesario modificar la estructura del contrato.

---

# Conclusión

NodeEvent representa el historial operacional de una NodeInstance mediante una colección de **EventRecord**.

Este modelo proporciona una representación uniforme, cronológica e inmutable de los hechos ocurridos durante la operación de la plataforma.

La separación entre métricas, eventos y alarmas permite construir un sistema de observabilidad robusto, trazable y preparado para arquitecturas distribuidas de gran escala.
