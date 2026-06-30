# Puertos de Red

## Descripción

Este documento define los puertos TCP y UDP utilizados por la plataforma **EJTV Broadcast Platform**, indicando su propósito, estado operativo y política de exposición a la red.

Su objetivo es mantener una referencia centralizada para la administración del firewall, los servicios del sistema y la arquitectura de comunicaciones.

---

# Política general

La plataforma adopta una política de seguridad basada en el principio de **mínimo privilegio**.

En consecuencia:

* Todos los puertos permanecen cerrados por defecto.
* Únicamente se habilitan los servicios estrictamente necesarios.
* La apertura de nuevos puertos requiere una justificación técnica y su correspondiente documentación.

---

# Servicios actualmente habilitados

| Puerto | Protocolo | Servicio | Estado     |
| -----: | --------- | -------- | ---------- |
|     22 | TCP       | SSH      | Producción |
|   9090 | TCP       | Cockpit  | Producción |

Estos son los únicos puertos accesibles desde la red en la configuración actual del servidor.

---

# Servicios internos

Los siguientes puertos corresponden a servicios internos del sistema operativo y no deben exponerse hacia redes externas.

|           Puerto | Protocolo | Servicio         | Observaciones                     |
| ---------------: | --------- | ---------------- | --------------------------------- |
|               53 | TCP/UDP   | systemd-resolved | Resolución DNS local              |
|              631 | TCP       | CUPS             | Escucha únicamente en localhost   |
| Puertos efímeros | TCP/UDP   | Sistema          | Uso interno del sistema operativo |

Estos servicios permanecen protegidos por la configuración del firewall y no requieren reglas adicionales.

---

# Servicios planificados

Las siguientes aplicaciones serán incorporadas en futuras etapas del proyecto.

| Puerto | Protocolo | Servicio                               | Estado    |
| -----: | --------- | -------------------------------------- | --------- |
|     80 | TCP       | HTTP                                   | Pendiente |
|    443 | TCP       | HTTPS                                  | Pendiente |
|   1935 | TCP       | RTMP                                   | Pendiente |
|   8554 | TCP       | RTSP (MediaMTX)                        | Pendiente |
|   8888 | TCP       | Interfaz Web MediaMTX (si se habilita) | Pendiente |
|   8890 | UDP       | SRT                                    | Pendiente |

Estos puertos permanecerán cerrados hasta que el servicio correspondiente sea implementado y validado.

---

# Relación con UFW

La administración de puertos se realiza exclusivamente mediante UFW.

La apertura de un nuevo puerto debe acompañarse de:

1. Implementación del servicio.
2. Validación funcional.
3. Registro en el firewall.
4. Actualización de este documento.
5. Actualización del documento del servicio correspondiente.

---

# Procedimiento para habilitar un puerto

Ejemplo:

```bash
sudo ufw allow 1935/tcp comment "RTMP"
```

Posteriormente deberá verificarse:

```bash
sudo ufw status numbered
```

y confirmar que el servicio escucha correctamente mediante:

```bash
ss -tln
```

o

```bash
ss -uln
```

según corresponda.

---

# Procedimiento para eliminar un puerto

Consultar las reglas:

```bash
sudo ufw status numbered
```

Eliminar una regla:

```bash
sudo ufw delete <número>
```

Verificar nuevamente el estado del firewall.

---

# Verificación de puertos

Puertos TCP

```bash
ss -tln
```

Puertos UDP

```bash
ss -uln
```

Estado del firewall

```bash
sudo ufw status verbose
```

Reglas activas

```bash
sudo ufw status numbered
```

---

# Buenas prácticas

* Mantener únicamente los puertos necesarios.
* Evitar la exposición de servicios internos.
* Documentar toda modificación.
* Utilizar comentarios descriptivos en las reglas de UFW.
* Verificar la apertura del puerto antes de poner un servicio en producción.
* Revisar periódicamente los puertos en escucha para detectar servicios no previstos.

---

# Estado actual de la plataforma

| Categoría                        |     Cantidad |
| -------------------------------- | -----------: |
| Puertos TCP abiertos             |            2 |
| Puertos UDP abiertos al exterior |            0 |
| Servicios públicos               | SSH, Cockpit |
| Política de entrada              |         DENY |
| Política de salida               |        ALLOW |

---

# Referencias

* `docs/network/firewall.md`
* `docs/security/hardening.md`
* `docs/services/ssh.md`
* `docs/services/cockpit.md`
* `BL-004.md`


# Gestión de Puertos de Red

## Plataforma EJTV Broadcast Platform

