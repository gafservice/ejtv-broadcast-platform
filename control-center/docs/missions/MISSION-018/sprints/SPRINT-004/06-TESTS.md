# SPRINT-004

# Pruebas

---

# Estado

**Completado**

---

# Versión

**1.0**

---

# Fecha

Julio 2026

---

# Introducción

Una vez implementado el módulo de monitoreo de servicios se realizó un
proceso completo de validación con el objetivo de verificar la correcta
integración entre las diferentes capas del sistema.

Las pruebas incluyeron validaciones unitarias, pruebas de integración,
consultas mediante la API REST y ejecución sobre el servidor Linux del
proyecto.

---

# Objetivos de las pruebas

Las pruebas realizadas buscan verificar que el sistema sea capaz de:

- detectar correctamente los servicios monitoreados;
- interpretar el estado operativo de cada servicio;
- obtener información de las instancias activas;
- construir correctamente los objetos del dominio;
- responder mediante la API REST;
- mantener la compatibilidad con los sprints anteriores.

---

# Pruebas del dominio

Se verificó el correcto funcionamiento de las nuevas entidades
incorporadas durante este sprint.

Componentes evaluados:

- ServiceStatus
- ServiceInstance
- MonitoredService
- ServiceMonitoringSnapshot

Las pruebas confirmaron la correcta creación e inicialización de los
objetos del dominio.

Resultado:

```
PASS
```

---

# Pruebas del adaptador Linux

Se verificó el funcionamiento del adaptador responsable de consultar el
estado de los servicios del sistema operativo.

Las pruebas incluyeron:

- consulta de servicios administrados por systemd;
- búsqueda de procesos activos;
- normalización de estados;
- creación de instancias;
- generación del snapshot de monitoreo.

Resultado:

```
PASS
```

---

# Pruebas de la capa de servicios

Se validó la integración entre el adaptador Linux y la clase
SystemService.

Se comprobó que el método:

```
get_service_monitoring()
```

retorna una estructura consistente e independiente de la infraestructura
subyacente.

Resultado:

```
PASS
```

---

# Pruebas de la API REST

Se verificó el correcto funcionamiento del endpoint incorporado durante
este sprint.

Endpoint probado:

```
GET /api/v1/system/services
```

Se comprobó:

- código HTTP;
- estructura JSON;
- serialización de objetos;
- consistencia del formato de respuesta.

Resultado:

```
PASS
```

---

# Pruebas de integración

Se ejecutó la batería completa de pruebas del backend para verificar que
la incorporación del nuevo módulo no afectara funcionalidades
implementadas anteriormente.

Resultado obtenido:

```
==============================

60 passed

==============================
```

No se detectaron regresiones durante la ejecución de la suite completa.

---

# Validación sobre el servidor

Posteriormente se ejecutó la aplicación sobre el servidor Linux utilizado
durante el desarrollo del proyecto.

Se verificó el comportamiento utilizando información real del sistema.

Los resultados confirmaron la correcta detección de:

- MediaMTX;
- Control Center Backend;
- procesos FFmpeg;
- estados operativos;
- PID;
- consumo de CPU;
- utilización de memoria;
- tiempo de ejecución.

---

# Validación mediante API

La respuesta del endpoint fue consultada utilizando herramientas de
prueba HTTP.

Se verificó que la información entregada por la API coincidiera con el
estado observado directamente en el servidor.

La validación confirmó la consistencia entre:

- servicios administrados por systemd;
- procesos Linux;
- representación del dominio;
- respuesta REST.

---

# Resultado de las pruebas

Todas las pruebas finalizaron satisfactoriamente.

Resumen:

| Prueba | Resultado |
|---------|:---------:|
| Dominio | ✅ |
| Adaptador Linux | ✅ |
| Servicios | ✅ |
| API REST | ✅ |
| Integración | ✅ |
| Servidor real | ✅ |

---

# Conclusiones

El módulo de monitoreo de servicios cumple con los objetivos establecidos
para el Sprint-004.

La arquitectura implementada demuestra estabilidad, mantiene la
compatibilidad con los sprints anteriores y proporciona una base sólida
para incorporar nuevas capacidades de supervisión en futuras etapas del
Control Center.

---

# Documento siguiente

**07-EVIDENCE.md**