# SPRINT-004

# Problema abordado

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

Las primeras etapas del Control Center permitieron consultar información
general del servidor, incluyendo identidad del equipo, utilización de
CPU, memoria principal, almacenamiento y tiempo de funcionamiento.

Aunque esta información proporciona una visión del estado del sistema
operativo, resulta insuficiente para administrar una plataforma de
distribución multimedia en producción.

La disponibilidad del servidor depende principalmente del estado de los
servicios que ejecutan las funciones críticas de la plataforma y no
únicamente de los recursos del sistema.

---

# Situación inicial

Antes de este sprint no existía un mecanismo que permitiera responder
preguntas fundamentales como:

- ¿MediaMTX se encuentra ejecutándose?
- ¿FFmpeg está procesando alguna señal?
- ¿El backend del Control Center continúa operativo?
- ¿Cuántas instancias existen de un proceso?
- ¿Cuánto tiempo lleva ejecutándose un servicio?
- ¿Cuál es el consumo de CPU y memoria de cada proceso?

Para obtener esta información era necesario ingresar manualmente al
servidor mediante SSH y ejecutar herramientas como:

```
systemctl
ps
pgrep
top
htop
```

Este procedimiento impedía que el frontend pudiera mostrar el estado real
de la infraestructura.

---

# Limitaciones detectadas

La ausencia de un sistema de monitoreo producía varias limitaciones
operativas.

## Dependencia de acceso SSH

La supervisión requería acceso directo al servidor Linux, lo que impedía
su utilización desde una interfaz web.

---

## Ausencia de una API

No existía un endpoint REST que permitiera consultar el estado operativo
de los servicios.

Como consecuencia, ninguna aplicación externa podía integrar esta
información.

---

## Diferencias entre mecanismos de supervisión

Linux administra algunos componentes mediante **systemd**, mientras que
otros se ejecutan como procesos independientes.

Cada mecanismo utiliza comandos y formatos diferentes, dificultando la
construcción de una interfaz uniforme.

---

## Información dispersa

Los datos necesarios para conocer el estado de un servicio se encontraban
distribuidos entre múltiples herramientas del sistema operativo.

No existía una representación unificada que pudiera ser consumida por el
backend.

---

## Escasa capacidad de expansión

La arquitectura anterior no permitía incorporar fácilmente nuevos
servicios para monitoreo.

Cada nuevo componente requeriría implementar nuevamente toda la lógica de
consulta.

---

# Impacto sobre el proyecto

Sin un sistema de monitoreo de servicios era imposible construir un
Control Center capaz de supervisar la infraestructura multimedia.

Esta limitación impedía desarrollar funcionalidades como:

- paneles operativos;
- indicadores de disponibilidad;
- alarmas automáticas;
- detección de fallos;
- administración centralizada;
- monitoreo remoto.

---

# Necesidad del sprint

Se requería una arquitectura capaz de abstraer las diferencias entre los
distintos mecanismos de supervisión presentes en Linux.

La solución debía:

- consultar servicios administrados por systemd;
- detectar procesos independientes;
- normalizar los estados de ejecución;
- representar múltiples instancias;
- publicar la información mediante una API REST.

Además, la implementación debía mantener la arquitectura en capas
adoptada por el proyecto, evitando que las capas superiores dependieran
directamente de comandos específicos del sistema operativo.

---

# Resultado esperado

Al finalizar este sprint el Control Center debe ser capaz de conocer el
estado operativo de los principales servicios de la plataforma mediante
una interfaz uniforme, reutilizable y desacoplada del mecanismo utilizado
para obtener la información.

Esta capacidad constituye el primer paso hacia un sistema integral de
supervisión de la infraestructura multimedia.

---

# Documento siguiente

**04-DESIGN.md**