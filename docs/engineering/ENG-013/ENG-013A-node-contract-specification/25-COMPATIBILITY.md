# 25. Compatibility

## Introducción

La **Compatibilidad** define las condiciones bajo las cuales dos implementaciones de la **Node Contract Specification (NCS)** pueden interoperar correctamente.

La compatibilidad constituye una propiedad del contrato.

No depende del lenguaje de programación, del sistema operativo, del protocolo de transporte ni del formato de serialización utilizado por las implementaciones.

Su objetivo es garantizar que Nodes y Network Operations Centers (NOC) puedan intercambiar información de forma consistente aun cuando implementen distintas versiones de la especificación.

---

# Propósito

El propósito de la Compatibilidad es establecer reglas uniformes para la interoperabilidad entre implementaciones de la Node Contract Specification.

Estas reglas permiten:

* preservar la interoperabilidad;
* facilitar migraciones progresivas;
* soportar múltiples versiones del contrato;
* reducir interrupciones operacionales;
* mantener la estabilidad del ecosistema.

---

# Responsabilidad

La Compatibilidad posee una única responsabilidad:

> Definir cuándo dos implementaciones pueden intercambiar información preservando el significado del contrato.

No define:

* estrategias de actualización;
* mecanismos de despliegue;
* sincronización de versiones.

Estas responsabilidades pertenecen a la arquitectura de la plataforma.

---

# Principios Fundamentales

Toda implementación compatible deberá respetar los siguientes principios.

## Compatibilidad Semántica

La interoperabilidad depende del significado del contrato.

No basta con que los datos puedan intercambiarse.

Las entidades deben conservar exactamente el mismo significado.

---

## Independencia Tecnológica

Dos implementaciones pueden ser compatibles aun cuando utilicen:

* distintos lenguajes;
* distintos sistemas operativos;
* distintos protocolos;
* distintos formatos de serialización.

---

## Evolución Controlada

La incorporación de nuevas funcionalidades no debe romper la compatibilidad cuando ello pueda evitarse.

---

## Estabilidad

Los elementos canónicos definidos por la especificación deben permanecer estables entre versiones compatibles.

---

# Niveles de Compatibilidad

La Node Contract Specification define cuatro niveles.

---

## Compatible

Dos implementaciones utilizan el mismo contrato y pueden interoperar completamente.

---

## Backward Compatible

Una implementación más reciente puede interpretar correctamente información producida por una versión anterior.

Ejemplo:

```text
NOC

NCS 1.2
```

↓

```text
Streaming Node

NCS 1.0
```

---

## Forward Compatible

Una implementación puede recibir información de una versión posterior ignorando aquellos elementos desconocidos que no afecten la interpretación del contrato.

Ejemplo:

Una nueva versión incorpora un atributo opcional.

La implementación anterior continúa funcionando.

---

## Incompatible

Las implementaciones no pueden interoperar porque el significado del contrato ha cambiado de forma incompatible.

Ejemplos:

* eliminación de atributos obligatorios;
* modificación del significado de una entidad;
* eliminación de estados canónicos;
* cambios incompatibles en la estructura del contrato.

---

# Negociación

Cuando dos implementaciones soporten múltiples versiones del contrato, podrán negociar la versión común más reciente compatible.

Ejemplo conceptual:

```text
Node A

1.0
1.1
1.2
```

↓

```text
Node B

1.0
1.1
```

↓

```text
Versión negociada

1.1
```

La estrategia concreta de negociación no forma parte de esta especificación.

---

# Extensiones

Las implementaciones podrán incorporar extensiones compatibles.

Toda extensión deberá:

* preservar el significado de las entidades existentes;
* no modificar elementos obligatorios;
* mantener la interoperabilidad con implementaciones que desconozcan la extensión.

---

# Elementos Desconocidos

Una implementación podrá ignorar atributos desconocidos cuando:

* sean opcionales;
* no modifiquen el significado del contrato;
* no comprometan la seguridad ni la integridad de la información.

---

# Relación con Versioning

Versioning responde:

> ¿Cómo evoluciona el contrato?

Compatibility responde:

> ¿Cuándo dos implementaciones pueden interoperar?

Ambos documentos son complementarios.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* preservar el significado de las entidades canónicas;
* respetar las reglas de compatibilidad definidas por la NCS;
* identificar la versión del contrato implementada.

---

**NO DEBE**

* asumir compatibilidad únicamente por igualdad numérica de versiones;
* modificar el significado de entidades existentes sin una nueva versión MAJOR;
* rechazar atributos opcionales desconocidos cuando sean compatibles.

---

**PUEDE**

* soportar múltiples versiones simultáneamente;
* negociar la versión del contrato;
* incorporar extensiones compatibles.

---

# Relación con el NOC

El Network Operations Center utilizará las reglas de compatibilidad para:

* validar la incorporación de nuevos Nodes;
* detectar incompatibilidades;
* coordinar migraciones;
* facilitar actualizaciones progresivas;
* mantener la estabilidad operacional de la plataforma.

---

# Consideraciones de Evolución

Las futuras versiones de la Node Contract Specification deberán preservar la compatibilidad siempre que resulte técnicamente posible.

Los cambios incompatibles deberán reservarse para nuevas versiones MAJOR.

---

# Conclusión

La Compatibilidad define las reglas que permiten la interoperabilidad entre implementaciones de la Node Contract Specification.

La separación entre evolución del contrato y compatibilidad operacional garantiza que la plataforma pueda crecer de forma ordenada, incorporando nuevas capacidades sin comprometer la estabilidad del ecosistema distribuido.

Este modelo constituye uno de los pilares fundamentales para la evolución a largo plazo de la plataforma Broadcast y de cualquier implementación basada en la Node Contract Specification.
