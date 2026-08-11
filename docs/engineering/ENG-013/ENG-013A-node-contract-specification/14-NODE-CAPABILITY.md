# 14. NodeCapability

## Introducción

El **NodeCapability** describe las funcionalidades que una **NodeInstance** es capaz de ofrecer dentro de la plataforma Broadcast.

Representa el conjunto de servicios, protocolos, características o recursos funcionales disponibles en una instancia determinada.

Las capacidades describen **qué puede hacer** una NodeInstance, independientemente de cuánto pueda hacer o de si actualmente está disponible para recibir nuevas tareas.

---

# Propósito

El propósito del NodeCapability es proporcionar una descripción uniforme de las funcionalidades soportadas por una NodeInstance.

Esta información permite al **Network Operations Center (NOC)**:

* identificar capacidades disponibles;
* construir inventarios funcionales;
* localizar servicios específicos;
* facilitar la planificación;
* apoyar la orquestación automática.

---

# Responsabilidad

NodeCapability posee una única responsabilidad:

> Describir las capacidades funcionales disponibles en una NodeInstance.

No representa:

* rendimiento;
* utilización;
* disponibilidad;
* capacidad instalada;
* estado operacional.

Estas dimensiones pertenecen a otras entidades del modelo.

---

# Naturaleza

Una capacidad representa una característica funcional.

Una capacidad:

* puede estar presente;
* puede estar ausente;
* puede cambiar entre distintas instancias del mismo Node.

Las capacidades describen funcionalidades, no rendimiento.

---

# Clasificación

Las capacidades pueden agruparse en diferentes categorías.

## Protocolos

Ejemplos:

* SRT
* RTMP
* RTSP
* HLS
* WebRTC
* MPEG-TS
* UDP

---

## Seguridad

Ejemplos:

* JWT
* OAuth2
* RBAC
* TLS
* mTLS

---

## Procesamiento

Ejemplos:

* GPU
* CPU Acceleration
* Hardware Encoding
* Hardware Decoding
* AI Inference

---

## Almacenamiento

Ejemplos:

* Local Storage
* NAS
* Object Storage
* Archive

---

## Monitoreo

Ejemplos:

* Metrics Export
* Health Checks
* Prometheus
* REST API
* SNMP

---

## Automatización

Ejemplos:

* Scheduler
* Workflow Engine
* Auto Recovery
* Auto Scaling

---

# Modelo Conceptual

Cada capacidad representa una característica independiente.

Ejemplo:

```text id="f0mbxh"
Streaming Node

Capabilities

✓ SRT
✓ RTMP
✓ HLS
✓ WebRTC
✓ REST API
✓ Metrics
```

Otra instancia del mismo Node puede publicar un conjunto diferente.

---

# Representación

Cada capacidad DEBE identificarse mediante un nombre canónico.

Ejemplo conceptual:

```text id="rrzrv7"
name

SRT
```

```text id="bzjlwm"
category

Protocol
```

```text id="0x6eaj"
enabled

true
```

```text id="z66vtg"
version

1.0
```

La especificación no impone un formato concreto de serialización.

---

# Relación con NodeType

El NodeType describe:

> ¿Qué función cumple el Node?

NodeCapability describe:

> ¿Qué funcionalidades ofrece esta instancia?

Ejemplo:

```text id="t5z31w"
NodeType

STREAMING
```

Capacidades:

```text id="srsm1u"
SRT

RTMP

HLS

WebRTC

REST API
```

Dos instancias del mismo NodeType pueden anunciar capacidades distintas.

---

# Relación con NodeCapacity

NodeCapability responde:

> ¿Qué puede hacer?

NodeCapacity responde:

> ¿Cuánto puede hacer?

Ejemplo:

```text id="ukquzt"
Capability

GPU Encoding
```

```text id="h9kglq"
Capacity

4 canales simultáneos
```

Ambos conceptos son independientes.

---

# Relación con NodeAvailability

Una NodeInstance puede poseer una capacidad determinada y, aun así, encontrarse temporalmente indisponible.

Ejemplo:

```text id="rua3uv"
Capability

WebRTC
```

```text id="tb06bd"
Availability

UNAVAILABLE
```

La capacidad existe.

Simplemente no puede utilizarse en ese momento.

---

# Evolución

Las capacidades pueden cambiar durante la vida de una NodeInstance.

Ejemplos:

* carga dinámica de módulos;
* activación de licencias;
* conexión de hardware;
* actualización del software.

Cuando esto ocurra, la instancia deberá publicar la nueva información.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* publicar las capacidades soportadas por la NodeInstance;
* utilizar nombres canónicos;
* mantener coherencia entre capacidades y NodeType.

---

**NO DEBE**

* utilizar NodeCapability para representar capacidad instalada;
* utilizar NodeCapability para representar disponibilidad;
* utilizar nombres ambiguos para las capacidades.

---

**PUEDE**

* incorporar capacidades adicionales;
* publicar capacidades opcionales;
* actualizar dinámicamente la lista de capacidades.

---

# Ejemplo Conceptual

```text id="mghrtx"
NodeInstance

Capabilities

• SRT
• RTMP
• HLS
• WebRTC
• REST API
• Prometheus
• GPU Encoding
```

Esta lista describe las funcionalidades disponibles.

No indica cuántas sesiones soporta la instancia ni si actualmente acepta nuevas conexiones.

---

# Relación con el NOC

El Network Operations Center utilizará las capacidades para:

* localizar servicios;
* construir inventarios funcionales;
* filtrar Nodes compatibles;
* asistir a sistemas automáticos de despliegue;
* facilitar diagnósticos.

La utilización concreta de cada capacidad dependerá de la política operacional del NOC.

---

# Consideraciones de Evolución

El catálogo de capacidades evolucionará con la plataforma.

Las nuevas capacidades deberán:

* mantener compatibilidad con versiones anteriores;
* utilizar nombres consistentes;
* preservar el significado de las capacidades existentes.

---

# Conclusión

NodeCapability representa el conjunto de funcionalidades disponibles en una NodeInstance.

Su función consiste en describir qué puede hacer la instancia, manteniendo una separación estricta respecto a su capacidad instalada, su estado operacional y su disponibilidad.

Esta entidad constituye el fundamento para la construcción de inventarios funcionales y para la futura automatización inteligente del Network Operations Center.
