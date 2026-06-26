    # MISIÓN 001

---

## Fecha

25 de junio de 2026

---

## Proyecto

EJTV Broadcast Platform

---

## Servidor

ejtv-01

---

## Objetivo

Construir el primer nodo de la plataforma.

---

## Actividades realizadas

- Instalación de Ubuntu 24.04.1 LTS.
- Preparación del SSD Samsung.
- Definición del hostname `ejtv-01`.
- Creación del usuario administrativo.
- Configuración inicial del servidor.

---

## Decisiones de ingeniería

- Se utilizó el particionado automático del instalador.
- No se empleó LVM.
- No se utilizó cifrado del disco.
- Los discos de datos permanecieron intactos.

---

## Lecciones aprendidas

- El instalador Desktop de Ubuntu simplifica la creación de la partición EFI.
- Es preferible utilizar el instalador estándar cuando no aporta valor complicar el particionado.
- La ingeniería debe concentrarse en la arquitectura de la plataforma y no en controlar detalles que el instalador resuelve correctamente.

---

## Estado

✅ Misión completada.

---

## Próxima misión

**MISIÓN 002**

Verificación inicial del servidor y actualización completa del sistema.