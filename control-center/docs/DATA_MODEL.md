# EJTV Control Center

# Modelo de Dominio

**Versión:** 1.0

**Estado:** Diseño

**Misión:** MISSION-017

---

# 1. Introducción

El presente documento define el modelo de dominio del EJTV Control Center.

Su objetivo consiste en identificar las entidades principales del sistema, sus responsabilidades, sus relaciones y las reglas que deberán mantenerse durante el desarrollo del Backend, la API, la base de datos, los reportes y los mecanismos de seguridad.

Este documento no define todavía una tecnología específica de almacenamiento.

No determina si la implementación utilizará SQLite, PostgreSQL u otra solución.

Primero se define el dominio.

La base de datos será una implementación posterior de este modelo.

---

# 2. Filosofía del Modelo

El modelo de dominio debe representar la operación real de la plataforma.

Por esta razón, las entidades principales no serán procesos Linux, archivos YAML ni rutas internas de MediaMTX.

Las entidades representarán conceptos administrativos y operativos comprensibles para el usuario.

Ejemplos:

- Canal
- Cliente
- Usuario
- Servicio
- Nodo
- Alarma
- Evento
- Configuración

La infraestructura técnica será administrada mediante adaptadores y relaciones internas.

---

# 3. Principios de Diseño

## Independencia tecnológica

Las entidades del dominio no dependerán directamente de MediaMTX, FFmpeg, systemd o una base de datos específica.

## Identidad única

Toda entidad deberá poseer un identificador único e inmutable.

## Trazabilidad

Toda modificación relevante deberá registrar:

- usuario;
- fecha;
- hora;
- acción;
- valor anterior;
- valor nuevo;
- resultado.

## Estados normalizados

Los estados de las entidades deberán utilizar valores definidos y consistentes.

## Eliminación controlada

Las entidades críticas no deberán eliminarse físicamente de forma inmediata.

Cuando corresponda, se utilizarán estados como:

- suspendido;
- archivado;
- deshabilitado;
- eliminado lógicamente.

## Auditoría

Toda operación sensible deberá generar un evento de auditoría.

---

# 4. Entidades Principales

## 4.1 Canal

### Propósito

Representa una señal audiovisual administrada por la plataforma.

El Canal constituye la entidad principal de la operación multimedia.

### Atributos iniciales

- identificador;
- nombre;
- código;
- descripción;
- estado;
- categoría;
- prioridad;
- logo;
- nodo asignado;
- fuente principal;
- fuente de respaldo;
- fecha de creación;
- fecha de modificación.

### Estados

- activo;
- detenido;
- iniciando;
- deteniendo;
- en espera;
- mantenimiento;
- alarma;
- error;
- archivado.

### Relaciones

Un Canal:

- pertenece a un Nodo;
- posee una o varias Fuentes;
- habilita uno o varios Protocolos;
- utiliza cero o más Servicios;
- puede asignarse a múltiples Clientes;
- genera Métricas;
- genera Eventos;
- puede generar Alarmas.

---

## 4.2 Fuente

### Propósito

Representa el origen de la señal audiovisual asociada a un Canal.

### Atributos iniciales

- identificador;
- nombre;
- tipo;
- dirección;
- puerto;
- interfaz de red;
- prioridad;
- estado;
- canal asociado;
- parámetros técnicos;
- fecha de creación.

### Tipos iniciales

- UDP unicast;
- UDP multicast;
- SRT;
- RTSP;
- RTMP;
- archivo;
- dispositivo de captura;
- fuente remota.

### Estados

- disponible;
- no disponible;
- degradada;
- esperando señal;
- error.

### Relaciones

Una Fuente:

- pertenece a un Canal;
- utiliza una Interfaz de Red;
- puede producir Métricas;
- puede generar Alarmas y Eventos.

---

## 4.3 Protocolo

### Propósito

Representa una capacidad de entrada o distribución habilitada para un Canal.

### Atributos iniciales

- identificador;
- nombre;
- dirección;
- puerto;
- modo;
- estado;
- parámetros;
- autenticación requerida;
- fecha de creación.

### Protocolos iniciales

- RTSP;
- RTMP;
- SRT;
- HLS;
- WebRTC;
- UDP;
- MPEG-TS.

### Relaciones

Un Protocolo:

- puede estar asociado a múltiples Canales;
- puede estar autorizado para múltiples Clientes;
- puede depender de uno o más Servicios;
- produce Métricas y Eventos.

---

## 4.4 Cliente

### Propósito

Representa una organización autorizada para consumir servicios de la plataforma.

### Atributos iniciales

- identificador;
- código;
- nombre;
- tipo;
- descripción;
- estado;
- contacto técnico;
- contacto administrativo;
- correo;
- teléfono;
- ancho de banda contratado;
- límite de conexiones;
- prioridad;
- fecha de alta;
- fecha de modificación.

