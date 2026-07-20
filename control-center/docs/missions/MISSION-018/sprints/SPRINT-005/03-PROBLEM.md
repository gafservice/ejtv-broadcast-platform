# SPRINT-005

# Problema

---

# Estado

**En desarrollo**

---

# Versión

**1.0**

---

# Fecha

Julio 2026

---

# Introducción

El Control Center nació con el propósito de supervisar la infraestructura
que soporta la plataforma de distribución multimedia.

Durante los primeros sprints de la MISSION-018 se incorporó el monitoreo
de recursos del sistema operativo y de los principales servicios Linux,
permitiendo conocer el estado general del servidor.

Sin embargo, el estado de un servicio no refleja necesariamente el estado
operativo del sistema multimedia que administra.

En consecuencia, aún existe una diferencia importante entre conocer que
MediaMTX está ejecutándose y conocer si la plataforma realmente está
transportando contenido audiovisual.

---

# Descripción del problema

MediaMTX es el componente encargado de administrar los flujos multimedia
de la plataforma.

Cada canal distribuido por el servidor es representado mediante un
`path`, el cual puede encontrarse en diferentes estados operativos.

Desde la perspectiva del sistema operativo, MediaMTX puede aparecer como
un servicio completamente funcional, mientras que internamente todos sus
canales podrían encontrarse sin señal o sin clientes conectados.

Por esta razón, el monitoreo realizado hasta el Sprint-004 resulta
insuficiente para determinar la disponibilidad real del servicio de
streaming.

---

# Limitaciones del monitoreo actual

Actualmente el Control Center puede responder preguntas como:

- ¿Está MediaMTX ejecutándose?
- ¿Cuál es el PID del proceso?
- ¿Cuánta memoria consume?
- ¿Qué porcentaje de CPU utiliza?
- ¿Cuánto tiempo lleva en ejecución?

Estas métricas describen únicamente el estado del proceso dentro del
sistema operativo.

No permiten conocer:

- qué canales existen;
- cuáles están transmitiendo;
- cuáles no tienen señal;
- cuántos clientes están conectados;
- qué protocolo utiliza cada canal;
- si un productor dejó de transmitir.

---

# Ejemplo del problema

Supóngase la siguiente situación.

El servicio MediaMTX permanece ejecutándose durante varios días sin
presentar fallos.

```
MediaMTX

Running

CPU ............ 3 %

RAM ............ 90 MB
```

Desde la perspectiva del sistema operativo, el servicio funciona
correctamente.

Sin embargo, internamente ocurre lo siguiente.

```
Path              Estado

enlace            Sin Publisher

canal-1           Sin Publisher

canal-2           Sin Publisher

backup            Sin Publisher
```

En este escenario ningún canal está recibiendo contenido.

Aunque el servidor continúa activo, la plataforma de distribución
multimedia no está prestando el servicio esperado.

El monitoreo implementado hasta el Sprint-004 no posee la capacidad de
detectar esta condición.

---

# Consecuencias

La ausencia de monitoreo funcional puede provocar:

- interrupciones de transmisión no detectadas;
- canales fuera de servicio;
- pérdida de contenido;
- retraso en la respuesta del operador;
- disminución de la disponibilidad del servicio;
- afectación de clientes conectados.

---

# Causa principal

El problema se origina porque el monitoreo actual observa únicamente el
estado del proceso Linux.

No existe una integración con la API interna de MediaMTX que permita
consultar la información operativa del servidor multimedia.

Como consecuencia, el Control Center carece de visibilidad sobre el
estado real de los flujos administrados por MediaMTX.

---

# Necesidad del Sprint

Para convertir el Control Center en una plataforma de supervisión
operativa es necesario incorporar un mecanismo capaz de consultar la API
de MediaMTX.

Esta integración permitirá conocer información que el sistema operativo
no puede proporcionar.

Entre ella:

- listado de `paths`;
- productores activos;
- lectores conectados;
- protocolos utilizados;
- estados internos;
- información específica del servidor multimedia.

---

# Restricciones

La solución debe cumplir varias condiciones.

## Independencia tecnológica

El dominio del Control Center no debe depender directamente del formato
JSON utilizado por MediaMTX.

---

## Desacoplamiento

La lógica del negocio no debe contener llamadas HTTP directas.

---

## Escalabilidad

La arquitectura debe permitir incorporar nuevos motores multimedia sin
modificar el dominio existente.

---

## Robustez

Errores de comunicación con MediaMTX no deben afectar el funcionamiento
general del Control Center.

---

# Riesgos

Durante la implementación deberán considerarse riesgos como:

- API no disponible;
- cambios de versión de MediaMTX;
- respuestas incompletas;
- pérdida temporal de conectividad;
- tiempos de espera elevados;
- errores de autenticación en futuras versiones.

---

# Estrategia de solución

Para resolver el problema se propone introducir una nueva capa de
integración especializada.

```
MediaMTX
      │
      ▼
MediaMTX Adapter
      │
      ▼
Domain Models
      │
      ▼
Application Services
      │
      ▼
REST API
      │
      ▼
Dashboard
```

El adaptador será el único componente responsable de interpretar la API
del servidor multimedia.

El resto del sistema trabajará exclusivamente con entidades propias del
dominio.

---

# Beneficios esperados

La incorporación del monitoreo de `paths` permitirá:

- conocer el estado real de los canales;
- detectar fallos antes de que sean reportados por los usuarios;
- construir paneles NOC en tiempo real;
- generar estadísticas operativas;
- incorporar sistemas de alertas;
- facilitar futuras tareas de administración.

---

# Relación con la MISSION-018

El Sprint-005 representa la transición entre el monitoreo del sistema
operativo y el monitoreo funcional del motor multimedia.

Mientras los sprints anteriores se enfocaron en la infraestructura, este
Sprint comienza a supervisar directamente el servicio que constituye el
núcleo de la plataforma de distribución.

Este cambio amplía significativamente la capacidad del Control Center y
establece la base para los siguientes módulos de monitoreo y operación.

---

# Conclusiones

El problema identificado demuestra que el monitoreo del sistema operativo
es una condición necesaria, pero no suficiente para garantizar la
disponibilidad de una plataforma multimedia.

La incorporación de un módulo especializado para consultar la API de
MediaMTX permitirá al Control Center obtener una visión integral del
estado operativo de los canales administrados por el servidor y avanzar
hacia un sistema de supervisión profesional.

---

# Documento siguiente

**04-DESIGN.md**