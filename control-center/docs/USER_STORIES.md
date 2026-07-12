# USER STORIES

**Proyecto:** EJTV Broadcast Platform

**Componente:** EJTV Control Center

**Versión:** 1.0

---

# 1. Introducción

## Objetivo

Este documento describe las necesidades funcionales que deberá satisfacer el EJTV Control Center desde el punto de vista de los diferentes tipos de usuarios que interactúan con la plataforma.

Las historias de usuario constituyen la base para el diseño del Backend, Frontend, API REST, Base de Datos y sistema de permisos.

Cada historia representa una necesidad operacional real que posteriormente será implementada mediante uno o varios módulos del sistema.

---

# Filosofía

Las historias aquí descritas no representan pantallas.

Representan necesidades de operación.

Una misma historia puede involucrar varios módulos del Control Center.

Del mismo modo, una pantalla puede satisfacer varias historias de usuario.

---

# Tipos de Usuario

La plataforma considera inicialmente los siguientes perfiles.

• Administrador

• Operador NOC

• Supervisor

• Auditor

• Cliente

En futuras versiones podrán incorporarse nuevos perfiles.

---

# Convenciones

Cada historia utilizará el siguiente formato.

ID

Nombre

Actor

Descripción

Prioridad

Módulos involucrados

Estado

---

# Prioridades

Alta

Media

Baja

---

# Estados

Pendiente

En Desarrollo

Implementada

Validada


## US-001

### Nombre

Visualizar el estado general de la plataforma.

### Actor

Operador NOC

### Descripción

El operador necesita observar inmediatamente el estado operativo de toda la plataforma al iniciar sesión.

Debe poder identificar rápidamente problemas sin recorrer diferentes pantallas.

### Resultado esperado

Visualizar:

Estado general

Canales activos

Servicios

Alarmas

Carga del servidor

Clientes conectados

Protocolos activos

### Prioridad

Alta

### Módulos

Dashboard

Monitoring

Services

Logs

### Estado

Pendiente



## US-002

### Nombre

Visualizar alarmas críticas.

### Actor

Operador

### Descripción

El operador debe identificar inmediatamente cualquier incidente crítico que afecte la operación.

### Resultado esperado

Listado de alarmas críticas.

Color diferenciado.

Hora.

Origen.

Nivel.

Acción sugerida.

### Prioridad

Alta
## US-010

### Nombre

Crear un canal.

### Actor

Administrador

### Descripción

El administrador necesita registrar un nuevo canal de televisión dentro de la plataforma.

### Información requerida

Nombre.

Identificador.

Descripción.

Protocolo.

Origen.

Destino.

Estado inicial.

### Resultado esperado

El canal queda disponible para operación.

### Prioridad

Alta


## US-011

Editar un canal existente.

## US-012

Eliminar un canal.


## US-013

Iniciar un canal.


## US-014

Detener un canal.


## US-015

Reiniciar un canal.


## US-016

Consultar estadísticas de un canal.


## US-020

Visualizar servicios del servidor.


## US-021

Reiniciar un servicio.

## US-022

Consultar estado de MediaMTX.

## US-023

Consultar estado de FFmpeg.


## US-024

Consultar estado del Firewall.

## US-025

Consultar estado del Sistema Operativo.


## US-030

Registrar cliente.


## US-031

Editar cliente.

## US-032

Suspender cliente.

## US-033

Consultar canales autorizados.

## US-034

Consultar consumo del cliente.

## US-040

Visualizar recursos del servidor.

## US-042

Consultar utilización de Memoria.

## US-043

Consultar utilización de Disco.

## US-044

Consultar utilización de Red.

## US-045

Consultar estado de protocolos.

## US-050

Crear usuario.

## US-051

Modificar usuario.

## US-052

Deshabilitar usuario.

## US-053

Restablecer contraseña.

## US-054

Consultar sesiones activas.

## US-060

Consultar eventos de seguridad.

## US-061

Administrar permisos.

## US-062

Administrar certificados.

## US-070

Generar reporte operativo.

## US-071

Exportar reporte PDF.

## US-072

Exportar reporte Excel.


## US-080

Modificar parámetros de la plataforma.

## US-082

Consultar historial de cambios.

## US-090

Consultar eventos históricos.

## US-091

Buscar eventos.

## US-092

Exportar registros.