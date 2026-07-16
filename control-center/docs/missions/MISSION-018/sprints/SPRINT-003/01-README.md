# SPRINT-003

# System Resources

---

# Estado

**Completado técnicamente**

---

# Versión

1.0

---

# Fecha

Julio 2026

---

# Misión

MISSION-018 — EJTV Control Center

---

# Capacidad

CAP-002 — System Resources

---

# Objetivo

Incorporar al EJTV Control Center la capacidad de consultar y exponer
el estado actual de los recursos principales del servidor Linux.

---

# Recursos incorporados

El Sprint agregó la consulta de:

- uso del procesador;
- cantidad de núcleos lógicos y físicos;
- frecuencia actual del procesador;
- memoria total, disponible y utilizada;
- espacio total, utilizado y libre del disco principal;
- tiempo de funcionamiento del servidor;
- instante de captura de la medición.

---

# Endpoint incorporado

```text
GET /api/v1/system/resources