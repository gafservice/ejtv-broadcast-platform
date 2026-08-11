# 28. Validation Rules

## Introducción

Las **Validation Rules** definen las reglas mediante las cuales una implementación determina si la información intercambiada mediante la **Node Contract Specification (NCS)** cumple con el contrato establecido.

La validación garantiza que la información pueda ser interpretada de forma consistente por cualquier implementación compatible.

El proceso de validación verifica el cumplimiento del contrato.

No modifica la información recibida.

---

# Propósito

El propósito de las Validation Rules es proporcionar un mecanismo uniforme para verificar la conformidad de la información intercambiada mediante la Node Contract Specification.

La validación permite:

* detectar errores;
* garantizar interoperabilidad;
* preservar la integridad del contrato;
* facilitar diagnósticos;
* soportar implementaciones consistentes.

---

# Responsabilidad

Las Validation Rules poseen una única responsabilidad:

> Verificar que una representación cumple con el contrato definido por la Node Contract Specification.

No definen:

* reglas de negocio;
* decisiones operacionales;
* políticas del NOC;
* corrección automática de errores.

Estas responsabilidades pertenecen a otros componentes de la arquitectura.

---

# Principios Fundamentales

Toda validación deberá respetar los siguientes principios.

## Objetividad

Una validación produce siempre el mismo resultado para la misma información.

No depende del contexto operacional.

---

## No Modificación

La validación nunca modifica la información evaluada.

Si una representación es inválida, deberá rechazarse o notificarse el error.

---

## Independencia

La validación depende únicamente del contrato.

No depende del lenguaje de programación, del transporte ni de la implementación.

---

## Reproducibilidad

Dos implementaciones compatibles deberán obtener el mismo resultado al validar la misma información.

---

# Niveles de Validación

La NCS define cuatro niveles de validación.

---

## 1. Validación Sintáctica

Verifica que la representación pueda interpretarse correctamente.

Ejemplos:

* JSON válido;
* CBOR válido;
* Protocol Buffers correctamente codificados.

---

## 2. Validación Estructural

Verifica que la estructura respete el contrato.

Ejemplos:

* atributos obligatorios presentes;
* tipos de datos correctos;
* colecciones válidas;
* jerarquía correcta.

---

## 3. Validación Semántica

Verifica que los valores pertenezcan al dominio definido por la especificación.

Ejemplos:

* NodeType válido;
* NodeStatus reconocido;
* nombres canónicos existentes.

---

## 4. Validación de Restricciones

Verifica que los valores respeten las restricciones del contrato.

Ejemplos:

* porcentajes entre 0 y 100;
* timestamps válidos;
* identificadores únicos;
* estados permitidos.

---

# Resultado de la Validación

Toda validación produce un **ValidationResult**.

Conceptualmente contiene:

```text
ValidationResult

status

errors

warnings

validated_at
```

---

## status

Indica el resultado global de la validación.

Valores recomendados:

* VALID
* INVALID
* WARNING

---

## errors

Colección de incumplimientos del contrato.

Los errores impiden considerar la representación como conforme.

---

## warnings

Observaciones que no rompen el contrato, pero pueden indicar situaciones que requieren atención.

---

## validated_at

Momento en que se ejecutó la validación.

---

# Conformance

Una implementación es **Conformant** cuando respeta todas las reglas obligatorias definidas por la Node Contract Specification.

La conformidad constituye una propiedad binaria.

Una implementación:

* es conforme; o
* no es conforme.

---

# Rechazo

Cuando la validación detecte incumplimientos obligatorios, la implementación podrá:

* rechazar la información;
* registrar el error;
* generar un evento;
* generar una alarma.

La política concreta pertenece a la implementación.

---

# Relación con la Serialización

La validación ocurre después de la deserialización.

El proceso conceptual es:

```text
Representación

↓

Deserialización

↓

Validación

↓

Modelo del Dominio
```

Una representación inválida nunca debe convertirse en una entidad válida del dominio.

---

# Relación con el NOC

El Network Operations Center utilizará las Validation Rules para:

* verificar información recibida;
* detectar Nodes incompatibles;
* proteger la consistencia del sistema;
* facilitar diagnósticos.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* validar la información antes de utilizarla;
* respetar los niveles de validación definidos por la NCS;
* preservar el contenido durante la validación;
* producir resultados reproducibles.

---

**NO DEBE**

* modificar la información validada;
* aceptar información que incumpla el contrato obligatorio;
* mezclar reglas del contrato con reglas de negocio.

---

**PUEDE**

* generar advertencias adicionales;
* incorporar validaciones específicas compatibles con la NCS;
* optimizar el proceso de validación.

---

# Consideraciones de Evolución

Las futuras versiones de la Node Contract Specification podrán incorporar nuevas reglas de validación sin modificar los principios fundamentales definidos en este documento.

Las nuevas validaciones deberán preservar la interoperabilidad entre implementaciones compatibles.

---

# Conclusión

Las Validation Rules establecen el mecanismo oficial mediante el cual una implementación verifica la conformidad de la información intercambiada mediante la Node Contract Specification.

La separación entre validación del contrato y reglas de negocio garantiza que todas las implementaciones interpreten la información de manera uniforme, preservando la consistencia, la interoperabilidad y la estabilidad del ecosistema distribuido.

La validación constituye el paso final antes de que la información pase a formar parte del modelo de dominio de una implementación compatible.
