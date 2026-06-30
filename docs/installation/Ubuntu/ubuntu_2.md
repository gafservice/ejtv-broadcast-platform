# Preparación del medio de instalación e instalación del sistema operativo

---

# Preparación del medio de instalación

Una vez seleccionada la distribución Linux que serviría como base para el proyecto, el siguiente paso consistió en preparar el medio de instalación.

Para ello se descargó la imagen oficial de **Ubuntu Desktop 24.04 LTS** desde el sitio web de Canonical.

La utilización de imágenes oficiales garantiza la integridad del sistema operativo y reduce el riesgo de incorporar software modificado o versiones no verificadas.

Posteriormente, la imagen ISO fue copiada a una memoria USB utilizando una herramienta especializada para la creación de medios de instalación arrancables.

Este dispositivo permitió iniciar el servidor directamente desde el instalador de Ubuntu sin modificar previamente el contenido de las unidades internas del equipo.

Antes de comenzar la instalación se verificó que el servidor reconociera correctamente el dispositivo USB y que el firmware permitiera iniciar el sistema desde dicho medio.

Superada esta verificación, se inició el proceso de instalación del sistema operativo.

---

# Inicio del instalador

El instalador de Ubuntu guía al usuario mediante una secuencia ordenada de decisiones relacionadas con el idioma, distribución del teclado, conectividad, almacenamiento y creación de usuarios.

Aunque muchas de estas opciones parecen simples, cada una puede afectar el comportamiento futuro del servidor.

Por esta razón se evitó aceptar automáticamente todas las opciones sugeridas por el instalador.

Cada pantalla fue analizada individualmente para verificar que la configuración seleccionada coincidiera con los objetivos definidos para **EJTV Broadcast Platform**.

---

# Selección del idioma

Durante la instalación se seleccionó el idioma **Español** para el proceso de instalación y para el entorno gráfico inicial.

Esta decisión facilita la administración cotidiana del sistema y resulta consistente con el idioma utilizado durante toda la documentación técnica del proyecto.

Es importante destacar que esta selección no limita la utilización de aplicaciones, documentación o herramientas en inglés cuando resulte necesario.

Ubuntu mantiene plena compatibilidad con ambos idiomas.

---

# Distribución del teclado

Se configuró la distribución correspondiente al teclado físico utilizado durante la instalación.

La correcta selección de este parámetro evita errores posteriores relacionados con caracteres especiales, símbolos utilizados durante la programación y comandos ejecutados desde la terminal.

Aunque este aspecto suele considerarse menor, una configuración incorrecta puede generar dificultades importantes durante la administración del servidor.

---

# Conectividad durante la instalación

Durante el proceso de instalación el servidor se conectó a la red local mediante una interfaz Ethernet.

Esta conexión permitió al instalador acceder a Internet para verificar la disponibilidad de actualizaciones recientes y descargar componentes adicionales cuando fue necesario.

Disponer de conectividad durante la instalación también permitió reducir la cantidad de actualizaciones requeridas inmediatamente después del primer arranque del sistema.

---

# Tipo de instalación

Ubuntu ofrece diferentes modalidades de instalación dependiendo del uso previsto del sistema.

Después de analizar las alternativas disponibles se seleccionó la instalación estándar.

Esta opción incorpora un conjunto equilibrado de herramientas que facilitan el desarrollo inicial de la plataforma sin agregar componentes innecesarios.

La instalación mínima, aunque reduce ligeramente el espacio ocupado en disco, habría requerido instalar posteriormente muchas de las aplicaciones necesarias para el desarrollo del proyecto.

La instalación estándar permitió disponer inmediatamente de un entorno de trabajo completamente funcional.

---

# Actualizaciones durante la instalación

Siempre que fue posible se permitió al instalador descargar las actualizaciones disponibles durante el proceso de instalación.

Esta decisión presenta varias ventajas.

En primer lugar, reduce el número de paquetes pendientes inmediatamente después del primer inicio.

En segundo lugar, incorpora correcciones de seguridad publicadas entre la generación de la imagen ISO y la fecha de instalación.

Finalmente, permite comenzar el desarrollo sobre una plataforma más cercana al estado actual de mantenimiento de Ubuntu.

---

# Software de terceros

Durante la instalación se evaluó la posibilidad de incorporar software adicional proporcionado por terceros.

