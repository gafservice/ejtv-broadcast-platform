# 11. NodeStatus

## Introducción

El **NodeStatus** describe el estado operacional actual de una **NodeInstance**.

Representa la fase del ciclo de vida en la que se encuentra la instancia durante un instante determinado.

El NodeStatus no mide rendimiento, disponibilidad ni calidad del servicio.

Su única responsabilidad consiste en indicar el estado operacional de la instancia.

---

# Propósito

El propósito del NodeStatus es responder una única pregunta:

> **¿Qué está haciendo la NodeInstance en este momento?**

El estado operacional permite al Network Operations Center (NOC) comprender la situación actual de una instancia sin necesidad de analizar métricas o eventos adicionales.

---

# Responsabilidad

NodeStatus posee una única responsabilidad:

> Representar el estado operacional de una NodeInstance.

No representa:

* salud;
* utilización;
* capacidad;
* rendimiento;
* criticidad;
* disponibilidad del servicio.

Estas responsabilidades pertenecen a otras entidades del modelo.

---

# Naturaleza

NodeStatus representa una condición temporal.

Puede cambiar múltiples veces durante la vida de una NodeInstance.

Los cambios de estado forman parte natural del ciclo operacional de la instancia.

---

# Catálogo Canónico de Estados

La versión 1.0 de la Node Contract Specification define los siguientes estados.

---

## CREATED

La instancia ha sido creada pero todavía no ha iniciado su proceso de inicialización.

---

## INITIALIZING

La instancia se encuentra inicializando recursos internos.

Puede incluir:

* carga de configuración;
* inicialización de componentes;
* apertura de conexiones;
* validaciones internas.

La instancia todavía no presta servicio.

---

## STARTING

La instancia está iniciando su operación normal.

Los servicios principales comienzan a estar disponibles.

---

## RUNNING

La instancia se encuentra operando normalmente.

Este estado indica únicamente que la instancia está ejecutándose.

No implica necesariamente que su salud sea óptima.

---

## DEGRADED

La instancia continúa operando, pero algunas funcionalidades presentan degradación.

Ejemplos:

* capacidad reducida;
* rendimiento inferior al esperado;
* funcionalidades parcialmente disponibles.

La instancia sigue prestando servicio.

---

## MAINTENANCE

La instancia se encuentra temporalmente fuera de operación debido a tareas programadas.

Ejemplos:

* actualización;
* mantenimiento preventivo;
* intervención manual.

---

## STOPPING

La instancia está finalizando su ejecución de forma controlada.

Se encuentra liberando recursos antes de detenerse completamente.

---

## STOPPED

La ejecución ha finalizado correctamente.

La instancia ya no presta servicio.

---

## FAILED

La instancia terminó debido a un error.

La recuperación puede requerir reinicio o intervención.

---

## UNKNOWN

El estado operacional no puede determinarse.

Generalmente indica pérdida de comunicación o información insuficiente.

---

# Máquina de Estados Conceptual

```text
                 CREATED
                     │
                     ▼
             INITIALIZING
                     │
                     ▼
               STARTING
                     │
                     ▼
               RUNNING
               │      │
               │      ▼
               │  DEGRADED
               │      │
               └──────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   MAINTENANCE             STOPPING
          │                     │
          ▼                     ▼
      STARTING             STOPPED
                                │
                                ▼
                             FAILED
```

La especificación no obliga a utilizar exactamente todas las transiciones representadas, pero sí define el significado de cada estado.

---

# Relación con NodeHealth

Es fundamental distinguir ambos conceptos.

NodeStatus responde:

> ¿Qué está haciendo la instancia?

NodeHealth responde:

> ¿Qué tan bien puede hacerlo?

Ejemplos:

| NodeStatus  | NodeHealth | Interpretación                                          |
| ----------- | ---------- | ------------------------------------------------------- |
| RUNNING     | HEALTHY    | Operación normal                                        |
| RUNNING     | WARNING    | Opera con degradación detectada                         |
| RUNNING     | CRITICAL   | Continúa ejecutándose, pero requiere atención inmediata |
| MAINTENANCE | HEALTHY    | Mantenimiento planificado                               |
| FAILED      | CRITICAL   | Ejecución terminada por error                           |

NodeStatus y NodeHealth son independientes.

---

# Persistencia

NodeStatus representa únicamente el estado actual.

Los cambios históricos deberán registrarse mediante NodeEvent.

El historial de estados no forma parte de NodeStatus.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* publicar exactamente un NodeStatus por NodeInstance;
* utilizar únicamente estados definidos por la especificación;
* actualizar el estado cuando ocurra una transición operacional.

---

**NO DEBE**

* utilizar NodeStatus para representar salud;
* utilizar NodeStatus para representar métricas;
* utilizar estados ambiguos;
* inventar nuevos estados sin extender formalmente la especificación.

---

**PUEDE**

* implementar internamente estados adicionales;
* mapear dichos estados al catálogo oficial antes de publicarlos.

---

# Ejemplo Conceptual

```text
Node
│
└── Instance
      │
      ├── NodeInfo
      └── NodeStatus
             RUNNING
```

El NOC interpreta que la instancia se encuentra operativa.

La evaluación de su rendimiento dependerá de otras entidades del modelo.

---

# Consideraciones de Evolución

La incorporación de nuevos estados deberá realizarse mediante una nueva versión de la Node Contract Specification.

Las implementaciones deberán preservar el significado semántico de los estados existentes.

---

# Conclusión

NodeStatus representa el estado operacional instantáneo de una NodeInstance.

Su función consiste exclusivamente en describir la fase del ciclo de vida en la que se encuentra la instancia.

La separación entre **NodeStatus** y **NodeHealth** constituye uno de los principios fundamentales de la Node-Oriented Architecture, ya que distingue claramente el comportamiento operativo de la condición real del servicio.
