# Creación del usuario administrativo

Una vez finalizada la copia de archivos y la instalación del sistema operativo, el instalador solicitó la creación del primer usuario del sistema.

En Linux, el primer usuario creado durante la instalación posee privilegios administrativos mediante el mecanismo **sudo**, permitiéndole realizar tareas de configuración sin necesidad de habilitar directamente la cuenta **root**.

Durante el desarrollo de **EJTV Broadcast Platform** se decidió utilizar un único usuario administrativo para las etapas iniciales del proyecto.

El usuario seleccionado fue:

| Parámetro   | Valor                                        |
| ----------- | -------------------------------------------- |
| Usuario     | **ejtv**                                     |
| Tipo        | Usuario administrativo                       |
| Privilegios | sudo                                         |
| Función     | Administración y desarrollo de la plataforma |

La utilización de un único usuario durante las primeras etapas simplifica la administración del sistema y facilita la trazabilidad de las acciones realizadas sobre el servidor.

En futuras etapas podrán incorporarse nuevos usuarios con privilegios diferenciados conforme aumenten las necesidades operativas de la plataforma.

---

# Configuración del nombre del servidor

Después de definir el usuario administrativo, se asignó un nombre permanente al servidor.

Dentro de una infraestructura de red, el nombre del equipo constituye uno de los elementos más importantes para su identificación.

Desde las primeras etapas del proyecto se decidió adoptar una convención de nombres sencilla, consistente y escalable.

El servidor principal recibió el nombre:

```text
ejtv-01
```

La selección de este nombre responde a varios criterios.

En primer lugar, identifica claramente la pertenencia del equipo al proyecto **EJTV Broadcast Platform**.

En segundo lugar, incorpora una numeración que permitirá agregar nuevos servidores sin modificar la convención establecida.

Por ejemplo:

```text
ejtv-01
ejtv-02
ejtv-03
...
```

Esta estrategia facilita la administración de infraestructuras con múltiples nodos y evita utilizar nombres ambiguos o difíciles de recordar.

---

# Primer inicio del sistema

Concluida la instalación, el instalador solicitó reiniciar el servidor.

Durante este primer reinicio se retiró el medio USB utilizado para la instalación, permitiendo que el equipo iniciara directamente desde la unidad SSD donde se encontraba instalado Ubuntu.

El proceso de arranque permitió verificar correctamente:

* inicialización del firmware;
* detección de los dispositivos de almacenamiento;
* carga del gestor de arranque;
* inicio del kernel Linux;
* carga de los servicios básicos del sistema;
* presentación de la pantalla de autenticación.

La ausencia de mensajes de error durante esta etapa confirmó que la instalación había finalizado correctamente.

---

# Primer inicio de sesión

Después del arranque del sistema se realizó el primer inicio de sesión utilizando el usuario administrativo creado durante la instalación.

Este procedimiento permitió verificar simultáneamente varios aspectos fundamentales:

* existencia del usuario;
* autenticación mediante contraseña;
* carga del entorno gráfico;
* creación del directorio personal;
* funcionamiento de los servicios básicos del sistema.

El inicio de sesión exitoso confirmó que la configuración inicial del sistema operativo se había completado correctamente.

A partir de este momento el servidor quedó listo para comenzar las tareas de configuración posteriores.

---

# Primera utilización de privilegios administrativos

Uno de los primeros procedimientos realizados después del inicio de sesión consistió en verificar el funcionamiento del mecanismo **sudo**.

Ubuntu utiliza este mecanismo para ejecutar tareas administrativas de manera controlada, evitando el uso permanente de la cuenta **root**.

La verificación consistió en ejecutar un comando administrativo desde la terminal.

Este procedimiento permitió confirmar que:

* el usuario pertenece al grupo de administradores;
* la autenticación mediante contraseña funciona correctamente;
* los privilegios administrativos fueron asignados durante la instalación.

La utilización de **sudo** constituye uno de los principios fundamentales de administración en sistemas Linux y será empleada durante todo el desarrollo de la plataforma.

---

# Primer reinicio del servidor

Una vez comprobado el funcionamiento general del sistema, se realizó un reinicio controlado del servidor.

Este procedimiento permitió verificar que la configuración persistiera correctamente entre sesiones.

Durante este reinicio se confirmó el correcto funcionamiento de:

* proceso de apagado;
* proceso de arranque;
* servicios esenciales del sistema;
* autenticación del usuario;
* carga del entorno gráfico.

La estabilidad observada durante este procedimiento confirmó que el servidor se encontraba preparado para continuar con las siguientes etapas de configuración.

---

# Estado alcanzado

Al concluir estas primeras verificaciones, el servidor presentaba las siguientes condiciones operativas:

* Ubuntu instalado correctamente.
* Usuario administrativo funcional.
* Nombre permanente del servidor configurado como **ejtv-01**.
* Inicio de sesión operativo.
* Privilegios administrativos mediante **sudo**.
* Reinicio exitoso sin errores.

Estas condiciones constituyen el punto de partida para todas las configuraciones posteriores relacionadas con actualización del sistema, instalación de herramientas de desarrollo y despliegue de los servicios que conformarán **EJTV Broadcast Platform**.

---

# Evidencia pendiente de incorporación

La siguiente sección de este documento incorporará la evidencia real obtenida directamente del servidor **ejtv-01**.

Entre las verificaciones previstas se encuentran:

* `hostnamectl`
* `id`
* `groups`
* `whoami`
* `sudo -v`
* `last reboot`
* `uptime`
* `loginctl`

Cada uno de estos comandos será acompañado por:

* comando ejecutado;
* salida real obtenida;
* interpretación técnica;
* conclusión de ingeniería.

Con ello quedará completamente documentado el estado inicial del servidor inmediatamente después de su instalación.
