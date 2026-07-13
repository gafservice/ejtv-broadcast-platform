# CHANGELOG — MISSION-017

**Misión:** MISSION-017

**Nombre:** Diseño Arquitectónico del EJTV Control Center

**Versión:** 1.0

**Estado:** Finalizada

**Fecha:** Julio 2026

---

# Resumen

La MISSION-017 marca el inicio del desarrollo del **EJTV Control Center**, un nuevo componente de la plataforma EJTV Broadcast Platform orientado a la administración, monitoreo y operación de la infraestructura multimedia.

Durante esta misión no se implementó código funcional.

El trabajo se concentró en establecer la arquitectura, la organización del proyecto y la documentación necesaria para iniciar el desarrollo del software en las siguientes etapas.

---

# Added

## Nuevo subproyecto

Se incorporó el subproyecto:

```text
control-center/
```

con la siguiente estructura inicial:

```text
control-center/

README.md
ROADMAP.md
CHANGELOG.md

backend/
frontend/
config/
docs/
tests/
logs/
```

---

## Documentación Arquitectónica

Se agregaron los siguientes documentos:

```text
control-center/docs/

ARCHITECTURE.md
MODULES.md
USER_STORIES.md
DATA_MODEL.md
API.md
PERMISSIONS.md
NAVIGATION.md
STYLE_GUIDE.md
```

---

## Documentación General

Se incorporaron:

```text
control-center/

README.md
ROADMAP.md
CHANGELOG.md
```

---

## Arquitectura

Se diseñó la arquitectura general del Control Center.

Se definió una arquitectura basada en capas.

```text
Frontend

↓

REST API

↓

Backend

↓

Adaptadores

↓

Infraestructura
```

---

## Modelo de Dominio

Se diseñó el modelo inicial del dominio incluyendo las entidades:

- Canal
- Fuente
- Cliente
- Usuario
- Rol
- Permiso
- Nodo
- Servicio
- Interfaz
- Protocolo
- Evento
- Alarma
- Configuración
- Reporte
- Métrica
- Sesión

---

## API

Se definió la primera versión de la API REST.

Características:

- REST
- JSON
- Versionada
- Stateless
- Escalable
- Segura

Versión inicial:

```text
/api/v1/
```

---

## Navegación

Se diseñó la navegación completa del sistema.

Modelo adoptado:

```text
Objeto

↓

Información

↓

Operación

↓

Histórico

↓

Configuración
```

---

## Seguridad

Se incorporó el modelo inicial de autorización.

Roles definidos:

- Administrador General
- Administrador Técnico
- Operador NOC
- Supervisor
- Auditor
- Consulta

---

## Identidad Visual

Se definieron reglas para:

- colores;
- tipografía;
- iconografía;
- botones;
- tablas;
- formularios;
- gráficos;
- navegación;
- mensajes.

---

## Roadmap

Se creó el roadmap independiente del Control Center.

---

## Historial

Se creó el CHANGELOG propio del Control Center.

---

# Changed

Se amplió el alcance del proyecto EJTV Broadcast Platform.

Hasta la MISSION-016 la plataforma estaba enfocada principalmente en la infraestructura multimedia.

A partir de la MISSION-017 se incorpora formalmente una segunda línea de desarrollo dedicada al software de administración.

---

Se estableció una separación clara entre:

- Plataforma Multimedia.
- Control Center.

---

Se definió una metodología específica para el desarrollo del Control Center basada en:

- documentación;
- arquitectura;
- implementación;
- validación;
- trazabilidad.

---

# Fixed

No aplica.

Durante esta misión no se realizaron correcciones funcionales sobre componentes existentes.

---

# Removed

No aplica.

No fueron eliminados módulos ni funcionalidades existentes.

---

# Security

Se adoptaron los siguientes principios:

- mínimo privilegio;
- autorización en Backend;
- API como único punto de acceso;
- auditoría obligatoria;
- separación entre operadores y clientes.

---

# Documentation

Se generó la documentación oficial correspondiente a:

- arquitectura;
- módulos;
- historias de usuario;
- dominio;
- API;
- permisos;
- navegación;
- identidad visual;
- roadmap;
- changelog;
- documentación principal.

---

# Engineering Decisions

Durante esta misión quedaron establecidas las siguientes decisiones arquitectónicas.

- El Frontend nunca accederá directamente a Linux.
- Toda comunicación utilizará la API.
- MediaMTX y FFmpeg serán abstraídos mediante adaptadores.
- La plataforma será orientada al dominio.
- La seguridad será responsabilidad exclusiva del Backend.
- La navegación será uniforme para todos los módulos.
- El desarrollo comenzará por el núcleo del Backend.

---

# Impacto

La misión establece la fundación técnica del EJTV Control Center.

Las siguientes misiones podrán concentrarse exclusivamente en la implementación del software respetando la arquitectura definida.

---

# Próxima misión

MISSION-018

Fundación del Backend del EJTV Control Center.

Se iniciará el desarrollo del núcleo de la aplicación incluyendo:

- Core.
- Configuración.
- Logging.
- Eventos.
- Persistencia.
- Servicios.
- API inicial.

---

# Estado Final

MISSION-017 finalizada correctamente.

La arquitectura del Control Center queda aprobada como referencia oficial para el desarrollo futuro del sistema.