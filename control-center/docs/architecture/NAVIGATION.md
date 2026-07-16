# EJTV Control Center

# Navegación de la Plataforma

**Versión:** 1.0

**Estado:** Diseño

**Misión:** MISSION-017

---

# 1. Introducción

El presente documento define la estructura de navegación del EJTV Control Center.

Su propósito consiste en establecer un modelo uniforme de interacción entre el operador y la plataforma, garantizando que todas las funciones sean accesibles de forma lógica, consistente y eficiente.

La navegación deberá minimizar la cantidad de pasos necesarios para ejecutar las tareas más frecuentes.

---

# 2. Filosofía

El operador nunca deberá sentirse perdido.

Cada pantalla deberá responder claramente a tres preguntas:

• ¿Dónde estoy?

• ¿Qué puedo hacer aquí?

• ¿Cómo regreso?

La navegación deberá mantenerse constante en toda la plataforma.

---

# 3. Principios de Navegación

## Simplicidad

Cada pantalla tendrá un propósito definido.

No se mezclarán funciones administrativas con funciones operativas.

---

## Consistencia

Todos los módulos utilizarán la misma organización.

La ubicación de botones, filtros y acciones será uniforme.

---

## Jerarquía

La navegación seguirá una estructura jerárquica.

Nunca existirá una pantalla inaccesible.

---

## Persistencia

El menú principal permanecerá disponible durante toda la sesión.

---

## Contexto

Cada pantalla indicará claramente el recurso sobre el cual está trabajando el usuario.

Ejemplo

Dashboard

↓

Channels

↓

ENLACE

↓

Logs

---

# 4. Flujo General

```text
Login

↓

Dashboard

├── Channels

├── Clients

├── Services

├── Monitoring

├── Reports

├── Logs

├── Users

├── Security

├── Configuration

└── System
```

---

# 5. Inicio de Sesión

El ingreso al sistema constituye el punto inicial de navegación.

Después de autenticarse correctamente el usuario será redirigido automáticamente al Dashboard.

Si el usuario posee restricciones de permisos, únicamente visualizará los módulos autorizados.

---

# 6. Dashboard

El Dashboard constituye el centro operativo del sistema.

Desde esta pantalla el operador podrá acceder a todos los módulos autorizados.

Información principal:

- estado general;
- canales;
- alarmas;
- clientes conectados;
- utilización del servidor;
- protocolos;
- servicios;
- eventos recientes.

Acciones rápidas:

- consultar canal;
- consultar servicio;
- reconocer alarma;
- abrir reporte;
- acceder al monitoreo.

---

# 7. Channels

```text
Dashboard

↓

Channels

↓

Listado

↓

Canal

├── Información

├── Protocolos

├── Fuentes

├── Métricas

├── Alarmas

├── Eventos

├── Logs

└── Configuración
```

Desde esta pantalla podrán ejecutarse acciones como:

- iniciar;
- detener;
- reiniciar;
- mantenimiento;
- consultar estadísticas.

---

# 8. Clients

```text
Dashboard

↓

Clients

↓

Cliente

├── Información

├── Canales

├── Protocolos

├── Direcciones

├── Credenciales

├── Sesiones

├── Consumo

└── Historial
```

---

# 9. Services

```text
Dashboard

↓

Services

↓

Servicio

├── Estado

├── Dependencias

├── Logs

├── Configuración

├── Métricas

└── Historial
```

Acciones disponibles:

- iniciar;
- detener;
- reiniciar;
- mantenimiento.

---

# 10. Monitoring

```text
Dashboard

↓

Monitoring

├── Sistema

├── CPU

├── Memoria

├── Disco

├── Red

├── Interfaces

├── Procesos

├── Temperatura

├── Bitrate

├── Latencia

└── Históricos
```

El módulo de monitoreo permitirá navegar desde una métrica general hasta el origen específico.

---

# 11. Reports

```text
Dashboard

↓

Reports

├── Operativos

├── Clientes

├── Canales

├── Auditoría

├── Seguridad

├── Rendimiento

└── Exportaciones
```

---

# 12. Logs

```text
Dashboard

↓

Logs

├── Sistema

├── MediaMTX

├── FFmpeg

├── Canales

├── Seguridad

├── Auditoría

└── Eventos
```

Los registros podrán filtrarse por:

- fecha;
- módulo;
- usuario;
- nivel;
- canal;
- servicio;
- nodo.

---

# 13. Users

```text
Dashboard

↓

Users

↓

Usuario

├── Información

├── Roles

├── Permisos

├── Sesiones

├── Auditoría

└── Configuración
```

---

# 14. Security

```text
Dashboard

↓

Security

├── Usuarios

├── Roles

├── Permisos

├── Certificados

├── Políticas

├── Auditoría

└── Eventos
```

---

# 15. Configuration

```text
Dashboard

↓

Configuration

├── Sistema

├── Canales

├── Servicios

├── Seguridad

├── Red

├── Protocolos

├── Versiones

└── Restauración
```

---

# 16. System

```text
Dashboard

↓

System

├── Información

├── Nodos

├── Interfaces

├── Versiones

├── Backups

├── Actualizaciones

└── Estado
```

---

# 17. Navegación Contextual

Cada pantalla utilizará rutas de navegación (Breadcrumb).

Ejemplo

```text
Dashboard / Channels / ENLACE / Logs
```

Esto permitirá regresar rápidamente a cualquier nivel.

---

# 18. Acciones Globales

Las siguientes funciones estarán disponibles desde cualquier pantalla:

- búsqueda global;
- notificaciones;
- alarmas activas;
- ayuda;
- perfil del usuario;
- cerrar sesión.

---

# 19. Diseño Responsivo

La navegación deberá adaptarse a:

- escritorio;
- portátil;
- tableta.

Las funciones principales deberán permanecer accesibles independientemente de la resolución.

---

# 20. Futuras Extensiones

La arquitectura permitirá incorporar nuevos módulos sin modificar la navegación existente.

Ejemplos:

- Publicidad;
- Programación;
- Facturación;
- Inteligencia Artificial;
- Automatización;
- Grabaciones;
- Clústeres;
- Multi-sede.

Cada nuevo módulo deberá integrarse respetando la estructura definida en este documento.

---

# 21. Conclusión

La navegación del EJTV Control Center constituye uno de los pilares de la experiencia del operador.

Una estructura consistente reduce el tiempo de aprendizaje, disminuye errores operativos y facilita la administración de plataformas complejas.

Toda nueva funcionalidad deberá integrarse siguiendo estas reglas para preservar la coherencia de la interfaz y garantizar una operación eficiente.