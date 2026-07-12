# EJTV Control Center

Sistema de administración, monitoreo y operación de la plataforma **EJTV Broadcast Platform**.

---

# Objetivo

El EJTV Control Center proporciona una interfaz unificada para administrar todos los componentes de la plataforma de distribución de contenidos multimedia.

Su propósito es permitir que los operadores administren canales, clientes, servicios, monitoreo, seguridad y configuración sin necesidad de acceder directamente al sistema operativo Linux.

El Control Center constituye la capa de administración de la plataforma.

---

# Principios de Diseño

El desarrollo del Control Center se basa en los siguientes principios:

- Arquitectura modular.
- Separación entre Frontend y Backend.
- API REST como único mecanismo de comunicación.
- Seguridad desde el diseño.
- Escalabilidad.
- Trazabilidad.
- Alta disponibilidad.
- Independencia de la infraestructura.

---

# Arquitectura General

```text
                 Operador

                     │

             Frontend Web

                     │

                REST API

                     │

          Backend Control Center

                     │

        ┌────────────┼────────────┐
        │            │            │
     MediaMTX     FFmpeg      Linux

                     │

              Plataforma EJTV
```

---

# Componentes

```text
control-center/

├── README.md
├── ROADMAP.md
├── CHANGELOG.md
│
├── backend/
│
├── frontend/
│
├── config/
│
├── docs/
│
├── tests/
│
└── logs/
```

---

# Documentación

Toda la documentación funcional se encuentra en:

```text
control-center/docs/
```

Documentos principales:

```
ARCHITECTURE.md
MODULES.md
USER_STORIES.md
DATA_MODEL.md
API.md
PERMISSIONS.md
NAVIGATION.md
STYLE_GUIDE.md
```

Estos documentos constituyen la especificación oficial del Control Center.

---

# Backend

El Backend implementará toda la lógica de negocio.

Será responsable de:

- autenticación;
- autorización;
- administración de canales;
- administración de clientes;
- monitoreo;
- eventos;
- alarmas;
- reportes;
- configuración;
- auditoría.

El Frontend nunca accederá directamente a MediaMTX ni al sistema operativo.

---

# Frontend

El Frontend proporcionará una interfaz moderna para los operadores.

Sus responsabilidades serán:

- visualización;
- interacción;
- formularios;
- navegación;
- dashboards;
- reportes;
- administración.

Toda operación será ejecutada mediante la API REST.

---

# API

Toda comunicación utilizará la API del Control Center.

Ejemplo:

```
Frontend

↓

REST API

↓

Backend

↓

MediaMTX
```

El Backend constituye el único punto autorizado para acceder a la infraestructura.

---

# Estado Actual

Actualmente el proyecto se encuentra en fase de diseño arquitectónico.

Completado:

```
✓ Arquitectura

✓ Módulos

✓ Historias de Usuario

✓ Modelo de Dominio

✓ API

✓ Roles y Permisos

✓ Navegación

✓ Guía de Estilo
```

Próxima etapa:

```
MISSION-018

Implementación del Backend.
```

---

# Roadmap

La planificación del Control Center se encuentra en:

```
ROADMAP.md
```

---

# Tecnologías Previstas

Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic

Frontend

- React
- TypeScript
- Tailwind CSS

Base de Datos

- PostgreSQL

Seguridad

- JWT
- HTTPS
- OAuth2 (futuro)

---

# Filosofía de Desarrollo

El Control Center será construido siguiendo una metodología incremental.

Cada componente deberá:

- diseñarse;
- documentarse;
- implementarse;
- probarse;
- validarse;
- documentarse nuevamente.

No se desarrollarán funcionalidades sin documentación previa.

---

# Organización del Proyecto

El desarrollo seguirá el siguiente orden:

```
Arquitectura

↓

Modelo de Dominio

↓

Persistencia

↓

Servicios

↓

API

↓

Frontend

↓

Integración

↓

Pruebas
```

Esta estrategia reduce retrabajos y facilita la evolución de la plataforma.

---

# Escalabilidad

La arquitectura está preparada para administrar:

- múltiples nodos;
- múltiples canales;
- múltiples clientes;
- múltiples operadores;
- múltiples sedes.

No depende de un único servidor.

---

# Contribución

Todo cambio deberá:

- respetar la arquitectura;
- mantener la compatibilidad con la documentación;
- incorporar pruebas cuando corresponda;
- registrar los cambios en el CHANGELOG.

Las modificaciones arquitectónicas deberán documentarse mediante un ADR.

---

# Licencia

Este componente forma parte del proyecto **EJTV Broadcast Platform**.

Su desarrollo sigue los principios de ingeniería definidos para toda la plataforma.

---

# Visión

El EJTV Control Center no es únicamente una aplicación web.

Es la plataforma desde la cual se administrará toda la infraestructura de distribución multimedia desarrollada para EJTV.

Su diseño busca proporcionar una solución robusta, escalable y preparada para evolucionar durante los próximos años, permitiendo integrar nuevos servicios, protocolos y capacidades sin modificar los principios fundamentales definidos en esta arquitectura.