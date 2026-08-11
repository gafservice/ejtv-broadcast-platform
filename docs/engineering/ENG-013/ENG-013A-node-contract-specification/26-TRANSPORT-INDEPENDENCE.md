# 26. Transport Independence

## Introducción

La **Transport Independence** establece que la **Node Contract Specification (NCS)** es completamente independiente del mecanismo utilizado para intercambiar información entre componentes de la plataforma.

El contrato define **qué información** se intercambia.

El transporte define **cómo** esa información viaja entre dos extremos.

Ambos conceptos son independientes.

Esta separación garantiza que la evolución de los mecanismos de comunicación no afecte al modelo de dominio definido por la NCS.

---

# Propósito

El propósito de la Transport Independence es garantizar que cualquier implementación compatible pueda intercambiar información utilizando distintos mecanismos de comunicación sin modificar el contrato lógico.

Este principio permite:

* independencia tecnológica;
* interoperabilidad;
* evolución de la infraestructura;
* reutilización del modelo de dominio;
* integración con distintos ecosistemas.

---

# Responsabilidad

Transport Independence posee una única responsabilidad:

> Separar el contrato de información de los mecanismos utilizados para transportarlo.

No define:

* protocolos específicos;
* configuraciones de red;
* mecanismos de autenticación;
* políticas de enrutamiento.

Estas responsabilidades pertenecen a la arquitectura de comunicaciones.

---

# Principios Fundamentales

Toda implementación compatible deberá respetar los siguientes principios.

## Separación

El contrato lógico y el transporte constituyen capas independientes.

Una modificación del transporte no deberá modificar el significado del contrato.

---

## Neutralidad

La Node Contract Specification no depende de ningún protocolo de comunicación específico.

---

## Transparencia

El transporte únicamente entrega información.

No modifica su significado.

No interpreta su contenido.

No altera la estructura definida por el contrato.

---

## Reutilización

La misma entidad puede intercambiarse mediante diferentes mecanismos de transporte sin modificar su estructura.

---

# Arquitectura

La Node Contract Specification propone la siguiente separación conceptual.

```text
Modelo del Dominio
        │
        ▼
Serialización
        │
        ▼
Transporte
```

Cada nivel posee responsabilidades independientes.

---

# Ejemplos

La misma entidad puede utilizar diferentes mecanismos de transporte.

Ejemplo:

```text
NodeSnapshot
```

↓

```text
JSON
```

↓

```text
HTTP
```

---

También:

```text
NodeSnapshot
```

↓

```text
CBOR
```

↓

```text
MQTT
```

---

O bien:

```text
NodeSnapshot
```

↓

```text
Protocol Buffers
```

↓

```text
gRPC
```

En todos los casos el contrato permanece exactamente igual.

---

# Protocolos Compatibles

La Node Contract Specification no limita los protocolos de comunicación.

Ejemplos compatibles incluyen:

* HTTP;
* HTTPS;
* WebSocket;
* MQTT;
* AMQP;
* Kafka;
* gRPC;
* ZeroMQ;
* NATS;
* DDS;
* otros mecanismos equivalentes.

La elección dependerá de la arquitectura de la plataforma.

---

# Relación con la Serialización

La serialización representa el modelo de dominio.

El transporte únicamente entrega dicha representación.

Ejemplo:

```text
NodeSnapshot
        │
        ▼
JSON
        │
        ▼
HTTP
```

Modificar el transporte no modifica la serialización.

Modificar la serialización no modifica el modelo del dominio.

---

# Independencia del Transporte

Una NodeInstance puede publicar exactamente la misma información mediante múltiples mecanismos simultáneamente.

Ejemplo:

```text
NodeSnapshot
        │
        ├── HTTP
        ├── MQTT
        ├── WebSocket
        └── Kafka
```

El contenido continúa siendo idéntico.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* preservar el significado del contrato independientemente del transporte utilizado;
* mantener la estructura definida por la Node Contract Specification;
* separar claramente el modelo de dominio del mecanismo de comunicación.

---

**NO DEBE**

* introducir diferencias semánticas dependiendo del protocolo utilizado;
* modificar entidades durante el transporte;
* incorporar lógica de negocio dentro del mecanismo de comunicación.

---

**PUEDE**

* utilizar uno o múltiples protocolos simultáneamente;
* cambiar de protocolo sin modificar el contrato;
* incorporar nuevos mecanismos de transporte compatibles con futuras tecnologías.

---

# Relación con el NOC

El Network Operations Center podrá comunicarse con distintas NodeInstance utilizando diferentes mecanismos de transporte.

Mientras las implementaciones respeten la Node Contract Specification, el NOC interpretará la información de manera uniforme, independientemente del protocolo utilizado.

Esta capacidad facilita la integración de tecnologías heterogéneas dentro de una misma plataforma distribuida.

---

# Consideraciones de Evolución

La incorporación de nuevos protocolos de comunicación no requerirá modificaciones en la Node Contract Specification.

La evolución del transporte constituye una decisión independiente del modelo de dominio y de la serialización.

Esta separación garantiza la estabilidad del contrato frente a la evolución tecnológica de las infraestructuras de comunicación.

---

# Conclusión

La Transport Independence establece uno de los principios fundamentales de la Node Contract Specification: el contrato de información es completamente independiente del mecanismo utilizado para transportarlo.

La separación entre modelo de dominio, serialización y transporte permite construir plataformas distribuidas, interoperables y preparadas para evolucionar con nuevas tecnologías sin comprometer la compatibilidad entre Nodes y el Network Operations Center.

Este principio asegura que la Node Contract Specification permanezca vigente más allá de la vida útil de cualquier protocolo de comunicación específico.
