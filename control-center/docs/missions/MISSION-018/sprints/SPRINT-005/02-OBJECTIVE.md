# SPRINT-005

# Objetivos

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

El Sprint-005 marca el inicio del monitoreo del motor multimedia de la
plataforma.

Hasta este punto, el Control Center ha demostrado la capacidad de
supervisar la infraestructura del servidor Linux y los servicios
principales del sistema.

Sin embargo, el objetivo de una plataforma de distribución multimedia no
es únicamente conocer si un servicio está en ejecución, sino comprender
el estado operativo de los canales administrados por dicho servicio.

Este sprint incorpora la primera etapa del monitoreo funcional de
MediaMTX.

---

# Objetivo general

Diseñar e implementar un módulo especializado para consultar el estado
operativo de los `paths` administrados por MediaMTX, transformando la
información obtenida mediante su API HTTP en entidades propias del
dominio del Control Center.

---

# Objetivos específicos

## 1. Diseñar la integración con MediaMTX

Definir una arquitectura desacoplada que permita consultar la API de
MediaMTX sin introducir dependencias directas entre el dominio del
Control Center y la estructura interna del servidor multimedia.

---

## 2. Implementar un adaptador especializado

Desarrollar un adaptador responsable de establecer comunicación con la
API HTTP de MediaMTX.

El adaptador deberá:

- establecer la conexión;
- realizar consultas HTTP;
- interpretar respuestas;
- detectar errores;
- traducir la información hacia el dominio interno.

---

## 3. Modelar el dominio multimedia

Definir entidades que representen los conceptos principales del sistema
de distribución multimedia.

Entre ellos:

- Snapshot del servidor;
- Path;
- Estado del Path;
- Publisher;
- Reader;
- Protocolo;
- Estadísticas.

Estas entidades deberán ser independientes del formato JSON utilizado por
MediaMTX.

---

## 4. Obtener la lista de paths

Consultar la API del servidor para recuperar todos los `paths`
registrados.

Cada `path` deberá contener información suficiente para determinar su
estado operativo.

---

## 5. Determinar el estado operativo

Analizar la información recibida para clasificar cada `path` según su
condición real.

Ejemplos:

- activo;
- sin productor;
- sin lectores;
- inactivo;
- error.

---

## 6. Identificar productores

Detectar la existencia de un productor activo para cada `path`.

El Control Center deberá distinguir claramente entre:

- un canal existente;
- un canal configurado;
- un canal transmitiendo.

---

## 7. Identificar lectores

Determinar cuántos clientes consumen cada flujo multimedia.

Esta información permitirá construir futuras estadísticas de utilización
del sistema.

---

## 8. Identificar protocolos

Detectar el protocolo utilizado por el origen del flujo.

Entre ellos:

- UDP;
- RTSP;
- RTMP;
- SRT;
- WebRTC;
- HLS.

---

## 9. Publicar un servicio de aplicación

Implementar una capa de servicios responsable de coordinar la consulta al
adaptador y construir un modelo de dominio consistente.

---

## 10. Exponer una API REST

Publicar un endpoint que permita consultar el estado operativo del motor
multimedia desde cualquier cliente autorizado.

La API deberá mantener el mismo estilo utilizado en los sprints
anteriores.

---

## 11. Incorporar manejo de errores

El sistema deberá detectar condiciones como:

- MediaMTX detenido;
- API no disponible;
- timeout;
- respuesta inválida;
- errores de comunicación.

Sin comprometer la estabilidad del Control Center.

---

## 12. Implementar pruebas automatizadas

Desarrollar pruebas unitarias para:

- entidades;
- adaptadores;
- servicios;
- API REST.

---

## 13. Validar sobre el servidor real

Ejecutar pruebas utilizando el servidor multimedia del proyecto.

La validación deberá confirmar que la información obtenida coincide con
el estado real observado en MediaMTX.

---

## 14. Mantener la arquitectura limpia

Toda la implementación deberá respetar los principios establecidos en la
MISSION-018:

- separación por capas;
- inversión de dependencias;
- responsabilidad única;
- independencia del dominio;
- alta cohesión;
- bajo acoplamiento.

---

# Objetivos técnicos

Al finalizar el Sprint deberán existir los siguientes componentes.

## Dominio

- entidades multimedia;
- enumeraciones;
- modelos de estado.

---

## Adaptadores

Nuevo adaptador:

```
MediaMTXAdapter
```

---

## Servicios

Nueva capa de servicio:

```
MediaMTXService
```

---

## API

Nuevo endpoint REST.

---

## Testing

Pruebas unitarias.

Pruebas de integración.

Validación real.

---

## Documentación

Actualización completa de la documentación técnica del Sprint.

---

# Objetivos de calidad

La implementación deberá cumplir:

- código legible;
- tipado consistente;
- documentación completa;
- pruebas automatizadas;
- manejo de excepciones;
- reutilización de componentes;
- facilidad de mantenimiento.

---

# Objetivos de escalabilidad

La arquitectura deberá permitir incorporar posteriormente soporte para
otros servidores multimedia.

Ejemplos:

- Wowza Streaming Engine;
- SRS;
- Nimble Streamer;
- Flussonic;
- servidores propietarios.

La incorporación de nuevos motores no deberá requerir modificaciones en
el dominio del Control Center.

---

# Objetivos de negocio

Desde la perspectiva del producto, este Sprint representa el primer paso
hacia un sistema de supervisión multimedia capaz de operar en entornos de
producción.

La información obtenida permitirá construir futuras funcionalidades como:

- paneles NOC;
- monitoreo en tiempo real;
- alertas automáticas;
- estadísticas;
- auditoría de canales;
- supervisión remota;
- administración centralizada.

---

# Resultado esperado

Al finalizar el Sprint, el Control Center deberá responder preguntas como:

- ¿Qué canales existen?
- ¿Cuáles están transmitiendo?
- ¿Cuántos clientes están conectados?
- ¿Qué protocolo utiliza cada canal?
- ¿Existe algún canal sin señal?
- ¿MediaMTX responde correctamente?

---

# Indicadores de éxito

El Sprint será considerado exitoso cuando:

- todos los `paths` puedan consultarse mediante la API;
- la información sea convertida correctamente al dominio;
- exista un endpoint REST funcional;
- las pruebas automatizadas sean satisfactorias;
- la validación sobre el servidor real sea exitosa;
- la documentación técnica esté completa;
- el Sprint pueda cerrarse mediante un nuevo commit del proyecto.

---

# Documento siguiente

**03-PROBLEM.md**   