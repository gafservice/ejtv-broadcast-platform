# MISIÓN 004

---

# Fecha

26 de junio de 2026

---

# Proyecto

EJTV Broadcast Platform

---

# Servidor

**ejtv-01**

---

# Línea Base

**BL-001 — Línea Base Inicial del Servidor**

---

# Objetivo

Actualizar completamente el sistema operativo Ubuntu, incorporando las últimas
correcciones de seguridad, mejoras de estabilidad y actualizaciones de software
disponibles para la versión instalada.

Esta misión tiene como finalidad garantizar que el servidor inicie la etapa de
desarrollo sobre una plataforma completamente actualizada y estable.

---

# Justificación

La instalación inicial de un sistema operativo representa únicamente el punto
de partida de una plataforma.

Entre el momento en que se publica una imagen de instalación y el instante en
que el sistema es desplegado pueden liberarse nuevas versiones de paquetes,
actualizaciones del kernel, correcciones de seguridad y mejoras de
compatibilidad.

Por esta razón, antes de instalar cualquier herramienta de desarrollo o
servicio propio de la plataforma, resulta indispensable sincronizar el servidor
con los repositorios oficiales de Ubuntu.

Esta práctica reduce vulnerabilidades conocidas, mejora la estabilidad del
sistema y proporciona una base homogénea para todas las etapas posteriores del
proyecto.

---

# Actividades planificadas

Durante esta misión se definieron las siguientes actividades.

* Verificación del estado inicial del servidor.
* Actualización del índice de paquetes.
* Actualización completa del sistema operativo.
* Eliminación de paquetes obsoletos.
* Limpieza de la caché de paquetes.
* Verificación del kernel instalado.
* Reinicio del servidor en caso de ser requerido.
* Validación del estado operativo posterior a la actualización.

---

# Evidencias previstas

Al finalizar la misión deberían obtenerse las siguientes evidencias.

* Registro completo del proceso de actualización.
* Lista de paquetes actualizados.
* Versión final del kernel.
* Espacio recuperado mediante limpieza.
* Estado operativo del servidor.
* Confirmación del funcionamiento de los servicios principales.

Toda esta información será documentada en:

```text
docs/installation/updates.md
```

---

# Decisiones de ingeniería

Durante esta misión se establecieron los siguientes criterios.

* Utilizar exclusivamente los repositorios oficiales de Ubuntu.
* No instalar software adicional durante la actualización.
* No modificar archivos de configuración del sistema.
* Ejecutar la actualización antes de incorporar cualquier componente propio de
  EJTV Broadcast Platform.
* Mantener evidencia completa de todas las operaciones realizadas.

---

# Criterios de aceptación

La misión se considerará finalizada cuando se cumplan simultáneamente las
siguientes condiciones.

* El sistema no presente paquetes pendientes de actualización.
* El gestor de paquetes funcione correctamente.
* Ubuntu inicie sin errores.
* Los servicios principales permanezcan operativos.
* El servidor conserve la conectividad de red.
* El acceso mediante SSH continúe disponible.
* Toda incidencia detectada durante la misión haya sido resuelta.

---

# Ejecución de la misión

La misión fue iniciada sobre la línea base **BL-001**, correspondiente al
estado inicial del servidor inmediatamente después de la instalación de Ubuntu.

Se verificó el estado general del sistema y posteriormente se ejecutó la
actualización completa mediante los repositorios oficiales de Ubuntu.

Durante el proceso se actualizaron correctamente los paquetes disponibles y se
ejecutaron las tareas de limpieza previstas.

Sin embargo, durante la fase de configuración final del sistema se detectó una
incidencia relacionada con el paquete **broadcom-sta-dkms**, la cual impidió
que el gestor de paquetes concluyera correctamente el proceso de actualización.

El resto del sistema continuó funcionando normalmente.

---

# Evidencias generadas

Como resultado de la ejecución se generaron las siguientes evidencias.

| Evidencia                                        | Estado         |
| ------------------------------------------------ | -------------- |
| Verificación inicial del servidor                | ✔              |
| Actualización de índices                         | ✔              |
| Actualización completa                           | ✔              |
| Limpieza de paquetes                             | ✔              |
| Registro del proceso (`mission_004_upgrade.log`) | ✔              |
| Verificación posterior                           | ✔              |
| Documento `updates.md`                           | En elaboración |
| Registro de incidencia INC-001                   | ✔              |

---

# Incidencias asociadas

## INC-001

Durante la configuración del paquete **broadcom-sta-dkms** se produjo un error
en la compilación del módulo DKMS correspondiente al kernel
**6.17.0-35-generic**.

El análisis preliminar demostró que el servidor opera exclusivamente mediante
interfaces Ethernet y que el controlador Broadcom no participa actualmente en
la arquitectura de **EJTV Broadcast Platform**.

La incidencia fue documentada de manera independiente en:

```text
docs/incidents/INC-001.md
```

Su resolución permitirá completar oficialmente esta misión.

---

# Estado actual

| Parámetro            | Estado          |
| -------------------- | --------------- |
| Fecha de inicio      | 26 junio 2026   |
| Línea Base           | BL-001          |
| Avance               | 90 %            |
| Estado               | 🟡 En ejecución |
| Incidencias abiertas | INC-001         |

---

# Condiciones para el cierre

La presente misión podrá declararse finalizada únicamente cuando se cumplan las
siguientes condiciones.

* Resolver completamente la incidencia **INC-001**.
* Restablecer el funcionamiento normal del gestor de paquetes.
* Confirmar que no existen paquetes pendientes de configurar.
* Actualizar la documentación técnica (`updates.md`).
* Verificar nuevamente el estado general del servidor.
* Registrar oficialmente el cierre de la misión.

---

# Relación con la arquitectura documental

La presente misión forma parte del sistema de documentación del proyecto y se
encuentra relacionada con los siguientes documentos.

| Documento              | Propósito                                                     |
| ---------------------- | ------------------------------------------------------------- |
| BL-001                 | Línea base sobre la cual se ejecuta la misión                 |
| updates.md             | Evidencia técnica de la actualización                         |
| INC-001                | Registro de la incidencia detectada                           |
| ADR-001 *(pendiente)*  | Decisión sobre el uso exclusivo de interfaces Ethernet        |
| PROC-001 *(pendiente)* | Procedimiento para la administración del controlador Broadcom |

---

# Conclusión

La **MISIÓN 004** permitió actualizar satisfactoriamente el sistema operativo y
validar la estabilidad general del servidor.

Durante su ejecución se detectó la primera incidencia técnica documentada del
proyecto (**INC-001**), relacionada con la compilación del controlador
**broadcom-sta-dkms**.

Aunque dicha incidencia no afecta la operación del servidor, impide considerar
la misión como completamente finalizada.

Una vez resuelta la incidencia y validadas las condiciones de cierre, la misión
será declarada oficialmente completada y el proyecto podrá continuar con la
**MISIÓN 005**, correspondiente a la instalación y configuración del sistema de
control de versiones Git.
