# 7. NodeId

## Introducción

El **NodeId** constituye la identidad canónica de un **Node** dentro de la **Node-Oriented Architecture (NOA)**.

Todo Node compatible con la plataforma DEBE poseer un único **NodeId** válido.

El NodeId permite al **Network Operations Center (NOC)** identificar, registrar, correlacionar y administrar un Node durante toda su vida lógica.

El NodeId representa la identidad lógica del servicio y permanece independiente de las ejecuciones concretas representadas por sus **NodeInstances**.

---

# Propósito

El propósito del NodeId es proporcionar una identidad estable, única e independiente de la implementación del Node.

El NodeId NO representa:

* direcciones IP;
* nombres DNS;
* nombres de host;
* nombres de contenedores;
* identificadores de procesos;
* identificadores internos de bases de datos;
* identificadores de NodeInstance.

Todos esos elementos pueden cambiar durante la vida del Node.

El NodeId no.

---

# Responsabilidad

El NodeId posee una única responsabilidad:

> Identificar de manera unívoca un Node.

Gracias a esta identidad el NOC puede:

* registrar Nodes;
* correlacionar información;
* asociar NodeInstances;
* consolidar métricas;
* consolidar eventos;
* consolidar alarmas;
* mantener trazabilidad histórica.

No posee ninguna otra responsabilidad.

---

# Requisitos Normativos

Toda implementación compatible:

## DEBE

* poseer exactamente un NodeId;
* mantener el mismo NodeId durante toda la vida lógica del Node;
* utilizar el mismo NodeId en todas las publicaciones realizadas por cualquiera de sus NodeInstances.

## NO DEBE

* modificar el NodeId durante la vida del Node;
* reutilizar el NodeId de otro Node activo;
* utilizar NodeIds ambiguos.

---

# Atributos

La primera versión de la especificación define los siguientes atributos.

## id

Identificador único del Node.

Constituye la identidad principal utilizada por el NOC.

Ejemplo:

```text
550e8400-e29b-41d4-a716-446655440000
```

---

## name

Nombre lógico del Node.

Debe ser corto, estable y legible.

Ejemplos:

```text
identity
```

```text
streaming
```

```text
alarm
```

---

## display_name

Nombre descriptivo utilizado por interfaces de usuario.

Ejemplos:

```text
Identity Service
```

```text
Primary Streaming Service
```

---

## created_at

Momento en que fue creada la identidad lógica del Node.

Este valor representa el registro inicial del Node dentro de la plataforma y no el inicio de una ejecución concreta.

---

# Propiedades

## Unicidad

No pueden existir dos Nodes activos con el mismo NodeId.

---

## Estabilidad

El NodeId permanece constante durante toda la vida lógica del Node.

La creación, eliminación o migración de NodeInstances no modifica el NodeId.

---

## Persistencia

La identidad del Node debe sobrevivir a reinicios, migraciones y reemplazos de infraestructura.

Reiniciar una NodeInstance NO implica crear un nuevo NodeId.

---

## Independencia

El NodeId no depende de:

* dirección IP;
* hostname;
* puerto;
* protocolo;
* infraestructura;
* proveedor de nube;
* mecanismo de despliegue.

---

# Ciclo de Vida

```text
Creación
    │
    ▼
Registro
    │
    ▼
Operación
    │
    ▼
Actualización
    │
    ▼
Retiro
```

Durante todas estas etapas el NodeId permanece inalterado.

Las NodeInstances pueden crearse, finalizar o migrarse sin afectar la identidad lógica del Node.

---

# Relación con NodeInstance

Cada Node puede poseer una o más NodeInstances.

Todas las NodeInstances pertenecientes a un mismo Node comparten exactamente el mismo NodeId.

Cada NodeInstance posee además un identificador propio denominado **NodeInstanceId**, cuya función es distinguir las diferentes ejecuciones del mismo Node.

```text
Node
│
├── NodeId
└── NodeInstances
      ├── NodeInstanceId
      ├── NodeInstanceId
      └── NodeInstanceId
```

El NodeId identifica el servicio lógico.

El NodeInstanceId identifica una ejecución específica de dicho servicio.

---

# Relación con otras Entidades

Conceptualmente, todas las entidades operacionales pertenecen a una NodeInstance, mientras que todas las NodeInstances pertenecen a un Node identificado mediante un único NodeId.

```text
Node
│
├── NodeId
└── NodeInstance [0..N]
        │
        ├── NodeInfo
        ├── NodeStatus
        ├── NodeHealth
        ├── NodeAvailability
        ├── NodeCapability
        ├── NodeCapacity
        ├── NodeMetric
        ├── NodeEvent
        ├── NodeAlarm
        ├── NodeHeartbeat
        └── NodeSnapshot
```

El NodeId constituye el punto de referencia común que permite al NOC correlacionar toda la información publicada por las distintas NodeInstances de un mismo Node.

---

# Consideraciones de Implementación

La presente especificación no impone un mecanismo específico para generar el identificador.

Las implementaciones pueden utilizar:

* UUID;
* ULID;
* identificadores corporativos;
* cualquier otro mecanismo equivalente.

El único requisito es garantizar la unicidad dentro del ecosistema de la plataforma.

---

# Compatibilidad

Las futuras versiones podrán incorporar nuevos atributos al NodeId.

Sin embargo:

* la identidad lógica del Node deberá preservarse;
* el significado de los atributos existentes no podrá modificarse;
* la compatibilidad entre versiones deberá mantenerse.

---

# Resumen

El NodeId constituye la identidad oficial de un Node.

Toda correlación realizada por el Network Operations Center depende de esta entidad.

Su estabilidad permite que un mismo servicio pueda ejecutarse mediante múltiples NodeInstances a lo largo del tiempo sin perder su identidad lógica ni la trazabilidad histórica de métricas, eventos, alarmas y snapshots.

Por esta razón, el NodeId constituye uno de los fundamentos principales del modelo de dominio definido por la Node Contract Specification.
