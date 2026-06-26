# Visión General del Sistema

> *"Antes de comprender cada componente, primero debemos comprender el sistema completo."*

---

# Introducción

Todo sistema complejo resulta más fácil de comprender cuando primero se observa
desde una perspectiva general.

Intentar estudiar cada componente de manera aislada suele dificultar la
comprensión de la plataforma y hace más complicado entender la relación que
existe entre los diferentes servicios.

Por esta razón, antes de profundizar en aspectos como la instalación del
sistema operativo, la configuración de la red o la implementación de los
distintos servicios, es importante comprender cómo funciona la plataforma en su
conjunto.

Este documento presenta una visión general de **EJTV Broadcast Platform** y
describe el recorrido que realiza un flujo audiovisual desde que ingresa al
servidor hasta que es entregado a un operador autorizado.

---

# ¿Qué es EJTV Broadcast Platform?

EJTV Broadcast Platform es una plataforma diseñada para recibir, administrar y
distribuir contenido audiovisual utilizando infraestructura basada en redes IP.

Su objetivo consiste en reemplazar el modelo tradicional de distribución
mediante enlaces satelitales por una arquitectura moderna, abierta y
completamente documentada.

La plataforma ha sido diseñada para operar de forma continua, ofrecer altos
niveles de disponibilidad y facilitar el mantenimiento mediante una
arquitectura modular.

Durante la primera etapa del proyecto la distribución se realizará utilizando
el protocolo **SRT (Secure Reliable Transport)**.

En el futuro podrán incorporarse otros protocolos sin modificar la filosofía
general de la plataforma.

---

# Nuestro objetivo

La plataforma tiene una única responsabilidad.

Recibir contenido audiovisual ya codificado.

Administrarlo de forma segura.

Distribuirlo hacia operadores autorizados.

Nada más.

Una decisión importante del proyecto consiste en no utilizar el servidor para
realizar procesos de codificación o transcodificación.

Estas tareas ya son ejecutadas por equipos especializados que forman parte de
la infraestructura de producción.

Esta decisión permite reducir considerablemente el consumo de recursos y mejora
la estabilidad del sistema.

---

# Componentes principales

Desde una perspectiva funcional, la plataforma está formada por seis grandes
componentes.

## Fuente de contenido

Corresponde al origen de la señal audiovisual.

Puede tratarse de un codificador profesional, un equipo Magewell o cualquier
otro dispositivo capaz de generar un flujo SRT compatible con la plataforma.

---

## Servidor EJTV

Constituye el núcleo operativo de la plataforma.

Su responsabilidad consiste en recibir los diferentes flujos audiovisuales,
administrarlos y ponerlos a disposición de los clientes autorizados.

Durante este proyecto utilizaremos una estación de trabajo Apple Mac Pro 5,1
equipada con Ubuntu LTS como sistema operativo.

---

## Plataforma de distribución

Sobre el servidor se ejecutarán los servicios responsables de administrar y
distribuir los flujos audiovisuales.

Cada servicio cumplirá una función específica dentro de la arquitectura.

La filosofía del proyecto consiste en evitar que un mismo componente asuma
múltiples responsabilidades.

---

## Seguridad

Todos los accesos hacia la plataforma serán controlados mediante mecanismos de
autenticación y políticas de seguridad.

El objetivo consiste en garantizar que únicamente operadores previamente
autorizados puedan acceder al contenido distribuido.

---

## Monitoreo

La plataforma incorporará herramientas que permitirán supervisar
permanentemente el estado del servidor, los servicios y la disponibilidad de
los flujos audiovisuales.

El monitoreo constituye una herramienta fundamental para garantizar la
continuidad del servicio.

---

## Clientes

Finalmente, los operadores de televisión por cable establecerán conexión con
la plataforma para recibir los diferentes canales disponibles.

Cada cliente accederá únicamente a los recursos para los cuales haya sido
autorizado.

---

# Flujo general de operación

El funcionamiento de la plataforma puede resumirse mediante el siguiente
recorrido.

```text
                 Fuente de contenido
                         │
                         ▼
               Recepción del flujo SRT
                         │
                         ▼
                 Servidor EJTV
                         │
                         ▼
              Administración del servicio
                         │
                         ▼
               Control de acceso y seguridad
                         │
                         ▼
               Distribución mediante SRT
                         │
                         ▼
          Operadores de televisión por cable
```

Este flujo representa el comportamiento general de la plataforma y servirá
como referencia para comprender los documentos técnicos que se desarrollarán en
los capítulos siguientes.

---

# Filosofía de operación

La plataforma ha sido diseñada siguiendo una idea muy sencilla.

Cada componente realiza únicamente la función para la cual fue incorporado.

Esta filosofía permite reducir la complejidad del sistema y facilita su
mantenimiento.

Como consecuencia, el servidor no realizará tareas que correspondan a otros
equipos de la infraestructura audiovisual.

Esta separación de responsabilidades constituye uno de los principios
fundamentales de EJTV Broadcast Platform.

---

# Evolución de la plataforma

Aunque la primera versión se concentrará exclusivamente en la distribución de
contenido mediante SRT, la arquitectura ha sido diseñada para facilitar su
crecimiento.

En futuras etapas podrán incorporarse nuevos protocolos, herramientas de
monitoreo, mecanismos avanzados de seguridad y funciones de administración sin
modificar la estructura general del sistema.

Esta capacidad de evolución constituye uno de los principales objetivos del
proyecto.

---

# Conclusión

Comprender la plataforma desde una perspectiva general facilita el estudio de
cada uno de sus componentes.

Los documentos que siguen desarrollarán en detalle aspectos como la
arquitectura, la red, la seguridad, los servicios y los procedimientos de
instalación.

Sin embargo, todos ellos describen diferentes partes de una misma plataforma.

Esa visión integral constituye el fundamento sobre el cual se desarrollará
todo el proyecto **EJTV Broadcast Platform**.
