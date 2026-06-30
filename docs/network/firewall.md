# Firewall del Servidor

## Descripción

El servidor de **EJTV Broadcast Platform** utiliza **Uncomplicated Firewall (UFW)** como mecanismo principal para la administración de reglas de filtrado de red.

UFW constituye una capa de abstracción sobre Netfilter e iptables, simplificando la administración del firewall sin perder compatibilidad con la infraestructura nativa del kernel Linux.

La configuración adoptada sigue el principio de **mínimo privilegio (Least Privilege)**, permitiendo únicamente el tráfico estrictamente necesario para la operación de la plataforma.

---

# Objetivos

La implementación del firewall tiene los siguientes objetivos:

* Reducir la superficie de ataque del servidor.
* Restringir conexiones entrantes no autorizadas.
* Proteger los servicios de administración.
* Facilitar la administración mediante reglas simples y documentadas.
* Mantener compatibilidad con Netfilter y systemd.
* Servir como base para la futura incorporación de servicios de broadcast.

---

# Arquitectura

```
                Internet
                    │
                    ▼
             +--------------+
             |     UFW      |
             |  Netfilter   |
             +--------------+
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
   SSH (22/TCP)          Cockpit (9090/TCP)
        │                       │
        └───────────┬───────────┘
                    │
                    ▼
             Ubuntu Server
```

Todo el tráfico no autorizado es descartado antes de alcanzar los servicios del sistema.

---

# Política de seguridad

La política general del firewall es:

| Dirección | Política |
| --------- | -------- |
| Entrada   | DENY     |
| Salida    | ALLOW    |
| Forward   | DENY     |

Esta configuración asegura que únicamente los servicios explícitamente autorizados sean accesibles desde la red.

---

# Servicios autorizados

Actualmente el servidor permite únicamente los siguientes servicios.

| Servicio | Puerto | Protocolo | Estado     |
| -------- | -----: | --------- | ---------- |
| SSH      |     22 | TCP       | Producción |
| Cockpit  |   9090 | TCP       | Producción |

Todos los demás puertos permanecen bloqueados.

---

# Servicios previstos

La arquitectura contempla la futura habilitación de los siguientes servicios.

| Servicio     |              Puerto | Estado    |
| ------------ | ------------------: | --------- |
| HTTP         |              80/TCP | Pendiente |
| HTTPS        |             443/TCP | Pendiente |
| RTMP         |            1935/TCP | Pendiente |
| SRT          |            8890/UDP | Pendiente |
| MediaMTX API | Según configuración | Pendiente |

Estos servicios permanecerán deshabilitados hasta su implementación y validación.

---

# Configuración implementada

Políticas por defecto

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

Servicios habilitados

```bash
sudo ufw allow 22/tcp comment "SSH"

sudo ufw allow 9090/tcp comment "Cockpit"
```

Activación

```bash
sudo ufw enable
```

---

# Administración

Consultar estado

```bash
sudo ufw status verbose
```

Consultar reglas numeradas

```bash
sudo ufw status numbered
```

Agregar una regla

```bash
sudo ufw allow <puerto>/<protocolo>
```

Eliminar una regla

```bash
sudo ufw delete <número>
```

Deshabilitar temporalmente

```bash
sudo ufw disable
```

Habilitar nuevamente

```bash
sudo ufw enable
```

---

# Integración con Netfilter

UFW administra automáticamente las reglas de Netfilter utilizando iptables.

No se recomienda modificar reglas directamente mediante iptables, ya que dichas modificaciones podrían perderse al actualizar la configuración de UFW.

Toda modificación debe realizarse mediante UFW.

---

# Validación

La configuración puede verificarse mediante:

```bash
sudo ufw status numbered verbose
```

También es posible verificar la integración con Netfilter utilizando:

```bash
sudo iptables -L -n
```

---

# Recuperación

Si una modificación provoca pérdida de conectividad, el acceso físico o mediante consola KVM permitirá ejecutar:

