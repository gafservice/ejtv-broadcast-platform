# MISIÓN 002

# Consolidación de la Plataforma Base

---

## Resumen Ejecutivo

La segunda misión del proyecto **EJTV Broadcast Platform** tuvo como propósito consolidar la instalación inicial del servidor y preparar el entorno de trabajo que servirá como base para el desarrollo de la plataforma.

Durante esta etapa se verificó el correcto funcionamiento del sistema operativo instalado en la misión anterior, se actualizaron todos los paquetes disponibles, se validó el hardware reconocido por Ubuntu y se incorporaron las primeras herramientas destinadas al desarrollo y documentación del proyecto.

Asimismo, se estableció el mecanismo de autenticación segura con GitHub mediante claves SSH, permitiendo la administración del repositorio sin necesidad de utilizar contraseñas o tokens de acceso.

Al finalizar esta misión, **ejtv-01** dejó de ser únicamente un servidor recién instalado para convertirse en la estación oficial de ingeniería del proyecto.

---

## Información General

| Campo             | Valor                   |
| ----------------- | ----------------------- |
| Fecha             | 26 de junio de 2026     |
| Proyecto          | EJTV Broadcast Platform |
| Servidor          | ejtv-01                 |
| Sistema Operativo | Ubuntu 24.04.1 LTS      |
| Estado            | Misión completada       |

---

## Objetivos

El objetivo principal de esta misión fue consolidar la plataforma base instalada durante la misión anterior, verificando su correcto funcionamiento e incorporando las herramientas necesarias para iniciar formalmente el desarrollo de **EJTV Broadcast Platform**.

Para alcanzar este objetivo se realizaron las siguientes actividades:

* Actualizar completamente Ubuntu.
* Verificar el reconocimiento del hardware instalado.
* Comprobar la configuración de red.
* Validar el funcionamiento de NTP.
* Habilitar el acceso remoto mediante SSH.
* Instalar Visual Studio Code.
* Configurar Git.
* Configurar autenticación mediante claves SSH con GitHub.
* Crear la estructura inicial del repositorio.
* Iniciar la documentación técnica del proyecto.

---

## Antecedentes

La instalación de un sistema operativo representa únicamente el primer paso en la construcción de una plataforma de ingeniería.

Antes de comenzar el desarrollo de software es necesario verificar que todos los componentes fundamentales del sistema funcionan correctamente y que las herramientas de desarrollo operan de manera confiable.

Por esta razón, la segunda misión estuvo orientada a transformar la instalación básica realizada durante la misión anterior en un entorno estable, reproducible y preparado para acompañar el crecimiento futuro del proyecto.

---

## Plataforma validada

Durante esta misión se verificó el correcto funcionamiento de los principales componentes del sistema.

| Componente         | Estado    |
| ------------------ | --------- |
| Ubuntu 24.04.1 LTS | Operativo |
| Kernel Linux       | Operativo |
| SSD principal      | Operativo |
| Red Ethernet       | Operativa |
| Sincronización NTP | Operativa |
| Servicio SSH       | Operativo |
| Git                | Operativo |
| Visual Studio Code | Operativo |
| GitHub SSH         | Operativo |

---

## Actividades realizadas

Durante esta misión se desarrollaron las siguientes actividades:

* Actualización completa del sistema operativo.
* Instalación de las herramientas básicas de desarrollo.
* Instalación de Visual Studio Code.
* Configuración del entorno inicial de trabajo.
* Configuración de Git.
* Generación del par de claves SSH utilizando el algoritmo Ed25519.
* Registro de la clave pública en GitHub.
* Configuración del repositorio para utilizar autenticación mediante SSH.
* Verificación de la comunicación segura con GitHub.
* Creación de la estructura documental inicial del proyecto.

---

## Decisiones de ingeniería

Durante esta etapa se adoptaron varias decisiones que definirán el flujo de trabajo del proyecto.

* Se seleccionó Visual Studio Code como editor oficial del proyecto.
* Se adoptó Git como sistema de control de versiones.
* Se eligió autenticación mediante claves SSH en lugar de HTTPS.
* Se estructuró el repositorio priorizando la documentación técnica desde las primeras etapas del desarrollo.
* Se estableció Markdown como formato principal para la documentación del proyecto.
* Se definió una organización modular de la documentación para facilitar su crecimiento futuro.

Estas decisiones buscan garantizar la trazabilidad del desarrollo y mantener un entorno homogéneo entre todos los futuros integrantes del proyecto.

---

## Validación

Al concluir esta misión se verificó satisfactoriamente que:

* El sistema operativo se encuentra completamente actualizado.
* El hardware fue reconocido correctamente por Ubuntu.
* La sincronización mediante NTP funciona correctamente.
* El servicio SSH acepta conexiones remotas.
* Git identifica correctamente al desarrollador.
* La autenticación mediante claves SSH con GitHub funciona correctamente.
* Visual Studio Code quedó instalado y operativo.
* El repositorio puede sincronizarse correctamente mediante Git.
* La estructura documental inicial quedó creada.

---

## Lecciones aprendidas

La consolidación temprana del entorno de desarrollo reduce considerablemente el riesgo de problemas durante las siguientes etapas del proyecto.

Asimismo, la autenticación mediante claves SSH demostró ser un mecanismo más seguro y práctico que el uso de contraseñas o tokens personales para la administración del repositorio.

Finalmente, se confirmó la importancia de documentar cada decisión técnica desde el inicio del proyecto, permitiendo reconstruir posteriormente el proceso completo de implementación.

---

## Estado de la plataforma

Al finalizar la Misión 002 el servidor **ejtv-01** dispone de un entorno completamente preparado para iniciar el desarrollo de la plataforma.

Además del sistema operativo correctamente configurado, el equipo incorpora las herramientas necesarias para documentar, versionar y mantener el software que será desarrollado durante las siguientes etapas del proyecto.

La plataforma ha dejado de ser únicamente un servidor Linux para convertirse en la estación oficial de ingeniería de **EJTV Broadcast Platform**.

---

## Conclusión

La segunda misión consolidó los cimientos técnicos sobre los cuales se desarrollará el resto del proyecto.

La actualización del sistema, la incorporación de las herramientas de desarrollo y la integración con GitHub permitieron establecer un entorno de trabajo estable, seguro y reproducible.

Cada decisión adoptada durante esta etapa respondió al principio de construir una plataforma que no solamente funcione correctamente, sino que también pueda mantenerse, documentarse y evolucionar con el paso del tiempo.

---

## Próxima misión

### MISIÓN 003

**Diseño de la arquitectura inicial de la plataforma, definición de los servicios fundamentales y preparación de la infraestructura para la incorporación de los componentes de streaming, monitoreo y administración del sistema.**