### Estados

- activo;
- suspendido;
- pendiente;
- bloqueado;
- archivado.

### Relaciones

Un Cliente:

- puede acceder a múltiples Canales;
- puede utilizar múltiples Protocolos;
- puede tener múltiples Credenciales;
- puede registrar múltiples Direcciones Autorizadas;
- genera Sesiones;
- genera Métricas;
- genera Eventos.

---

## 4.5 Dirección Autorizada

### Propósito

Representa una dirección IP o red permitida para un Cliente.

### Atributos iniciales

- identificador;
- dirección;
- máscara;
- descripción;
- estado;
- cliente asociado;
- fecha de creación.

### Relaciones

Una Dirección Autorizada:

- pertenece a un Cliente;
- puede estar restringida a determinados Canales o Protocolos.

---

## 4.6 Usuario

### Propósito

Representa una persona autorizada para operar el Control Center.

### Atributos iniciales

- identificador;
- nombre;
- apellidos;
- nombre de usuario;
- correo;
- departamento;
- cargo;
- estado;
- contraseña protegida;
- último acceso;
- fecha de creación;
- fecha de modificación.

### Estados

- activo;
- suspendido;
- bloqueado;
- pendiente;
- deshabilitado.

### Relaciones

Un Usuario:

- posee uno o varios Roles;
- puede tener Permisos directos;
- genera Sesiones;
- genera Eventos de Auditoría;
- realiza Cambios de Configuración;
- puede reconocer Alarmas.

---

## 4.7 Rol

### Propósito

Representa un conjunto organizado de permisos.

### Atributos iniciales

- identificador;
- nombre;
- descripción;
- estado;
- nivel;
- fecha de creación.

### Roles iniciales

- administrador general;
- administrador técnico;
- operador NOC;
- supervisor;
- auditor;
- consulta.

### Relaciones

Un Rol:

- posee múltiples Permisos;
- puede asignarse a múltiples Usuarios.

---

## 4.8 Permiso

### Propósito

Representa la autorización para ejecutar una acción específica.

### Atributos iniciales

- identificador;
- código;
- módulo;
- recurso;
- acción;
- descripción.

### Ejemplos

- `dashboard.read`
- `channels.create`
- `channels.start`
- `channels.stop`
- `services.restart`
- `clients.update`
- `users.manage`
- `configuration.apply`
- `logs.read`
- `reports.export`

### Relaciones

Un Permiso:

- puede pertenecer a múltiples Roles;
- puede asignarse directamente a un Usuario cuando sea estrictamente necesario.

---

## 4.9 Sesión de Usuario

### Propósito

Representa una sesión autenticada dentro del Control Center.

### Atributos iniciales

- identificador;
- usuario;
- dirección IP;
- agente de usuario;
- fecha de inicio;
- última actividad;
- fecha de cierre;
- estado;
- motivo de cierre.

### Estados

- activa;
- expirada;
- cerrada;
- revocada;
- bloqueada.

---

## 4.10 Nodo

### Propósito

Representa una unidad de infraestructura administrable por el Control Center.

Actualmente el primer Nodo corresponde a:

```text
ejtv-01
```

El modelo deberá permitir incorporar en el futuro:

```text
ejtv-02
ejtv-03
ejtv-04
```

### Atributos iniciales

- identificador;
- nombre;
- hostname;
- descripción;
- dirección de administración;
- estado;
- sistema operativo;
- versión;
- ubicación;
- zona horaria;
- fecha de registro.

### Estados

- disponible;
- degradado;
- no disponible;
- mantenimiento;
- desconocido.

### Relaciones

Un Nodo:

- posee múltiples Servicios;
- posee múltiples Interfaces de Red;
- administra múltiples Canales;
- produce Métricas;
- genera Eventos y Alarmas.

---

## 4.11 Interfaz de Red

### Propósito

Representa una interfaz física o lógica perteneciente a un Nodo.

### Atributos iniciales

- identificador;
- nombre;
- nombre alternativo;
- dirección MAC;
- dirección IPv4;
- dirección IPv6;
- máscara;
- gateway;
- velocidad;
- rol;
- estado;
- nodo asociado.

### Roles iniciales

- administración;
- ingesta;
- publicación;
- respaldo;
- pruebas;
- almacenamiento.

### Estados

- activa;
- inactiva;
- sin enlace;
- degradada;
- desconocida.

---

## 4.12 Servicio

### Propósito

Representa un componente funcional administrable de la plataforma.

### Atributos iniciales

- identificador;
- nombre;
- tipo;
- descripción;
- estado;
- versión;
- prioridad;
- nodo;
- nombre interno;
- modo de inicio;
- fecha de creación.

### Tipos iniciales

- multimedia;
- procesamiento;
- administración;
- seguridad;
- monitoreo;
- respaldo;
- sistema.

