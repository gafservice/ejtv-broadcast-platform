# 4. Contract Principles

## Introducción

La **Node Contract Specification (NCS)** establece un conjunto de principios fundamentales que regulan el comportamiento de todos los nodos compatibles con la plataforma Broadcast.

Estos principios garantizan la interoperabilidad entre componentes, reducen el acoplamiento entre servicios y permiten que la plataforma evolucione de forma consistente a lo largo del tiempo.

Toda implementación compatible DEBE cumplir las reglas definidas en este documento.

---

# Principio 1 — Identidad Única

Todo Node DEBE poseer una identidad única dentro del ecosistema de la plataforma.

La identidad del nodo constituye el mecanismo oficial utilizado para:

* registrar nodos;
* identificar instancias;
* correlacionar eventos;
* administrar alarmas;
* consolidar métricas;
* generar snapshots.

La identidad lógica de un Node NO DEBE cambiar durante su ciclo de vida.

---

# Principio 2 — Responsabilidad Única

Todo Node DEBE tener una responsabilidad funcional claramente definida.

Un Node NO DEBE asumir responsabilidades pertenecientes a otros nodos.

Ejemplos:

* Identity administra identidad.
* Streaming administra distribución multimedia.
* Alarm administra alarmas.
* Metrics administra métricas.

Esta separación favorece una arquitectura altamente cohesiva.

---

# Principio 3 — Autonomía

Cada Node DEBE administrar de manera independiente:

* su configuración;
* sus recursos;
* sus procesos;
* su estado operacional;
* sus métricas;
* sus eventos;
* sus alarmas.

El funcionamiento interno del nodo no forma parte del contrato.

---

# Principio 4 — Contrato Común

Todo Node DEBE publicar su información utilizando exclusivamente la Node Contract Specification.

El NOC NO DEBE depender de estructuras específicas de un nodo particular.

Toda interoperabilidad se fundamenta en el cumplimiento del contrato común.

---

# Principio 5 — Desacoplamiento

Los Nodes NO DEBEN depender del conocimiento interno de otros nodos.

Un Node:

* NO DEBE acceder directamente al estado interno de otro nodo;
* NO DEBE asumir tecnologías utilizadas por otros componentes;
* NO DEBE requerir implementaciones específicas del NOC.

Toda interacción operacional deberá realizarse mediante interfaces definidas por la arquitectura.

---

# Principio 6 — Publicación de Estado

Todo Node DEBE ser capaz de describir su estado operacional.

La información publicada DEBE representar fielmente la condición actual del nodo.

El Node NO DEBE publicar información falsa, incompleta o inconsistente.

La calidad del NOC depende directamente de la calidad de la información publicada por los nodos.

---

# Principio 7 — Observabilidad

La observabilidad constituye una responsabilidad del Node.

Cada implementación DEBE proporcionar información suficiente para que el NOC pueda determinar:

* disponibilidad;
* estado operativo;
* salud;
* utilización;
* capacidad;
* eventos relevantes;
* alarmas activas.

La observabilidad forma parte del diseño del nodo y no constituye una funcionalidad adicional.

---

# Principio 8 — Independencia Tecnológica

La Node Contract Specification NO impone restricciones sobre:

* lenguaje de programación;
* sistema operativo;
* infraestructura;
* framework;
* motor de persistencia;
* plataforma de despliegue.

El único requisito obligatorio consiste en implementar correctamente el contrato.

---

# Principio 9 — Compatibilidad

Toda implementación DEBE respetar la versión vigente de la Node Contract Specification.

Las extensiones propietarias NO DEBEN comprometer la interoperabilidad entre nodos.

Las modificaciones incompatibles deberán introducirse mediante una nueva versión formal del contrato.

---

# Principio 10 — Escalabilidad

La incorporación de nuevos nodos NO DEBE requerir modificaciones en el NOC Core.

El sistema deberá permitir:

* múltiples tipos de nodos;
* múltiples instancias del mismo tipo;
* incorporación dinámica de nuevos componentes;
* crecimiento horizontal de la infraestructura.

La arquitectura ha sido diseñada para evolucionar mediante la incorporación de nodos, no mediante modificaciones del núcleo del sistema.

---

# Principio 11 — Neutralidad del Transporte

La Node Contract Specification define el contenido del contrato, no el mecanismo utilizado para transportarlo.

El contrato podrá transmitirse mediante:

* REST;
* WebSocket;
* gRPC;
* MQTT;
* AMQP;
* Kafka;
* Redis Streams;
* archivos JSON;
* cualquier mecanismo equivalente.

El cambio del protocolo de transporte NO DEBE modificar la estructura lógica del contrato.

---

# Principio 12 — Evolución Controlada

Toda evolución de la Node Contract Specification DEBE preservar la estabilidad del ecosistema.

Las nuevas capacidades deberán incorporarse mediante mecanismos de versionado y compatibilidad definidos por esta especificación.

El crecimiento de la plataforma NO DEBE producir fragmentación del contrato.

---

# Resumen de Principios

Todo Node compatible con la plataforma:

* posee una identidad única;
* cumple una única responsabilidad funcional;
* administra su propio estado;
* publica información mediante la NCS;
* mantiene autonomía operacional;
* respeta el contrato común;
* preserva la compatibilidad entre versiones;
* favorece el desacoplamiento;
* garantiza la observabilidad;
* puede evolucionar independientemente del resto del sistema.

---

# Conclusión

Los principios definidos en este documento constituyen el fundamento normativo de la **Node Contract Specification**.

Toda implementación compatible con la plataforma Broadcast deberá respetar estas reglas para garantizar una arquitectura distribuida, interoperable y sostenible.

El cumplimiento de estos principios asegura que la evolución futura de la plataforma pueda realizarse mediante la incorporación de nuevos nodos, sin comprometer la estabilidad del **Network Operations Center** ni de la **Node-Oriented Architecture**.

