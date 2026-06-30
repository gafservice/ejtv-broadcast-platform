# Instalación del Sistema Operativo Ubuntu

> *"La instalación del sistema operativo constituye el punto de partida sobre el cual se desarrollará toda la infraestructura tecnológica de EJTV Broadcast Platform. Una correcta planificación durante esta etapa simplifica el mantenimiento futuro y facilita la evolución de la plataforma."*

---

# Resumen Ejecutivo

El sistema operativo representa la primera capa de software sobre la cual se construirá **EJTV Broadcast Platform**.

Su selección condiciona aspectos tan importantes como la estabilidad del servidor, la disponibilidad de herramientas de desarrollo, la compatibilidad con el hardware, la facilidad de administración y el soporte a largo plazo.

Durante esta etapa se realizó la instalación inicial de **Ubuntu 24.04 LTS**, configurando el servidor **ejtv-01** como la plataforma base para el desarrollo de todos los servicios que formarán parte del proyecto.

La instalación no consistió únicamente en copiar archivos al disco.

Cada decisión adoptada durante este proceso fue analizada considerando el crecimiento esperado de la plataforma, la facilidad de mantenimiento y la necesidad de disponer de un entorno estable para el desarrollo de software, la administración del servidor y la documentación técnica del proyecto.

Este documento describe las decisiones de ingeniería adoptadas durante la instalación inicial, los criterios utilizados para seleccionar la distribución Linux y el estado obtenido al finalizar el proceso.

---

# Objetivo

Documentar el proceso de instalación del sistema operativo utilizado por **EJTV Broadcast Platform**, justificando cada una de las decisiones adoptadas durante esta etapa y estableciendo una referencia técnica que permita reconstruir la plataforma en el futuro.

---

# Alcance

El presente documento comprende exclusivamente la instalación inicial del sistema operativo.

Incluye:

* selección de la distribución Linux;
* justificación de la versión instalada;
* criterios utilizados durante la instalación;
* configuración inicial del servidor;
* creación del usuario administrativo;
* asignación del nombre del equipo;
* verificación básica del funcionamiento del sistema.

No incluye la instalación de aplicaciones adicionales, servicios de red, herramientas de desarrollo ni configuraciones específicas de seguridad.

Estos aspectos serán desarrollados posteriormente en documentos independientes dentro de la sección **Installation**.

---

# La importancia de la primera instalación

La instalación del sistema operativo representa uno de los momentos más importantes durante la construcción de cualquier infraestructura informática.

Aunque posteriormente podrán incorporarse nuevos servicios, aplicaciones o mecanismos de seguridad, todas esas funcionalidades dependerán de la calidad de esta primera instalación.

Por esta razón, durante el desarrollo de **EJTV Broadcast Platform** se decidió dedicar el tiempo necesario para analizar cuidadosamente cada una de las opciones ofrecidas por el instalador.

El objetivo no consistía únicamente en obtener un sistema funcional.

Se buscaba construir una plataforma estable, fácil de mantener y preparada para evolucionar durante muchos años.

La experiencia demuestra que muchas dificultades operativas aparecen como consecuencia de decisiones aparentemente pequeñas tomadas durante la instalación inicial.

Aspectos como el nombre del servidor, la organización del almacenamiento, la selección de usuarios administrativos o el tipo de instalación elegida pueden influir significativamente en la administración futura del sistema.

Por esta razón, cada decisión adoptada durante esta etapa fue documentada y justificada.

---

# Selección de la distribución Linux

Desde las primeras etapas del proyecto se definió que toda la plataforma se desarrollaría utilizando software de código abierto.

Esta decisión permitió reducir la dependencia de soluciones propietarias, facilitar el acceso a la documentación técnica y aprovechar una amplia comunidad de desarrollo.

Entre las diferentes distribuciones Linux disponibles se analizaron varias alternativas ampliamente utilizadas en entornos de servidores, incluyendo Debian, Ubuntu Server, Ubuntu Desktop, Rocky Linux y AlmaLinux.

Después del análisis correspondiente se seleccionó **Ubuntu 24.04 LTS**.