### Estados

- activo;
- detenido;
- iniciando;
- deteniendo;
- error;
- mantenimiento;
- desconocido.

### Relaciones

Un Servicio:

- pertenece a un Nodo;
- puede depender de otros Servicios;
- puede estar relacionado con uno o varios Canales;
- genera Métricas;
- genera Eventos y Alarmas.

---

## 4.13 Dependencia de Servicio

### Propósito

Representa una relación de dependencia entre dos Servicios.

### Atributos iniciales

- servicio origen;
- servicio requerido;
- tipo de dependencia;
- criticidad;
- descripción.

### Tipos

- obligatorio;
- recomendado;
- opcional.

Esta entidad permitirá calcular impacto y causa probable durante una falla.

---

## 4.14 Métrica

### Propósito

Representa una medición puntual de la plataforma.

### Atributos iniciales

- identificador;
- origen;
- tipo de origen;
- nombre;
- valor;
- unidad;
- fecha y hora;
- calidad;
- etiquetas.

### Ejemplos

- CPU;
- RAM;
- disco;
- swap;
- temperatura;
- bitrate;
- latencia;
- pérdida;
- cantidad de lectores;
- bytes recibidos;
- bytes enviados;
- frames con error.

### Relaciones

Una Métrica puede pertenecer a:

- un Nodo;
- una Interfaz;
- un Servicio;
- un Canal;
- un Cliente;
- un Protocolo.

---

## 4.15 Alarma

### Propósito

Representa una condición anormal que requiere atención.

### Atributos iniciales

- identificador;
- título;
- descripción;
- severidad;
- estado;
- origen;
- fecha de apertura;
- fecha de reconocimiento;
- fecha de cierre;
- usuario que reconoce;
- usuario que cierra;
- causa;
- acción recomendada.

### Severidades

- informativa;
- advertencia;
- menor;
- mayor;
- crítica.

### Estados

- abierta;
- reconocida;
- en investigación;
- resuelta;
- cerrada;
- suprimida.

### Relaciones

Una Alarma:

- se origina a partir de Métricas o Eventos;
- puede asociarse a un Canal, Servicio, Nodo, Cliente o Protocolo;
- genera Eventos de Auditoría.

---

## 4.16 Evento

### Propósito

Representa un hecho ocurrido dentro de la plataforma.

### Atributos iniciales

- identificador;
- fecha y hora;
- módulo;
- origen;
- tipo;
- nivel;
- acción;
- resultado;
- descripción;
- usuario;
- identificador de correlación;
- datos adicionales.

### Niveles

- trace;
- debug;
- info;
- notice;
- warning;
- error;
- critical;
- alert;
- emergency.

### Relaciones

Un Evento puede estar asociado a:

- Usuario;
- Canal;
- Cliente;
- Servicio;
- Nodo;
- Alarma;
- Configuración;
- Sesión.

---

## 4.17 Configuración

### Propósito

Representa un parámetro administrado por el Control Center.

### Atributos iniciales

- identificador;
- módulo;
- clave;
- valor;
- tipo;
- descripción;
- versión;
- estado;
- fecha de creación;
- fecha de aplicación;
- usuario responsable.

### Estados

- borrador;
- validada;
- aplicada;
- rechazada;
- reemplazada;
- restaurada.

### Relaciones

Una Configuración:

- pertenece a un módulo;
- puede generar múltiples Versiones;
- genera Eventos de Auditoría;
- puede afectar Canales, Servicios, Protocolos, Seguridad o Monitoreo.

---

## 4.18 Versión de Configuración

### Propósito

Representa una versión histórica de una Configuración.

### Atributos iniciales

- identificador;
- configuración;
- versión;
- valor anterior;
- valor nuevo;
- motivo;
- usuario;
- fecha;
- resultado de validación;
- resultado de aplicación.

---

## 4.19 Reporte

### Propósito

Representa una solicitud o resultado de generación de información consolidada.

### Atributos iniciales

- identificador;
- nombre;
- tipo;
- formato;
- estado;
- período;
- filtros;
- usuario solicitante;
- fecha de solicitud;
- fecha de finalización;
- ubicación del archivo;
- error.

### Estados

- pendiente;
- generando;
- completado;
- fallido;
- expirado.

---

## 4.20 Credencial de Cliente

### Propósito

Representa un mecanismo de autenticación utilizado por un Cliente para consumir servicios.

### Atributos iniciales

- identificador;
- cliente;
- tipo;
- nombre de usuario;
- secreto protegido;
- token;
- certificado;
- fecha de creación;
- fecha de expiración;
- estado.

### Tipos

- usuario y contraseña;
- token;
- certificado;
- clave compartida;
- autenticación por IP.

---

## 4.21 Asignación de Canal

### Propósito

