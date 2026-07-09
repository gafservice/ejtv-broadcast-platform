# EJTV Control Center - Arquitectura Inicial

## Objetivo

El EJTV Control Center será el sistema de administración, monitoreo y operación de la plataforma EJTV.

Su función principal será permitir la administración remota de:

- Servicios
- Canales
- Protocolos
- Clientes
- Usuarios
- Alarmas
- Logs
- Estadísticas

sin exponer directamente el servidor Linux al operador.

---

## Principio de diseño

El operador no debe ejecutar comandos Linux.

El operador debe interactuar con una interfaz segura.

Ejemplo:

```text
Botón: Reiniciar ENLACE
        ↓
Backend EJTV
        ↓
systemctl restart ejtv-enlace

