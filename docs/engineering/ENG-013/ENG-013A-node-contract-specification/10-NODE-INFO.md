# 10. NodeInfo

## Introducción

El **NodeInfo** describe el entorno de ejecución de una **NodeInstance**.

Su propósito es proporcionar al **Network Operations Center (NOC)** la información necesaria para identificar dónde y cómo se encuentra ejecutándose una instancia determinada.

A diferencia del **NodeId**, que representa la identidad lógica del Node, el NodeInfo describe información propia del entorno operativo.

---

# Propósito

El propósito del NodeInfo es representar el contexto de ejecución de una NodeInstance.

Permite al NOC:

* identificar el servidor donde se ejecuta;
* conocer el sistema operativo;
* identificar la arquitectura;
* localizar la instancia;
* facilitar diagnósticos;
* apoyar tareas de operación.

NodeInfo no representa identidad lógica.

Representa información operacional del entorno.

---

# Responsabilidad

NodeInfo posee una única responsabilidad:

> Describir el entorno donde se ejecuta una NodeInstance.

No contiene:

* métricas;
* estado;
* salud;
* alarmas;
* eventos.

Estas responsabilidades pertenecen a otras entidades del dominio.

---

# Atributos

## instance_id

Identificador único de la NodeInstance.

Este identificador distingue una ejecución concreta del Node.

Ejemplo:

```text
streaming-primary
```

---

## hostname

Nombre del host donde se ejecuta la instancia.

Ejemplo:

```text
broadcast-node-01
```

---

## fqdn

Nombre de dominio completamente calificado.

Ejemplo:

```text
broadcast-node-01.company.local
```

---

## platform

Plataforma de ejecución.

Ejemplos:

```text
Bare Metal
Virtual Machine
Docker
Kubernetes
Cloud Instance
Embedded Device
```

---

## operating_system

Sistema operativo.

Ejemplo:

```text
Ubuntu Server 24.04 LTS
```

---

## kernel

Versión del kernel.

Ejemplo:

```text
Linux 6.8.0
```

---

## architecture

Arquitectura del procesador.

Ejemplos:

```text
x86_64
arm64
riscv64
```

---

## runtime

Entorno de ejecución.

Ejemplos:

```text
Python 3.13
Go 1.25
Rust 1.92
```

---

## location

Ubicación lógica de la instancia.

Ejemplos:

```text
San José
Miami
Madrid
AWS us-east-1
```

La especificación no impone un formato específico.

---

## boot_time

Momento en que inició la instancia.

No representa la creación del Node.

Representa el inicio de la ejecución actual.

---

## uptime

Tiempo continuo de operación.

Permite evaluar estabilidad operacional.

---

# Información Opcional

Las implementaciones pueden publicar información adicional.

Ejemplos:

* dirección MAC;
* direcciones IP;
* versión del BIOS;
* fabricante;
* modelo del servidor;
* número de serie del equipo;
* identificador del contenedor;
* identificador del clúster;
* zona de disponibilidad.

Toda información opcional deberá mantener compatibilidad con la especificación.

---

# Relación con Node

```text
Node
    │
    └── NodeInstance
             │
             └── NodeInfo
```

NodeInfo nunca pertenece directamente al Node.

Siempre pertenece a una NodeInstance.

---

# Relación con NodeId

NodeId responde:

> ¿Quién soy?

NodeInfo responde:

> ¿Dónde estoy ejecutándome?

Ambos conceptos son completamente independientes.

---

# Persistencia

Parte de la información contenida en NodeInfo puede cambiar durante la vida de una NodeInstance.

Ejemplos:

* dirección IP;
* uptime;
* ubicación lógica;
* plataforma de despliegue.

Estos cambios no afectan la identidad lógica del Node.

---

# Requisitos Normativos

Toda implementación compatible:

**DEBE**

* publicar un NodeInfo por cada NodeInstance;
* mantener la coherencia entre los atributos publicados;
* actualizar la información cuando cambie el entorno de ejecución.

---

**NO DEBE**

* incluir métricas en NodeInfo;
* incluir estados operacionales;
* incluir alarmas;
* incluir eventos;
* utilizar NodeInfo como mecanismo de identificación lógica.

---

**PUEDE**

* publicar atributos adicionales compatibles;
* ocultar información sensible cuando existan restricciones de seguridad;
* adaptar la información publicada según el entorno donde se ejecute la instancia.

---

# Ejemplo Conceptual

```text
Node
│
└── Instance
      │
      └── NodeInfo
            hostname: broadcast-node-01
            platform: Bare Metal
            operating_system: Ubuntu Server 24.04
            architecture: x86_64
            runtime: Python 3.13
            location: San José
```

---

# Consideraciones de Seguridad

La publicación de información del entorno debe equilibrar observabilidad y seguridad.

Las implementaciones pueden omitir o anonimizar atributos que revelen detalles sensibles de la infraestructura, siempre que dicha omisión no impida la correcta operación del NOC.

La decisión de publicar información sensible corresponde a la política de seguridad de la organización.

---

# Conclusión

NodeInfo representa el contexto operativo de una NodeInstance.

Su función es proporcionar al Network Operations Center una descripción clara y consistente del entorno donde se ejecuta la instancia, manteniendo una separación estricta entre identidad lógica, infraestructura y estado operacional.

Esta separación constituye uno de los principios fundamentales del modelo de dominio definido por la Node Contract Specification.