Representa la autorización de un Cliente para acceder a un Canal mediante determinados Protocolos.

### Atributos iniciales

- identificador;
- cliente;
- canal;
- estado;
- fecha de inicio;
- fecha de finalización;
- límite de conexiones;
- límite de ancho de banda;
- prioridad.

### Relaciones

Una Asignación:

- pertenece a un Cliente;
- pertenece a un Canal;
- habilita uno o varios Protocolos;
- puede utilizar una Credencial específica.

---

# 5. Relaciones Principales

```text
Nodo
 ├── Interfaces de Red
 ├── Servicios
 └── Canales
      ├── Fuentes
      ├── Protocolos
      ├── Métricas
      ├── Eventos
      └── Alarmas

Cliente
 ├── Direcciones autorizadas
 ├── Credenciales
 ├── Sesiones
 └── Asignaciones de Canal
      ├── Canal
      └── Protocolos

Usuario
 ├── Roles
 │    └── Permisos
 ├── Sesiones
 ├── Eventos de Auditoría
 └── Cambios de Configuración

Monitoring
 ├── Métricas
 ├── Alarmas
 └── Eventos

Reports
 ├── Métricas históricas
 ├── Eventos
 ├── Alarmas
 └── Configuraciones
```

---

# 6. Reglas de Integridad

## Canales

- Todo Canal deberá pertenecer a un Nodo.
- Todo Canal deberá tener al menos una Fuente registrada.
- No podrán existir dos Canales activos con el mismo código.
- La eliminación de un Canal deberá ser lógica cuando existan históricos asociados.

## Clientes

- Todo Cliente deberá poseer un código único.
- Un Cliente suspendido no podrá iniciar nuevas sesiones.
- El acceso a un Canal requerirá una Asignación activa.

## Usuarios

- El nombre de usuario y el correo deberán ser únicos.
- Un Usuario bloqueado no podrá autenticarse.
- No deberá eliminarse el último Administrador General activo.

## Servicios

- Un Servicio no podrá iniciarse si falta una dependencia obligatoria.
- Las acciones críticas deberán generar auditoría.
- Un Servicio en mantenimiento no deberá generar alarmas de indisponibilidad normales.

## Configuración

- Una Configuración no podrá aplicarse sin validación.
- Toda aplicación deberá crear una Versión.
- Toda restauración deberá registrarse como una nueva operación.

## Eventos

- Los Eventos de auditoría no deberán modificarse.
- Todo Evento deberá poseer fecha, origen, nivel y resultado.
- Los eventos relacionados deberán compartir un identificador de correlación.

---

# 7. Identificadores

Las entidades utilizarán identificadores internos independientes de sus nombres visibles.

Ejemplo:

```text
id: 7c2f...
code: enlace
name: ENLACE
```

El nombre puede cambiar.

El identificador no.

Los códigos utilizados en rutas o integraciones deberán validarse y normalizarse.

---

# 8. Fechas y Horas

Todas las fechas deberán almacenarse internamente con zona horaria explícita.

La presentación utilizará la zona horaria configurada para el operador o la plataforma.

No se almacenarán fechas ambiguas.

---

# 9. Datos Sensibles

Los siguientes datos deberán protegerse:

- contraseñas;
- tokens;
- secretos;
- claves compartidas;
- certificados privados;
- información de sesión.

Nunca deberán almacenarse en texto plano.

Los eventos y reportes no deberán exponer secretos.

---

# 10. Históricos y Retención

El sistema distinguirá entre:

- estado actual;
- histórico de métricas;
- histórico de alarmas;
- auditoría;
- eventos técnicos;
- versiones de configuración;
- sesiones.

Cada categoría tendrá políticas de retención independientes.

---

# 11. Escalabilidad

El modelo deberá soportar:

- múltiples Nodos;
- cientos de Canales;
- miles de Clientes;
- múltiples usuarios concurrentes;
- grandes volúmenes de Métricas y Eventos;
- infraestructura distribuida.

Las entidades operativas y los datos históricos podrán almacenarse de manera separada cuando el crecimiento lo requiera.

---

# 12. Evolución

En futuras versiones podrán incorporarse entidades como:

- Contrato;
- Factura;
- Publicidad;
- Programación;
- Grabación;
- Incidente;
- Mantenimiento;
- Notificación;
- Sede;
- Clúster;
- Perfil de codificación;
- Política de automatización.

Estas extensiones deberán respetar las entidades y relaciones definidas en este documento.

---

# 13. Conclusión

El modelo de dominio constituye la base lógica del EJTV Control Center.

Su propósito no consiste únicamente en organizar información para una base de datos.

Su finalidad es representar de manera coherente la realidad operativa de la plataforma.

Toda implementación futura deberá respetar este modelo y documentar formalmente cualquier modificación estructural mediante una decisión arquitectónica.