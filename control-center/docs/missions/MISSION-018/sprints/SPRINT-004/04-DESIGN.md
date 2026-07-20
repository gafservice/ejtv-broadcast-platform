# SPRINT-004

# Diseño de la Solución

---

# Estado

**Completado**

---

# Versión

**1.0**

---

# Fecha

Julio 2026

---

# Introducción

El diseño del Sprint-004 tiene como objetivo incorporar un mecanismo
flexible y extensible para supervisar el estado operativo de los
servicios críticos del servidor Linux.

La solución debía integrarse con la arquitectura por capas del Control
Center, evitando dependencias directas entre la API REST y las
herramientas propias del sistema operativo.

Con este enfoque, cualquier cambio futuro en el mecanismo de supervisión
podrá implementarse únicamente en la capa de infraestructura, sin afectar
el dominio ni las capas superiores.

---

# Principios de diseño

La solución fue desarrollada siguiendo los principios adoptados durante
toda la MISSION-018.

## Separación de responsabilidades

Cada capa mantiene una única responsabilidad claramente definida.

- Dominio:
  representación del modelo de monitoreo.

- Infraestructura:
  obtención de información desde Linux.

- Servicios:
  coordinación entre dominio e infraestructura.

- API REST:
  exposición de la información al cliente.

---

## Desacoplamiento

El dominio no conoce comandos Linux, procesos ni llamadas a systemd.

Toda la interacción con el sistema operativo permanece encapsulada dentro
del adaptador Linux.

Esto permite sustituir en el futuro la fuente de información sin modificar
el resto del sistema.

---

## Extensibilidad

La arquitectura fue diseñada para facilitar la incorporación de nuevos
servicios monitoreados.

Agregar un nuevo componente únicamente requiere incorporar su mecanismo
de detección dentro del adaptador correspondiente, manteniendo intactas
las demás capas.

---

## Normalización

Los diferentes mecanismos de supervisión existentes en Linux producen
información heterogénea.

El diseño introduce un conjunto de estados normalizados para representar
el estado operativo de cualquier servicio:

- Running
- Stopped
- Failed
- Unknown

Esta normalización simplifica el consumo de la información por parte del
frontend.

---

# Arquitectura implementada

El flujo de información sigue la arquitectura utilizada en todo el
Control Center.

```
              Linux
                 │
                 │
      ┌──────────────────────┐
      │ Linux Adapter        │
      │                      │
      │ systemd              │
      │ procesos             │
      └──────────┬───────────┘
                 │
                 │
      ┌──────────────────────┐
      │ SystemService        │
      └──────────┬───────────┘
                 │
                 │
      ┌──────────────────────┐
      │ API REST             │
      └──────────┬───────────┘
                 │
                 │
      GET /api/v1/system/services
                 │
                 ▼
            Frontend
```

---

# Modelo de dominio

El dominio incorpora entidades específicas para representar el monitoreo
de servicios.

## ServiceStatus

Representa el estado lógico de un servicio mediante una enumeración
normalizada.

---

## ServiceInstance

Representa una instancia individual de un proceso.

Incluye información como:

- PID
- CPU
- Memoria
- Tiempo de ejecución
- Momento de captura

---

## MonitoredService

Representa un servicio completo.

Contiene:

- nombre
- estado
- lista de instancias

---

## ServiceMonitoringSnapshot

Representa una captura completa del estado de todos los servicios
monitoreados en un instante determinado.

Este objeto constituye la respuesta principal entregada por la capa de
servicios.

---

# Adaptador Linux

El adaptador Linux concentra toda la interacción con el sistema
operativo.

Entre sus responsabilidades se encuentran:

- consultar servicios administrados por systemd;
- localizar procesos mediante PID;
- obtener consumo de CPU;
- consultar memoria utilizada;
- calcular tiempo de ejecución;
- construir los objetos del dominio.

La información obtenida nunca es expuesta directamente al resto del
backend.

---

# Capa de servicios

La capa de servicios coordina la ejecución del adaptador Linux y entrega
una representación independiente de la infraestructura.

Esta capa constituye el punto de acceso utilizado por la API REST.

---

# API REST

La API incorpora un nuevo endpoint dedicado al monitoreo de servicios.

```
GET /api/v1/system/services
```

El endpoint devuelve una captura completa del estado de los servicios
configurados utilizando el formato estándar definido para el proyecto.

---

# Beneficios del diseño

La arquitectura implementada ofrece varias ventajas.

- Bajo acoplamiento.
- Alta cohesión.
- Fácil mantenimiento.
- Facilidad para incorporar nuevos servicios.
- Independencia respecto del sistema operativo.
- Reutilización de componentes.
- Compatibilidad con futuros paneles de monitoreo.

---

# Preparación para futuros sprints

El diseño implementado permitirá incorporar nuevas capacidades sin
modificar la estructura general del backend.

Entre ellas:

- monitoreo de canales multimedia;
- monitoreo de clientes conectados;
- supervisión de transcodificación;
- alarmas automáticas;
- paneles NOC;
- métricas históricas;
- notificaciones de eventos.

---

# Documento siguiente

**05-IMPLEMENTATION.md**