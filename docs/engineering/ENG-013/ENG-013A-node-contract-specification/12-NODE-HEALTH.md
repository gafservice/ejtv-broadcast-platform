# 12. NodeHealth

## Introducción

El **NodeHealth** representa la condición operacional de una **NodeInstance**.

Describe la capacidad de la instancia para desempeñar correctamente la función para la cual fue diseñada.

El NodeHealth constituye una evaluación operacional obtenida a partir del análisis de múltiples indicadores internos y externos.

No representa una métrica individual, sino una valoración integral del estado de la instancia.

---

# Propósito

El propósito del NodeHealth es responder una única pregunta:

> **¿Qué tan bien puede cumplir esta NodeInstance su función?**

Esta evaluación permite al **Network Operations Center (NOC)** determinar el nivel de confianza operacional de la instancia.

---

# Responsabilidad

NodeHealth posee una única responsabilidad:

> Representar la condición operacional de una NodeInstance.

No representa:

* estado del ciclo de vida;
* disponibilidad para recibir carga;
* utilización de recursos;
* capacidad instalada.

Estas responsabilidades pertenecen a otras entidades del modelo.

---

# Naturaleza

NodeHealth representa una evaluación.

Puede calcularse considerando múltiples indicadores, entre ellos:

* utilización de CPU;
* utilización de memoria;
* temperatura;
* latencia;
* errores internos;
* tiempos de respuesta;
* pérdida de paquetes;
* disponibilidad de dependencias.

La Node Contract Specification no impone un algoritmo específico para calcular esta evaluación.

---

# Catálogo Canónico

La versión 1.0 define los siguientes niveles de salud.

---

## HEALTHY

La instancia opera dentro de los parámetros esperados.

No existen condiciones que comprometan el servicio.

---

## WARNING

Se detectan condiciones que requieren atención.

La instancia continúa operando, pero existen indicadores que podrían evolucionar hacia una degradación.

Ejemplos:

* utilización elevada;
* incremento de latencia;
* temperatura creciente;
* errores esporádicos.

---

## DEGRADED

La instancia continúa prestando servicio, pero una parte de sus capacidades se encuentra afectada.

El impacto es observable desde el punto de vista operacional.

Ejemplos:

* reducción de rendimiento;
* pérdida parcial de funcionalidades;
* capacidad reducida.

---

## CRITICAL

La condición operacional es crítica.

La instancia requiere intervención inmediata.

Aunque todavía pueda encontrarse ejecutándose, existe un alto riesgo de interrupción del servicio.

---

## UNKNOWN

No existe información suficiente para determinar la condición operacional.

Generalmente corresponde a:

* pérdida de comunicación;
* ausencia de métricas;
* imposibilidad de evaluar la instancia.

---

# Relación con NodeStatus

NodeStatus responde:

> ¿Qué está haciendo la instancia?

NodeHealth responde:

> ¿Qué tan bien puede hacerlo?

Ejemplos:

| NodeStatus | NodeHealth | Interpretación                               |
| ---------- | ---------- | -------------------------------------------- |
| RUNNING    | HEALTHY    | Opera normalmente                            |
| RUNNING    | WARNING    | Opera, pero requiere seguimiento             |
| RUNNING    | DEGRADED   | Continúa prestando servicio con limitaciones |
| RUNNING    | CRITICAL   | Riesgo elevado de fallo                      |
| FAILED     | CRITICAL   | La instancia terminó debido a un error       |

NodeStatus y NodeHealth son conceptos independientes.

---

# Relación con NodeAvailability

NodeAvailability responde una pregunta distinta:

> ¿Puede aceptar nuevas tareas?

Una misma instancia puede presentar distintas combinaciones.

Ejemplos:

| Status      | Health   | Availability |
| ----------- | -------- | ------------ |
| RUNNING     | HEALTHY  | AVAILABLE    |
| RUNNING     | HEALTHY  | UNAVAILABLE  |
| RUNNING     | WARNING  | AVAILABLE    |
| RUNNING     | CRITICAL | AVAILABLE    |
| MAINTENANCE | HEALTHY  | UNAVAILABLE  |
| FAILED      | CRITICAL | UNAVAILABLE  |

La especificación no establece una relación obligatoria entre estas entidades.

Cada una representa una dimensión independiente del modelo operacional.

---

# Evaluación

La forma de calcular NodeHealth depende de la naturaleza del Node.

Ejemplos:

## Streaming Node

Puede considerar:

* bitrate;
* pérdida de paquetes;
* lectores activos;
* utilización de CPU;
* errores de codificación.

---

## Identity Node

Puede considerar:

* tiempos de autenticación;
* errores de autorización;
* disponibilidad de la base de datos;
* utilización de recursos.

---

## Transcoding Node

Puede considerar:

* utilización de GPU;
* temperatura;
* velocidad de codificación;
* colas de trabajo;
* memoria disponible.

La especificación únicamente define el resultado de la evaluación, no el algoritmo utilizado.

---

# Persistencia

NodeHealth representa la evaluación actual.

La evolución histórica deberá registrarse mediante NodeEvent o mecanismos específicos de monitoreo.

NodeHealth no mantiene historial.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* publicar exactamente un NodeHealth por NodeInstance;
* utilizar únicamente valores definidos por la especificación;
* actualizar la evaluación cuando cambie la condición operacional.

---

**NO DEBE**

* utilizar NodeHealth para representar estado;
* utilizar NodeHealth para representar disponibilidad;
* calcular NodeHealth a partir de una única métrica cuando ello produzca una evaluación engañosa;
* introducir niveles de salud no definidos por la especificación sin una extensión formal.

---

**PUEDE**

* utilizar algoritmos propios de evaluación;
* ponderar indicadores según el tipo de Node;
* incorporar inteligencia artificial o modelos predictivos para estimar la salud, siempre que el resultado publicado pertenezca al catálogo oficial.

---

# Ejemplo Conceptual

```text
Node
│
└── Instance
      │
      ├── NodeStatus
      │      RUNNING
      │
      ├── NodeHealth
      │      WARNING
      │
      └── NodeAvailability
             AVAILABLE
```

La instancia continúa ejecutándose, presenta una condición que requiere seguimiento y aún puede aceptar nuevas tareas.

---

# Consideraciones de Evolución

Las futuras versiones de la Node Contract Specification podrán incorporar nuevos métodos de evaluación.

Sin embargo:

* el significado de los niveles existentes deberá preservarse;
* la interpretación operacional deberá permanecer consistente entre versiones;
* los algoritmos internos podrán evolucionar sin modificar el contrato.

---

# Conclusión

NodeHealth representa la evaluación integral de la condición operacional de una NodeInstance.

Su función consiste en indicar qué tan bien puede desempeñar la función para la cual fue diseñada, independientemente de su estado operativo o de su disponibilidad para aceptar nuevas tareas.

La separación entre **NodeStatus**, **NodeHealth** y **NodeAvailability** constituye uno de los principios fundamentales de la Node Contract Specification y proporciona una representación multidimensional del estado operacional de la plataforma.
