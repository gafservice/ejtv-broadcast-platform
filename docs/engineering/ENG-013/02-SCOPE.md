# ENG-013 — Scope

## Propósito

El propósito de esta ingeniería es definir e implementar la infraestructura del **Network Operations Center (NOC)** de la plataforma Broadcast.

El NOC será el sistema responsable de supervisar el estado operativo de toda la plataforma mediante una arquitectura distribuida basada en nodos y un contrato de comunicación común.

Esta ingeniería establece las bases sobre las cuales se desarrollarán todos los mecanismos de observabilidad, monitoreo y operación de la plataforma.

---

# Alcance General

ENG-013 comprende el diseño, especificación e implementación de los componentes necesarios para que cualquier servicio de la plataforma pueda integrarse al NOC utilizando un contrato estándar.

El alcance incluye tanto la definición conceptual como la implementación del núcleo del sistema y sus interfaces de operación.

---

# Componentes Incluidos

La presente ingeniería comprende los siguientes componentes.

## 1. Node Contract Specification

Definición del contrato oficial que deberán implementar todos los nodos de la plataforma.

Incluye:

* identidad del nodo;
* clasificación funcional;
* estado operativo;
* información descriptiva;
* salud del nodo;
* capacidades;
* capacidad instalada y disponible;
* métricas;
* eventos;
* alarmas;
* heartbeat;
* snapshots;
* reglas de serialización;
* versionado del contrato.

---

## 2. Node Registry

Diseño e implementación del registro central de nodos.

Será responsable de:

* registrar nodos;
* identificar nodos activos;
* mantener la información publicada;
* administrar el ciclo de vida de cada nodo.

---

## 3. NOC Core

Implementación del núcleo operacional encargado de:

* recibir información de los nodos;
* consolidar snapshots;
* calcular el estado operativo;
* administrar eventos;
* administrar alarmas;
* exponer información para los dashboards.

---

## 4. Dashboard Terminal

Desarrollo de una consola operacional basada en terminal que permita visualizar el estado de toda la plataforma en tiempo real.

---

## 5. Dashboard Web

Desarrollo de una interfaz gráfica para la supervisión y operación del sistema mediante navegador web.

---

## 6. Modelo de Observabilidad

Definición de los mecanismos comunes para representar:

* métricas;
* eventos;
* alarmas;
* capacidad;
* salud;
* estado operativo.

---

## 7. Integración con Identity

El acceso al Dashboard Web utilizará el subsistema Identity desarrollado en ENG-012.

ENG-013 consumirá los servicios de autenticación y autorización existentes sin duplicar funcionalidades relacionadas con identidad.

---

# Componentes Explícitamente Excluidos

No forman parte de ENG-013 los siguientes desarrollos.

## Identity

No se desarrollarán nuevas funcionalidades relacionadas con:

* autenticación;
* autorización;
* administración de usuarios;
* administración de roles;
* auditoría.

Estas capacidades pertenecen a ENG-012.

---

## Streaming

No forma parte de esta ingeniería la implementación interna de:

* MediaMTX;
* FFmpeg;
* ingestas;
* publicación de señales;
* protocolos multimedia.

El Streaming Node únicamente deberá publicar información mediante el Node Contract.

---

## Transcodificación

No se desarrollarán motores de codificación o transcodificación multimedia.

Los futuros nodos de transcodificación serán consumidores del contrato definido durante esta ingeniería.

---

## Automatización

No se implementarán motores de automatización, orquestación o ejecución de tareas.

Estos componentes serán desarrollados en ingenierías posteriores.

---

## Procesamiento Interno de Servicios

Cada servicio continuará siendo responsable de:

* su lógica de negocio;
* sus algoritmos;
* su persistencia;
* su configuración;
* sus procesos internos.

El NOC únicamente observará el estado publicado por dichos servicios.

---

# Límites Arquitectónicos

El NOC nunca ejecutará lógica de negocio perteneciente a otros componentes.

Su responsabilidad será exclusivamente:

* observar;
* consolidar;
* representar;
* alertar;
* registrar;
* coordinar información operacional.

Esto garantiza un bajo acoplamiento entre el NOC y el resto de la plataforma.

---

# Responsabilidades del NOC

El NOC será responsable de:

* descubrir nodos registrados;
* recibir heartbeats;
* almacenar snapshots;
* calcular el estado operativo global;
* consolidar métricas;
* administrar eventos;
* administrar alarmas;
* presentar información a los operadores.

No será responsable de modificar el comportamiento interno de los nodos.

---

# Principio de Independencia

Cada nodo podrá evolucionar de manera independiente siempre que continúe implementando el Node Contract vigente.

Como consecuencia:

* el NOC no dependerá del lenguaje de programación utilizado por cada nodo;
* el NOC no dependerá del sistema operativo donde se ejecute cada nodo;
* el NOC no dependerá del protocolo utilizado para transportar la información, siempre que el contrato permanezca inalterado.

Este principio constituye la base para una arquitectura distribuida y escalable.

---

# Resultado Esperado

Al finalizar ENG-013 existirá una infraestructura de supervisión completamente desacoplada de las implementaciones internas de la plataforma.

La incorporación de un nuevo servicio requerirá únicamente implementar el Node Contract, sin necesidad de modificar el NOC Core ni los dashboards existentes.

Esta característica garantizará la escalabilidad técnica y la evolución sostenible de la plataforma a largo plazo.
