# 18. NodeAlarm

## Introducción

El **NodeAlarm** representa el conjunto de alarmas activas e históricas generadas por una **NodeInstance**.

Una alarma representa una condición operacional que requiere atención por parte del **Network Operations Center (NOC)** o de un sistema automático de respuesta.

A diferencia de una métrica, que representa una observación, o de un evento, que representa un hecho ocurrido, una alarma representa una condición que requiere seguimiento hasta su resolución.

La Node Contract Specification modela las alarmas como una colección de registros independientes denominados **AlarmRecord**.

---

# Propósito

El propósito del NodeAlarm es proporcionar una representación uniforme de las condiciones operacionales que requieren atención.

Las alarmas permiten al NOC:

* detectar incidentes;
* priorizar problemas;
* iniciar acciones automáticas;
* notificar operadores;
* mantener trazabilidad de incidentes;
* verificar la resolución de condiciones críticas.

---

# Responsabilidad

NodeAlarm posee una única responsabilidad:

> Representar condiciones operacionales que requieren atención.

No representa:

* métricas;
* eventos;
* estado operacional;
* salud;
* disponibilidad.

Estas dimensiones pertenecen a otras entidades del modelo.

---

# Modelo del Dominio

NodeAlarm representa una colección de registros de alarma.

```text
NodeAlarm
│
├── AlarmRecord
├── AlarmRecord
├── AlarmRecord
└── ...
```

Cada AlarmRecord representa una condición independiente.

---

# AlarmRecord

Un **AlarmRecord** representa una condición operacional detectada por una NodeInstance o por el NOC.

Una alarma permanece vigente hasta que su ciclo de vida finaliza.

---

# Atributos de AlarmRecord

Todo AlarmRecord posee los siguientes atributos.

## alarm_id

Identificador único de la alarma.

Ejemplo:

```text
alm-87f42ab1
```

---

## alarm_type

Nombre canónico de la alarma.

Ejemplos:

```text
CPU_HIGH
```

```text
NETWORK_LOST
```

```text
STREAM_OFFLINE
```

---

## severity

Nivel de criticidad de la alarma.

La versión 1.0 define:

* INFO
* WARNING
* MINOR
* MAJOR
* CRITICAL

La severidad representa el impacto operacional esperado.

---

## state

Estado actual de la alarma.

La versión 1.0 define:

* ACTIVE
* ACKNOWLEDGED
* RESOLVED
* CLOSED

---

## timestamp

Momento en que la alarma fue generada.

---

## source

NodeInstance que originó la alarma.

---

## title

Resumen corto de la alarma.

Ejemplo:

```text
CPU usage exceeded threshold
```

---

## description

Descripción detallada de la condición detectada.

Debe proporcionar suficiente contexto para comprender el problema.

---

## acknowledged

Indica si un operador confirmó la recepción de la alarma.

Valores:

* true
* false

---

## acknowledged_by

Identificador del operador o sistema que realizó el reconocimiento.

Este atributo es opcional.

---

## acknowledged_at

Momento en que la alarma fue reconocida.

Este atributo es opcional.

---

## resolved_at

Momento en que la condición dejó de existir.

---

## closed_at

Momento en que la alarma fue cerrada definitivamente.

---

## correlation_id

Identificador utilizado para relacionar la alarma con otros eventos o alarmas pertenecientes a una misma operación.

---

## attributes

Colección opcional de pares clave-valor con información adicional.

Ejemplo:

```text
stream = Canal-01

threshold = 95%

current_value = 98.2%
```

---

# Ciclo de Vida

Toda alarma evoluciona siguiendo un ciclo de vida.

```text
ACTIVE
   │
   ▼
ACKNOWLEDGED
   │
   ▼
RESOLVED
   │
   ▼
CLOSED
```

Una alarma nunca vuelve a estados anteriores.

Si la condición reaparece, deberá generarse una nueva alarma.

---

# Catálogo Canónico

La versión 1.0 define el siguiente conjunto inicial.

## Recursos

* CPU_HIGH
* MEMORY_HIGH
* DISK_FULL
* STORAGE_LOW
* GPU_OVERHEAT

---

## Red

* NETWORK_LOST
* NETWORK_DEGRADED
* HIGH_PACKET_LOSS
* HIGH_LATENCY

---

## Streaming

* STREAM_OFFLINE
* STREAM_UNAVAILABLE
* PUBLISHER_LOST
* READER_LIMIT_REACHED
* BITRATE_DEGRADED

---

## Seguridad

* AUTHENTICATION_FAILURE_RATE
* AUTHORIZATION_FAILURE_RATE
* INVALID_TOKEN_RATE

---

## Plataforma

* SERVICE_UNAVAILABLE
* DATABASE_UNAVAILABLE
* CONFIGURATION_ERROR
* CAPACITY_EXHAUSTED

---

# Relación con NodeMetric

Una alarma puede originarse a partir de una o múltiples métricas.

Ejemplo:

```text
Metric

cpu_usage = 98%
```

↓

```text
Alarm

CPU_HIGH
```

---

# Relación con NodeEvent

Una alarma también puede originarse a partir de uno o varios eventos.

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

---

# Relación con NodeHealth

Una alarma no modifica directamente NodeHealth.

Sin embargo, el algoritmo de evaluación de salud puede considerar la existencia de alarmas activas.

La Node Contract Specification no impone dicha relación.

---

# Persistencia

Los AlarmRecord deberán conservarse durante el tiempo definido por la política operacional.

Las alarmas cerradas continúan formando parte del historial operacional.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* publicar alarmas mediante AlarmRecord;
* utilizar nombres canónicos;
* asignar un alarm_id único;
* mantener el ciclo de vida de la alarma;
* conservar la trazabilidad mediante timestamps.

---

**NO DEBE**

* reutilizar alarmas ya cerradas;
* modificar el historial de una alarma;
* utilizar nombres ambiguos;
* mezclar varias alarmas dentro de un mismo AlarmRecord.

---

**PUEDE**

* generar alarmas automáticamente;
* permitir reconocimiento manual;
* incorporar atributos adicionales compatibles con la especificación;
* relacionar alarmas mediante correlation_id.

---

# Ejemplo Conceptual

```text
NodeAlarm

├── CPU_HIGH
├── STREAM_OFFLINE
├── NETWORK_LOST
└── CAPACITY_EXHAUSTED
```

Cada AlarmRecord representa una condición independiente que requiere seguimiento.

---

# Relación con el NOC

El Network Operations Center utilizará NodeAlarm para:

* priorizar incidentes;
* mostrar paneles de operación;
* activar automatizaciones;
* escalar problemas;
* generar reportes;
* medir tiempos de respuesta (MTTA);
* medir tiempos de resolución (MTTR).

Las políticas específicas de tratamiento serán responsabilidad del NOC Core.

---

# Consideraciones de Evolución

La estructura de NodeAlarm permanecerá estable.

Las futuras versiones de la Node Contract Specification podrán ampliar el catálogo de alarmas sin modificar la estructura del contrato.

Esto garantiza la compatibilidad entre versiones y facilita la evolución de la plataforma.

---

# Conclusión

NodeAlarm representa las condiciones operacionales que requieren atención mediante una colección de **AlarmRecord**.

La separación entre métricas, eventos y alarmas permite construir un modelo de observabilidad robusto, donde las observaciones, los hechos y las acciones necesarias permanecen claramente diferenciados.

Esta arquitectura proporciona una base sólida para la operación, la automatización y la gestión de incidentes en la plataforma Broadcast.
