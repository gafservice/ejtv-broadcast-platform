# SPRINT-005

# Pruebas

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

El Sprint-005 incorpora el primer módulo de monitoreo funcional del
servidor multimedia MediaMTX.

Las pruebas definidas en este documento tienen como objetivo verificar
que la integración entre el Control Center y la API HTTP de MediaMTX sea
correcta, consistente y estable.

Las validaciones abarcan pruebas unitarias, integración y operación sobre
el servidor real.

---

# Objetivos de las pruebas

Las pruebas deberán demostrar que:

- el adaptador consulta correctamente la API;
- las respuestas JSON son interpretadas correctamente;
- el dominio permanece desacoplado de MediaMTX;
- el servicio construye un Snapshot consistente;
- la API REST devuelve información válida;
- los errores son manejados correctamente;
- la implementación funciona sobre el servidor del proyecto.

---

# Tipos de pruebas

Durante el Sprint se realizarán:

- pruebas unitarias;
- pruebas de integración;
- pruebas funcionales;
- validación sobre servidor real.

---

# Pruebas del dominio

Se validará la correcta construcción de las entidades del dominio.

Entre ellas:

- MediaMTXSnapshot;
- MediaPath;
- MediaPublisher;
- MediaReader;
- MediaProtocol;
- MediaStatistics.

Las pruebas verificarán:

- creación;
- validación;
- consistencia;
- serialización.

---

# Pruebas del adaptador

El adaptador deberá validarse utilizando respuestas simuladas.

Se comprobará:

- conexión HTTP;
- lectura del JSON;
- transformación al dominio;
- manejo de errores;
- timeout;
- respuestas inválidas.

---

# Pruebas del servicio

La capa de servicios deberá comprobar:

- consulta al adaptador;
- creación del Snapshot;
- integración con el dominio;
- propagación de errores controlados.

---

# Pruebas de la API REST

Se verificará el nuevo endpoint.

Aspectos a validar:

- código HTTP;
- estructura JSON;
- contenido;
- manejo de errores;
- respuesta cuando MediaMTX no está disponible.

---

# Pruebas de integración

Las pruebas de integración deberán confirmar la interacción entre:

```
MediaMTX

↓

Adapter

↓

Domain

↓

Service

↓

REST API
```

El flujo completo deberá ejecutarse correctamente.

---

# Validación sobre el servidor

La validación final utilizará el servidor multimedia del proyecto.

Durante esta etapa se verificará:

- disponibilidad de MediaMTX;
- consulta exitosa de la API;
- recuperación de los paths;
- estado de cada path;
- publishers;
- readers;
- protocolos detectados.

---

# Casos de prueba

## Caso 1

MediaMTX disponible.

Resultado esperado:

La API responde correctamente.

---

## Caso 2

MediaMTX detenido.

Resultado esperado:

El Control Center informa el error sin detenerse.

---

## Caso 3

MediaMTX responde sin paths.

Resultado esperado:

Snapshot válido con lista vacía.

---

## Caso 4

Path con Publisher.

Resultado esperado:

Estado ACTIVE.

---

## Caso 5

Path sin Publisher.

Resultado esperado:

Estado NO_PUBLISHER.

---

## Caso 6

Path con Readers.

Resultado esperado:

Cantidad de lectores correcta.

---

## Caso 7

Respuesta HTTP inválida.

Resultado esperado:

Error controlado.

---

## Caso 8

Timeout.

Resultado esperado:

Excepción controlada.

---

# Criterios de aceptación

El Sprint será considerado validado cuando:

- todas las pruebas unitarias sean satisfactorias;
- todas las pruebas de integración finalicen correctamente;
- el servidor real responda correctamente;
- la API REST publique la información esperada;
- el Control Center continúe funcionando ante errores.

---

# Evidencias esperadas

Al finalizar las pruebas deberán existir evidencias de:

- ejecución del backend;
- respuesta de MediaMTX;
- respuesta REST;
- pruebas automatizadas;
- validación del servidor real.

---

# Resultado esperado

La batería de pruebas deberá confirmar que el nuevo módulo de monitoreo
de MediaMTX puede integrarse al Control Center manteniendo la estabilidad
del sistema y respetando la arquitectura definida para la MISSION-018.

---

# Estado de avance

| Prueba | Estado |
|---------|:------:|
| Dominio | ⏳ |
| Adaptador | ⏳ |
| Servicio | ⏳ |
| REST API | ⏳ |
| Integración | ⏳ |
| Servidor real | ⏳ |

---

# Documento siguiente

**07-EVIDENCE.md**