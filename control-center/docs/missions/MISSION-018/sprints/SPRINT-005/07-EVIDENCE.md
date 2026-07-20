# SPRINT-005

# Evidencias

---

# Estado

**En desarrollo**

---

# Versión

**1.0**

---

# Fecha

Julio 2026

---

# Introducción

Este documento recopila las evidencias técnicas obtenidas durante el
desarrollo del Sprint-005.

Su propósito es demostrar objetivamente que los componentes
implementados funcionan correctamente y cumplen con los objetivos
establecidos para este Sprint.

Las evidencias incluyen resultados de pruebas automatizadas,
validaciones sobre el servidor real, respuestas de la API, registros del
sistema y cualquier otro elemento técnico que permita verificar el
correcto funcionamiento del módulo de monitoreo de MediaMTX.

---

# Objetivos de las evidencias

Las evidencias deberán demostrar:

- correcta integración con MediaMTX;
- funcionamiento del adaptador;
- construcción del modelo de dominio;
- operación del servicio de aplicación;
- funcionamiento de la API REST;
- validación sobre el servidor multimedia;
- estabilidad del sistema.

---

# Organización de las evidencias

Las evidencias podrán clasificarse en las siguientes categorías:

```
evidence/

├── api/
├── json/
├── logs/
├── screenshots/
├── tests/
└── diagrams/
```

Cada categoría almacenará la información correspondiente a una etapa de
la validación.

---

# Evidencias de implementación

## Adaptador MediaMTX

**Estado**

⏳ Pendiente

**Evidencias esperadas**

- consulta HTTP exitosa;
- interpretación del JSON;
- construcción de entidades del dominio.

---

## Modelos del dominio

**Estado**

⏳ Pendiente

**Evidencias esperadas**

- creación de objetos;
- validación de estados;
- serialización;
- pruebas unitarias.

---

## Servicio de aplicación

**Estado**

⏳ Pendiente

**Evidencias esperadas**

- generación del Snapshot;
- integración con el adaptador;
- respuesta consistente.

---

## API REST

**Estado**

⏳ Pendiente

**Evidencias esperadas**

- respuesta HTTP;
- estructura JSON;
- códigos de estado;
- tiempos de respuesta.

---

# Evidencias de pruebas

## Pruebas unitarias

**Estado**

⏳ Pendiente

Se incorporarán:

- salida de pytest;
- cobertura;
- resultados obtenidos.

---

## Pruebas de integración

**Estado**

⏳ Pendiente

Se documentarán:

- interacción entre capas;
- consultas reales;
- resultados.

---

## Validación sobre servidor real

**Estado**

⏳ Pendiente

Se registrarán:

- consulta al servidor;
- listado de paths;
- publishers;
- readers;
- protocolos;
- estados.

---

# Evidencias REST

Se documentarán ejemplos reales de las respuestas producidas por el
Control Center.

Ejemplo:

```json
{
    "status": "OK",
    "paths": []
}
```

Los ejemplos finales corresponderán a la implementación definitiva.

---

# Evidencias MediaMTX

Se incorporarán respuestas reales obtenidas desde la API del servidor.

Ejemplo:

```
GET /v3/paths/list
```

Respuesta:

```json
{
    ...
}
```

---

# Evidencias del Dashboard

Cuando el Dashboard consuma el nuevo endpoint se documentará:

- visualización;
- actualización;
- consistencia de datos.

---

# Evidencias de rendimiento

Durante la validación se registrarán métricas como:

- tiempo de respuesta;
- latencia de consulta;
- consumo de CPU;
- consumo de memoria;
- estabilidad.

---

# Evidencias de errores

También deberán documentarse los escenarios de error.

Ejemplos:

- timeout;
- MediaMTX detenido;
- respuesta inválida;
- error HTTP.

Cada caso deberá indicar:

- condición inicial;
- comportamiento observado;
- resultado esperado.

---

# Registro cronológico

| Fecha | Actividad | Resultado |
|---------|-----------|-----------|
| Pendiente | Inicio del Sprint | ⏳ |

Esta tabla se actualizará durante el desarrollo del Sprint.

---

# Cumplimiento de la Definition of Done

| Criterio | Estado |
|----------|:------:|
| Arquitectura aprobada | ⏳ |
| Implementación completa | ⏳ |
| Código revisado | ⏳ |
| Pruebas unitarias | ⏳ |
| Pruebas de integración | ⏳ |
| Validación servidor | ⏳ |
| Documentación | ⏳ |
| Evidencias completas | ⏳ |

---

# Conclusiones

Al finalizar el Sprint este documento contendrá toda la evidencia
necesaria para demostrar el correcto funcionamiento del módulo de
integración con MediaMTX y servirá como respaldo técnico para auditorías,
mantenimiento y futuras evoluciones del producto.

---

# Documento siguiente

**08-CHANGELOG.md**