```bash
sudo ufw disable
```

Una vez recuperado el acceso, las reglas podrán corregirse y habilitarse nuevamente.

---

# Buenas prácticas

* No abrir puertos innecesarios.
* Documentar cada nueva regla incorporada.
* Utilizar comentarios descriptivos en las reglas.
* Revisar periódicamente las reglas configuradas.
* Mantener la política **Default Deny**.
* Habilitar únicamente servicios previamente validados.
* Evitar el uso simultáneo de reglas manuales de iptables y UFW.

---

# Referencias relacionadas

* `docs/security/hardening.md`
* `docs/network/ports.md`
* `docs/services/ssh.md`
* `docs/services/cockpit.md`
* `MISSION_008.md`
* `BL-004.md`


# Firewall y Política de Seguridad de Red

## Plataforma EJTV Broadcast Platform

**Documento:** docs/network/firewall.md

**Versión:** 1.1

**Última actualización:** 2026-06-29

---

# 1. Objetivo

Este documento establece la política oficial de seguridad de red utilizada por la plataforma **EJTV Broadcast Platform**.

Su finalidad es definir los criterios para la exposición de servicios, administración de puertos y configuración del firewall, garantizando un entorno seguro, reproducible y fácilmente administrable.

Toda modificación relacionada con puertos o servicios de red deberá documentarse previamente en este documento y reflejarse posteriormente en la línea base correspondiente.

---

# 2. Filosofía de seguridad

La arquitectura de seguridad de la plataforma se basa en los siguientes principios:

* Principio de mínimo privilegio.
* Exponer únicamente los servicios estrictamente necesarios.
* Mantener documentados todos los puertos abiertos.
* Separar claramente los entornos de laboratorio y producción.
* Integrar el firewall como parte del proceso de instalación de cada servicio.
* Verificar el estado del firewall después de cualquier modificación.

La seguridad no depende únicamente del firewall; forma parte del diseño integral de la plataforma.

---

# 3. Estado actual

Al cierre de la **MISSION-010** el firewall del servidor permanece deshabilitado.

Estado observado:

```bash
sudo ufw status verbose
```

Resultado:

```text
Status: inactive
```

Esta decisión fue adoptada para facilitar las pruebas de integración de los servicios durante la fase inicial del proyecto.

La activación definitiva del firewall se realizará una vez finalizada la integración de los servicios principales.

---

# 4. Servicios autorizados

Actualmente la plataforma incorpora los siguientes servicios:

| Servicio   | Puerto | Protocolo | Estado         |
| ---------- | ------ | --------- | -------------- |
| SSH        | 22     | TCP       | Producción     |
| Cockpit    | 9090   | TCP       | Administración |
| RTSP       | 8554   | TCP       | Laboratorio    |
| RTP        | 8000   | UDP       | Laboratorio    |
| RTCP       | 8001   | UDP       | Laboratorio    |
| RTMP       | 1935   | TCP       | Laboratorio    |
| HLS        | 8888   | TCP       | Laboratorio    |
| WebRTC     | 8889   | TCP       | Laboratorio    |
| WebRTC ICE | 8189   | UDP       | Laboratorio    |
| SRT        | 8890   | UDP       | Laboratorio    |
| MoQ        | 8892   | TCP / UDP | Experimental   |

---

# 5. Política de apertura de puertos

## Entorno de laboratorio

Durante las pruebas de desarrollo podrán habilitarse todos los puertos requeridos por los servicios implementados.

El objetivo es facilitar la validación funcional y el diagnóstico del sistema.

---

## Entorno de producción

En producción deberán permanecer abiertos únicamente los puertos necesarios para los servicios efectivamente utilizados.

Se recomienda:

* mantener SSH restringido a la red administrativa;
* limitar Cockpit a direcciones IP autorizadas;
* deshabilitar protocolos multimedia no utilizados;
* bloquear cualquier puerto no documentado.

---

# 6. Reglas recomendadas de UFW

## Instalación

