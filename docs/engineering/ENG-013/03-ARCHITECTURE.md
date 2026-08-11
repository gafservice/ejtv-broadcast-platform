# ENG-013 — Architecture

## Introducción

La arquitectura del **Network Operations Center (NOC)** está basada en un modelo distribuido denominado **Node-Oriented Architecture (NOA)**.

En esta arquitectura, todos los componentes de la plataforma son representados como nodos autónomos capaces de publicar su estado utilizando un contrato de comunicación común.

El NOC no interactúa directamente con las implementaciones internas de cada servicio.

Su única responsabilidad consiste en consumir el contrato publicado por cada nodo, consolidar la información recibida y proporcionar una visión unificada del estado operacional de toda la plataforma.

---

# Principios Arquitectónicos

La arquitectura del NOC se fundamenta en los siguientes principios.

## Arquitectura Orientada a Nodos

Todo componente operativo de la plataforma deberá implementarse como un Node.

Ejemplos:

* Identity Node
* Streaming Node
* Metrics Node
* Alarm Node
* Automation Node
* Database Node
* Transcoding Node
* Scheduler Node
* futuros nodos especializados

Todos poseen exactamente la misma interfaz conceptual hacia el NOC.

---

## Contrato Único

El NOC nunca consume implementaciones particulares.

Todos los nodos publican información utilizando un único contrato denominado **Node Contract**.

Esto garantiza que cualquier nodo pueda incorporarse al sistema sin modificar el núcleo del NOC.

---

## Bajo Acoplamiento

Los nodos desconocen la implementación interna de otros nodos.

El único elemento compartido entre ellos es el contrato de comunicación.

Esta característica permite que cada componente evolucione de manera independiente.

---

## Alta Cohesión

Cada nodo es responsable únicamente de su propia función.

Ejemplos:

* Identity administra identidad.
* Streaming administra distribución multimedia.
* Metrics calcula métricas.
* Alarm administra alarmas.
* Automation ejecuta automatizaciones.

El NOC únicamente observa su estado.

---

# Arquitectura General

```text
                                 +----------------------+
                                 |        NOC Core      |
                                 +----------+-----------+
                                            |
             =====================================================
             |         |          |          |          |         |
             |         |          |          |          |         |
      Identity     Streaming    Metrics    Alarm   Automation  Others
        Node          Node        Node      Node       Node      ...
             |         |          |          |          |
             +---------+----------+----------+----------+
                        Node Contract Specification
```

El NOC Core actúa como consumidor universal del contrato.

No existe lógica específica para cada tipo de nodo.

---

# Componentes de la Arquitectura

La arquitectura se encuentra dividida en cuatro niveles principales.

## Nivel 1 — Nodes

Cada servicio funcional de la plataforma constituye un nodo independiente.

Cada nodo mantiene su propia lógica de negocio y únicamente publica información operacional.

---

## Nivel 2 — Node Contract

Todos los nodos implementan exactamente la misma especificación.

El contrato define:

* identidad;
* estado;
* salud;
* capacidades;
* capacidad;
* métricas;
* eventos;
* alarmas;
* heartbeat;
* snapshots.

---

## Nivel 3 — NOC Core

El núcleo del NOC recibe la información publicada por todos los nodos.

Entre sus responsabilidades se encuentran:

* registrar nodos;
* mantener el inventario;
* consolidar snapshots;
* calcular el estado operativo;
* administrar eventos;
* administrar alarmas;
* exponer información para visualización.

---

## Nivel 4 — Dashboards

Los dashboards consumen exclusivamente la información generada por el NOC Core.

Nunca consultan directamente a los nodos.

Esta decisión garantiza una única fuente oficial de información operacional.

---

# Flujo de Información

La arquitectura sigue un flujo unidireccional de información.

```text
Node
   │
   ▼
Node Contract
   │
   ▼
NOC Core
   │
   ▼
Dashboards
   │
   ▼
Operadores
```

Los operadores nunca interactúan directamente con los nodos.

Toda la información operacional proviene del NOC Core.

---

# Independencia Tecnológica

El Node Contract constituye la única dependencia compartida por todos los componentes.

Como consecuencia:

* cada nodo puede utilizar un lenguaje de programación diferente;
* cada nodo puede ejecutarse sobre distintos sistemas operativos;
* cada nodo puede desplegarse localmente o en la nube;
* el protocolo de transporte puede variar sin afectar la arquitectura.

La interoperabilidad depende únicamente del cumplimiento del contrato.

---

# Escalabilidad

La incorporación de un nuevo nodo requiere únicamente implementar el Node Contract.

El NOC Core no necesita ser modificado.

Este principio permite que la plataforma evolucione sin incrementar el acoplamiento entre sus componentes.

---

# Extensibilidad

La arquitectura permite incorporar nuevos tipos de nodos sin alterar el funcionamiento del sistema.

Ejemplos futuros:

* AI Node
* Vision Node
* Edge Node
* Cloud Node
* Archive Node
* Analytics Node
* Billing Node

Todos podrán integrarse mediante el mismo contrato de comunicación.

---

# Fuente Única de Verdad

El NOC Core constituye la fuente oficial del estado operacional de la plataforma.

Toda visualización, reporte, alarma o panel deberá obtener su información desde el NOC Core.

Los dashboards no deberán consultar directamente a los nodos individuales.

Esta decisión garantiza consistencia, trazabilidad y una única interpretación del estado de la infraestructura.

---

# Beneficios de la Arquitectura

La adopción de una arquitectura orientada a nodos proporciona las siguientes ventajas:

* bajo acoplamiento entre servicios;
* alta cohesión funcional;
* escalabilidad horizontal;
* facilidad para incorporar nuevos nodos;
* independencia tecnológica;
* simplificación del monitoreo;
* evolución controlada mediante contratos;
* mayor mantenibilidad del sistema;
* crecimiento sostenible de la plataforma.

---

# Conclusión

La **Node-Oriented Architecture (NOA)** establece un modelo uniforme para todos los componentes de la plataforma Broadcast.

Cada nodo conserva su autonomía funcional, mientras que el NOC proporciona una visión operacional unificada basada exclusivamente en un contrato común.

Esta separación de responsabilidades convierte al NOC en una infraestructura estable, extensible y preparada para acompañar la evolución de la plataforma durante los próximos años.
