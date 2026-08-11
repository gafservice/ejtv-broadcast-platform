# 24. Versioning

## Introducción

El **Versioning** define las reglas mediante las cuales evoluciona la **Node Contract Specification (NCS)**, garantizando la compatibilidad entre diferentes implementaciones y versiones del contrato.

La versión identifica el estado evolutivo de la especificación.

No representa la versión del software, del sistema operativo o de la implementación.

---

# Propósito

El propósito del Versioning es permitir la evolución controlada de la Node Contract Specification sin comprometer la interoperabilidad entre Nodes y el Network Operations Center (NOC).

El modelo de versionado permite:

* incorporar nuevas funcionalidades;
* corregir errores;
* preservar la compatibilidad;
* facilitar migraciones;
* coordinar implementaciones distribuidas.

---

# Responsabilidad

El Versioning posee una única responsabilidad:

> Definir cómo evoluciona el contrato de la Node Contract Specification.

No define:

* versiones del software;
* versiones del sistema operativo;
* versiones de librerías;
* versiones de protocolos de transporte.

Estas versiones pertenecen a la implementación.

---

# Alcance

La versión corresponde exclusivamente al contrato lógico definido por la NCS.

Dos implementaciones diferentes pueden utilizar:

* distintos lenguajes;
* diferentes sistemas operativos;
* distintos formatos de serialización;
* diferentes mecanismos de transporte;

y continuar siendo completamente compatibles siempre que implementen la misma versión de la Node Contract Specification.

---

# Semantic Versioning

La NCS adopta un esquema basado en:

```text id="n9d0l9"
MAJOR.MINOR.PATCH
```

Ejemplo:

```text id="jfcjlwm"
1.0.0
```

---

# Cambios PATCH

Los cambios PATCH corrigen errores sin modificar el contrato.

Ejemplos:

* correcciones editoriales;
* aclaraciones normativas;
* ejemplos adicionales.

Los cambios PATCH deben preservar la compatibilidad completa.

---

# Cambios MINOR

Los cambios MINOR incorporan funcionalidades compatibles con versiones anteriores.

Ejemplos:

* nuevos atributos opcionales;
* nuevos nombres canónicos;
* nuevas capacidades;
* nuevas métricas;
* nuevas alarmas.

Las implementaciones compatibles con la versión anterior deberán continuar funcionando.

---

# Cambios MAJOR

Los cambios MAJOR modifican el contrato de manera incompatible.

Ejemplos:

* eliminación de atributos obligatorios;
* cambio del significado de una entidad;
* modificación de reglas normativas;
* eliminación de estados canónicos.

Una nueva versión MAJOR puede requerir adaptaciones en las implementaciones.

---

# Compatibilidad

La Node Contract Specification distingue tres niveles de compatibilidad.

## Compatibilidad hacia atrás

Una implementación reciente puede interpretar información generada por versiones anteriores.

---

## Compatibilidad hacia adelante

Una implementación puede ignorar atributos desconocidos siempre que ello no altere la interpretación del contrato.

---

## Compatibilidad entre implementaciones

Dos implementaciones son compatibles cuando cumplen la misma versión del contrato, independientemente de la tecnología utilizada.

---

# Identificación

Toda implementación compatible deberá publicar la versión de la Node Contract Specification utilizada.

Ejemplo:

```text id="vjjlwm"
contract_version

1.0.0
```

Esta información puede incorporarse en entidades como:

* NodeSnapshot;
* HeartbeatRecord;
* EventRecord;
* AlarmRecord;
* MetricSample.

---

# Evolución del Contrato

La evolución deberá respetar los siguientes principios.

## Estabilidad

El contrato debe permanecer estable entre versiones compatibles.

---

## Extensibilidad

Las nuevas funcionalidades deberán incorporarse sin modificar el significado de las entidades existentes siempre que sea posible.

---

## Compatibilidad

La evolución debe minimizar la necesidad de modificar implementaciones existentes.

---

## Claridad

Todo cambio deberá documentarse mediante el correspondiente ChangeLog de la especificación.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* indicar la versión de la Node Contract Specification implementada;
* respetar las reglas de Semantic Versioning;
* preservar la compatibilidad cuando corresponda.

---

**NO DEBE**

* modificar el significado de una entidad sin incrementar la versión MAJOR;
* eliminar elementos obligatorios en una versión MINOR;
* reutilizar números de versión para contratos diferentes.

---

**PUEDE**

* incorporar extensiones compatibles;
* implementar versiones posteriores del contrato;
* soportar múltiples versiones simultáneamente cuando resulte necesario.

---

# Relación con el NOC

El Network Operations Center utilizará la información de versión para:

* validar compatibilidad;
* detectar Nodes desactualizados;
* coordinar migraciones;
* facilitar diagnósticos;
* planificar actualizaciones de la plataforma.

La versión del contrato constituye un elemento esencial para la interoperabilidad de la infraestructura distribuida.

---

# Consideraciones de Evolución

La Node Contract Specification está diseñada para evolucionar de manera incremental.

La incorporación de nuevas entidades o capacidades deberá realizarse preservando, siempre que sea posible, la compatibilidad entre versiones.

Los cambios incompatibles deberán reservarse para nuevas versiones MAJOR.

---

# Conclusión

El Versioning establece el marco mediante el cual evoluciona la Node Contract Specification.

La adopción de Semantic Versioning, junto con principios claros de compatibilidad y estabilidad, garantiza que la especificación pueda crecer de forma ordenada sin comprometer la interoperabilidad entre Nodes, el NOC y futuras implementaciones.

La separación entre la versión del contrato y la versión de las implementaciones asegura que la evolución tecnológica de la plataforma pueda producirse de manera independiente de la evolución del modelo de información definido por la NCS.