**Documento:** docs/network/ports.md

**Versión:** 1.1

**Última actualización:** 2026-06-29

---

# 1. Objetivo

Este documento define la asignación oficial de puertos TCP y UDP utilizados por la plataforma **EJTV Broadcast Platform**.

Su propósito es mantener un registro único de los servicios de red implementados, evitando conflictos entre aplicaciones y facilitando las tareas de instalación, mantenimiento, monitoreo y seguridad.

Toda incorporación de nuevos servicios deberá reflejarse en este documento antes de ser considerada parte de la línea base del sistema.

---

# 2. Filosofía de diseño

La administración de puertos de la plataforma sigue los siguientes principios:

* Cada servicio utiliza únicamente los puertos estrictamente necesarios.
* Se evita la reutilización de puertos entre componentes distintos.
* Todos los puertos utilizados deben estar documentados.
* Los puertos expuestos hacia redes externas deberán justificarse técnicamente.
* Los servicios internos podrán permanecer restringidos mediante políticas de firewall.

---

# 3. Servicios actualmente implementados

## SSH

| Parámetro  | Valor                                    |
| ---------- | ---------------------------------------- |
| Puerto     | 22                                       |
| Protocolo  | TCP                                      |
| Servicio   | OpenSSH                                  |
| Estado     | Producción                               |
| Exposición | Permitida únicamente para administración |

---

## Cockpit

| Parámetro  | Valor                         |
| ---------- | ----------------------------- |
| Puerto     | 9090                          |
| Protocolo  | TCP                           |
| Servicio   | Cockpit                       |
| Estado     | Laboratorio                   |
| Exposición | Red administrativa únicamente |

---

## MediaMTX

### RTSP

| Parámetro     | Valor                                   |
| ------------- | --------------------------------------- |
| Puerto        | 8554                                    |
| Protocolo     | TCP                                     |
| Finalidad     | Recepción y distribución de flujos RTSP |
| Estado actual | Activo                                  |
| Producción    | Sí                                      |
| Observaciones | Puerto principal del servidor RTSP      |

---

### RTP

| Parámetro     | Valor                                                        |
| ------------- | ------------------------------------------------------------ |
| Puerto        | 8000                                                         |
| Protocolo     | UDP                                                          |
| Finalidad     | Transporte RTP                                               |
| Estado actual | Activo                                                       |
| Producción    | Sí (si se utiliza RTSP sobre UDP)                            |
| Observaciones | Puede deshabilitarse si únicamente se utiliza RTSP sobre TCP |

---

### RTCP

| Parámetro     | Valor                 |
| ------------- | --------------------- |
| Puerto        | 8001                  |
| Protocolo     | UDP                   |
| Finalidad     | Control RTCP          |
| Estado actual | Activo                |
| Producción    | Sí                    |
| Observaciones | Asociado al flujo RTP |

---

### RTMP

| Parámetro     | Valor                                   |
| ------------- | --------------------------------------- |
| Puerto        | 1935                                    |
| Protocolo     | TCP                                     |
| Finalidad     | Recepción de transmisiones RTMP         |
| Estado actual | Activo                                  |
| Producción    | Opcional                                |
| Observaciones | Principalmente utilizado por OBS Studio |

---

### HLS

| Parámetro     | Valor                            |
| ------------- | -------------------------------- |
| Puerto        | 8888                             |
| Protocolo     | TCP                              |
| Finalidad     | Publicación HTTP Live Streaming  |
| Estado actual | Activo                           |
| Producción    | Sí                               |
| Observaciones | Accesible mediante navegador web |

---

### WebRTC

| Parámetro     | Valor                              |
| ------------- | ---------------------------------- |
| Puerto        | 8889                               |
| Protocolo     | TCP                                |
| Finalidad     | Señalización WebRTC                |
| Estado actual | Activo                             |
| Producción    | Sí                                 |
| Observaciones | Interfaz HTTP para clientes WebRTC |

---

### WebRTC ICE

| Parámetro     | Valor                                     |
| ------------- | ----------------------------------------- |
| Puerto        | 8189                                      |
| Protocolo     | UDP                                       |
| Finalidad     | Intercambio ICE                           |
| Estado actual | Activo                                    |
| Producción    | Sí                                        |
| Observaciones | Necesario para conexiones WebRTC directas |

---

### SRT

| Parámetro     | Valor                                  |
| ------------- | -------------------------------------- |
| Puerto        | 8890                                   |
| Protocolo     | UDP                                    |
| Finalidad     | Secure Reliable Transport              |
| Estado actual | Activo                                 |
| Producción    | Opcional                               |
| Observaciones | Utilizado para enlaces de alta calidad |

