# 19. NodeHeartbeat

## Introducción

El **NodeHeartbeat** representa el mecanismo mediante el cual una **NodeInstance** confirma periódicamente su presencia operacional ante el **Network Operations Center (NOC)**.

Su propósito no consiste en describir el estado interno de la instancia, sino en demostrar que continúa activa, accesible y participando en la **Node Contract Specification (NCS)**.

A diferencia de una métrica, un evento o una alarma, el Heartbeat constituye una señal periódica de existencia.

La NCS modela esta información mediante un registro denominado **HeartbeatRecord**.

---

# Propósito

El propósito del NodeHeartbeat es proporcionar un mecanismo uniforme para verificar la presencia continua de una NodeInstance.

El Heartbeat permite al NOC:

* detectar pérdida de comunicación;
* confirmar la existencia de una instancia;
* medir continuidad operacional;
* supervisar la conectividad entre Nodes y el NOC;
* iniciar procesos automáticos de recuperación.

---

# Responsabilidad

NodeHeartbeat posee una única responsabilidad:

> Confirmar periódicamente la presencia operacional de una NodeInstance.

No representa:

* estado operacional;
* salud;
* disponibilidad;
* métricas;
* eventos;
* alarmas.

Estas responsabilidades pertenecen a otras entidades del modelo.

---

# Modelo del Dominio

NodeHeartbeat representa el último latido conocido de una NodeInstance.

```text
NodeHeartbeat
│
└── HeartbeatRecord
```

Cada HeartbeatRecord reemplaza al anterior.

El historial de Heartbeats no forma parte del contrato; si una implementación desea conservarlo, deberá hacerlo como una decisión propia del NOC.

---

# HeartbeatRecord

Un **HeartbeatRecord** representa la confirmación periódica de presencia emitida por una NodeInstance.

Cada HeartbeatRecord constituye una fotografía mínima del estado de conectividad de la instancia.

---

# Atributos de HeartbeatRecord

Todo HeartbeatRecord posee los siguientes atributos.

## heartbeat_id

Identificador único del Heartbeat.

Ejemplo:

```text
hb-8baf20d1
```

---

## instance_id

Identificador de la NodeInstance que genera el Heartbeat.

---

## sequence

Número secuencial del Heartbeat.

Permite detectar:

* pérdidas;
* duplicados;
* desorden en la recepción.

Ejemplo:

```text
15432
```

---

## timestamp

Momento exacto en que fue emitido el Heartbeat.

---

## contract_version

Versión de la Node Contract Specification utilizada por la instancia.

Ejemplo:

```text
1.0
```

---

## uptime

Tiempo continuo de ejecución de la NodeInstance.

Permite identificar reinicios sin necesidad de eventos adicionales.

---

## checksum (Opcional)

Huella de integridad del contenido del Heartbeat.

Puede utilizarse para verificar la integridad de la comunicación cuando la implementación lo requiera.

---

# Frecuencia

La Node Contract Specification no impone una frecuencia específica de Heartbeat.

Cada implementación podrá definir el intervalo más adecuado según sus necesidades operacionales.

Ejemplos:

* 1 segundo;
* 5 segundos;
* 10 segundos;
* 30 segundos.

El intervalo deberá mantenerse suficientemente corto para detectar fallos de manera oportuna y suficientemente largo para evitar tráfico innecesario.

---

# Supervisión

El NOC supervisará la recepción continua de Heartbeats.

Una ausencia de Heartbeats no implica automáticamente una falla de la NodeInstance.

Puede deberse a:

* pérdida de conectividad;
* congestión de red;
* mantenimiento;
* reinicio;
* fallo del NOC.

La interpretación corresponde al NOC Core.

---

# Relación con NodeStatus

NodeStatus responde:

> ¿Qué está haciendo la instancia?

NodeHeartbeat responde:

> ¿Sigue presente?

Ambos conceptos son completamente independientes.

Una instancia puede mantener un estado **RUNNING** registrado, pero dejar de enviar Heartbeats.

En ese caso el NOC detectará la pérdida de presencia sin modificar directamente el significado de NodeStatus.

---

# Relación con NodeHealth

NodeHealth representa una evaluación operacional.

NodeHeartbeat únicamente confirma presencia.

La existencia de Heartbeats no implica necesariamente una condición saludable.

Una NodeInstance puede continuar enviando Heartbeats mientras presenta un estado **CRITICAL**.

---

# Relación con NodeAlarm

La pérdida de Heartbeats puede originar una alarma.

Ejemplo:

```text
Heartbeat perdido
```

↓

```text
Tiempo máximo excedido
```

↓

```text
Alarm

NODE_UNREACHABLE
```

El Heartbeat no constituye una alarma.

Es únicamente la evidencia utilizada para detectar la pérdida de presencia.

---

# Persistencia

El contrato únicamente requiere mantener el último Heartbeat recibido.

Las implementaciones podrán conservar el historial completo con fines estadísticos o de auditoría.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* publicar Heartbeats periódicamente;
* asignar un identificador único a cada Heartbeat;
* incluir timestamp;
* mantener la secuencia de emisión;
* indicar la versión del contrato utilizada.

---

**NO DEBE**

* utilizar Heartbeat para publicar métricas;
* utilizar Heartbeat para representar estado;
* utilizar Heartbeat para representar salud;
* generar eventos periódicos equivalentes al Heartbeat.

---

**PUEDE**

* ajustar la frecuencia de publicación;
* incluir mecanismos de verificación de integridad;
* añadir atributos compatibles con futuras versiones de la especificación.

---

# Ejemplo Conceptual

```text
HeartbeatRecord

heartbeat_id: hb-8baf20d1

instance_id: streaming-primary

sequence: 15432

timestamp: 2026-08-09T20:15:00Z

contract_version: 1.0

uptime: 03:41:28
```

---

# Relación con el NOC

El Network Operations Center utilizará NodeHeartbeat para:

* confirmar presencia;
* detectar silencios operacionales;
* medir continuidad;
* iniciar procesos automáticos de recuperación;
* alimentar mecanismos de alta disponibilidad.

NodeHeartbeat constituye la evidencia primaria de que una NodeInstance continúa participando activamente en la plataforma.

---

# Consideraciones de Evolución

La estructura de NodeHeartbeat permanecerá estable.

Las futuras versiones de la Node Contract Specification podrán incorporar nuevos atributos de control, integridad o sincronización sin modificar el propósito fundamental del Heartbeat.

---

# Conclusión

NodeHeartbeat representa el mecanismo oficial mediante el cual una NodeInstance confirma periódicamente su presencia operacional.

Su función consiste exclusivamente en demostrar que la instancia continúa participando en la Node Contract Specification.

La separación entre métricas, eventos, alarmas y Heartbeats permite construir un modelo de observabilidad robusto, donde la presencia, el comportamiento y las condiciones operacionales permanecen claramente diferenciados.

NodeHeartbeat constituye el fundamento para la detección de pérdida de conectividad, la supervisión distribuida y la construcción de sistemas de alta disponibilidad sobre la plataforma Broadcast.
