# Visión

> *"Construimos plataformas que pueden entenderse."*

---

## Introducción

Toda plataforma tecnológica tiene un propósito.

Algunas nacen para resolver un problema puntual.

Otras simplemente buscan incorporar nuevas tecnologías.

**EJTV Broadcast Platform** nace con un objetivo diferente.

Queremos construir una plataforma profesional para la distribución de contenido
audiovisual sobre redes IP que pueda mantenerse, comprenderse y evolucionar
durante muchos años.

Nuestra visión no se limita a desarrollar un servidor basado en Linux.

Queremos construir una plataforma cuya arquitectura pueda ser entendida por
cualquier ingeniero que participe en su mantenimiento, independientemente del
momento en que se incorpore al proyecto.

---

## Nuestra visión

Aspiramos a desarrollar una plataforma abierta para la distribución
profesional de contenido audiovisual que combine estabilidad, seguridad,
simplicidad y documentación técnica de alta calidad.

Cada componente deberá poder evolucionar sin comprometer el funcionamiento del
resto del sistema.

Cada decisión deberá encontrarse documentada.

Cada modificación deberá poder comprenderse.

Nuestro objetivo no consiste únicamente en mantener un servidor funcionando.

Nuestro objetivo consiste en construir una plataforma que pueda continuar
evolucionando durante muchos años.

---

## Lo que queremos dejar

Nos gustaría que dentro de algunos años cualquier ingeniero pudiera abrir este
repositorio y comprender:

- cómo nació la plataforma;
- por qué se tomaron determinadas decisiones;
- cómo funciona cada componente;
- cómo ampliar el sistema;
- cómo mantenerlo de forma segura.

Si logramos eso, habremos construido algo mucho más valioso que un servidor.

Habremos construido conocimiento.


# Evolución de la Visión

La plataforma entra en una nueva etapa de evolución técnica.

Una vez consolidado el núcleo de distribución Broadcast IP y validadas las principales capacidades de streaming, el desarrollo se concentrará en la construcción del **ENGINEERING NOC (Engineering Network Operations Center)**.

El ENGINEERING NOC constituye el núcleo de ingeniería de la plataforma y tendrá como propósito proporcionar observabilidad, diagnóstico y administración integral de toda la infraestructura de distribución de video sobre redes IP.

Esta evolución no modifica la misión original del proyecto.

La fortalece.

La distribución profesional de video continúa siendo el objetivo principal, pero ahora acompañada por capacidades avanzadas de ingeniería que permitan comprender el comportamiento completo del sistema.

---

# Visión de Largo Plazo

La plataforma evolucionará siguiendo tres etapas fundamentales.

## 1. Observabilidad

Comprender completamente el comportamiento de la plataforma.

Incluye:

- Sistema Operativo
- CPU
- Memoria
- Almacenamiento
- Interfaces de red
- Servicios
- MediaMTX
- FFmpeg
- Publishers
- Readers
- Paths
- Sesiones
- Diagnósticos

El objetivo es que un ingeniero pueda conocer el estado completo de la plataforma desde una única consola.

---

## 2. Portabilidad

La plataforma deberá poder instalarse sobre diferentes infraestructuras sin modificaciones en el código fuente.

Entre ellas:

- Servidores físicos
- Máquinas virtuales
- Infraestructura local
- Nube pública
- Nube privada

Durante el proceso de instalación el sistema descubrirá automáticamente las capacidades del hardware y adaptará su funcionamiento a los recursos disponibles.

La plataforma nunca dependerá de configuraciones específicas del servidor utilizado durante el desarrollo.

---

## 3. Tolerancia a Fallos

Una vez alcanzadas la observabilidad y la portabilidad, la plataforma evolucionará hacia una arquitectura resiliente.

Esta etapa incorporará progresivamente capacidades como:

- Backup
- Mirror
- Replicación
- Health Checks
- Failover
- Recuperación automática
- Monitoreo de nodos

El objetivo será garantizar la continuidad del servicio mediante mecanismos de redundancia y recuperación controlada.

---

# Principio Rector

La plataforma deberá permitir que un ingeniero pueda diagnosticar la gran mayoría de los problemas de una infraestructura profesional de distribución Broadcast IP sin abandonar la consola del ENGINEERING NOC.

---

# Filosofía de Desarrollo

Toda nueva funcionalidad deberá fortalecer al menos una de las siguientes capacidades:

- Observabilidad
- Portabilidad
- Tolerancia a fallos

Las funcionalidades comerciales y administrativas se desarrollarán posteriormente sobre esta base técnica, preservando la estabilidad, la mantenibilidad y la escalabilidad de la plataforma.

---

> **"No estamos construyendo únicamente una plataforma para transmitir video. Estamos construyendo una plataforma de ingeniería capaz de comprender, operar, diagnosticar y garantizar la distribución profesional de video sobre redes IP."**