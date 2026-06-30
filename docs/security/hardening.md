# Hardening del Servidor

## Descripción

Este documento define la estrategia de endurecimiento (Hardening) aplicada al servidor de la **EJTV Broadcast Platform**.

El objetivo es reducir la superficie de ataque del sistema operativo mediante la aplicación de buenas prácticas de seguridad, limitando los servicios expuestos, restringiendo accesos innecesarios y manteniendo una configuración consistente durante todo el ciclo de vida de la plataforma.

El proceso de hardening es incremental y acompaña el desarrollo de la infraestructura del proyecto.

---

# Objetivos

La estrategia de hardening busca:

* Reducir la superficie de ataque del servidor.
* Limitar el acceso únicamente a los servicios necesarios.
* Proteger los mecanismos de administración remota.
* Mantener una configuración documentada y reproducible.
* Facilitar futuras auditorías de seguridad.
* Establecer una base segura para los servicios de broadcast.

---

# Principios de seguridad

La configuración del servidor sigue los siguientes principios:

* Mínimo privilegio (Least Privilege).
* Defensa en profundidad (Defense in Depth).
* Servicios mínimos.
* Configuración reproducible.
* Cambios documentados.
* Validación después de cada modificación.

---

# Estado actual del hardening

## Sistema operativo

* Ubuntu Server 24.04 LTS.
* Actualizaciones aplicadas.
* Sistema base documentado.

---

## Firewall

Se implementó **UFW (Uncomplicated Firewall)** como mecanismo principal de filtrado de paquetes.

Política actual:

| Dirección | Política |
| --------- | -------- |
| Entrada   | DENY     |
| Salida    | ALLOW    |
| Reenvío   | DENY     |

Servicios autorizados:

| Servicio |   Puerto |
| -------- | -------: |
| SSH      |   22/TCP |
| Cockpit  | 9090/TCP |

Todos los demás servicios permanecen bloqueados.

---

## Administración remota

La administración del servidor se realiza mediante:

* OpenSSH.
* Cockpit.

Ambos servicios forman parte de la línea base del proyecto.

---

## Configuración SSH

Actualmente se mantiene la configuración estándar de OpenSSH complementada mediante archivos de configuración independientes ubicados en:

```text
/etc/ssh/sshd_config.d/
```

Esta estrategia permite preservar la configuración original distribuida por Ubuntu y simplifica futuras actualizaciones del sistema.

Las modificaciones implementadas hasta el momento incluyen:

* Validación de la configuración.
* Separación entre configuración base y configuración personalizada.
* Respaldo de la configuración original.

---

## Gestión de servicios

Todos los servicios son administrados mediante **systemd**, permitiendo:

* Inicio automático.
* Monitoreo del estado.
* Registro mediante journal.
* Administración centralizada.

---

## Gestión del firewall

La administración del firewall se realiza exclusivamente mediante **UFW**.

No se recomienda modificar reglas directamente mediante iptables.

---

# Buenas prácticas

Durante la administración del servidor deberán seguirse las siguientes recomendaciones.

* Mantener únicamente los servicios necesarios.
* Deshabilitar servicios que no se utilicen.
* Documentar toda modificación.
* Aplicar actualizaciones de seguridad periódicamente.
* Mantener respaldos de configuraciones críticas.
* Validar todos los cambios antes de ponerlos en producción.

---

# Medidas implementadas

| Medida                       | Estado |
| ---------------------------- | :----: |
| Actualización del sistema    |    ✅   |
| OpenSSH                      |    ✅   |
| Cockpit                      |    ✅   |
| Firewall UFW                 |    ✅   |
| Política Default Deny        |    ✅   |
| Configuración modular de SSH |    ✅   |
| Respaldo de configuraciones  |    ✅   |

---

# Medidas planificadas

Las siguientes acciones forman parte del plan de hardening y serán implementadas conforme avance el proyecto.

| Medida                                    | Estado    |
| ----------------------------------------- | --------- |
| Fail2Ban                                  | Pendiente |
| HTTPS con certificados TLS                | Pendiente |
| Certificados Let's Encrypt                | Pendiente |
| Autenticación mediante claves SSH         | Pendiente |
| Deshabilitar autenticación por contraseña | Pendiente |
| Auditoría periódica de puertos            | Pendiente |
| Copias de seguridad automáticas           | Pendiente |
| Monitoreo de integridad                   | Pendiente |

---

# Auditoría

Después de cada modificación relacionada con la seguridad deberán verificarse como mínimo los siguientes aspectos:

* Estado del firewall.
* Servicios activos.
* Configuración de SSH.
* Puertos abiertos.
* Estado de systemd.
* Registros del sistema.

Toda modificación deberá quedar registrada en la documentación correspondiente.

---

# Documentos relacionados

* `docs/network/firewall.md`
* `docs/network/ports.md`
* `docs/services/ssh.md`
* `docs/services/cockpit.md`
* `docs/security/authentication.md`
* `docs/security/certificates.md`
* `docs/security/backups.md`
* `BL-004.md`
* `BL-005.md`
