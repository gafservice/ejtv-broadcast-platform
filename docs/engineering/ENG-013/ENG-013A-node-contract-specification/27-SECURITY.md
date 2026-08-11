# 27. Security

## Introducción

La **Security** define los principios de seguridad que deben preservar las implementaciones compatibles con la **Node Contract Specification (NCS)** durante el intercambio de información entre NodeInstances y el **Network Operations Center (NOC)**.

La Node Contract Specification define **qué propiedades de seguridad deben protegerse**.

No define los mecanismos tecnológicos mediante los cuales dichas propiedades son implementadas.

Esta separación garantiza la independencia entre el contrato lógico y las tecnologías de seguridad utilizadas por cada implementación.

---

# Propósito

El propósito de Security es establecer un conjunto uniforme de principios que permitan proteger la integridad, autenticidad y confiabilidad de la información intercambiada mediante la Node Contract Specification.

Estos principios permiten:

* proteger el contrato;
* preservar la integridad de la información;
* garantizar la autenticidad del origen;
* facilitar auditorías;
* soportar arquitecturas seguras.

---

# Responsabilidad

Security posee una única responsabilidad:

> Definir las propiedades de seguridad que deben preservarse durante el intercambio de información de la Node Contract Specification.

No define:

* protocolos criptográficos;
* algoritmos de cifrado;
* certificados digitales;
* mecanismos de autenticación;
* políticas de autorización.

Estas responsabilidades pertenecen a la infraestructura de seguridad de la plataforma.

---

# Principios Fundamentales

Toda implementación compatible deberá preservar los siguientes principios.

---

## Confidencialidad

La información intercambiada deberá protegerse frente a accesos no autorizados cuando la arquitectura de la plataforma así lo requiera.

La Node Contract Specification no impone un mecanismo específico de protección.

---

## Integridad

Toda implementación deberá garantizar que la información recibida corresponda exactamente a la información emitida.

La detección de modificaciones constituye un requisito fundamental del contrato.

---

## Autenticidad

El receptor deberá poder verificar el origen de la información.

La forma de realizar dicha verificación dependerá de la implementación.

---

## Autorización

Las operaciones sobre la Node Contract Specification deberán ejecutarse únicamente por entidades autorizadas.

La política de autorización pertenece al subsistema de identidad de la plataforma.

---

## Auditabilidad

Las operaciones relevantes deberán poder reconstruirse posteriormente mediante los mecanismos de observabilidad definidos por la NCS.

---

## Trazabilidad

Toda información intercambiada deberá poder relacionarse con la NodeInstance que la originó.

---

# Independencia Tecnológica

La Node Contract Specification no depende de tecnologías específicas de seguridad.

Las implementaciones podrán utilizar, entre otras:

* TLS;
* mTLS;
* VPN;
* IPSec;
* firmas digitales;
* mecanismos HMAC;
* certificados X.509;
* otras tecnologías equivalentes.

La elección corresponde a la arquitectura de la plataforma.

---

# Relación con Identity

La autenticación y autorización de usuarios, servicios y operadores pertenecen al subsistema **Identity Application Layer (ENG-012)**.

La Node Contract Specification asume la existencia de un mecanismo de identidad compatible.

La NCS no redefine dicho mecanismo.

---

# Integridad del Contrato

Las implementaciones deberán proteger el contenido del contrato frente a modificaciones no autorizadas.

Cuando la arquitectura lo requiera, podrán utilizarse mecanismos de verificación como:

* firmas digitales;
* códigos de autenticación de mensajes (MAC);
* funciones hash;
* verificaciones criptográficas equivalentes.

La especificación no impone una tecnología concreta.

---

# Protección del Transporte

La protección del canal de comunicación constituye una responsabilidad independiente del contrato.

La elección del mecanismo de protección dependerá del protocolo y de la infraestructura utilizada.

---

# Auditoría

Toda implementación deberá permitir la reconstrucción de las operaciones relevantes utilizando las entidades definidas por la Node Contract Specification.

En particular:

* EventRecord;
* AlarmRecord;
* HeartbeatRecord;
* NodeSnapshot.

Estos registros constituyen la base de la auditoría operacional.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* preservar la integridad del contrato;
* garantizar la autenticidad del origen cuando resulte aplicable;
* mantener la trazabilidad de la información;
* respetar las políticas de identidad y autorización de la plataforma.

---

**NO DEBE**

* modificar el significado del contrato durante el intercambio;
* incorporar mecanismos de seguridad que alteren la semántica de las entidades;
* asumir una tecnología específica como requisito de la Node Contract Specification.

---

**PUEDE**

* utilizar cualquier tecnología de protección compatible con la arquitectura;
* incorporar mecanismos adicionales de verificación;
* aplicar distintos niveles de protección según el entorno operacional.

---

# Relación con el NOC

El Network Operations Center utilizará los principios definidos por este documento para verificar la confiabilidad de la información recibida desde las NodeInstances.

La validación de identidad, integridad y autorización permitirá garantizar que las decisiones operacionales del NOC se basen en información auténtica y consistente.

---

# Consideraciones de Evolución

La evolución de las tecnologías de seguridad no requerirá modificaciones en la Node Contract Specification.

La incorporación de nuevos algoritmos, protocolos o mecanismos criptográficos no alterará el contrato lógico definido por la NCS.

Esta separación garantiza la vigencia del contrato frente a la evolución continua del estado del arte en ciberseguridad.

---

# Conclusión

La Security establece los principios de protección que deben preservar las implementaciones compatibles con la Node Contract Specification.

Al separar las propiedades de seguridad de las tecnologías específicas que las implementan, la NCS mantiene su independencia tecnológica y garantiza que el contrato pueda evolucionar sin quedar ligado a mecanismos concretos de autenticación, cifrado o transporte.

Este enfoque convierte a la seguridad en una propiedad transversal del contrato y no en una característica dependiente de una implementación particular.
