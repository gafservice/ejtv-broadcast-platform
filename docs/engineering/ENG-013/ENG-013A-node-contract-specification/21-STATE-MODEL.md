# 21. State Model

## Introducción

El **State Model** define las reglas generales que gobiernan la evolución de las entidades de la **Node Contract Specification (NCS)**.

Mientras los documentos anteriores describen la estructura del dominio, el State Model establece cómo pueden cambiar los estados durante el ciclo de vida de una NodeInstance.

El objetivo del State Model es garantizar un comportamiento consistente entre todas las implementaciones compatibles con la NCS.

---

# Propósito

El propósito del State Model es proporcionar un marco uniforme para la evolución de los estados publicados por una NodeInstance.

El modelo permite:

* mantener consistencia operacional;
* evitar transiciones inválidas;
* facilitar la interoperabilidad;
* simplificar la automatización;
* garantizar un comportamiento predecible.

---

# Alcance

El State Model no define estados específicos.

Los estados específicos pertenecen a entidades como:

* NodeStatus;
* NodeHealth;
* NodeAvailability;
* futuras entidades compatibles.

El State Model únicamente define las reglas de transición.

---

# Principios Fundamentales

Toda transición de estado debe cumplir los siguientes principios.

## Consistencia

Toda transición debe conducir a un estado válido definido por la especificación.

---

## Determinismo

Ante las mismas condiciones, una implementación debe producir la misma transición.

---

## Atomicidad

Toda transición debe completarse de forma íntegra.

No deben existir estados parcialmente aplicados.

---

## Observabilidad

Toda transición significativa debe ser observable mediante NodeEvent.

---

## Trazabilidad

Toda transición debe poder reconstruirse posteriormente utilizando los eventos registrados.

---

# Máquina de Estados

Cada entidad que publique estados puede modelarse mediante una máquina de estados independiente.

Ejemplo conceptual:

```text
Estado A
    │
    ▼
Estado B
    │
    ▼
Estado C
```

Cada entidad define su propio conjunto de estados y transiciones permitidas.

---

# Transiciones

Una transición representa el cambio entre dos estados válidos.

Toda transición posee:

* estado de origen;
* estado de destino;
* condición de transición;
* instante de ocurrencia.

---

# Estados Iniciales

Toda máquina de estados debe definir un estado inicial claramente identificado.

Este estado representa el punto de partida del ciclo de vida de la entidad.

---

# Estados Terminales

Una implementación puede definir estados terminales.

Un estado terminal representa una condición desde la cual no pueden producirse nuevas transiciones sin iniciar un nuevo ciclo de vida.

---

# Estados Recuperables

Un estado recuperable permite que la entidad continúe evolucionando sin reiniciar completamente su ciclo de vida.

La clasificación entre estados terminales y recuperables dependerá de cada entidad.

---

# Eventos de Transición

Las transiciones significativas deben generar eventos compatibles con NodeEvent.

Ejemplo conceptual:

```text
RUNNING
    │
INSTANCE_STOPPED
    ▼
STOPPED
```

El evento documenta la transición.

No constituye la transición.

---

# Independencia

Cada entidad administra su propia máquina de estados.

No existe una sincronización obligatoria entre:

* NodeStatus;
* NodeHealth;
* NodeAvailability.

Las relaciones entre ellas dependerán de la implementación.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* definir estados válidos;
* permitir únicamente transiciones válidas;
* mantener consistencia durante las transiciones;
* registrar las transiciones significativas mediante NodeEvent.

---

**NO DEBE**

* permitir transiciones ambiguas;
* publicar estados inconsistentes;
* modificar retroactivamente estados ya observados.

---

**PUEDE**

* incorporar estados adicionales compatibles con la especificación;
* definir políticas específicas de transición;
* utilizar mecanismos internos para validar cambios de estado.

---

# Relación con el NOC

El Network Operations Center utilizará el State Model para:

* interpretar el comportamiento de los Nodes;
* validar transiciones;
* detectar inconsistencias;
* reconstruir la evolución operacional;
* soportar automatización y recuperación.

---

# Consideraciones de Evolución

El State Model constituye un marco general de comportamiento.

Las futuras versiones de la Node Contract Specification podrán incorporar nuevas máquinas de estados para entidades adicionales sin modificar los principios definidos en este documento.

---

# Conclusión

El State Model define las reglas generales que gobiernan la evolución de los estados dentro de la Node Contract Specification.

La separación entre entidades, estados, eventos y transiciones proporciona una base consistente para la construcción de sistemas distribuidos, interoperables y predecibles, facilitando la evolución futura de la plataforma sin comprometer la compatibilidad entre implementaciones.
