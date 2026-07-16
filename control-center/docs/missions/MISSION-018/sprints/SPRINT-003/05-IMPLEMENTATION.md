# SPRINT-003

# IMPLEMENTATION

---

# Objetivo

Implementar la capacidad **System Resources** dentro del backend del
EJTV Control Center siguiendo la arquitectura por capas definida para el
proyecto.

---

# Componentes implementados

Durante este Sprint se desarrollaron los siguientes componentes.

---

# Dominio

Se incorporaron nuevos modelos de dominio para representar los recursos
del servidor.

Modelos implementados:

- CPUInfo
- MemoryInfo
- DiskInfo
- UptimeInfo
- SystemResources

Cada modelo valida sus propios datos y permanece completamente
independiente del sistema operativo.

---

# Contrato

Se amplió la interfaz:

```text
SystemAdapter
```

Nuevos métodos incorporados:

```text
cpu_info()

memory_info()

disk_info()

uptime_info()
```

Estos métodos representan el contrato oficial para cualquier adaptador
del sistema.

---

# Adaptador Linux

Se implementó:

```text
LinuxSystemAdapter
```

La implementación utiliza la biblioteca:

```text
psutil
```

para consultar información real del servidor.

Información obtenida:

- utilización del procesador;
- núcleos físicos;
- núcleos lógicos;
- frecuencia del CPU;
- memoria;
- almacenamiento;
- tiempo de actividad.

---

# Servicio

Se amplió:

```text
SystemService
```

Nuevo método:

```text
get_system_resources()
```

Responsabilidades:

- consultar el adaptador;
- construir el objeto SystemResources;
- devolver el resultado a la API.

---

# API REST

Se incorporó el endpoint:

```text
GET /api/v1/system/resources
```

La respuesta mantiene el formato estándar utilizado por el backend.

La información publicada incluye:

- CPU;
- memoria;
- disco;
- uptime;
- instante de captura.

---

# Serialización

Se incorporó una función auxiliar para serializar correctamente
estructuras de datos compuestas por múltiples dataclasses.

Esto permite publicar objetos complejos mediante la API sin exponer la
estructura interna del dominio.

---

# Dependencias

Se incorporó oficialmente:

```text
psutil
```

como dependencia del backend.

---

# Pruebas implementadas

Se desarrollaron nuevas pruebas para:

- modelos del dominio;
- adaptador Linux;
- servicio;
- endpoint REST.

Además se ejecutó la suite completa del backend.

Resultado:

```text
46 passed

0 failed

1 warning no bloqueante
```

---

# Validación funcional

La implementación fue validada mediante consultas reales utilizando:

```bash
curl http://127.0.0.1:8000/api/v1/system/info

curl http://127.0.0.1:8000/api/v1/system/resources
```

Ambos endpoints respondieron correctamente con información obtenida
directamente del servidor Linux.

---

# Archivos modificados

Durante el Sprint se modificaron principalmente los siguientes módulos:

```text
backend/app/domain/system/

backend/app/adapters/base/

backend/app/adapters/linux/

backend/app/services/

backend/app/api/v1/

backend/tests/

backend/requirements.txt
```

---

# Resultado

El Sprint incorpora de forma permanente la capacidad **System Resources**
al EJTV Control Center.

La plataforma puede consultar recursos reales del servidor, procesarlos
mediante la capa de servicios y publicarlos mediante una API REST,
manteniendo la arquitectura limpia definida para el proyecto.

---

# Estado

**IMPLEMENTACIÓN COMPLETADA**

---