# PROC-001

> *"Todo procedimiento debe permitir reproducir una operación de manera controlada y, cuando sea técnicamente posible, restaurar el estado anterior del sistema."*

---

# Procedimiento Operativo

## Identificador

PROC-001

---

## Título

Administración del controlador Broadcom STA

---

## Estado

🟢 Vigente

---

## Fecha

26 de junio de 2026

---

## Proyecto

EJTV Broadcast Platform

---

## Relacionado con

* BL-001
* MISIÓN 004
* INC-001
* ADR-001

---

# 1. Objetivo

Establecer el procedimiento oficial para administrar el controlador
**Broadcom STA** instalado en el servidor **ejtv-01**, incluyendo tanto su
desinstalación como su eventual reinstalación.

El procedimiento busca garantizar que cualquier modificación realizada sobre el
controlador pueda ejecutarse de manera controlada, documentada y reversible.

---

# 2. Alcance

Este procedimiento aplica únicamente al servidor:

```text
ejtv-01
```

No debe utilizarse sobre otros equipos sin verificar previamente el hardware
instalado y la arquitectura de comunicaciones correspondiente.

---

# 3. Contexto

Durante la ejecución de la **MISIÓN 004** se detectó una incidencia relacionada
con el paquete **broadcom-sta-dkms**, el cual no logró compilar correctamente
el módulo correspondiente al kernel Linux 6.17.

El análisis posterior determinó que el servidor opera exclusivamente mediante
interfaces Ethernet y que la interfaz Broadcom no participa actualmente en la
arquitectura de **EJTV Broadcast Platform**.

La decisión arquitectónica correspondiente quedó documentada en **ADR-001**.

---

# 4. Requisitos

Antes de ejecutar este procedimiento deberán cumplirse las siguientes
condiciones.

* Acceso administrativo mediante sudo.
* Copia de seguridad de la documentación.
* Confirmación de que la conectividad del servidor utiliza Ethernet.
* Verificación del estado actual del gestor de paquetes.

---

# 5. Verificación previa

Antes de modificar el sistema se recomienda ejecutar las siguientes
verificaciones.

## Hardware de red

```bash
lspci | grep -i -E "network|wireless|broadcom"
```

---

## Estado de las interfaces

```bash
nmcli device status
```

---

## Estado del paquete

```bash
apt policy broadcom-sta-dkms
```

---

## Estado de DKMS

```bash
dkms status
```

---

## Estado del gestor de paquetes

```bash
sudo dpkg --audit
```

Toda esta información deberá conservarse como evidencia previa a la ejecución
del procedimiento.

---

# 6. Procedimiento de desinstalación

## Paso 1

Eliminar el paquete Broadcom STA.

```bash
sudo apt purge broadcom-sta-dkms
```

---

## Paso 2

Eliminar dependencias que ya no sean necesarias.

```bash
sudo apt autoremove -y
```

---

## Paso 3

Limpiar la caché de paquetes.

```bash
sudo apt clean
```

---

## Paso 4

Completar cualquier configuración pendiente.

```bash
sudo dpkg --configure -a
```

---

## Paso 5

Actualizar nuevamente el índice de paquetes.

```bash
sudo apt update
```

---

# 7. Validación posterior

Una vez finalizada la desinstalación deberán realizarse las siguientes
verificaciones.

## Estado de DKMS

```bash
dkms status
```

No deberá aparecer ninguna entrada correspondiente a Broadcom STA.

---

## Estado del gestor de paquetes

```bash
sudo dpkg --audit
```

No deberán existir paquetes pendientes.

---

## Estado de los servicios

```bash
systemctl --failed
```

El resultado esperado es:

```text
0 loaded units listed.
```

---

## Estado de las interfaces

```bash
nmcli device status
```

Las interfaces Ethernet deberán permanecer operativas.

---

# 8. Procedimiento de reinstalación

Si en el futuro fuera necesario volver a utilizar la interfaz inalámbrica
Broadcom, el controlador podrá reinstalarse mediante el siguiente
procedimiento.

---

## Paso 1

Actualizar el índice de paquetes.

```bash
sudo apt update
```

---

## Paso 2

Instalar nuevamente el controlador.

```bash
sudo apt install broadcom-sta-dkms
```

---

## Paso 3

Verificar el estado de DKMS.

```bash
dkms status
```

---

## Paso 4

Verificar el reconocimiento del hardware.

```bash
lspci | grep -i broadcom
```

---

## Paso 5

Verificar el estado de las interfaces.

```bash
nmcli device status
```

---

# 9. Procedimiento de reversión

Si durante la desinstalación se detectara algún comportamiento inesperado,
deberá interrumpirse el procedimiento y reinstalar inmediatamente el paquete
mediante el procedimiento descrito en la sección anterior.

Posteriormente deberán repetirse todas las verificaciones de validación para
confirmar que el servidor recuperó su estado operativo.

---

# 10. Riesgos

| Riesgo                                   | Mitigación                                    |
| ---------------------------------------- | --------------------------------------------- |
| Pérdida de conectividad inalámbrica      | El servidor utiliza Ethernet                  |
| Error durante la eliminación             | Procedimiento de reversión                    |
| Reinstalación incompatible con el kernel | Validar DKMS antes de cerrar el procedimiento |

---

# 11. Evidencias requeridas

La ejecución del procedimiento deberá generar como mínimo las siguientes
evidencias.

* Estado inicial de DKMS.
* Estado inicial de NetworkManager.
* Registro de la eliminación del paquete.
* Estado final de DKMS.
* Estado final del gestor de paquetes.
* Confirmación de operación normal del servidor.

---

# 12. Criterios de aceptación

El procedimiento se considerará completado cuando:

* El gestor de paquetes no presente errores.
* DKMS no registre incidencias.
* Las interfaces Ethernet permanezcan operativas.
* El servidor continúe funcionando normalmente.
* La incidencia **INC-001** pueda declararse resuelta.

---

# 13. Relación documental

Este procedimiento forma parte del sistema documental de
**EJTV Broadcast Platform**.

Se encuentra relacionado con:

| Documento  | Propósito                                              |
| ---------- | ------------------------------------------------------ |
| BL-001     | Línea base del servidor                                |
| MISIÓN 004 | Actividad que originó el procedimiento                 |
| INC-001    | Incidencia técnica asociada                            |
| ADR-001    | Decisión arquitectónica que justifica el procedimiento |
| updates.md | Evidencia de la ejecución                              |

---

# Conclusión

El presente procedimiento establece la metodología oficial para administrar el
controlador **Broadcom STA** dentro de **EJTV Broadcast Platform**.

Más allá de la incidencia que motivó su creación, este documento define un
modelo de trabajo basado en operaciones controladas, evidencia técnica,
validación posterior y capacidad de reversión.

Este enfoque garantiza que cualquier modificación realizada sobre la
infraestructura pueda ejecutarse de manera segura, reproducible y plenamente
trazable durante toda la vida útil del proyecto.

