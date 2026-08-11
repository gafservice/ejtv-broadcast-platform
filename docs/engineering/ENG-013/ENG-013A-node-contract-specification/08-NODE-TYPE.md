# 8. NodeType

## Introducción

El **NodeType** define la categoría funcional de un **Node** dentro de la **Node-Oriented Architecture (NOA)**.

Mientras el **NodeId** responde a la pregunta:

> ¿Quién es este Node?

El **NodeType** responde:

> ¿Qué función cumple este Node dentro de la plataforma?

El NodeType constituye una clasificación lógica utilizada por el Network Operations Center (NOC) para organizar, agrupar y comprender los diferentes servicios que conforman la infraestructura.

---

# Propósito

El propósito del NodeType es identificar la responsabilidad funcional de un Node.

Esta clasificación permite al NOC:

* organizar el inventario de servicios;
* agrupar Nodes similares;
* aplicar políticas específicas por categoría;
* construir vistas operacionales;
* facilitar la administración de la plataforma.

El NodeType no representa una implementación ni una tecnología.

Representa exclusivamente una función arquitectónica.

---

# Definición

Un NodeType es una categoría funcional estable.

Todo Node DEBE pertenecer exactamente a un único NodeType.

El NodeType forma parte de la identidad arquitectónica del Node y permanece constante durante toda su vida lógica.

---

# Responsabilidad

El NodeType tiene una única responsabilidad:

> Clasificar funcionalmente un Node.

No describe:

* estado operativo;
* salud;
* capacidad;
* infraestructura;
* ubicación;
* rendimiento.

Estos aspectos pertenecen a otras entidades del modelo.

---

# Propiedades

Todo NodeType posee las siguientes características.

## Estabilidad

El tipo funcional de un Node NO DEBE cambiar durante su ciclo de vida.

---

## Unicidad Conceptual

Cada NodeType representa una única responsabilidad arquitectónica.

Dos NodeTypes distintos NO DEBEN describir la misma función.

---

## Independencia Tecnológica

El NodeType no depende de:

* lenguaje de programación;
* sistema operativo;
* plataforma;
* proveedor;
* infraestructura.

---

# Catálogo Canónico

La primera versión de la Node Contract Specification define el siguiente catálogo inicial.

## IDENTITY

Responsable de:

* autenticación;
* autorización;
* administración de usuarios;
* administración de roles.

---

## STREAMING

Responsable de:

* recepción de señales;
* distribución multimedia;
* publicación de contenido;
* administración de protocolos de streaming.

---

## TRANSCODING

Responsable de:

* codificación;
* transcodificación;
* conversión de formatos;
* procesamiento multimedia.

---

## METRICS

Responsable de:

* recopilación;
* procesamiento;
* consolidación de métricas.

---

## ALARM

Responsable de:

* generación;
* administración;
* seguimiento de alarmas.

---

## AUTOMATION

Responsable de:

* ejecución automática de tareas;
* orquestación;
* programación de acciones.

---

## STORAGE

Responsable de:

* almacenamiento;
* gestión de contenido;
* persistencia de objetos.

---

## DATABASE

Responsable de:

* administración de bases de datos;
* persistencia estructurada;
* servicios de datos.

---

## NETWORK

Responsable de:

* conectividad;
* infraestructura de red;
* servicios de comunicación.

---

## EDGE

Responsable de:

* procesamiento distribuido;
* presencia regional;
* integración remota.

---

## SYSTEM

Responsable de:

* servicios internos;
* infraestructura base;
* componentes comunes.

---

# Extensibilidad

El catálogo de NodeTypes podrá ampliarse en futuras versiones.

Toda incorporación deberá:

* representar una nueva responsabilidad arquitectónica;
* evitar duplicidad funcional;
* mantener compatibilidad con versiones anteriores.

---

# Relación con Node

Todo Node posee exactamente un NodeType.

```text id="x5vw0o"
Node
│
├── NodeId
└── NodeType
```

Esta relación permanece estable durante toda la vida lógica del Node.

---

# Relación con NodeInstance

Todas las NodeInstances pertenecientes a un Node comparten el mismo NodeType.

Ejemplo:

```text id="1hjol4"
Node
│
├── NodeType
│      STREAMING
│
└── Instances
       ├── Instance A
       ├── Instance B
       └── Instance C
```

Las instancias representan diferentes ejecuciones del mismo tipo funcional.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* definir exactamente un NodeType;
* utilizar un valor perteneciente al catálogo oficial;
* mantener el mismo NodeType durante toda la vida lógica del Node.

---

**NO DEBE**

* cambiar el NodeType durante la ejecución;
* utilizar múltiples NodeTypes para un mismo Node;
* utilizar NodeTypes ambiguos o incompatibles con la especificación.

---

**PUEDE**

* incorporar nuevos NodeTypes mediante futuras versiones de la Node Contract Specification;
* definir extensiones compatibles aprobadas por la arquitectura.

---

# Ejemplo Conceptual

```text id="5jlwm4"
Node
│
├── NodeId
│      streaming
│
├── NodeType
│      STREAMING
│
└── Instances
       ├── streaming-primary
       ├── streaming-backup
       └── streaming-edge
```

Todas las instancias pertenecen al mismo NodeType.

---

# Consideraciones de Evolución

La incorporación de nuevos NodeTypes no deberá afectar el funcionamiento del NOC Core.

El NOC deberá ser capaz de administrar cualquier NodeType compatible con la especificación sin requerir modificaciones específicas para cada categoría.

Este principio garantiza la escalabilidad de la arquitectura y preserva el desacoplamiento entre el NOC y los servicios de la plataforma.

---

# Conclusión

El NodeType constituye la clasificación funcional oficial de un Node dentro de la Node-Oriented Architecture.

Su propósito es describir la responsabilidad arquitectónica del componente sin hacer referencia a su implementación, infraestructura o estado operacional.

Gracias a esta separación entre identidad, tipo e instancia, la plataforma puede crecer incorporando nuevos servicios sin modificar los principios fundamentales definidos por la Node Contract Specification.
