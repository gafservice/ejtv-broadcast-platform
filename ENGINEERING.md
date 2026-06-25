# Ingeniería

> *"La tecnología cambia constantemente.
> Los principios de ingeniería permanecen."*

---

# Introducción

Toda plataforma tecnológica es el resultado de cientos de decisiones.

Algunas de ellas parecen pequeñas.

Otras modifican completamente la arquitectura del sistema.

Con el paso del tiempo es fácil recordar qué decisiones fueron tomadas.

Lo realmente difícil es recordar **por qué** fueron tomadas.

Por esta razón, **EJTV Broadcast Platform** establece desde el inicio una
metodología de ingeniería cuyo objetivo consiste en documentar el razonamiento
que existe detrás de cada decisión técnica.

Nuestro propósito no es únicamente construir una plataforma funcional.

Queremos construir una plataforma que pueda comprenderse, mantenerse y
evolucionar durante muchos años.

---

# ¿Qué entendemos por ingeniería?

En este proyecto entendemos la ingeniería como el proceso de transformar una
necesidad en una solución técnica mediante decisiones fundamentadas.

Una buena solución no es necesariamente la más compleja.

Tampoco la más moderna.

Una buena solución es aquella que resuelve correctamente el problema,
puede mantenerse con facilidad y continúa siendo válida con el paso del
tiempo.

Por esta razón evitaremos incorporar componentes únicamente porque sean
novedosos o populares.

Cada tecnología deberá demostrar claramente el valor que aporta a la
plataforma.

---

# Nuestra forma de trabajar

Toda actividad desarrollada durante este proyecto seguirá el mismo proceso.

No implementaremos soluciones de forma improvisada.

Cada decisión deberá recorrer el siguiente ciclo.

```text
Necesidad
      │
      ▼
Comprensión
      │
      ▼
Investigación
      │
      ▼
Alternativas
      │
      ▼
Evaluación
      │
      ▼
Decisión
      │
      ▼
Implementación
      │
      ▼
Validación
      │
      ▼
Documentación
      │
      ▼
Mantenimiento
```

Este proceso será utilizado durante todo el proyecto,
independientemente del tamaño o complejidad de la tarea.

---

# Cómo tomamos decisiones

Antes de incorporar cualquier componente responderemos siempre las siguientes
preguntas.

## ¿Qué problema queremos resolver?

La primera responsabilidad consiste en comprender correctamente el problema.

Una solución aplicada sobre un problema mal entendido normalmente genera más
inconvenientes de los que resuelve.

---

## ¿Qué alternativas existen?

Rara vez existe una única solución.

Analizaremos diferentes alternativas considerando aspectos como:

- estabilidad;
- seguridad;
- facilidad de mantenimiento;
- consumo de recursos;
- documentación disponible;
- compatibilidad con la arquitectura.

---

## ¿Por qué elegimos una alternativa?

Toda decisión deberá quedar documentada.

Nuestro objetivo es que cualquier ingeniero pueda comprender por qué una
tecnología fue seleccionada y cuáles fueron las razones para descartar otras
opciones.

---

# Nuestra filosofía documental

La documentación forma parte del proyecto.

No constituye una actividad adicional realizada al finalizar la
implementación.

Cada documento deberá permitir que otra persona pueda comprender la plataforma
sin necesidad de consultar directamente con quienes participaron en su
desarrollo.

Por esta razón todos los documentos seguirán una estructura común.

Cada capítulo responderá siempre las siguientes preguntas.

- ¿Qué es?
- ¿Por qué existe?
- ¿Cómo funciona?
- ¿Cómo se implementa?
- ¿Cómo verificamos que funciona?

De esta manera la documentación se convierte también en una herramienta de
aprendizaje.

---

# Nuestro criterio de calidad

Para nosotros una tarea no termina únicamente cuando el sistema funciona.

Una tarea solamente se considera finalizada cuando cumple todas las
condiciones siguientes.

- La solución funciona correctamente.
- Ha sido validada.
- Se encuentra documentada.
- Fue registrada en el repositorio Git.
- Puede ser comprendida por otro ingeniero.

Si alguna de estas condiciones no se cumple, la tarea continúa abierta.

---

# Control de cambios

Toda modificación importante deberá responder cuatro preguntas.

## ¿Qué cambió?

Describe claramente el cambio realizado.

---

## ¿Por qué cambió?

Explica la necesidad que motivó la modificación.

---

## ¿Qué impacto produce?

Describe cómo afecta el funcionamiento general de la plataforma.

---

## ¿Cómo volver atrás?

Siempre que sea posible deberá existir un procedimiento para regresar al
estado anterior en caso de ser necesario.

---

# Simplicidad

La simplicidad constituye uno de los principios fundamentales de este
proyecto.

Siempre preferiremos la solución más sencilla que cumpla correctamente los
objetivos definidos.

Una arquitectura sencilla resulta más fácil de comprender, mantener y
ampliar.

La complejidad solamente será aceptada cuando aporte un beneficio claramente
demostrable.

---

# Aprendizaje continuo

Este proyecto también constituye una herramienta de aprendizaje.

Cada documento deberá enseñar.

Cada decisión deberá aportar conocimiento.

Cada etapa del desarrollo deberá enriquecer la experiencia de quienes
participen en el proyecto.

Nuestro objetivo no consiste únicamente en construir infraestructura.

Queremos comprender profundamente cada componente que forma parte de ella.

---

# Nuestro compromiso

Nos comprometemos a construir una plataforma basada en los siguientes
principios.

- Ingeniería antes que improvisación.
- Comprensión antes que implementación.
- Estabilidad antes que nuevas funcionalidades.
- Documentación antes que memoria.
- Simplicidad antes que complejidad.
- Seguridad desde el diseño.
- Aprendizaje permanente.

---

# Nuestra definición de éxito

El éxito de este proyecto no se medirá únicamente por la capacidad de
distribuir contenido audiovisual.

Consideraremos que la plataforma ha alcanzado su objetivo cuando cualquier
ingeniero pueda comprender su arquitectura, mantenerla con seguridad y
continuar su evolución utilizando la documentación de este repositorio.

---

# Nuestra frase

> **Construimos plataformas que pueden entenderse.**

Creemos que una plataforma que solamente funciona depende de quienes la
construyeron.

Una plataforma que puede comprenderse puede mantenerse, evolucionar y seguir
aportando valor durante muchos años.

Ese es el verdadero objetivo de **EJTV Broadcast Platform**.