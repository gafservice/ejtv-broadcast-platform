# ARCHITECTURE — MISSION-018

**Misión:** MISSION-018

**Nombre:** Network Operations Center (NOC) Web

**Estado:** En desarrollo

---

# 1. Introducción

La MISSION-018 implementa el **Network Operations Center (NOC)** de la plataforma de distribución de video.

Su objetivo es proporcionar una interfaz unificada para supervisar el estado operativo del servidor, los recursos del sistema, los servicios internos y la infraestructura de streaming en tiempo real.

La arquitectura fue diseñada bajo principios de modularidad, separación de responsabilidades y escalabilidad, permitiendo incorporar nuevas capacidades sin afectar los componentes existentes.

---

# 2. Objetivos Arquitectónicos

- Centralizar el monitoreo operacional.
- Desacoplar la lógica de negocio de la infraestructura.
- Facilitar la incorporación de nuevos paneles.
- Integrar métricas reales del sistema.
- Integrar MediaMTX mediante adaptadores.
- Preparar la plataforma para un Dashboard Web.
- Mantener una arquitectura orientada a dominio.

---

# 3. Arquitectura General

```
                     +----------------------------+
                     |        Dashboard Web       |
                     +-------------+--------------+
                                   |
                              REST API
                                   |
                     +-------------v--------------+
                     | Dashboard Application      |
                     +-------------+--------------+
                                   |
                 +-----------------+------------------+
                 |                 |                  |
                 |                 |                  |
          Dashboard Service   Session Service   System Service
                 |                 |                  |
         +-------+------+     +----+-----+      +-----+------+
         |              |     |          |      |            |
      Domain        Renderers Models  MediaMTX  System Metrics
                                   |
                              MediaMTX API
                                   |
                            Streaming Server
```

---

# 4. Capas del Sistema

La arquitectura está organizada en capas claramente definidas.

## Presentación

Responsable de mostrar la información al operador.

Incluye:

- Dashboard Terminal.
- Dashboard Web.
- Paneles especializados.
- Renderizadores.

---

## Aplicación

Coordina los casos de uso del sistema.

Responsabilidades:

- Orquestación.
- Actualización del Dashboard.
- Integración entre dominios.
- Construcción del modelo presentado al operador.

---

## Dominio

Contiene la lógica de negocio.

Dominios actuales:

- Sistema.
- Streaming.
- Sesiones.
- Dashboard.

Cada dominio mantiene independencia respecto a la infraestructura.

---

## Adaptadores

Permiten integrar servicios externos.

Actualmente existen adaptadores para:

- MediaMTX.
- Sistema operativo.
- API REST.

Los adaptadores aíslan el resto del sistema de cambios en las implementaciones externas.

---

# 5. Dashboard

El Dashboard está construido mediante paneles independientes.

Cada panel posee:

- Modelo.
- Renderer.
- Servicios asociados.

Esto permite agregar nuevos paneles sin modificar los existentes.

Paneles actuales:

- CPU.
- Memoria.
- Disco.
- Interfaces de red.
- Throughput.
- Uptime.
- Servicios.
- Streaming.
- Clientes activos.
- Sesiones.

---

# 6. Arquitectura del Dominio

## Dominio Sistema

Responsable de recopilar métricas del servidor.

Incluye:

- CPU.
- Memoria.
- Disco.
- Red.
- Interfaces.
- Uptime.

---

## Dominio Streaming

Gestiona el estado operativo de la infraestructura de streaming.

Incluye:

- Paths.
- Publishers.
- Readers.
- Health.
- Protocolos.

---

## Dominio Sessions

Representa las conexiones activas de clientes.

Modela:

- Cliente.
- Protocolo.
- Calidad.
- Bitrate.
- Estado.
- Tiempo de conexión.

---

## Dominio Dashboard

Consolida toda la información proveniente de los demás dominios para generar una única vista operacional.

---

# 7. Integración con MediaMTX

La comunicación con MediaMTX se realiza mediante adaptadores especializados.

Información obtenida:

- Clientes activos.
- Sesiones.
- Métricas.
- Estado de los paths.
- Información Prometheus.
- Estado general del servidor.

Esta integración desacopla el Dashboard de la implementación específica del servidor de streaming.

---

# 8. REST API

La misión incorpora la base de la API REST.

Objetivos:

- Servir información al Dashboard Web.
- Permitir integraciones externas.
- Facilitar automatización.
- Soportar futuras aplicaciones móviles.

---

# 9. Flujo General de Datos

```
Servidor Linux
        │
        │
MediaMTX
        │
        ▼
Adaptadores
        │
        ▼
Dominios
        │
        ▼
Servicios
        │
        ▼
Dashboard Application
        │
        ▼
REST API
        │
        ▼
Dashboard Terminal
Dashboard Web
```

---

# 10. Principios de Diseño

La arquitectura sigue los siguientes principios:

- Separación de responsabilidades.
- Arquitectura por capas.
- Orientación al dominio.
- Bajo acoplamiento.
- Alta cohesión.
- Modularidad.
- Escalabilidad.
- Testabilidad.
- Evolución incremental.

---

# 11. Estado Actual

Actualmente la arquitectura permite:

- Supervisar recursos del sistema.
- Monitorear servicios.
- Obtener métricas reales.
- Visualizar sesiones activas.
- Integrar MediaMTX.
- Presentar información en Dashboard Terminal.
- Exponer información mediante REST API.

La base arquitectónica se considera preparada para la evolución del Dashboard Web.

---

# 12. Evolución Prevista

Las siguientes capacidades ampliarán la arquitectura:

- Identity.
- Alarm Management.
- Event Management.
- Reporting.
- Analytics.
- Automatización.
- IA aplicada a operaciones.
- Dashboard Web completo.

Todas estas capacidades reutilizarán la arquitectura establecida en esta misión.

---

# 13. Referencias

- README.md
- TIMELINE.md
- CHANGELOG.md
- DECISIONS.md
- docs/engineering/
- docs/architecture/
- docs/decisions/