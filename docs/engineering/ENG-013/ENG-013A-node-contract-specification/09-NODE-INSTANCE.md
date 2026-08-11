# 9. NodeInstance

## Introducción

Una **NodeInstance** representa una ejecución concreta de un **Node** dentro de la plataforma Broadcast.

Mientras el Node constituye una entidad lógica permanente, la NodeInstance representa una manifestación operacional de dicho Node en un entorno de ejecución específico.

Esta separación permite que un mismo Node pueda ejecutarse simultáneamente en múltiples ubicaciones físicas o virtuales sin perder su identidad lógica.

---

# Propósito

El propósito de una NodeInstance es representar el estado operacional de una ejecución específica del Node.

La NodeInstance constituye la unidad mínima de observación del Network Operations Center (NOC).

Toda la información dinámica de la plataforma se encuentra asociada a una NodeInstance.

---

# Definición

Una NodeInstance representa una ejecución viva de un Node.

Una instancia puede ejecutarse como:

* proceso del sistema operativo;
* servicio;
* contenedor;
* máquina virtual;
* dispositivo físico;
* función distribuida;
* servicio en la nube.

La arquitectura no impone restricciones sobre el mecanismo de ejecución.

---

# Relación con Node

Todo Node puede poseer cero o más NodeInstances.

```text
Node
│
├── NodeId
├── NodeType
└── NodeInstances
```

Las instancias pertenecen exclusivamente a un único Node.

Una NodeInstance NO PUEDE pertenecer simultáneamente a varios Nodes.

---

# Identidad de la Instancia

Toda NodeInstance DEBE poseer un identificador propio.

Se define el concepto de:

```text
NodeInstanceId
```

Este identificador:

* identifica la ejecución concreta;
* es único dentro del Node;
* permite distinguir múltiples instancias simultáneas.

Ejemplo:

```text
Streaming Node

Instance:
streaming-primary

Instance:
streaming-backup

Instance:
streaming-edge-panama
```

Las tres instancias comparten el mismo NodeId, pero poseen distintos NodeInstanceId.

---

# Ciclo de Vida

Una NodeInstance posee un ciclo de vida independiente del Node.

```text
Creación
      │
      ▼
Inicialización
      │
      ▼
Registro
      │
      ▼
Operación
      │
      ▼
Heartbeat
      │
      ▼
Finalización
```

Una instancia puede desaparecer sin que desaparezca el Node lógico.

---

# Estado Operacional

Toda información dinámica pertenece a la NodeInstance.

Incluye:

* estado;
* salud;
* información de ejecución;
* métricas;
* eventos;
* alarmas;
* heartbeat;
* snapshots.

El Node únicamente mantiene la identidad lógica.

---

# Componentes de una NodeInstance

Conceptualmente, una NodeInstance está compuesta por:

```text
NodeInstance
│
├── NodeInstanceId
├── NodeInfo
├── NodeStatus
├── NodeHealth
├── NodeCapability
├── NodeCapacity
├── NodeMetric
├── NodeEvent
├── NodeAlarm
├── NodeHeartbeat
└── NodeSnapshot
```

Estos componentes describen completamente el estado operacional de una instancia.

---

# NodeInfo

Describe el entorno donde se ejecuta la instancia.

Ejemplos:

* hostname;
* sistema operativo;
* arquitectura;
* dirección IP;
* versión del runtime;
* contenedor;
* proceso.

Toda esta información puede cambiar sin modificar el Node.

---

# NodeStatus

Describe el estado operacional actual de la instancia.

Ejemplos:

* STARTING;
* RUNNING;
* STOPPING;
* FAILED;
* MAINTENANCE.

---

# NodeHealth

Resume la condición general de la instancia.

Representa una evaluación operacional construida a partir de múltiples indicadores.

---

# NodeCapability

Describe las funcionalidades disponibles en la instancia.

Ejemplos:

* GPU;
* SRT;
* RTMP;
* HLS;
* WebRTC.

Las capacidades pueden variar entre distintas instancias del mismo Node.

---

# NodeCapacity

Representa la capacidad instalada y disponible de la instancia.

Ejemplos:

* canales disponibles;
* CPU libre;
* memoria disponible;
* almacenamiento.

---

# NodeMetric

Representa mediciones continuas obtenidas durante la ejecución.

Ejemplos:

* utilización de CPU;
* memoria;
* tráfico;
* bitrate;
* temperatura;
* latencia.

---

# NodeEvent

Representa hechos ocurridos durante la vida de la instancia.

Ejemplos:

* inicio;
* parada;
* cambio de configuración;
* conexión de clientes.

---

# NodeAlarm

Representa condiciones que requieren atención.

Ejemplos:

* CPU elevada;
* pérdida de conectividad;
* sobretemperatura;
* almacenamiento insuficiente.

---

# NodeHeartbeat

Representa la señal periódica enviada por la instancia para indicar que continúa operativa.

El Heartbeat constituye el mecanismo principal para detectar la pérdida de comunicación.

---

# NodeSnapshot

Representa una fotografía completa del estado de una NodeInstance en un instante determinado.

Todo Snapshot pertenece exactamente a una única NodeInstance.

---

# Requisitos Normativos

Toda NodeInstance compatible:

**DEBE**

* pertenecer a un único Node;
* poseer un NodeInstanceId;
* publicar información mediante la Node Contract Specification;
* mantener actualizado su estado operacional;
* enviar Heartbeats periódicos.

---

**NO DEBE**

* pertenecer a múltiples Nodes;
* reutilizar el identificador de otra instancia activa;
* mezclar identidad lógica con información de ejecución.

---

**PUEDE**

* iniciarse y finalizar múltiples veces durante la vida del Node;
* migrarse entre servidores;
* cambiar de infraestructura;
* actualizar sus capacidades durante la ejecución cuando la naturaleza del servicio lo permita.

---

# Escalabilidad

La separación entre Node y NodeInstance permite soportar:

* alta disponibilidad;
* balanceo de carga;
* clústeres;
* edge computing;
* despliegues híbridos;
* elasticidad en la nube.

La incorporación de nuevas instancias no requiere modificar el modelo de dominio.

---

# Ejemplo Conceptual

```text
Streaming Node
│
├── NodeId
│
└── NodeInstances
      │
      ├── streaming-primary
      │      RUNNING
      │
      ├── streaming-backup
      │      RUNNING
      │
      └── streaming-edge-panama
             WARNING
```

El Node representa el servicio lógico.

Cada NodeInstance representa una ejecución independiente.

---

# Relación con el NOC

El Network Operations Center administra NodeInstances.

El estado agregado del Node se obtiene consolidando la información publicada por todas sus instancias.

Las decisiones operacionales del NOC se basan en la observación de las NodeInstances, mientras que el inventario y la clasificación se organizan a nivel de Node.

---

# Conclusión

La NodeInstance constituye la representación operacional de un Node.

La separación entre identidad lógica y ejecución concreta permite que la plataforma soporte múltiples instancias simultáneas, migraciones, alta disponibilidad y escalabilidad horizontal sin comprometer la estabilidad del modelo de dominio.

Esta distinción convierte a la Node-Oriented Architecture en una arquitectura preparada para infraestructuras distribuidas y de crecimiento continuo.