La decisión respondió principalmente a los siguientes factores:

* estabilidad demostrada en entornos de producción;
* amplio soporte por parte de Canonical;
* disponibilidad de documentación oficial;
* excelente compatibilidad con hardware moderno y heredado;
* gran disponibilidad de paquetes de software;
* comunidad internacional muy activa;
* ciclo de soporte extendido mediante versiones LTS.

Estas características convierten a Ubuntu en una plataforma adecuada tanto para el desarrollo como para la operación de servidores de propósito general.

---

# ¿Por qué Ubuntu Desktop y no Ubuntu Server?

Una de las primeras decisiones de ingeniería consistió en seleccionar la variante de Ubuntu que serviría como base para el proyecto.

Aunque Ubuntu Server constituye una excelente alternativa para infraestructuras de producción, durante esta primera etapa se optó por utilizar **Ubuntu Desktop**.

Esta decisión respondió a necesidades específicas del proyecto.

El servidor no solamente funcionará como plataforma de ejecución de servicios.

También será utilizado como estación principal de desarrollo.

Durante el proyecto se emplearán herramientas como:

* Visual Studio Code.
* LaTeX.
* Draw.io.
* Navegadores web.
* Clientes Git.
* Herramientas de diagnóstico.
* Aplicaciones gráficas de monitoreo.

Disponer de un entorno gráfico reduce considerablemente el tiempo requerido para configurar y validar nuevas funcionalidades durante las etapas iniciales del desarrollo.

Además, Ubuntu Desktop incorpora desde su instalación inicial un conjunto importante de herramientas que posteriormente también pueden administrarse mediante terminal, permitiendo combinar la comodidad del entorno gráfico con la flexibilidad de la línea de comandos.

Es importante destacar que la utilización de Ubuntu Desktop durante el desarrollo no impide que futuras versiones de la plataforma puedan migrarse hacia una instalación más especializada si las necesidades operativas así lo requieren.

La arquitectura definida para **EJTV Broadcast Platform** mantiene esta posibilidad abierta desde el inicio del proyecto.

---

# Selección de la versión LTS

Ubuntu publica periódicamente dos tipos principales de versiones.

Las versiones estándar incorporan rápidamente nuevas funcionalidades, mientras que las versiones **Long Term Support (LTS)** priorizan la estabilidad y reciben soporte durante un período considerablemente mayor.

Dado que **EJTV Broadcast Platform** constituye un proyecto de largo plazo, se consideró más conveniente seleccionar una versión LTS.

Esta decisión proporciona varias ventajas.

En primer lugar, reduce la necesidad de realizar migraciones frecuentes del sistema operativo.

En segundo lugar, ofrece una plataforma más estable para el desarrollo continuo del software.

Finalmente, facilita la compatibilidad entre las diferentes herramientas utilizadas durante el proyecto.

La versión seleccionada fue **Ubuntu 24.04 LTS**, la cual representa la base tecnológica sobre la cual continuará evolucionando la plataforma durante los próximos años.

---

# Principios que guiaron la instalación

Antes de iniciar el proceso de instalación se definieron varios principios que orientarían todas las decisiones posteriores.

Estos principios permitieron mantener un criterio uniforme durante toda la preparación del servidor.

Entre ellos destacan:

* privilegiar la simplicidad sobre configuraciones innecesariamente complejas;
* utilizar únicamente los componentes realmente necesarios;
* facilitar el mantenimiento futuro del sistema;
* preservar la capacidad de expansión de la plataforma;
* documentar todas las decisiones relevantes;
* mantener la compatibilidad con futuras actualizaciones del sistema operativo;
* evitar configuraciones que dificulten la recuperación del servidor.

Estos principios continúan vigentes y serán utilizados como referencia durante todas las etapas posteriores del proyecto.

---

## Continúa en la Parte 2

La siguiente sección documentará detalladamente la preparación del medio de instalación, el proceso seguido durante la instalación de Ubuntu, las decisiones relacionadas con el particionado del disco y la configuración inicial realizada por el instalador.
