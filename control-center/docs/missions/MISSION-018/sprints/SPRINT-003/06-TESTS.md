# SPRINT-003

# TESTS

---

# Objetivo

Verificar que la implementación de la capacidad **System Resources**
funciona correctamente en todas las capas de la arquitectura.

---

# Alcance

Se validaron los siguientes componentes:

- Dominio.
- Adaptador Linux.
- Servicio.
- API REST.
- Arquitectura.
- Integración.

---

# Pruebas unitarias

## Dominio

Archivo:

```text
backend/tests/domain/test_system_resources.py
```

Verificaciones realizadas:

- creación de CPUInfo;
- creación de MemoryInfo;
- creación de DiskInfo;
- creación de UptimeInfo;
- creación de SystemResources;
- validación de porcentajes;
- validación de memoria utilizada;
- validación de timezone;
- inmutabilidad.

Resultado:

```text
PASSED
```

---

## Adaptador Linux

Archivo:

```text
backend/tests/adapters/test_system_adapter.py
```

Verificaciones realizadas:

- hostname;
- sistema operativo;
- kernel;
- CPU;
- memoria;
- disco;
- uptime.

Resultado:

```text
PASSED
```

---

## Servicio

Archivo:

```text
backend/tests/services/test_system_service.py
```

Verificaciones realizadas:

- get_system_info();
- get_system_resources();
- cumplimiento del contrato del adaptador.

Resultado:

```text
PASSED
```

---

## API

Archivo:

```text
backend/tests/test_system_api.py
```

Verificaciones realizadas:

- GET /api/v1/system/info;
- preservación del Request-ID;
- GET /api/v1/system/resources.

Resultado:

```text
PASSED
```

---

## Arquitectura

Archivo:

```text
backend/tests/architecture/
```

Verificaciones realizadas:

- separación de capas;
- cumplimiento del contrato;
- aislamiento del adaptador Linux.

Resultado:

```text
PASSED
```

---

## Integración

Archivo:

```text
backend/tests/integration/test_system_real.py
```

Resultado:

```text
PASSED
```

---

# Validación funcional

Además de las pruebas automatizadas, se realizaron consultas reales
contra la API ejecutando:

```bash
curl http://127.0.0.1:8000/api/v1/system/info

curl http://127.0.0.1:8000/api/v1/system/resources
```

Ambos endpoints respondieron correctamente con datos reales del servidor.

---

# Resultado global

Suite completa ejecutada:

```text
46 passed
0 failed
1 warning (no bloqueante)
```

---

# Conclusión

La capacidad **System Resources** quedó validada tanto mediante pruebas
automatizadas como mediante consultas reales sobre el servidor EJTV.

El Sprint-003 se considera técnicamente aprobado.

---