# 23. Serialization

## Introducción

La **Serialización** define las reglas mediante las cuales las entidades de la **Node Contract Specification (NCS)** son representadas para su intercambio entre procesos, servicios y sistemas distribuidos.

La serialización constituye una representación del modelo de dominio.

No forma parte del modelo de dominio en sí mismo.

La estructura semántica de la NCS permanece independiente del mecanismo utilizado para representar la información.

---

# Propósito

El propósito de la Serialización es garantizar que cualquier implementación compatible pueda intercambiar información preservando íntegramente el significado definido por la Node Contract Specification.

La serialización permite:

* intercambio de información;
* interoperabilidad;
* persistencia;
* replicación;
* integración con sistemas externos.

---

# Responsabilidad

La Serialización posee una única responsabilidad:

> Representar las entidades de la Node Contract Specification para su transmisión o almacenamiento.

No define:

* protocolos de transporte;
* mecanismos de comunicación;
* políticas de seguridad;
* estrategias de almacenamiento.

Estas responsabilidades pertenecen a otros componentes de la arquitectura.

---

# Principios Fundamentales

Toda representación serializada debe cumplir los siguientes principios.

## Independencia

La serialización no modifica el modelo de dominio.

Las entidades mantienen exactamente el mismo significado independientemente del formato utilizado.

---

## Determinismo

La misma información debe producir una representación equivalente cuando se serializa utilizando el mismo formato y las mismas reglas.

---

## Integridad

La serialización debe preservar todos los datos definidos por la especificación.

No deberán perderse atributos durante el proceso de serialización o deserialización.

---

## Autocontención

Toda representación deberá contener la información necesaria para ser interpretada correctamente por una implementación compatible.

---

## Neutralidad Tecnológica

La Node Contract Specification no depende de un formato específico de serialización.

---

# Formatos Compatibles

La especificación no impone un formato único.

Ejemplos de formatos compatibles incluyen:

* JSON;
* CBOR;
* MessagePack;
* Protocol Buffers;
* Avro;
* FlatBuffers.

La elección corresponde a la implementación.

---

# Tipos de Datos

Las implementaciones deberán preservar el significado de los tipos definidos por la especificación.

Ejemplos:

* entero;
* número decimal;
* cadena de texto;
* booleano;
* fecha y hora;
* colección;
* objeto compuesto.

El tipo lógico tiene prioridad sobre la representación física.

---

# Nombres Canónicos

Los nombres definidos por la Node Contract Specification constituyen parte del contrato.

Las implementaciones no deberán modificar dichos nombres durante la serialización.

Ejemplo:

```text
cpu_usage
```

Debe conservar exactamente ese nombre.

---

# Objetos Compuestos

Las entidades compuestas deberán preservar su estructura interna.

Ejemplo:

```text
NodeSnapshot
│
├── NodeStatus
├── NodeHealth
├── NodeAvailability
├── NodeMetric
└── NodeAlarm
```

La representación podrá variar.

La estructura conceptual deberá permanecer inalterada.

---

# Extensibilidad

La serialización deberá permitir la incorporación de nuevos atributos compatibles con versiones futuras.

Las implementaciones deberán ignorar atributos desconocidos cuando ello no comprometa la interpretación del contrato.

---

# Compatibilidad

La serialización deberá facilitar la interoperabilidad entre diferentes versiones de la Node Contract Specification.

Los mecanismos específicos de compatibilidad se definen en el documento **Versioning**.

---

# Relación con el Transporte

La serialización es independiente del mecanismo de transporte.

Ejemplos válidos:

```text
NodeSnapshot
    ↓
JSON
    ↓
HTTP
```

```text
NodeSnapshot
    ↓
CBOR
    ↓
MQTT
```

```text
NodeSnapshot
    ↓
Protocol Buffers
    ↓
gRPC
```

El protocolo de transporte no modifica el significado del contenido serializado.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* preservar el significado del modelo de dominio;
* utilizar los nombres canónicos definidos por la especificación;
* mantener la integridad de la información durante la serialización y deserialización;
* conservar los tipos lógicos definidos por la NCS.

---

**NO DEBE**

* alterar la semántica de los datos;
* modificar nombres canónicos;
* eliminar atributos obligatorios;
* depender de un formato de serialización específico.

---

**PUEDE**

* utilizar cualquier formato compatible;
* incorporar atributos adicionales compatibles con la especificación;
* optimizar la representación física siempre que preserve el contrato lógico.

---

# Relación con el NOC

El Network Operations Center intercambiará información serializada con las NodeInstance utilizando el formato y el protocolo definidos por cada implementación.

El NOC interpretará dicha información conforme al modelo de dominio de la Node Contract Specification, independientemente de su representación física.

---

# Consideraciones de Evolución

La incorporación de nuevos formatos de serialización no requerirá modificaciones en el modelo de dominio.

La Node Contract Specification permanecerá independiente de la tecnología utilizada para representar sus entidades.

---

# Conclusión

La Serialización define el mecanismo mediante el cual las entidades de la Node Contract Specification pueden representarse para su intercambio y almacenamiento.

La separación entre el modelo de dominio y su representación física garantiza la interoperabilidad, la extensibilidad y la independencia tecnológica de la plataforma Broadcast.

Esta arquitectura permite que la Node Contract Specification evolucione sin quedar ligada a un formato específico de serialización, preservando el contrato lógico como el verdadero núcleo del sistema.
