# MISSION-008

## Implementación y validación del firewall UFW

---

## Objetivo

Implementar el firewall del servidor utilizando **Uncomplicated Firewall (UFW)** con el propósito de establecer una política de seguridad basada en el principio de mínimo privilegio, permitiendo únicamente el acceso a los servicios necesarios para la administración del sistema.

---

## Fecha

2026-06-26

---

# Estado inicial

Antes de realizar cualquier modificación se efectuó un diagnóstico completo del estado del sistema.

### Sistema operativo

Ubuntu 24.04.4 LTS

### Kernel

Linux 6.17.0-35-generic

### Estado del firewall

* UFW instalado.
* Firewall deshabilitado.
* Sin reglas configuradas.
* Políticas de iptables en modo ACCEPT.
* Sin configuraciones heredadas.

### Servicios detectados

Durante el diagnóstico se identificaron los siguientes servicios escuchando en la red:

| Servicio                     |   Puerto | Estado    |
| ---------------------------- | -------: | --------- |
| SSH                          |   22/TCP | Activo    |
| Cockpit                      | 9090/TCP | Activo    |
| DNS Local (systemd-resolved) |       53 | Localhost |
| CUPS                         |      631 | Localhost |

Los servicios enlazados únicamente a la interfaz de loopback no requirieron reglas adicionales de firewall.

---

# Configuración aplicada

Se estableció una política conservadora basada en el principio **Default Deny**.

Las acciones ejecutadas fueron las siguientes.

## Política por defecto

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

Resultado:

* Todo el tráfico entrante queda bloqueado por defecto.
* Todo el tráfico saliente permanece permitido.

---

## Acceso SSH

Se autorizó el acceso remoto mediante SSH.

```bash
sudo ufw allow 22/tcp comment 'SSH'
```

---

## Consola Cockpit

Se habilitó el acceso HTTPS a Cockpit.

```bash
sudo ufw allow 9090/tcp comment 'Cockpit'
```

---

## Activación del firewall

Finalmente se habilitó UFW.

```bash
sudo ufw enable
```

---

# Validación

Se verificó correctamente:

* Activación del firewall.
* Políticas por defecto.
* Persistencia del servicio.
* Integración con Netfilter.
* Reglas IPv4.
* Reglas IPv6.
* Disponibilidad del acceso SSH.
* Disponibilidad del acceso Cockpit.

La verificación se realizó mediante:

```bash
sudo ufw status numbered verbose
```

---

# Estado final

Política de entrada

```
DENY
```

Política de salida

```
ALLOW
```

Política de reenvío

```
DISABLED
```

Reglas habilitadas

| Servicio |   Puerto | Estado    |
| -------- | -------: | --------- |
| SSH      |   22/TCP | Permitido |
| Cockpit  | 9090/TCP | Permitido |

No existen otros puertos expuestos al exterior.

---

# Consideraciones de seguridad

La activación del firewall se realizó únicamente después de autorizar previamente el acceso SSH y Cockpit, evitando la pérdida de conectividad administrativa durante la implementación.

La política adoptada sigue el principio de **mínimo privilegio**, permitiendo únicamente los servicios expresamente autorizados.

Los puertos asociados a futuras aplicaciones de broadcast (MediaMTX, RTMP, SRT, HTTP y HTTPS) permanecerán cerrados hasta que dichos servicios sean implementados y validados.

---

# Resultado

**MISSION-008 finalizada satisfactoriamente.**

El servidor dispone ahora de un firewall operativo basado en UFW, integrado con Netfilter y configurado con una política de seguridad por defecto que bloquea todas las conexiones entrantes no autorizadas.

Esta implementación constituye la base de seguridad de la plataforma **EJTV Broadcast Platform** y será utilizada en las siguientes etapas de despliegue de servicios.
