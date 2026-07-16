# SPRINT-003

# OBJECTIVE

---

# Objetivo General

Implementar la capacidad **System Resources** dentro del EJTV Control Center,
permitiendo obtener, consolidar y publicar información en tiempo real sobre
los recursos principales del servidor Linux mediante una API REST,
manteniendo la arquitectura por capas definida para el proyecto.

---

# Objetivos Específicos

## 1. Extender el dominio

Incorporar nuevos modelos de dominio que representen los recursos del
servidor como objetos de negocio independientes.

Los modelos incorporados son:

- CPUInfo
- MemoryInfo
- DiskInfo
- UptimeInfo
- SystemResources

---

## 2. Ampliar el contrato del adaptador

Extender la interfaz **SystemAdapter** para soportar la obtención de
información relacionada con:

- procesador;
- memoria;
- almacenamiento;
- tiempo de actividad.

La implementación debía mantener el principio de inversión de
dependencias, evitando que las capas superiores dependieran de Linux.

---

## 3. Implementar el adaptador Linux

Desarrollar la implementación concreta del contrato utilizando la
biblioteca **psutil**, encapsulando completamente el acceso al sistema
operativo.

El adaptador debía obtener información real del servidor sin exponer
dependencias del sistema al dominio o a la capa de servicios.

---

## 4. Incorporar la lógica de aplicación

Ampliar **SystemService** para consolidar la información obtenida por el
adaptador y construir el objeto de dominio **SystemResources**.

La lógica debía permanecer libre de dependencias específicas del sistema
operativo.

---

## 5. Publicar la información mediante la API

Incorporar el endpoint:

```text
GET /api/v1/system/resources
```

utilizando el mismo formato de respuesta estándar empleado por el resto
del backend.

---

## 6. Validar la implementación

Verificar el funcionamiento mediante:

- pruebas unitarias;
- pruebas del dominio;
- pruebas del adaptador;
- pruebas del servicio;
- pruebas de arquitectura;
- pruebas de integración;
- pruebas de API;
- consultas reales utilizando `curl`.

---

# Alcance

El Sprint-003 incorpora la infraestructura necesaria para exponer el
estado actual del servidor Linux.

La información publicada comprende:

- utilización del procesador;
- núcleos físicos y lógicos;
- frecuencia del procesador;
- memoria total, utilizada y disponible;
- almacenamiento total, utilizado y libre;
- tiempo de actividad del servidor;
- instante de captura de la información.

No forma parte del alcance de este Sprint el monitoreo de servicios
multimedia, procesos del sistema, interfaces de red o eventos del
servidor, los cuales serán desarrollados en Sprint posteriores.

---

# Criterios de éxito

El Sprint se considera completado cuando:

- todos los modelos del dominio se implementan correctamente;
- el contrato del adaptador se amplía sin romper la arquitectura;
- el adaptador Linux obtiene información real del servidor;
- el servicio consolida correctamente los recursos del sistema;
- el endpoint `/api/v1/system/resources` responde satisfactoriamente;
- la totalidad de la suite de pruebas finaliza sin errores;
- la capacidad queda integrada de forma permanente al EJTV Control Center.

---

# Resultado esperado

Al finalizar el Sprint, el EJTV Control Center dispone de una nueva
capacidad permanente para consultar el estado operativo del servidor y
publicarlo mediante una API REST, constituyendo la base para el futuro
Dashboard de monitoreo del sistema.