# 13. NodeAvailability

## Introducción

El **NodeAvailability** representa la disponibilidad operacional de una **NodeInstance** para aceptar nuevas cargas de trabajo.

Mientras que:

* **NodeStatus** describe qué está haciendo la instancia.
* **NodeHealth** describe qué tan bien puede realizar su función.

El **NodeAvailability** responde una tercera pregunta independiente:

> **¿Puede esta NodeInstance aceptar nuevas tareas en este momento?**

Esta separación permite desacoplar la ejecución, la condición operacional y la capacidad efectiva de prestar servicio.

---

# Propósito

El propósito del NodeAvailability es proporcionar al **Network Operations Center (NOC)** y a los componentes de orquestación una indicación explícita sobre la posibilidad de utilizar una NodeInstance.

La disponibilidad constituye la principal referencia para:

* balanceadores de carga;
* planificadores;
* orquestadores;
* sistemas automáticos de recuperación;
* mecanismos de alta disponibilidad.

---

# Responsabilidad

NodeAvailability posee una única responsabilidad:

> Indicar si una NodeInstance está disponible para recibir nuevas tareas.

No representa:

* estado operacional;
* salud;
* utilización;
* capacidad instalada;
* rendimiento.

Estas dimensiones pertenecen a otras entidades del dominio.

---

# Naturaleza

NodeAvailability representa una decisión operacional.

Esta decisión puede depender de múltiples factores.

Ejemplos:

* política administrativa;
* capacidad restante;
* mantenimiento;
* saturación;
* dependencia externa;
* balanceo de carga;
* estrategia de alta disponibilidad.

La especificación no impone un algoritmo para determinar la disponibilidad.

---

# Catálogo Canónico

La versión 1.0 de la Node Contract Specification define los siguientes estados.

---

## AVAILABLE

La NodeInstance puede aceptar nuevas tareas.

La instancia participa normalmente en la operación de la plataforma.

---

## LIMITED

La NodeInstance continúa aceptando trabajo, pero con restricciones.

Ejemplos:

* límite reducido de sesiones;
* capacidad temporalmente restringida;
* degradación controlada;
* políticas de admisión parciales.

---

## DRAINING

La NodeInstance deja de aceptar nuevas tareas.

Sin embargo, continúa atendiendo las tareas previamente asignadas hasta su finalización.

Este estado resulta especialmente útil para:

* mantenimiento;
* migraciones;
* actualizaciones;
* reemplazos controlados.

---

## UNAVAILABLE

La NodeInstance no acepta nuevas tareas.

La indisponibilidad puede ser consecuencia de:

* políticas operacionales;
* mantenimiento;
* saturación;
* fallos;
* intervención manual.

---

## UNKNOWN

No existe información suficiente para determinar la disponibilidad.

Generalmente indica pérdida de comunicación o ausencia de información válida.

---

# Independencia

NodeAvailability es completamente independiente de NodeStatus y NodeHealth.

Ejemplos válidos:

| Status      | Health   | Availability | Interpretación                                       |
| ----------- | -------- | ------------ | ---------------------------------------------------- |
| RUNNING     | HEALTHY  | AVAILABLE    | Operación normal                                     |
| RUNNING     | HEALTHY  | LIMITED      | Acepta carga limitada                                |
| RUNNING     | HEALTHY  | DRAINING     | Finaliza trabajo existente sin aceptar nuevas tareas |
| RUNNING     | HEALTHY  | UNAVAILABLE  | Disponible técnicamente, pero retirada del servicio  |
| RUNNING     | WARNING  | AVAILABLE    | Continúa aceptando trabajo                           |
| RUNNING     | CRITICAL | AVAILABLE    | La política aún permite recibir tareas               |
| MAINTENANCE | HEALTHY  | UNAVAILABLE  | Mantenimiento programado                             |
| FAILED      | CRITICAL | UNAVAILABLE  | Fuera de servicio                                    |

La especificación no obliga a una relación fija entre estas dimensiones.

---

# Criterios de Evaluación

Cada implementación puede utilizar diferentes criterios para determinar la disponibilidad.

Ejemplos:

## Streaming Node

* número máximo de lectores;
* ancho de banda disponible;
* utilización de CPU;
* utilización de memoria;
* capacidad de red.

---

## Transcoding Node

* canales activos;
* utilización de GPU;
* temperatura;
* memoria de video disponible;
* colas pendientes.

---

## Identity Node

* tiempos de autenticación;
* disponibilidad de la base de datos;
* capacidad restante del servicio.

---

# Relación con NodeCapacity

NodeCapacity describe:

> **¿Cuánta capacidad existe?**

NodeAvailability responde:

> **¿Puede utilizarse esa capacidad ahora mismo?**

Una NodeInstance puede disponer de capacidad instalada suficiente y, aun así, declararse temporalmente no disponible por razones operacionales.

---

# Persistencia

NodeAvailability representa únicamente la condición actual.

Los cambios históricos deberán registrarse mediante NodeEvent.

La especificación no mantiene historial dentro de NodeAvailability.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* publicar exactamente un NodeAvailability por NodeInstance;
* utilizar únicamente valores definidos por la especificación;
* actualizar la disponibilidad cuando cambien las condiciones operacionales.

---

**NO DEBE**

* utilizar NodeAvailability como indicador de salud;
* utilizar NodeAvailability como estado operacional;
* utilizar NodeAvailability para representar métricas;
* inventar estados fuera del catálogo oficial sin extender formalmente la especificación.

---

**PUEDE**

* aplicar políticas propias para calcular la disponibilidad;
* modificar dinámicamente la disponibilidad durante la ejecución;
* combinar múltiples indicadores para determinar el estado publicado.

---

# Ejemplo Conceptual

```text id="n2xgmw"
Node
│
└── NodeInstance
      │
      ├── NodeStatus
      │      RUNNING
      │
      ├── NodeHealth
      │      HEALTHY
      │
      └── NodeAvailability
             DRAINING
```

La instancia continúa ejecutándose correctamente, pero no acepta nuevas tareas porque está siendo retirada de servicio de forma controlada.

---

# Relación con el NOC

El Network Operations Center utilizará NodeAvailability como referencia principal para la toma de decisiones relacionadas con:

* distribución de carga;
* activación de instancias;
* retiro programado;
* mantenimiento;
* automatización;
* recuperación ante fallos.

Las políticas específicas serán responsabilidad del NOC Core y no forman parte de esta especificación.

---

# Consideraciones de Evolución

Las futuras versiones de la Node Contract Specification podrán incorporar nuevos estados de disponibilidad o mecanismos más avanzados de evaluación.

Sin embargo:

* el significado de los estados existentes deberá mantenerse;
* la independencia respecto a NodeStatus y NodeHealth deberá preservarse;
* la compatibilidad entre versiones deberá garantizarse.

---

# Conclusión

NodeAvailability representa la disponibilidad efectiva de una NodeInstance para recibir nuevas cargas de trabajo.

Su función es proporcionar una dimensión operacional independiente del estado y de la salud de la instancia, permitiendo que el Network Operations Center y los componentes de orquestación tomen decisiones coherentes sobre balanceo, mantenimiento, recuperación y planificación de capacidad.

La incorporación de NodeAvailability completa el modelo operacional tridimensional definido por la Node Contract Specification y proporciona una base sólida para la evolución futura de la plataforma hacia arquitecturas distribuidas, altamente disponibles y escalables.