---

### MoQ

| Parámetro     | Valor                                                                                    |
| ------------- | ---------------------------------------------------------------------------------------- |
| Puerto        | 8892                                                                                     |
| Protocolo     | TCP / UDP                                                                                |
| Finalidad     | Media over QUIC                                                                          |
| Estado actual | Activo                                                                                   |
| Producción    | Experimental                                                                             |
| Observaciones | Tecnología en evolución; mantener únicamente para pruebas mientras se evalúa su adopción |

---

# 4. Resumen general

| Puerto | TCP | UDP | Servicio   |   Producción   |
| ------ | :-: | :-: | ---------- | :------------: |
| 22     |  ✔  |     | SSH        |        ✔       |
| 9090   |  ✔  |     | Cockpit    | Administración |
| 1935   |  ✔  |     | RTMP       |    Opcional    |
| 8554   |  ✔  |     | RTSP       |        ✔       |
| 8000   |     |  ✔  | RTP        |        ✔       |
| 8001   |     |  ✔  | RTCP       |        ✔       |
| 8888   |  ✔  |     | HLS        |        ✔       |
| 8889   |  ✔  |     | WebRTC     |        ✔       |
| 8189   |     |  ✔  | WebRTC ICE |        ✔       |
| 8890   |     |  ✔  | SRT        |    Opcional    |
| 8892   |  ✔  |  ✔  | MoQ        |  Experimental  |

---

# 5. Validación

Los puertos activos pueden verificarse mediante:

```bash
ss -tuln
```

Para revisar únicamente los puertos asociados a MediaMTX:

```bash
ss -tuln | grep -E "8554|1935|8888|8889|8890|8892|8000|8001|8189"
```

Verificar el servicio:

```bash
systemctl status mediamtx
```

Comprobar el proceso en ejecución:

```bash
ps -ef | grep mediamtx
```

---

# 6. Pruebas funcionales

## Verificación del servicio

```bash
systemctl start mediamtx
```

Resultado esperado:

* Servicio activo.
* Sin errores en `journalctl`.

---

## Verificación de puertos

```bash
ss -tuln
```

Resultado esperado:

Todos los puertos definidos para MediaMTX aparecen en estado `LISTEN` (TCP) o `UNCONN` (UDP), según corresponda.

---

## Verificación de registros

```bash
journalctl -u mediamtx -n 30
```

Resultado esperado:

Inicialización correcta de RTSP, RTMP, HLS, WebRTC, SRT y MoQ, sin mensajes de error.

---

# 7. Recomendaciones de seguridad

* Mantener abiertos únicamente los puertos requeridos por los servicios utilizados.
* Restringir el acceso a SSH (22) y Cockpit (9090) a la red administrativa.
* Deshabilitar protocolos que no sean necesarios para el entorno de producción.
* Revisar periódicamente la lista de puertos activos mediante `ss -tuln`.
* Aplicar reglas de UFW acordes con el perfil de despliegue (laboratorio o producción).

---

# 8. Troubleshooting

## El puerto no aparece abierto

Verificar:

```bash
systemctl status mediamtx
```

Comprobar los registros:

```bash
journalctl -u mediamtx
```

---

## Conflicto de puerto

Identificar el proceso que utiliza el puerto:

```bash
sudo ss -tulpn
```

o

```bash
sudo lsof -i :8554
```

Liberar el puerto o modificar la configuración de MediaMTX si existe un conflicto justificado.

---

## El servicio no inicia

Validar la configuración:

```bash
/opt/ejtv/mediamtx/bin/mediamtx /opt/ejtv/mediamtx/config/mediamtx.yml
```

Revisar el archivo de configuración y el registro del servicio antes de reiniciarlo.

---

# 9. Engineering Notes

La plataforma adopta una política de documentación explícita de puertos para garantizar la trazabilidad de todas las comunicaciones de red.

La incorporación de nuevos servicios deberá reflejarse primero en este documento y posteriormente en las reglas del firewall, evitando configuraciones implícitas o puertos abiertos sin documentación.

---

# 10. Checklist

* [x] Todos los puertos documentados.
* [x] Protocolos identificados.
* [x] Servicios asociados.
* [x] Estado de producción definido.
* [x] Comandos de validación incluidos.
* [x] Procedimientos de prueba documentados.
* [x] Recomendaciones de seguridad incorporadas.
* [x] Procedimientos de diagnóstico incluidos.

