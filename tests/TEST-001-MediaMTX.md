# TEST-001

# Validación de Instalación de MediaMTX

**Documento:** TEST-001-MediaMTX.md

**Versión:** 1.0

**Fecha:** 2026-06-29

**Estado:** Aprobado

---

# 1. Objetivo

Validar que el servidor **MediaMTX** fue instalado correctamente dentro de la plataforma **EJTV Broadcast Platform**, verificando su integridad, configuración, funcionamiento como servicio `systemd` y disponibilidad de todos los protocolos de transmisión habilitados.

---

# 2. Alcance

Esta prueba verifica:

* instalación del binario;
* integridad mediante SHA256;
* estructura de directorios;
* configuración inicial;
* funcionamiento del servicio systemd;
* inicio automático;
* apertura de puertos;
* funcionamiento del proceso;
* registros del sistema.

No se validan aún transmisiones de audio o video, las cuales serán objeto de pruebas posteriores.

---

# 3. Entorno de prueba

| Parámetro         | Valor                     |
| ----------------- | ------------------------- |
| Plataforma        | EJTV Broadcast Platform   |
| Sistema Operativo | Ubuntu Server 24.04.4 LTS |
| Kernel            | Linux 6.17.0-35-generic   |
| Arquitectura      | x86_64                    |
| Hardware          | Apple Mac Pro 5,1         |
| Usuario           | ejtv                      |
| Fecha             | 2026-06-29                |

---

# 4. Requisitos previos

Antes de ejecutar esta prueba deberá verificarse:

* Ubuntu operativo.
* SSH funcionando.
* NTP sincronizado.
* Acceso administrativo mediante `sudo`.
* Directorio `/opt/ejtv/mediamtx` existente.

---

# 5. Procedimiento

## 5.1 Verificar instalación

```bash
ls -lah /opt/ejtv/mediamtx
```

Resultado esperado:

La estructura de directorios deberá encontrarse completa.

---

## 5.2 Verificar binario

```bash
/opt/ejtv/mediamtx/bin/mediamtx --version
```

Resultado esperado:

```text
v1.19.0
```

---

## 5.3 Verificar configuración

```bash
ls -lah /opt/ejtv/mediamtx/config
```

Resultado esperado:

Debe existir el archivo:

```text
mediamtx.yml
```

---

## 5.4 Verificar servicio

```bash
systemctl status mediamtx
```

Resultado esperado:

```text
Active: active (running)
```

---

## 5.5 Verificar inicio automático

```bash
systemctl is-enabled mediamtx
```

Resultado esperado:

```text
enabled
```

---

## 5.6 Verificar proceso

```bash
ps -ef | grep mediamtx | grep -v grep
```

Resultado esperado:

El proceso MediaMTX deberá encontrarse en ejecución.

---

## 5.7 Verificar puertos

```bash
ss -tuln | grep -E "8554|1935|8888|8889|8890|8892|8000|8001|8189"
```

Resultado esperado:

Todos los puertos correspondientes a los protocolos habilitados deberán encontrarse en estado `LISTEN` (TCP) o `UNCONN` (UDP).

---

## 5.8 Verificar journal

```bash
journalctl -u mediamtx -n 30 --no-pager
```

Resultado esperado:

No deberán observarse errores durante el inicio del servicio.

---

## 5.9 Verificar estructura

```bash
tree -L 3 /opt/ejtv/mediamtx
```

Resultado esperado:

La estructura deberá coincidir con la línea base BL-005.

---

## 5.10 Verificar registro de versión

```bash
cat /opt/ejtv/mediamtx/releases/installed_versions.log
```

Resultado esperado:

Debe registrarse la versión instalada y el hash SHA256 correspondiente.

---

# 6. Criterios de aceptación

La prueba se considera satisfactoria cuando:

* El servicio inicia correctamente.
* El binario responde con la versión instalada.
* La configuración es accesible.
* El servicio permanece activo.
* El inicio automático está habilitado.
* Todos los puertos aparecen disponibles.
* No existen errores críticos en el `journal`.
* La estructura de directorios coincide con la línea base.

---

# 7. Evidencias

Durante la ejecución de esta prueba deberán almacenarse:

* Captura del estado del servicio.
* Salida de `systemctl status`.
* Salida de `ss -tuln`.
* Salida de `journalctl`.
* Captura del árbol de directorios.
* Registro de la versión instalada.

Las evidencias deberán conservarse dentro de:

```text
docs/evidencias/mission-010/
```

---

# 8. Resultado obtenido

| Verificación            | Resultado |
| ----------------------- | :-------: |
| Binario instalado       |     ✅     |
| SHA256 válido           |     ✅     |
| Configuración instalada |     ✅     |
| Servicio systemd        |     ✅     |
| Inicio automático       |     ✅     |
| Proceso activo          |     ✅     |
| Puertos abiertos        |     ✅     |
| Journal sin errores     |     ✅     |
| Registro de versión     |     ✅     |
| Línea base actualizada  |     ✅     |

---

# 9. Conclusiones

La instalación de **MediaMTX v1.19.0** fue validada satisfactoriamente.

El servidor quedó integrado como servicio nativo de la plataforma EJTV Broadcast Platform, iniciando automáticamente durante el arranque del sistema y exponiendo correctamente los protocolos RTSP, RTMP, HLS, WebRTC, SRT y MoQ.

Los resultados obtenidos cumplen con los criterios de aceptación establecidos para la MISSION-010.

---

# 10. Referencias

* `docs/services/mediamtx.md`
* `docs/missions/MISSION-010.md`
* `docs/baseline/BL-005.md`
* `docs/network/ports.md`
* `docs/network/firewall.md`
* `CHANGELOG/CHANGELOG-m010.md`

---

# 11. Checklist final

* [x] Instalación validada.
* [x] Integridad verificada.
* [x] Configuración comprobada.
* [x] Servicio operativo.
* [x] Inicio automático confirmado.
* [x] Puertos verificados.
* [x] Journal revisado.
* [x] Evidencias almacenadas.
* [x] Línea base actualizada.
* [x] Documentación completada.