Sin embargo, siguiendo los principios establecidos para **EJTV Broadcast Platform**, se procuró mantener la plataforma lo más cercana posible a una instalación estándar de Ubuntu.

La incorporación de componentes adicionales se realizará únicamente cuando exista una necesidad claramente justificada y siempre quedará documentada dentro del repositorio del proyecto.

Este enfoque simplifica el mantenimiento futuro y facilita la reproducción del entorno en otros servidores.

---

# Organización del almacenamiento

Uno de los aspectos más importantes de toda instalación corresponde a la organización inicial del almacenamiento.

Antes de modificar cualquier unidad existente se verificó cuidadosamente la información almacenada en el servidor para evitar la pérdida accidental de datos.

Durante esta etapa se decidió utilizar el SSD dedicado al sistema operativo como unidad principal de instalación.

Los demás discos presentes en el servidor permanecieron sin modificaciones.

Esta decisión permitió separar claramente el sistema operativo de los futuros espacios destinados al almacenamiento de datos, grabaciones y respaldos.

La organización detallada del almacenamiento será desarrollada posteriormente en el documento **storage.md**.

---

# Selección del sistema de archivos

Para la partición principal del sistema operativo se utilizó el sistema de archivos **EXT4**.

Esta decisión respondió principalmente a su estabilidad, amplio soporte dentro del ecosistema Linux y excelente desempeño en aplicaciones de servidor.

EXT4 constituye actualmente uno de los sistemas de archivos más utilizados en entornos Linux y ofrece un equilibrio adecuado entre rendimiento, confiabilidad y facilidad de administración.

---

# ¿Por qué no se utilizó LVM?

Durante la instalación se evaluó la posibilidad de utilizar **Logical Volume Manager (LVM)**.

Aunque esta tecnología proporciona una gran flexibilidad para administrar particiones y ampliar volúmenes de almacenamiento, durante esta primera etapa del proyecto se decidió no utilizarla.

La principal razón fue mantener una estructura de almacenamiento sencilla y fácil de comprender.

La arquitectura definida para **EJTV Broadcast Platform** prioriza inicialmente la simplicidad y la claridad administrativa sobre mecanismos avanzados de virtualización del almacenamiento.

En etapas futuras, cuando la plataforma incorpore nuevos discos o almacenamiento redundante, la utilización de LVM podrá reevaluarse si resulta conveniente.

---

# ¿Por qué no se utilizó cifrado del disco?

Otra decisión importante consistió en no habilitar el cifrado completo del disco durante la instalación inicial.

Esta decisión respondió a varios factores.

En primer lugar, el servidor operará dentro de un entorno físico controlado.

En segundo lugar, el cifrado completo del disco introduce complejidad adicional durante ciertas tareas de mantenimiento y recuperación del sistema.

Finalmente, el objetivo principal de esta primera etapa consistía en construir una plataforma estable para el desarrollo de la infraestructura.

Esto no significa que la seguridad haya sido ignorada.

La protección de la plataforma se implementará mediante una arquitectura de seguridad multicapa basada en autenticación, firewall, control de accesos y monitoreo, aspectos desarrollados dentro de **SECURITY_ARCHITECTURE.md**.

---

# Inicio de la copia de archivos

Una vez confirmadas todas las opciones anteriores, el instalador inició la copia del sistema operativo hacia el SSD seleccionado.

Durante esta etapa se creó automáticamente la estructura inicial de particiones, se instalaron los paquetes base del sistema y se configuró el cargador de arranque.

Al finalizar este proceso, el servidor quedó preparado para realizar su primer inicio utilizando el sistema operativo recién instalado.

---

# Estado alcanzado

Al concluir la instalación se obtuvo un sistema Linux completamente funcional, preparado para continuar con la configuración inicial del servidor.

En este punto todavía no se habían instalado aplicaciones adicionales ni servicios específicos de **EJTV Broadcast Platform**.

Sin embargo, ya existía una base estable sobre la cual continuar el desarrollo de la plataforma.

---

## Continúa en la Parte 3

La siguiente sección documentará la creación del usuario administrativo, la configuración del nombre del servidor **ejtv-01**, el primer arranque del sistema operativo y las verificaciones realizadas para confirmar que la instalación había concluido satisfactoriamente.
