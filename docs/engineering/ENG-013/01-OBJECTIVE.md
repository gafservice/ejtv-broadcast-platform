# ENG-013 — Objective

## Objetivo General

Diseñar e implementar la arquitectura completa del **Network Operations Center (NOC)** de la plataforma Broadcast, estableciendo un modelo distribuido basado en nodos capaces de publicar su estado mediante un contrato de comunicación común, independiente de su implementación interna.

El resultado será una infraestructura de monitoreo unificada, escalable y extensible, preparada para supervisar todos los componentes presentes y futuros de la plataforma.

---

# Objetivos Específicos

Durante la ingeniería ENG-013 se desarrollarán los siguientes objetivos específicos:

## 1. Definir el Node Contract

Diseñar una especificación canónica que establezca el lenguaje común utilizado por todos los nodos de la plataforma.

Esta especificación deberá definir:

* identidad del nodo;
* clasificación funcional;
* estado operativo;
* información descriptiva;
* salud del nodo;
* capacidades;
* capacidad disponible;
* métricas;
* eventos;
* alarmas;
* heartbeat;
* snapshots;
* reglas de serialización;
* versionado del contrato.

---

## 2. Implementar el NOC Core

Desarrollar el núcleo del sistema encargado de:

* registrar nodos;
* recibir información publicada;
* mantener el estado operativo global;
* administrar eventos;
* administrar alarmas;
* consolidar métricas;
* exponer información para los dashboards.

---

## 3. Desarrollar el Dashboard Terminal

Construir una consola operacional basada en terminal que permita visualizar en tiempo real el estado de toda la plataforma.

Entre otras funciones deberá mostrar:

* estado de cada nodo;
* utilización de recursos;
* alarmas activas;
* eventos recientes;
* capacidad instalada;
* salud general de la infraestructura.

---

## 4. Desarrollar el Dashboard Web

Implementar una interfaz gráfica que permita operar el NOC desde un navegador web.

El Dashboard Web deberá consumir exclusivamente la información publicada por el NOC Core, sin depender de implementaciones específicas de los nodos.

---

# Alcance

ENG-013 comprende el diseño e implementación de toda la infraestructura de supervisión de la plataforma.

Incluye:

* especificación del contrato común;
* arquitectura distribuida basada en nodos;
* procesamiento de métricas;
* administración de eventos;
* administración de alarmas;
* cálculo del estado operativo;
* dashboards de operación.

---

# Fuera del Alcance

La presente ingeniería no contempla el desarrollo funcional interno de los distintos servicios de negocio.

No forma parte de ENG-013 el desarrollo de:

* Identity (ENG-012);
* motores de streaming;
* transcodificación multimedia;
* automatizaciones de negocio;
* procesamiento interno de métricas;
* lógica específica de cada nodo.

Cada uno de estos servicios únicamente deberá implementar el contrato definido durante esta ingeniería.

---

# Criterios de Éxito

La ingeniería será considerada completada cuando:

* exista una especificación oficial del Node Contract;
* cualquier nodo pueda integrarse implementando únicamente dicho contrato;
* el NOC Core pueda registrar y supervisar múltiples nodos simultáneamente;
* los dashboards representen el estado de la plataforma utilizando exclusivamente información publicada mediante el contrato;
* la incorporación de un nuevo tipo de nodo no requiera modificaciones en la arquitectura del NOC.

---

# Principio Rector

El NOC no monitorea aplicaciones.

El NOC monitorea nodos.

Todo componente que desee formar parte de la plataforma deberá comportarse como un Node e implementar el contrato común definido por ENG-013.

Este principio constituye el fundamento arquitectónico de toda la ingeniería.
