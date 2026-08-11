# 22. Time Model

## Introducción

El **Time Model** define las reglas temporales utilizadas por la **Node Contract Specification (NCS)** para representar, ordenar y correlacionar la información publicada por una **NodeInstance**.

El tiempo constituye un elemento fundamental para la observabilidad, la trazabilidad y la coordinación entre componentes distribuidos.

La Node Contract Specification establece un modelo temporal uniforme para garantizar la interoperabilidad entre todas las implementaciones.

---

# Propósito

El propósito del Time Model es proporcionar un marco común para representar el tiempo dentro de la plataforma.

Este modelo permite:

* ordenar eventos;
* correlacionar información;
* sincronizar Nodes;
* reconstruir secuencias operacionales;
* facilitar el análisis histórico.

---

# Responsabilidad

El Time Model posee una única responsabilidad:

> Definir cómo se representa y utiliza el tiempo dentro de la Node Contract Specification.

No define:

* mecanismos de sincronización;
* políticas NTP;
* configuraciones del sistema operativo.

Estas decisiones pertenecen a la implementación.

---

# Principios Fundamentales

Toda implementación compatible deberá seguir los siguientes principios.

## Tiempo Universal

Todo instante deberá representarse utilizando **UTC**.

No deberán utilizarse zonas horarias locales dentro del contrato.

---

## Formato

Toda representación temporal deberá utilizar el formato **ISO 8601** compatible con **RFC 3339**.

Ejemplo:

```text
2026-08-09T21:45:31.483Z
```

---

## Precisión

La precisión mínima recomendada es de milisegundos.

Las implementaciones podrán utilizar una precisión superior cuando resulte necesario.

---

## Inmutabilidad

Todo instante temporal representa un hecho ocurrido.

Una vez publicado, no debe modificarse.

---

# Instantes Temporales

Un instante representa un momento específico.

Ejemplos:

* observed_at;
* occurred_at;
* raised_at;
* captured_at;
* sent_at.

Cada entidad utiliza el instante que mejor describe su naturaleza.

---

# Duraciones

El contrato permite representar intervalos de tiempo.

Ejemplos:

* uptime;
* duración de sesión;
* duración de mantenimiento;
* tiempo de procesamiento.

La unidad recomendada es el segundo o sus subdivisiones.

---

# Intervalos

Un intervalo representa un período comprendido entre dos instantes.

Ejemplo:

```text
started_at

↓

finished_at
```

Los intervalos pueden utilizarse para auditoría, análisis y planificación.

---

# Orden Temporal

Toda implementación debe preservar el orden lógico de los hechos.

Cuando existan diferencias entre el momento de ocurrencia y el momento de procesamiento, ambos instantes deberán distinguirse claramente.

---

# Sincronización

La Node Contract Specification asume que los Nodes mantienen una referencia temporal razonablemente sincronizada.

La especificación no impone un mecanismo específico de sincronización.

Las implementaciones podrán utilizar:

* NTP;
* PTP;
* GNSS;
* otros mecanismos equivalentes.

---

# Relación con las Entidades

Las entidades de la NCS utilizan el tiempo de forma específica.

## MetricSample

observed_at

---

## EventRecord

occurred_at

---

## AlarmRecord

raised_at

---

## HeartbeatRecord

sent_at

---

## NodeSnapshot

captured_at

Cada nombre refleja el significado temporal de la información publicada.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* utilizar UTC;
* representar los instantes mediante ISO 8601 / RFC 3339;
* mantener coherencia temporal;
* preservar el orden lógico de los hechos.

---

**NO DEBE**

* utilizar formatos ambiguos;
* depender de zonas horarias locales;
* modificar instantes ya publicados.

---

**PUEDE**

* utilizar mayor precisión temporal;
* conservar información adicional de sincronización;
* incorporar mecanismos avanzados de correlación temporal.

---

# Relación con el NOC

El Network Operations Center utilizará el Time Model para:

* ordenar información;
* correlacionar eventos;
* reconstruir incidentes;
* generar líneas de tiempo;
* calcular métricas de disponibilidad y rendimiento.

La consistencia temporal constituye un requisito fundamental para la operación distribuida.

---

# Consideraciones de Evolución

Las futuras versiones de la Node Contract Specification podrán incorporar nuevos conceptos temporales sin modificar los principios fundamentales definidos en este documento.

Esto garantiza la compatibilidad entre implementaciones y facilita la evolución del contrato.

---

# Conclusión

El Time Model establece un marco uniforme para representar el tiempo dentro de la Node Contract Specification.

La adopción de un modelo temporal consistente garantiza la interoperabilidad entre Nodes, facilita la trazabilidad operacional y proporciona la base necesaria para la observabilidad, la automatización y la coordinación de sistemas distribuidos.
