El objetivo de esta misión consiste en implementar el servicio Secure Shell (SSH) como mecanismo principal para la administración remota del servidor ejtv-01.

Durante esta misión se documentará la instalación, configuración, endurecimiento y validación del servicio, estableciendo una plataforma segura para las futuras tareas de mantenimiento, actualización y operación del sistema.

La configuración obtenida constituirá la base para la administración remota de la plataforma EJTV Broadcast Platform durante las etapas de integración, pruebas y operación.

# S-001 — Estado general del servicio SSH

## Objetivo

Verificar el estado operativo del servicio OpenSSH Server instalado sobre el servidor ejtv-01, comprobando que el demonio encargado de aceptar conexiones remotas se encuentre correctamente iniciado y configurado para ejecutarse automáticamente durante el arranque del sistema operativo.

---

## Comandos ejecutados

```bash
systemctl status ssh
systemctl is-enabled ssh
systemctl is-active ssh 


---

# S-002 — Versión instalada

```markdown
# S-002 — Verificación de la versión de OpenSSH

## Objetivo

Verificar la versión del software OpenSSH instalada sobre el servidor, con el fin de registrar la línea base del servicio de administración remota utilizada durante el desarrollo del proyecto.

---

## Comando ejecutado

```bash
ssh -V

OpenSSH_9.6p1
OpenSSL 3.0.13
Ubuntu 24.04 LTS


---

# S-003 — Paquetes instalados

```markdown
# S-003 — Verificación de los componentes OpenSSH instalados

## Objetivo

Comprobar que todos los componentes necesarios para el funcionamiento del servicio SSH se encuentren correctamente instalados.

---

## Comando ejecutado

```bash
dpkg -l | grep openssh


# S-005 — Integración del servicio SSH con systemd

## Objetivo

Verificar la correcta integración del servicio OpenSSH Server con el sistema de administración de servicios **systemd**, comprobando su estado operativo, habilitación durante el arranque y mecanismo de recarga de configuración.

---

## Comandos ejecutados

```bash
systemctl status ssh
systemctl status ssh.socket
systemctl list-unit-files | grep ssh
```

---

## Evidencia obtenida

La inspección realizada confirmó que el servicio principal **ssh.service** se encuentra correctamente registrado dentro de systemd.

Durante la validación se obtuvo la siguiente información:

- Servicio habilitado para iniciar automáticamente.
- Estado operativo **active (running)**.
- Inicio automático durante el proceso de arranque.
- Ejecución mediante el proceso `/usr/sbin/sshd`.
- Escucha simultánea sobre IPv4 e IPv6 utilizando el puerto TCP 22.

Asimismo, se verificó la existencia de la unidad **ssh.socket**, la cual permanece deshabilitada debido a que el servidor utiliza el modelo tradicional basado en un demonio residente (`ssh.service`) y no mediante activación por socket.

---

## Interpretación

La configuración implementada corresponde al esquema recomendado para servidores de propósito general, donde el servicio SSH permanece permanentemente disponible para aceptar conexiones remotas.

La presencia de la unidad `ssh.socket` responde a la arquitectura moderna de OpenSSH integrada con systemd, aunque no forma parte de la configuración actualmente utilizada por el servidor.

---

## Conclusión

El servicio SSH quedó correctamente integrado con systemd, iniciando automáticamente durante el arranque del sistema y proporcionando disponibilidad permanente para la administración remota del servidor.

# S-006 — Configuración efectiva del servidor SSH

## Objetivo

Verificar la configuración efectiva utilizada por el servidor OpenSSH, identificando los parámetros realmente aplicados durante la ejecución del servicio, independientemente de que estos provengan del archivo principal de configuración o de los valores predeterminados incorporados por OpenSSH.

---

## Comando ejecutado

```bash
sudo sshd -T
```

---

## Evidencia obtenida

La inspección de la configuración efectiva permitió confirmar, entre otros aspectos, los siguientes parámetros relevantes:

- Puerto TCP 22.
- Escucha sobre IPv4 e IPv6.
- Autenticación mediante claves públicas habilitada.
- Autenticación mediante contraseña habilitada.
- Acceso del usuario root restringido a autenticación mediante claves.
- Integración con PAM habilitada.
- Subsistema SFTP activo.
- Algoritmos modernos de intercambio de claves y cifrado habilitados por defecto.
- Registro de eventos con nivel **INFO**.

---

## Interpretación

La configuración efectiva corresponde a la instalación estándar proporcionada por Ubuntu Server 24.04 LTS, priorizando compatibilidad y facilidad de administración sin aplicar todavía políticas específicas de endurecimiento.

Se verificó igualmente que OpenSSH incorpora automáticamente algoritmos criptográficos modernos y mecanismos de autenticación seguros compatibles con las recomendaciones actuales.

---

## Conclusión

La configuración efectiva constituye una línea base adecuada para iniciar la etapa de endurecimiento del servicio SSH, manteniendo un punto de referencia claramente documentado previo a la aplicación de políticas de seguridad propias del proyecto EJTV Broadcast Platform.

# S-007 — Validación operativa del servicio SSH

## Objetivo

Comprobar la consistencia de la configuración del servicio OpenSSH y verificar que los cambios de configuración puedan aplicarse mediante recarga del servicio sin afectar su disponibilidad.

---

## Comandos ejecutados

```bash
sudo sshd -t
sudo systemctl reload ssh
systemctl status ssh
```

---

## Evidencia obtenida

La validación sintáctica realizada mediante `sshd -t` finalizó sin reportar errores de configuración.

Posteriormente se ejecutó una recarga del servicio utilizando `systemctl reload ssh`, observándose que el demonio recibió correctamente la señal **SIGHUP**, recargando su configuración sin interrumpir el servicio.

Durante la recarga el servidor continuó escuchando conexiones tanto sobre IPv4 como IPv6 utilizando el puerto TCP 22.

---

## Interpretación

La ausencia de errores durante la validación sintáctica confirma que la configuración utilizada por OpenSSH es consistente y puede ser procesada correctamente por el demonio del servicio.

La recarga dinámica mediante `systemctl reload` demuestra que futuras modificaciones de configuración podrán aplicarse sin necesidad de reiniciar completamente el servicio, minimizando la interrupción de las conexiones remotas.

---

## Conclusión

El servicio SSH superó satisfactoriamente todas las pruebas de validación realizadas, quedando preparado para iniciar la siguiente etapa correspondiente al endurecimiento de la configuración de seguridad.
