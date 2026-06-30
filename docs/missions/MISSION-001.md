# MISIÓN 001

# Nacimiento de EJTV-01

---

## Resumen Ejecutivo

La presente misión marca el inicio formal del proyecto **EJTV Broadcast Platform**.

Durante esta primera etapa se construyó la plataforma física que servirá como base para el desarrollo, integración, validación y operación del sistema de distribución de contenidos audiovisuales.

Para ello se reutilizó una estación **Apple Mac Pro 5,1**, equipada con almacenamiento de estado sólido (SSD) y capacidad suficiente para desempeñarse inicialmente como servidor de desarrollo y estación de ingeniería.

Sobre esta plataforma se instaló **Ubuntu 24.04.1 LTS**, estableciendo la identidad del servidor, la estructura básica del sistema operativo y los primeros criterios de ingeniería que guiarán la evolución futura del proyecto.

Al concluir esta misión quedó disponible el primer nodo operativo de la plataforma, preparado para iniciar las siguientes etapas de configuración e integración.

---

## Información General

| Campo             | Valor                   |
| ----------------- | ----------------------- |
| Fecha             | 25 de junio de 2026     |
| Proyecto          | EJTV Broadcast Platform |
| Servidor          | ejtv-01                 |
| Sistema Operativo | Ubuntu 24.04.1 LTS      |
| Estado            | Misión completada       |

---

## Objetivos

El objetivo principal de esta misión fue construir el primer nodo operativo de **EJTV Broadcast Platform**, estableciendo una base estable, reproducible y documentada para el desarrollo futuro de la plataforma.

Para alcanzar este objetivo se realizaron las siguientes actividades:

* Instalar Ubuntu 24.04.1 LTS.
* Preparar el almacenamiento principal del servidor.
* Definir la identidad del nodo mediante el hostname **ejtv-01**.
* Crear el usuario administrativo inicial.
* Verificar el funcionamiento básico del sistema.
* Documentar las decisiones de ingeniería adoptadas durante el proceso.

---

## Antecedentes

Todo proyecto de ingeniería requiere una plataforma sólida sobre la cual construir los componentes que le darán vida.

En el caso de **EJTV Broadcast Platform**, la primera decisión consistió en seleccionar el equipo que funcionaría como servidor principal durante las etapas iniciales del desarrollo.

Más que adquirir hardware nuevo, se decidió reutilizar una estación **Apple Mac Pro 5,1**, una plataforma ampliamente reconocida por su estabilidad, capacidad de expansión y disponibilidad en el mercado de segunda mano.

Esta decisión permitió disponer de un equipo con recursos suficientes para funcionar simultáneamente como servidor de desarrollo y estación de ingeniería, optimizando los recursos disponibles sin comprometer el crecimiento futuro del proyecto.

---

## Plataforma utilizada

Durante esta misión se utilizó la siguiente plataforma de hardware.

| Componente               | Descripción                                     |
| ------------------------ | ----------------------------------------------- |
| Equipo                   | Apple Mac Pro 5,1                               |
| Arquitectura             | x86-64                                          |
| Almacenamiento principal | SSD Samsung                                     |
| Memoria RAM              | 8 GB                                            |
| Tarjeta gráfica          | AMD Radeon HD 5770                              |
| Función                  | Servidor de desarrollo y estación de ingeniería |

La elección de esta plataforma no respondió únicamente a criterios económicos.

También se consideró su facilidad de mantenimiento, disponibilidad de interfaces de expansión y capacidad para soportar múltiples servicios simultáneamente durante las siguientes fases del proyecto.

---

## Actividades realizadas

Durante esta primera misión se ejecutaron las siguientes actividades:

* Instalación de Ubuntu 24.04.1 LTS.
* Configuración del particionado automático mediante GPT y UEFI.
* Preparación del SSD principal.
* Definición del hostname **ejtv-01**.
* Creación del usuario administrativo.
* Configuración inicial del sistema operativo.
* Verificación del acceso a la red mediante DHCP.
* Sincronización automática del reloj utilizando NTP.

---

## Decisiones de ingeniería

Durante el proceso de instalación se adoptaron las siguientes decisiones técnicas:

* Se utilizó el particionado automático proporcionado por el instalador de Ubuntu.
* No se implementó LVM durante esta etapa del proyecto.
* No se habilitó cifrado del disco del sistema.
* Los discos destinados al almacenamiento de datos permanecieron sin modificaciones.
* Se seleccionó Ubuntu Desktop debido a que el servidor también funcionará inicialmente como estación de ingeniería y documentación.

Cada una de estas decisiones busca privilegiar la estabilidad, la simplicidad de mantenimiento y la facilidad de reproducción del entorno de trabajo.

---

## Validación

Al finalizar esta misión se verificó satisfactoriamente que:

* Ubuntu inicia correctamente.
* El sistema reconoce el SSD principal.
* El servidor obtiene dirección IP mediante DHCP.
* El servicio NTP sincroniza correctamente la hora del sistema.
* El hostname **ejtv-01** quedó definido correctamente.
* El usuario administrativo posee acceso al sistema.
* La plataforma quedó preparada para iniciar la siguiente etapa del proyecto.

---

## Lecciones aprendidas

La experiencia obtenida durante esta misión permitió confirmar varios aspectos importantes.

El instalador Desktop de Ubuntu simplifica considerablemente la preparación inicial del sistema, especialmente en plataformas UEFI.

Asimismo, se comprobó que el particionado automático proporciona una configuración adecuada para las necesidades actuales del proyecto, evitando complejidad innecesaria durante las primeras etapas del desarrollo.

Finalmente, quedó reafirmado uno de los principios fundamentales definidos para **EJTV Broadcast Platform**:

> La ingeniería debe concentrarse en las decisiones que aportan valor al proyecto, permitiendo que las herramientas resuelvan de forma automática aquellas tareas que ya han sido suficientemente validadas.

---

## Estado de la plataforma

Al concluir la Misión 001 se dispone de un servidor completamente operativo, preparado para continuar con la configuración del entorno de desarrollo y la incorporación progresiva de los diferentes servicios que conformarán la plataforma.

El sistema operativo quedó instalado y funcionando correctamente, estableciendo la base sobre la cual se desarrollarán todas las etapas posteriores del proyecto.

---

## Conclusión

La primera misión no consistió únicamente en instalar un sistema operativo.

Representó el nacimiento de la plataforma sobre la cual evolucionará **EJTV Broadcast Platform** durante los próximos años.

Cada decisión adoptada durante esta etapa fue documentada con el propósito de preservar el conocimiento generado y facilitar el mantenimiento futuro del sistema.

Porque una plataforma que solamente funciona puede dejar de ser útil cuando quienes la construyeron ya no están.

En cambio, una plataforma que puede comprenderse puede mantenerse, evolucionar y seguir aportando valor durante muchos años.

---

## Próxima misión

### MISIÓN 002

**Verificación integral del servidor, actualización completa del sistema operativo y preparación del entorno de ingeniería para el desarrollo de EJTV Broadcast Platform.**
