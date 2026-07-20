# SPRINT-004

# Evidencias

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

Durante el desarrollo del Sprint-004 se obtuvieron diversas evidencias
que demuestran el correcto funcionamiento del módulo de monitoreo de
servicios implementado en el Control Center.

Las evidencias corresponden tanto a la ejecución de pruebas
automatizadas como a la validación realizada sobre el servidor Linux del
proyecto.

---

# Evidencia 1

## Compilación del backend

El proyecto compiló correctamente después de incorporar las nuevas
entidades del dominio, el adaptador Linux, la capa de servicios y el
nuevo endpoint REST.

No se presentaron errores de compilación.

Resultado:

```
Compilación exitosa
```

---

# Evidencia 2

## Ejecución de pruebas

Se ejecutó la totalidad de la suite de pruebas del backend.

Resultado obtenido:

```
==============================

60 passed

==============================
```

La ejecución confirmó que las nuevas funcionalidades no introducen
regresiones sobre componentes desarrollados en sprints anteriores.

---

# Evidencia 3

## Endpoint REST

Se verificó el correcto funcionamiento del endpoint:

```
GET /api/v1/system/services
```

La API respondió correctamente utilizando el formato estándar definido
para el proyecto.

Se comprobó la correcta serialización de:

- servicios;
- estados;
- instancias;
- métricas de procesos.

---

# Evidencia 4

## Detección de MediaMTX

El sistema identificó correctamente el estado operativo del servicio
MediaMTX.

Información validada:

- estado;
- PID;
- utilización de CPU;
- memoria;
- tiempo de ejecución.

La información obtenida coincidió con el estado observado directamente en
el servidor.

---

# Evidencia 5

## Detección de FFmpeg

El sistema verificó correctamente la existencia de procesos FFmpeg.

Cuando no existían procesos activos, el estado reportado fue coherente
con la situación observada en el servidor.

La arquitectura implementada permite detectar múltiples instancias cuando
estas se encuentren ejecutándose.

---

# Evidencia 6

## Detección del Backend

El proceso Uvicorn correspondiente al Control Center fue detectado
correctamente.

Se verificó:

- PID;
- utilización de CPU;
- memoria utilizada;
- tiempo de ejecución.

La información coincidió con la ejecución real del backend.

---

# Evidencia 7

## Integración entre capas

Se comprobó el flujo completo de información.

```
Linux
   │
   ▼
Linux Adapter
   │
   ▼
SystemService
   │
   ▼
API REST
   │
   ▼
Cliente
```

Cada capa entregó correctamente la información a la siguiente sin romper
el desacoplamiento definido por la arquitectura.

---

# Evidencia 8

## Validación sobre el servidor

Las pruebas fueron ejecutadas utilizando el servidor Linux destinado al
desarrollo de la plataforma multimedia.

La información obtenida mediante la API fue comparada con la información
reportada por las herramientas del sistema operativo.

Se verificó la consistencia entre:

- systemd;
- procesos Linux;
- objetos del dominio;
- respuesta REST.

---

# Resumen de evidencias

| Evidencia | Resultado |
|-----------|:---------:|
| Compilación | ✅ |
| Suite de pruebas | ✅ |
| Endpoint REST | ✅ |
| MediaMTX | ✅ |
| FFmpeg | ✅ |
| Backend | ✅ |
| Integración | ✅ |
| Servidor real | ✅ |

---

# Conclusiones

Las evidencias obtenidas demuestran que el Sprint-004 fue implementado y
validado satisfactoriamente.

El Control Center incorpora ahora un mecanismo confiable para supervisar
el estado operativo de los servicios críticos del servidor, manteniendo
la arquitectura desacoplada definida para el proyecto.

Esta funcionalidad constituye la base para los siguientes sprints
orientados al monitoreo de canales multimedia, clientes conectados,
procesos de transcodificación y paneles de supervisión en tiempo real.

---

# Documento siguiente

**08-CHANGELOG.md**