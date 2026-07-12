# EJTV Control Center

# CHANGELOG

**Versión del documento:** 1.0

**Estado:** Vigente

---

# Propósito

Este documento registra la evolución funcional, técnica y arquitectónica del EJTV Control Center.

Su objetivo es mantener una trazabilidad clara de los cambios realizados durante el desarrollo del componente, permitiendo conocer:

- qué fue incorporado;
- qué fue modificado;
- qué fue corregido;
- qué fue eliminado;
- en cuál misión se realizó el cambio;
- qué documentación fue actualizada.

El CHANGELOG deberá actualizarse como parte obligatoria del cierre de cada misión.

---

# Convenciones

Los cambios se clasificarán utilizando las siguientes categorías:

## Added

Funcionalidades, documentos, módulos o capacidades nuevas.

## Changed

Modificaciones realizadas sobre elementos existentes.

## Fixed

Correcciones de errores funcionales, técnicos o documentales.

## Deprecated

Funciones que continúan disponibles, pero cuyo uso será retirado en futuras versiones.

## Removed

Funciones, archivos o componentes eliminados.

## Security

Cambios relacionados con autenticación, autorización, auditoría, certificados o protección de la plataforma.

## Documentation

Creación o actualización de documentación técnica, funcional u operativa.

---

# Estado de versiones

| Versión | Misión | Estado | Descripción |
|---|---|---|---|
| 0.1.0 | MISSION-017 | En cierre | Arquitectura y fundación documental |
| 0.2.0 | MISSION-018 | Pendiente | Fundación del Backend |
| 0.3.0 | MISSION-019 | Pendiente | API y servicios iniciales |
| 0.4.0 | MISSION-020 | Pendiente | Frontend y Dashboard |
| 1.0.0 | Por definir | Pendiente | Primera versión operativa |

---

# [0.1.0] — MISSION-017

## Estado

En proceso de cierre.

## Objetivo

Diseñar la arquitectura y establecer la fundación documental del EJTV Control Center antes de iniciar su implementación.

---

## Added

- Estructura inicial del subproyecto `control-center/`.
- Separación entre Backend, Frontend, configuración, documentación, pruebas y registros.
- Arquitectura modular orientada a entidades operativas.
- Concepto de Canal como unidad principal de administración.
- Separación entre Usuarios del Control Center y Clientes consumidores de servicios.
- Modelo de Nodo para soportar infraestructura distribuida.
- Modelo de Adaptadores para desacoplar la lógica de negocio de MediaMTX, FFmpeg, Linux y systemd.
- Definición inicial de API REST versionada.
- Modelo inicial de roles y permisos.
- Navegación general del Control Center.
- Reglas iniciales de identidad visual y comportamiento de interfaz.
- ROADMAP específico del Control Center.
- CHANGELOG específico del Control Center.

---

## Documentation

Se crearon o ampliaron los siguientes documentos:

```text
control-center/README.md
control-center/ROADMAP.md
control-center/CHANGELOG.md
control-center/docs/ARCHITECTURE.md
control-center/docs/MODULES.md
control-center/docs/USER_STORIES.md
control-center/docs/DATA_MODEL.md
control-center/docs/API.md
control-center/docs/PERMISSIONS.md
control-center/docs/NAVIGATION.md
control-center/docs/STYLE_GUIDE.md