```bash
sudo apt install ufw
```

---

## Habilitar UFW

```bash
sudo ufw enable
```

---

## Permitir SSH

```bash
sudo ufw allow 22/tcp
```

---

## Permitir Cockpit

```bash
sudo ufw allow 9090/tcp
```

---

## Permitir RTSP

```bash
sudo ufw allow 8554/tcp
```

---

## Permitir RTP

```bash
sudo ufw allow 8000/udp
```

---

## Permitir RTCP

```bash
sudo ufw allow 8001/udp
```

---

## Permitir RTMP

```bash
sudo ufw allow 1935/tcp
```

---

## Permitir HLS

```bash
sudo ufw allow 8888/tcp
```

---

## Permitir WebRTC

```bash
sudo ufw allow 8889/tcp
sudo ufw allow 8189/udp
```

---

## Permitir SRT

```bash
sudo ufw allow 8890/udp
```

---

## Permitir MoQ

```bash
sudo ufw allow 8892/tcp
sudo ufw allow 8892/udp
```

---

# 7. Validación

Verificar estado del firewall:

```bash
sudo ufw status verbose
```

---

Verificar reglas instaladas:

```bash
sudo ufw status numbered
```

---

Comprobar los puertos abiertos:

```bash
ss -tuln
```

---

Verificar servicios activos:

```bash
systemctl status mediamtx
```

---

# 8. Pruebas funcionales

## Prueba de reglas

Habilitar el firewall:

```bash
sudo ufw enable
```

Comprobar que los servicios continúan accesibles desde un cliente autorizado.

---

## Prueba de reinicio

Reiniciar el servidor:

```bash
sudo reboot
```

Verificar nuevamente:

```bash
sudo ufw status
```

y

```bash
ss -tuln
```

---

## Prueba de acceso

Desde otro equipo verificar:

* acceso SSH;
* acceso Cockpit;
* acceso RTSP;
* acceso HLS.

Los servicios autorizados deberán responder correctamente.

---

# 9. Recuperación

Si una regla genera problemas durante las pruebas:

Deshabilitar temporalmente el firewall:

```bash
sudo ufw disable
```

Eliminar una regla específica:

```bash
sudo ufw delete <número>
```

Restablecer la configuración:

```bash
sudo ufw reset
```

Volver a aplicar las reglas documentadas antes de habilitar nuevamente el servicio.

---

# 10. Troubleshooting

## El servicio dejó de responder

Verificar:

```bash
sudo ufw status verbose
```

Comprobar que el puerto correspondiente se encuentra permitido.

---

## El puerto continúa cerrado

Verificar primero que el servicio esté en ejecución:

```bash
systemctl status mediamtx
```

Posteriormente comprobar que exista una regla para dicho puerto.

---

## El firewall bloquea una conexión legítima

Revisar las reglas activas:

```bash
sudo ufw status numbered
```

Identificar la regla responsable y modificarla únicamente si se encuentra documentada y justificada.

---

# 11. Engineering Notes

Durante la fase de desarrollo se decidió mantener el firewall deshabilitado para facilitar la integración progresiva de los servicios y simplificar las tareas de diagnóstico.

Esta decisión es válida únicamente para el entorno de laboratorio.

Antes del despliegue en producción se deberá realizar una revisión integral de todos los puertos documentados, habilitando únicamente aquellos estrictamente necesarios para la operación del sistema.

La política oficial de la plataforma establece que ningún puerto podrá permanecer abierto sin estar documentado en `docs/network/ports.md`.

---

# 12. Checklist

* [x] Filosofía de seguridad definida.
* [x] Estado actual documentado.
* [x] Política de laboratorio documentada.
* [x] Política de producción documentada.
* [x] Reglas recomendadas de UFW incluidas.
* [x] Procedimientos de validación documentados.
* [x] Pruebas funcionales descritas.
* [x] Procedimientos de recuperación incluidos.
* [x] Troubleshooting documentado.
* [x] Notas de ingeniería registradas.
