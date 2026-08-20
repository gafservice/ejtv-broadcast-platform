# 01. Node Health — Failure and Recovery Evidence

## Introducción

El presente documento registra la evidencia operacional obtenida durante la validación del mecanismo de **Node Health** implementado como parte de **ENG-013B — NOC Core / Node SDK**.

La validación fue realizada sobre el servidor físico `ejtv-01`, utilizando el runtime real del NOC y el monitor terminal integrado.

El objetivo de la prueba consistió en verificar que la política operacional de interfaces de red configurada para el Node se reflejara correctamente en el cálculo de **Network Health** y **Node Health**, y que los cambios físicos de conectividad fueran detectados y reflejados automáticamente por el NOC.

Las pruebas descritas en este documento ya fueron ejecutadas físicamente. Este documento registra los resultados obtenidos y no requiere repetir las interrupciones de interfaces utilizadas durante la validación.

---

## Entorno de validación

La validación fue realizada sobre:

```text
Node:       ejtv-01
Plataforma: Broadcast Platform
Componente: ENG-013B — NOC Core / Node SDK
Monitor:    NOC Terminal
```

La cadena operacional validada fue:

```text
Servidor físico
    ↓
LinuxSystemAdapter
    ↓
SystemService
    ↓
TelemetryRefreshService
    ↓
Network Health
    ↓
Node Health
    ↓
NodeHealthDiagnostic
    ↓
DashboardApplication
    ↓
NOC Terminal
```

Esta cadena permite que cambios observados en el estado físico del servidor se propaguen hasta la representación operacional presentada al operador.

---

## Política operacional de interfaces

La política del Node `ejtv-01` se encuentra definida en:

```text
control-center/config/nodes/ejtv-01.yaml
```

Durante la validación se utilizó la siguiente clasificación operacional:

| Interfaz  | Rol         | expected_up | critical |
| --------- | ----------- | ----------: | -------: |
| `enp9s0`  | INGEST      |        true |     true |
| `ens2f0`  | PUBLICATION |        true |     true |
| `ens2f1`  | BACKUP      |       false |    false |
| `enp10s0` | TEST        |       false |    false |
| `lo`      | LOOPBACK    |        true |    false |

Esta política distingue entre interfaces necesarias para la operación del Node e interfaces cuya disponibilidad no debe degradar su estado general.

---

## Prueba 1 — Falla de interfaz opcional

### Objetivo

Verificar que la pérdida de una interfaz clasificada como opcional no provoque una degradación incorrecta del Node.

La interfaz utilizada fue:

```text
enp10s0
Role:        TEST
expected_up: false
critical:    false
```

### Acción realizada

Se llevó físicamente la interfaz `enp10s0` a estado no operacional.

### Resultado observado

El NOC permaneció en:

```text
NODE HEALTH: HEALTHY
NETWORK:     HEALTHY
Issues:      0
```

### Interpretación

El comportamiento observado fue correcto.

La indisponibilidad de `enp10s0` no generó una condición de falla porque la política del Node establece explícitamente que esta interfaz no es requerida para su operación normal.

Esto demuestra que el cálculo de salud no interpreta indiscriminadamente toda interfaz en estado DOWN como una falla operacional.

---

## Prueba 2 — Falla de interfaz crítica

### Objetivo

Verificar que la pérdida de una interfaz requerida y crítica produzca una degradación inmediata del estado del Node.

La interfaz utilizada fue:

```text
enp9s0
Role:        INGEST
expected_up: true
critical:    true
```

### Acción realizada

Se llevó físicamente la interfaz `enp9s0` a estado no operacional.

### Resultado observado

El NOC Terminal reportó:

```text
NODE HEALTH: CRITICAL
System:      HEALTHY
Network:     CRITICAL
Issues:      1
```

La interfaz afectada fue identificada como:

```text
enp9s0: CRITICAL
```

y el diagnóstico presentó la razón:

```text
Required critical interface is not operational
```

### Interpretación

El resultado confirma que la política configurada para el Node fue aplicada correctamente por el runtime.

El estado `CRITICAL` no fue producido por una falla general del sistema operativo, ya que:

```text
System: HEALTHY
```

permaneció sin degradación.

La causa fue aislada específicamente en el dominio de red:

```text
Network: CRITICAL
```

Esto demuestra separación entre la salud general del sistema y la salud de la infraestructura de red.

---

## Impacto operacional sobre streaming

La pérdida de `enp9s0` no solamente produjo una modificación lógica del estado de Network Health.

La interfaz corresponde al camino de ingreso utilizado por el servicio de streaming, por lo que la interrupción produjo también un impacto observable sobre la operación real.

Durante la falla se observaron los siguientes valores:

```text
Paths:          0
Readers:        0
SRT:            0
Input traffic:  0
Output traffic: 0
STREAM HEALTH:  UNKNOWN
```

La secuencia operacional observada puede representarse como:

