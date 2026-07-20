# SPRINT-005

# Diseño

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

El Sprint-005 incorpora el primer mecanismo de integración entre el
Control Center y el servidor multimedia MediaMTX.

A diferencia de los sprints anteriores, donde la información era obtenida
directamente desde el sistema operativo Linux, este Sprint introduce una
nueva fuente de datos basada en una API HTTP.

La arquitectura propuesta mantiene la independencia entre el dominio del
Control Center y la implementación específica de MediaMTX.

---

# Objetivos del diseño

La arquitectura deberá cumplir los siguientes objetivos.

- mantener la separación entre dominio e infraestructura;
- evitar dependencias directas con MediaMTX;
- facilitar las pruebas unitarias;
- permitir la incorporación de nuevos motores multimedia;
- reutilizar la infraestructura desarrollada durante los sprints
  anteriores.

---

# Arquitectura general

El flujo completo de información será el siguiente.

```
                    MediaMTX

                        │

                HTTP REST API

                        │

                        ▼

             MediaMTX Adapter

                        │

                        ▼

              Domain Objects

                        │

                        ▼

              MediaMTX Service

                        │

                        ▼

                 REST API

                        │

                        ▼

            Dashboard / Cliente
```

Cada nivel posee una única responsabilidad.

---

# Capas de la arquitectura

## Infraestructura

Responsable de la comunicación con MediaMTX.

Funciones principales:

- realizar peticiones HTTP;
- interpretar respuestas;
- detectar errores;
- transformar JSON en objetos del dominio.

---

## Dominio

Representa el modelo conceptual del sistema multimedia.

El dominio no debe conocer:

- HTTP;
- JSON;
- Requests;
- URLs;
- MediaMTX.

El dominio únicamente representa conceptos propios del negocio.

---

## Servicios

Coordinan la interacción entre el adaptador y el dominio.

No contienen lógica relacionada con HTTP.

---

## API

Expone la información hacia clientes externos mediante endpoints REST.

---

# Organización del proyecto

La nueva estructura prevista será similar a:

```
backend/app/

├── adapters/
│   ├── base/
│   ├── linux/
│   └── mediamtx/
│
├── domain/
│   ├── system/
│   └── streaming/
│
├── services/
│
└── api/
```

---

# Adaptador MediaMTX

El adaptador será el único componente autorizado para comunicarse con
MediaMTX.

Su interfaz deberá mantenerse estable independientemente de la versión
del servidor multimedia.

Funciones previstas:

```
connect()

get_paths()

get_path()

health()

metrics()
```

En futuras versiones podrán incorporarse nuevas funciones sin modificar
el resto de la arquitectura.

---

# Modelo del dominio

El dominio utilizará entidades propias.

Ejemplo inicial:

```
MediaMTXSnapshot

MediaPath

MediaPublisher

MediaReader

MediaProtocol

MediaStatistics
```

Estas entidades representan conceptos del negocio y no estructuras JSON.

---

# Flujo de datos

```
JSON MediaMTX

↓

Adapter

↓

Entities

↓

Service

↓

REST Response
```

El formato JSON desaparecerá inmediatamente después del adaptador.

---

# Principio de desacoplamiento

El dominio nunca accederá directamente a:

```
requests.get()

http://localhost:9997

response.json()
```

Toda interacción con MediaMTX quedará encapsulada en el adaptador.

---

# Manejo de errores

El adaptador deberá controlar:

- timeout;
- servidor no disponible;
- respuestas inválidas;
- errores HTTP;
- datos incompletos.

Los errores deberán transformarse en excepciones propias del dominio.

---

# Configuración

La dirección del servidor no deberá encontrarse codificada.

Ejemplo:

```
MEDIA_MTX_URL

MEDIA_MTX_TIMEOUT
```

Estas variables podrán modificarse sin recompilar el proyecto.

---

# Escalabilidad

La arquitectura permitirá incorporar posteriormente nuevos adaptadores.

Ejemplo:

```
Linux Adapter

MediaMTX Adapter

Docker Adapter

FFmpeg Adapter

GPU Adapter

SNMP Adapter
```

Todos coexistiendo bajo el mismo modelo de servicios.

---

# Extensibilidad

El mismo diseño permitirá incorporar soporte para otros servidores
multimedia.

Ejemplos:

- Wowza Streaming Engine;
- SRS;
- Nimble Streamer;
- Flussonic.

Sin modificar el dominio.

---

# Integración con el Sprint-004

El Sprint-004 desarrolló el monitoreo del estado de los servicios Linux.

El Sprint-005 reutilizará dicha infraestructura para determinar si
MediaMTX está disponible antes de consultar su API.

De esta forma ambas funcionalidades se complementan.

---

# Consideraciones de rendimiento

La consulta a MediaMTX deberá ser ligera.

Se evitarán consultas repetitivas innecesarias.

En versiones futuras podrán incorporarse:

- caché temporal;
- polling configurable;
- actualización por eventos;
- WebSockets.

---

# Diseño para pruebas

La arquitectura deberá facilitar el uso de dobles de prueba.

Durante las pruebas unitarias será posible reemplazar el adaptador real
por implementaciones simuladas.

Esto permitirá validar la lógica del dominio sin depender de un servidor
MediaMTX en ejecución.

---

# Resultado esperado

Al finalizar el Sprint el Control Center dispondrá de una arquitectura
capaz de integrar motores multimedia mediante adaptadores
independientes, preservando la separación entre infraestructura, dominio
y servicios.

Esta arquitectura servirá como base para los siguientes módulos de
monitoreo de canales, clientes, estadísticas y eventos.

---

# Documento siguiente

**05-IMPLEMENTATION.md**