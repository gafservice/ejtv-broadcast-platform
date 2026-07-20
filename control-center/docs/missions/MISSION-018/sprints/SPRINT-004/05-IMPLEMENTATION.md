# SPRINT-004

# Implementación

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

El Sprint-004 incorpora al Control Center la capacidad de supervisar el
estado operativo de los principales servicios que conforman la
infraestructura multimedia.

La implementación fue realizada respetando la arquitectura por capas del
proyecto, manteniendo completamente desacopladas las responsabilidades de
dominio, infraestructura, servicios y API REST.

La información obtenida desde el sistema operativo es transformada en
objetos del dominio antes de ser expuesta mediante la interfaz REST.

---

# Componentes implementados

La implementación se dividió en cuatro áreas principales:

- Dominio
- Infraestructura
- Servicios
- API REST

---

# Dominio

Se incorporaron nuevas entidades para representar el monitoreo de
servicios.

## ServiceStatus

Se implementó una enumeración para representar el estado lógico de cada
servicio.

Estados soportados:

- Running
- Stopped
- Failed
- Unknown

Esta abstracción evita que el resto del sistema dependa directamente de
los estados propios de systemd o del sistema operativo.

---

## ServiceInstance

Representa una instancia individual de un proceso.

Información almacenada:

- PID
- utilización de CPU
- memoria utilizada
- tiempo de ejecución
- instante de captura

Esta entidad permite representar servicios que poseen múltiples procesos
activos.

---

## MonitoredService

Representa un servicio completo.

Cada objeto contiene:

- nombre del servicio;
- estado operativo;
- colección de instancias detectadas.

---

## ServiceMonitoringSnapshot

Representa una captura completa del estado del sistema en un momento
determinado.

Este objeto constituye la respuesta principal utilizada por la capa de
servicios y posteriormente por la API REST.

---

# Infraestructura

La capa de infraestructura fue ampliada mediante el adaptador Linux.

El adaptador concentra toda la interacción con el sistema operativo.

Sus responsabilidades incluyen:

- consultar servicios administrados por systemd;
- localizar procesos activos;
- obtener PID;
- medir utilización de CPU;
- consultar memoria utilizada;
- calcular tiempo de ejecución;
- construir objetos del dominio.

Con este enfoque ninguna otra capa necesita conocer comandos Linux.

---

# Servicios monitoreados

Durante este sprint se incorporó soporte para los siguientes servicios.

## MediaMTX

La detección se realiza mediante systemd.

Información obtenida:

- estado;
- PID;
- tiempo de ejecución;
- utilización de recursos.

---

## FFmpeg

La detección se realiza mediante búsqueda de procesos activos.

El sistema permite identificar la presencia o ausencia de procesos
FFmpeg y obtener información de cada instancia encontrada.

---

## Control Center Backend

El backend es detectado mediante el proceso Uvicorn.

La implementación permite conocer si el servicio REST permanece
ejecutándose y cuáles son sus características de ejecución.

---

# Capa de servicios

Se amplió la clase **SystemService** incorporando un nuevo método
responsable de coordinar el monitoreo.

Nuevo método:

```
get_service_monitoring()
```

Este método invoca el adaptador Linux, construye el objeto
ServiceMonitoringSnapshot y retorna una representación independiente del
sistema operativo.

---

# API REST

Se incorporó un nuevo endpoint para consultar el estado operativo de los
servicios.

```
GET /api/v1/system/services
```

La respuesta mantiene el mismo formato utilizado por el resto de la API,
garantizando consistencia entre todos los endpoints del proyecto.

---

# Flujo de ejecución

La secuencia implementada es la siguiente.

```
Cliente REST
      │
      ▼
GET /api/v1/system/services
      │
      ▼
System Router
      │
      ▼
SystemService
      │
      ▼
Linux Adapter
      │
      ├── systemd
      └── procesos Linux
      │
      ▼
Objetos del Dominio
      │
      ▼
Respuesta JSON
```

---

# Pruebas implementadas

La implementación fue acompañada por nuevas pruebas automatizadas.

Se incorporaron pruebas para:

- entidades del dominio;
- adaptador Linux;
- capa de servicios;
- API REST;
- integración completa.

Estas pruebas verifican tanto la correcta construcción de los objetos del
dominio como el funcionamiento del endpoint REST.

---

# Validación sobre el servidor

La implementación fue ejecutada sobre el servidor Linux utilizado durante
el desarrollo del proyecto.

Las pruebas confirmaron la correcta detección de:

- MediaMTX en ejecución;
- Backend del Control Center;
- procesos FFmpeg activos o detenidos;
- consumo de recursos por proceso.

Los resultados obtenidos coincidieron con el estado real observado en el
servidor.

---

# Resultado de implementación

Con este sprint el Control Center deja de limitarse a consultar recursos
del sistema y adquiere la capacidad de supervisar el estado operativo de
los servicios críticos de la plataforma.

Esta funcionalidad constituye la base para la incorporación de módulos de
monitoreo más avanzados durante los siguientes sprints.

---

# Documento siguiente

**06-TESTS.md**