```text
enp9s0 DOWN
    ↓
Network Health = CRITICAL
    ↓
Node Health = CRITICAL
    ↓
Media ingest unavailable
    ↓
Paths / Readers / SRT / Traffic = 0
    ↓
Stream Health = UNKNOWN
```

Este comportamiento constituye evidencia de que una falla física real de infraestructura puede ser detectada por el Node y reflejada simultáneamente en los dominios correspondientes del NOC.

---

## Separación entre Node Health y Stream Health

La prueba permitió además validar una propiedad arquitectónica importante.

**Node Health** y **Stream Health** permanecen como conceptos separados.

La pérdida de una interfaz crítica produjo:

```text
Node Health   → CRITICAL
Network       → CRITICAL
Stream Health → UNKNOWN
```

El estado del stream no fue utilizado para sustituir ni redefinir el estado del Node.

De igual manera, el estado del Node no fue utilizado para fabricar un estado artificial del stream.

Esta separación permite que cada dominio conserve su propia semántica y facilita posteriormente la correlación de eventos y alarmas sin introducir acoplamiento incorrecto entre infraestructura y servicios multimedia.

---

## Prueba 3 — Recuperación operacional

### Objetivo

Verificar que el Node pudiera detectar automáticamente la recuperación de la interfaz crítica y regresar a un estado operacional saludable.

### Acción realizada

La interfaz `enp9s0` fue restaurada a su condición operacional.

### Resultado observado

El NOC regresó automáticamente a:

```text
NODE HEALTH: HEALTHY
Network:     HEALTHY
Issues:      0
```

La operación de streaming también se recuperó:

```text
Paths:         2
Readers:       1
SRT:           1
STREAM HEALTH: HEALTHY
```

### Recuperación sin reinicio

No fue necesario reiniciar el NOC para obtener la recuperación del estado.

El runtime detectó nuevamente la condición física del servidor y propagó el nuevo estado a través de la cadena de telemetría.

La secuencia observada fue:

```text
enp9s0 restored
    ↓
Network Health = HEALTHY
    ↓
Node Health = HEALTHY
    ↓
Issues = 0
    ↓
Media ingest restored
    ↓
Paths = 2
Readers = 1
SRT = 1
    ↓
Stream Health = HEALTHY
```

---

## Resultado de la validación

Las pruebas operacionales demostraron los siguientes comportamientos:

1. una interfaz opcional puede quedar no operacional sin degradar incorrectamente el Node;
2. una interfaz crítica requerida produce una condición `CRITICAL` cuando deja de estar operacional;
3. el diagnóstico identifica la interfaz responsable de la degradación;
4. el diagnóstico expone una razón operacional legible para el operador;
5. System Health permanece independiente de Network Health;
6. una falla física de la interfaz de ingest produce consecuencias reales y observables sobre el servicio de streaming;
7. Node Health y Stream Health conservan semánticas independientes;
8. la recuperación física de la interfaz es detectada automáticamente;
9. el Node retorna a estado `HEALTHY` sin intervención sobre el runtime del NOC;
10. el servicio de streaming recupera su operación y vuelve a ser observado como `HEALTHY`.

---

## Criterios de aceptación

| Criterio                                         | Resultado |
| ------------------------------------------------ | --------- |
| Interfaz opcional no degrada Node Health         | PASS      |
| Interfaz crítica caída degrada Network Health    | PASS      |
| Interfaz crítica caída degrada Node Health       | PASS      |
| System Health permanece independiente            | PASS      |
| Interfaz afectada es identificada                | PASS      |
| Razón de la falla es expuesta                    | PASS      |
| Impacto real sobre streaming es observable       | PASS      |
| Node Health y Stream Health permanecen separados | PASS      |
| Recuperación de interfaz es detectada            | PASS      |
| Node Health retorna automáticamente a HEALTHY    | PASS      |
| Streaming retorna a HEALTHY                      | PASS      |
| Recuperación no requiere reiniciar el NOC        | PASS      |

---

## Conclusión

La validación operacional demuestra que el mecanismo de Node Health implementado en ENG-013B responde correctamente ante cambios reales de la infraestructura física del servidor.

La política declarativa de interfaces configurada para `ejtv-01` permite distinguir entre interfaces opcionales e interfaces críticas, evitando falsos positivos y permitiendo detectar condiciones que comprometen la operación real del Node.

La prueba sobre `enp9s0` demostró además una relación observable entre una falla física de infraestructura y la pérdida del servicio de ingest, sin eliminar la separación conceptual entre Node Health y Stream Health.

Finalmente, la recuperación automática confirma que el runtime puede observar la restauración de la infraestructura y reconstruir el estado operacional del Node sin requerir reinicios manuales.

Esta evidencia establece una base funcional para el siguiente nivel del NOC:

```text
Node Health / Stream Health
        ↓
Events
        ↓
Operational Alarms
        ↓
Correlation
        ↓
NOC Terminal
        ↓
NOC Web
```
