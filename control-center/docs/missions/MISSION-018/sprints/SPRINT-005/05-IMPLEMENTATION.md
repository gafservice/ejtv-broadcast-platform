# SPRINT-005

# Implementación

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

El Sprint-005 implementa el primer mecanismo de integración entre el
Control Center y MediaMTX mediante su API HTTP.

La implementación amplía la arquitectura desarrollada durante los
sprints anteriores incorporando un nuevo adaptador especializado para el
monitoreo del servidor multimedia.

El objetivo es transformar la información expuesta por MediaMTX en
entidades propias del dominio, manteniendo el desacoplamiento entre la
infraestructura y la lógica del negocio.

---

# Alcance de la implementación

Durante este Sprint se implementarán los siguientes componentes:

- Adaptador MediaMTX.
- Modelos del dominio.
- Servicio de aplicación.
- Endpoint REST.
- Pruebas automatizadas.
- Validación sobre el servidor real.

---

# Componentes implementados

## 1. Adaptador MediaMTX

Se desarrollará un adaptador encargado de comunicarse con la API HTTP del
servidor multimedia.

Responsabilidades:

- establecer comunicación HTTP;
- consultar la API;
- interpretar respuestas;
- detectar errores;
- convertir JSON en entidades del dominio.

La implementación deberá evitar que el resto del sistema conozca la
estructura interna de MediaMTX.

---

## 2. Configuración

La dirección del servidor y demás parámetros de conexión deberán
obtenerse mediante configuración.

Ejemplo:

```
MEDIA_MTX_URL
MEDIA_MTX_TIMEOUT
```

No deberán existir direcciones codificadas dentro del código fuente.

---

## 3. Consulta de la API

La implementación deberá consultar inicialmente el endpoint:

```
GET /v3/paths/list
```

El objetivo será recuperar el estado de todos los `paths`
administrados por MediaMTX.

---

## 4. Transformación de datos

Las respuestas obtenidas desde MediaMTX serán convertidas en objetos del
dominio.

La conversión deberá realizarse inmediatamente después de recibir la
respuesta HTTP.

Ninguna estructura JSON deberá propagarse hacia las capas superiores.

---

## 5. Modelado del dominio

Durante este Sprint se implementarán las entidades necesarias para
representar el estado del servidor multimedia.

Entre ellas:

- MediaMTXSnapshot;
- MediaPath;
- MediaPublisher;
- MediaReader;
- MediaProtocol;
- MediaStatistics.

Los nombres definitivos podrán ajustarse durante la implementación.

---

## 6. Servicio de aplicación

Se implementará un servicio responsable de coordinar la interacción entre
el adaptador y el dominio.

Sus responsabilidades serán:

- consultar el adaptador;
- validar la información;
- construir el modelo del dominio;
- devolver un Snapshot consistente.

---

## 7. API REST

Se publicará un nuevo endpoint para consultar el estado del servidor
multimedia.

El endpoint devolverá información normalizada utilizando el mismo formato
empleado en el resto del Control Center.

---

## 8. Manejo de errores

La implementación contemplará:

- servidor no disponible;
- timeout;
- errores HTTP;
- respuestas inválidas;
- estructuras incompletas.

El Control Center deberá continuar funcionando aun cuando MediaMTX no se
encuentre disponible.

---

## 9. Registro de eventos

Las condiciones de error deberán registrarse mediante el sistema de
logging existente.

Esto facilitará las tareas de diagnóstico y mantenimiento.

---

## 10. Integración con el Sprint-004

Antes de consultar la API HTTP se verificará el estado del servicio
MediaMTX utilizando la infraestructura desarrollada durante el
Sprint-004.

De esta manera se evitarán consultas innecesarias cuando el servicio se
encuentre detenido.

---

# Flujo de implementación

```
MediaMTX

↓

HTTP GET

↓

MediaMTX Adapter

↓

JSON

↓

Domain Objects

↓

MediaMTX Service

↓

REST API

↓

Cliente
```

---

# Principios aplicados

La implementación respetará los siguientes principios:

- responsabilidad única;
- separación por capas;
- independencia del dominio;
- bajo acoplamiento;
- alta cohesión;
- inversión de dependencias;
- facilidad de prueba.

---

# Consideraciones de mantenimiento

La estructura implementada permitirá incorporar posteriormente nuevas
consultas a la API de MediaMTX sin modificar el resto de la aplicación.

Entre ellas:

- sesiones;
- métricas;
- configuración;
- estadísticas;
- clientes conectados;
- protocolos;
- eventos.

---

# Resultado esperado

Al finalizar la implementación el Control Center será capaz de consultar
el estado operativo de los `paths` administrados por MediaMTX y exponer
dicha información mediante una API REST desacoplada del formato interno
del servidor multimedia.

---

# Estado de avance

| Componente | Estado |
|------------|:------:|
| Adaptador MediaMTX | ⏳ |
| Configuración | ⏳ |
| Dominio | ⏳ |
| Servicio | ⏳ |
| Endpoint REST | ⏳ |
| Manejo de errores | ⏳ |
| Pruebas | ⏳ |
| Validación | ⏳ |

---

# Observaciones

Este documento será actualizado durante el desarrollo del Sprint para
reflejar la implementación final de cada componente.

---

# Documento siguiente

**06-TESTS.md**