# SPRINT-003

# EVIDENCE

---

# Objetivo

Registrar las evidencias obtenidas durante la validación del Sprint-003
correspondiente a la capacidad **System Resources**.

---

# Evidencia 1 — Suite completa de pruebas

Se ejecutó la totalidad de las pruebas del backend mediante:

```bash
PYTHONPATH=backend pytest backend/tests -v
```

Resultado:

```text
========================================

46 passed

0 failed

1 warning (no bloqueante)

========================================
```

Conclusión:

Toda la arquitectura quedó validada sin errores.

---

# Evidencia 2 — Endpoint System Info

Consulta ejecutada:

```bash
curl http://127.0.0.1:8000/api/v1/system/info
```

Resultado:

```json
{
    "hostname": "ejtv-01",
    "operating_system": "Ubuntu 24.04.4 LTS",
    "kernel": "6.17.0-35-generic"
}
```

Resultado:

El endpoint respondió correctamente.

---

# Evidencia 3 — Endpoint System Resources

Consulta ejecutada:

```bash
curl http://127.0.0.1:8000/api/v1/system/resources
```

Resultado obtenido:

```json
{
    "cpu": {
        "usage_percent": 29.1,
        "logical_cores": 8,
        "physical_cores": 4,
        "frequency_mhz": 2925.7618
    },
    "memory": {
        "total_bytes": 8313946112,
        "available_bytes": 3305046016,
        "used_bytes": 5008900096,
        "usage_percent": 60.2
    },
    "disk": {
        "total_bytes": 501809635328,
        "used_bytes": 49568509952,
        "free_bytes": 426675322880,
        "usage_percent": 10.4
    },
    "uptime": {
        "uptime_seconds": 1258256
    },
    "captured_at": "2026-07-16T13:35:26.841605Z"
}
```

Conclusión:

La información corresponde al estado real del servidor EJTV.

---

# Evidencia 4 — Inicio del servidor

El backend inició correctamente mediante:

```bash
PYTHONPATH=backend uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000
```

Registro observado:

```text
Application startup complete.

Uvicorn running on http://0.0.0.0:8000
```

Conclusión:

La aplicación inicia sin errores.

---

# Evidencia 5 — Arquitectura validada

Durante la ejecución de la suite se verificó:

- Dominio.
- Adaptadores.
- Servicios.
- API.
- Integración.
- Arquitectura.

No se detectaron violaciones de dependencia entre capas.

---

# Resultado del Sprint

El Sprint-003 incorporó exitosamente la capacidad permanente
**System Resources** al EJTV Control Center.

La plataforma puede consultar recursos reales del servidor Linux y
publicarlos mediante una API REST manteniendo la arquitectura definida
para el proyecto.

---

# Estado

**SPRINT-003 COMPLETADO TÉCNICAMENTE**

---

# Evidencia 6 — Acceso desde una red externa

La API fue publicada temporalmente mediante una regla NAT en el router
y una autorización temporal del puerto TCP 8000 en el firewall UFW.

Se verificó desde una red externa el acceso a:

```text
GET /api/v1/system/info
GET /api/v1/system/resources
GET /docs