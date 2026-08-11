# 2. Philosophy

## Introducción

La **Node Contract Specification (NCS)** no define únicamente un conjunto de estructuras de datos.

Define una filosofía de diseño para la construcción de sistemas distribuidos dentro de la plataforma Broadcast.

Esta filosofía establece que todos los componentes de la plataforma deben comportarse como nodos autónomos, capaces de describir su estado operacional mediante un contrato común, sin exponer detalles de su implementación interna.

La arquitectura resultante favorece la simplicidad, el desacoplamiento y la evolución sostenible del sistema.

---

# Filosofía Fundamental

El principio rector de la Node Contract Specification puede resumirse en una única afirmación:

> **El NOC no conoce implementaciones; el NOC conoce nodos.**

Cada nodo es responsable de su propia lógica de negocio.

El NOC únicamente consume la información que el nodo decide publicar conforme a esta especificación.

Como consecuencia, el NOC nunca depende de tecnologías, bibliotecas, protocolos internos o decisiones de implementación particulares.

---

# Autonomía de los Nodos

Cada nodo constituye una unidad funcional independiente.

Un nodo:

* administra sus propios recursos;
* ejecuta su propia lógica;
* mantiene su propio estado interno;
* decide cómo obtener sus métricas;
* controla sus procesos internos.

La única responsabilidad compartida consiste en publicar su estado utilizando el Node Contract.

---

# Contrato sobre Implementación

La interoperabilidad de la plataforma se fundamenta en contratos, no en implementaciones.

Dos nodos completamente distintos podrán integrarse al mismo NOC siempre que ambos implementen correctamente la Node Contract Specification.

El NOC no distingue entre tecnologías, sino entre contratos compatibles.

---

# Observabilidad por Diseño

La observabilidad no constituye una funcionalidad adicional.

Forma parte del diseño inicial de cada nodo.

Todo nodo compatible con la plataforma DEBE ser capaz de describir su estado operacional de forma estructurada y verificable.

La supervisión deja de ser un proceso externo y pasa a formar parte de la arquitectura del sistema.

---

# Desacoplamiento

La Node Contract Specification reduce el acoplamiento entre componentes mediante una única dependencia compartida: el contrato.

Los nodos no requieren conocer:

* la implementación del NOC;
* otros nodos;
* la infraestructura donde serán desplegados;
* los mecanismos utilizados para visualizar la información.

Mientras el contrato permanezca estable, los componentes podrán evolucionar de manera independiente.

---

# Evolución Independiente

Cada nodo puede:

* cambiar internamente;
* incorporar nuevas funcionalidades;
* modificar algoritmos;
* optimizar procesos;
* migrar de lenguaje de programación;
* cambiar de sistema operativo.

Siempre que continúe respetando la versión vigente del contrato, el resto de la plataforma permanecerá completamente funcional.

---

# Fuente de Verdad

Cada nodo constituye la única fuente autorizada para describir su propio estado.

El NOC no interpreta comportamientos internos ni intenta inferir información que el nodo no haya publicado.

Toda la información operacional utilizada por el NOC proviene directamente de los nodos mediante la Node Contract Specification.

---

# Responsabilidad Única

Cada componente posee una única responsabilidad claramente definida.

Los nodos administran servicios.

El NOC administra observabilidad.

Los dashboards administran visualización.

Esta separación favorece una arquitectura mantenible, coherente y fácil de evolucionar.

---

# Escalabilidad

La plataforma debe poder crecer mediante la incorporación de nuevos nodos, sin modificar la arquitectura existente.

La integración de un nuevo servicio deberá requerir únicamente:

1. implementar la Node Contract Specification;
2. registrarse ante el NOC.

No deberán realizarse modificaciones específicas en el núcleo del sistema para soportar nuevos tipos de nodos.

---

# Neutralidad Tecnológica

La Node Contract Specification no favorece ninguna tecnología particular.

Un nodo podrá desarrollarse utilizando cualquier lenguaje de programación, siempre que implemente correctamente el contrato.

Asimismo, podrá ejecutarse sobre diferentes sistemas operativos, infraestructuras o plataformas de despliegue.

La interoperabilidad depende exclusivamente del cumplimiento de la especificación.

---

# Estabilidad

La estabilidad del contrato constituye un objetivo prioritario.

Toda modificación incompatible DEBE realizarse mediante una nueva versión formal de la especificación.

Las implementaciones NO DEBEN introducir extensiones incompatibles que comprometan la interoperabilidad del ecosistema.

---

# Principios Normativos

La presente especificación utiliza los siguientes niveles de obligatoriedad:

* **DEBE (MUST):** requisito obligatorio para toda implementación compatible.
* **NO DEBE (MUST NOT):** comportamiento expresamente prohibido.
* **DEBERÍA (SHOULD):** recomendación cuya omisión requiere una justificación técnica.
* **NO DEBERÍA (SHOULD NOT):** comportamiento normalmente desaconsejado.
* **PUEDE (MAY):** comportamiento opcional permitido por la especificación.

Estos términos deberán interpretarse de forma consistente en todos los documentos de la Node Contract Specification.

---

# Filosofía de Largo Plazo

La Node Contract Specification ha sido diseñada para acompañar la evolución de la plataforma durante toda su vida útil.

Su objetivo no es resolver únicamente las necesidades actuales, sino proporcionar una base arquitectónica estable que permita incorporar nuevos nodos, nuevas tecnologías y nuevas capacidades sin alterar los principios fundamentales del sistema.

La estabilidad del contrato representa la estabilidad de la arquitectura.

---

# Conclusión

La Node Contract Specification establece una filosofía donde la interoperabilidad surge de contratos compartidos y no del conocimiento mutuo entre componentes.

Cada nodo conserva su autonomía funcional, mientras que el NOC proporciona una visión unificada del estado operacional de la plataforma.

Esta filosofía convierte a la **Node-Oriented Architecture (NOA)** en una arquitectura distribuida, desacoplada, escalable y preparada para evolucionar de manera sostenible durante los próximos años.
