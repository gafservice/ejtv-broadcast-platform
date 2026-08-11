# 16. NodeMetric

## Introducción

El **NodeMetric** representa el conjunto de mediciones operacionales publicadas por una **NodeInstance**.

Las métricas constituyen la principal fuente de información utilizada por el **Network Operations Center (NOC)** para observar el comportamiento de la plataforma en tiempo real.

La Node Contract Specification modela las métricas como una colección de muestras independientes denominadas **MetricSample**.

---

# Propósito

El propósito del NodeMetric es proporcionar una representación uniforme, extensible y tecnológicamente independiente de las mediciones operacionales de una NodeInstance.

Las métricas permiten al NOC:

* observar el comportamiento del sistema;
* calcular tendencias;
* detectar anomalías;
* generar alarmas;
* evaluar salud;
* alimentar procesos de automatización.

---

# Responsabilidad

NodeMetric posee una única responsabilidad:

> Publicar mediciones objetivas del comportamiento de una NodeInstance.

No representa:

* estado operacional;
* salud;
* disponibilidad;
* capacidad instalada;
* decisiones operacionales.

Estas dimensiones pertenecen a otras entidades del modelo.

---

# Modelo del Dominio

NodeMetric representa una colección de muestras.

```text
NodeMetric
│
├── MetricSample
├── MetricSample
├── MetricSample
└── ...
```

Cada muestra describe una medición independiente.

---

# MetricSample

Un **MetricSample** representa una observación puntual de una variable operacional.

No representa una serie temporal.

No representa un promedio histórico.

Representa únicamente el valor observado en un instante determinado.

---

# Atributos de MetricSample

Todo MetricSample posee los siguientes atributos.

## metric

Nombre canónico de la métrica.

Ejemplos:

```text
cpu_usage
```

```text
memory_usage
```

```text
network_rx
```

```text
temperature
```

---

## value

Valor observado.

Ejemplos:

```text
85.4
```

```text
12
```

```text
1024
```

---

## unit

Unidad de medida.

Ejemplos:

```text
%
```

```text
Mbps
```

```text
channels
```

```text
°C
```

---

## timestamp

Momento exacto en que fue obtenida la medición.

Toda métrica debe encontrarse asociada a un instante temporal.

---

## quality

Nivel de confianza de la medición.

La versión 1.0 define los siguientes valores:

* GOOD
* DEGRADED
* INVALID
* UNKNOWN

La calidad describe la confiabilidad de la medición, no la condición del Node.

---

# Ejemplo de MetricSample

```text
MetricSample

metric: cpu_usage

value: 82.3

unit: %

timestamp: 2026-08-09T18:45:00Z

quality: GOOD
```

---

# Catálogo Canónico de Métricas

La primera versión de la Node Contract Specification define un conjunto inicial de métricas canónicas.

## Recursos del Sistema

* cpu_usage
* cpu_temperature
* memory_usage
* disk_usage
* disk_io
* network_rx
* network_tx
* uptime

---

## Streaming

* active_streams
* active_publishers
* active_readers
* bitrate_in
* bitrate_out
* dropped_packets
* packet_loss
* latency

---

## Transcoding

* gpu_usage
* gpu_memory
* active_jobs
* encoding_fps
* decoding_fps

---

## Identity

* authentication_rate
* authorization_rate
* active_sessions
* active_tokens

---

## Storage

* storage_used
* storage_available
* object_count
* io_latency

---

# Relación con NodeCapacity

NodeCapacity responde:

> ¿Cuál es el límite del recurso?

NodeMetric responde:

> ¿Cuál es la utilización observada?

Ejemplo:

```text
Capacidad

Streaming Channels

Maximum: 16
```

```text
Métrica

active_streams

12
```

La utilización no modifica la capacidad instalada.

---

# Relación con NodeHealth

NodeHealth puede calcularse utilizando múltiples MetricSample.

Ejemplo:

```text
cpu_usage

96%
```

```text
temperature

91°C
```

```text
packet_loss

8%
```

Estas métricas pueden conducir a una evaluación de salud **CRITICAL**.

La especificación no impone el algoritmo de evaluación.

---

# Relación con NodeAlarm

Las métricas constituyen una de las principales fuentes para la generación de alarmas.

Ejemplo:

```text
cpu_usage > 95%
```

↓

```text
Alarm

CPU_HIGH
```

El umbral utilizado dependerá de la política operacional.

---

# Actualización

Las métricas pueden publicarse periódicamente.

La frecuencia dependerá del tipo de Node.

Ejemplos:

* cada segundo;
* cada cinco segundos;
* cada minuto;
* bajo demanda.

La Node Contract Specification no impone un intervalo fijo.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* publicar las métricas mediante MetricSample;
* utilizar nombres canónicos;
* incluir timestamp en cada muestra;
* publicar únicamente valores válidos.

---

**NO DEBE**

* utilizar NodeMetric para representar estado;
* utilizar NodeMetric para representar capacidad;
* modificar el significado de una métrica canónica;
* mezclar múltiples métricas dentro de un mismo MetricSample.

---

**PUEDE**

* publicar nuevas métricas compatibles;
* omitir métricas no aplicables;
* utilizar diferentes frecuencias de actualización.

---

# Ejemplo Conceptual

```text
NodeMetric

├── cpu_usage
├── memory_usage
├── network_rx
├── network_tx
├── active_streams
├── bitrate_out
└── temperature
```

Cada MetricSample representa una medición independiente.

---

# Relación con el NOC

El Network Operations Center utilizará NodeMetric para:

* visualización en tiempo real;
* análisis histórico;
* generación de alarmas;
* cálculo de salud;
* automatización;
* planificación de capacidad;
* análisis predictivo.

NodeMetric constituye la principal fuente de información objetiva del sistema.

---

# Consideraciones de Evolución

La estructura de NodeMetric permanecerá estable.

La incorporación de nuevas métricas requerirá únicamente ampliar el catálogo canónico.

No será necesario modificar la estructura del contrato.

---

# Conclusión

NodeMetric representa las mediciones operacionales de una NodeInstance mediante una colección de **MetricSample**.

Este modelo permite describir de forma uniforme cualquier tipo de observación, independientemente del NodeType o de la tecnología utilizada.

La separación entre métricas, capacidad, estado, salud y disponibilidad convierte a NodeMetric en el fundamento del modelo de observabilidad de la plataforma Broadcast.

