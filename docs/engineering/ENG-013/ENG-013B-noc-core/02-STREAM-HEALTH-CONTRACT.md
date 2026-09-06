# ENG-013B — Stream Health Evolution Contract

**Documento propuesto:** `02-STREAM-HEALTH-CONTRACT.md`

**Ingeniería:** ENG-013 — Network Operations Center

**Etapa:** ENG-013B — NOC Core

**Subsistema:** Stream Health

**Estado:** Contrato arquitectónico previo a implementación multiprotocolo

---

## 1. Propósito

El presente documento define el contrato arquitectónico, operacional y de evolución de **Stream Health** dentro de **ENG-013B — NOC Core** de la plataforma Broadcast.

Stream Health es responsable de transformar evidencia observable de los servicios multimedia —sesiones, conexiones, métricas, tráfico y telemetría específica de protocolo— en un estado operacional interpretable por el NOC.

El objetivo no es únicamente responder:

```
```

```
¿Está bien o está mal el streaming?
```

El objetivo final es que el NOC pueda responder:

```
```

```
¿QUÉ está fallando?
¿DÓNDE está fallando?
¿QUÉ servicio está afectado?
¿QUÉ protocolo está afectado?
¿QUÉ cliente o conexión está afectado?
¿QUÉ rol cumple?
¿POR QUÉ fue clasificado así?
¿DESDE CUÁNDO existe la condición?
¿ES transitoria o persistente?
¿CUÁL es el alcance?
¿CUÁL es el impacto?
¿QUÉ transición ocurrió?
¿QUÉ Event registró esa transición?
¿EXISTE una Alarm?
¿REQUIERE intervención del operador?
¿QUÉ evidencia histórica existe?
```

El diseño deberá soportar:

```
```

```
N servicios
×
N protocolos
×
N clientes/conexiones
×
N Nodes
```

sin introducir dependencias rígidas sobre nombres, cantidades o topologías particulares.

---

# PARTE I — AUTORIDAD Y BASELINE ARQUITECTÓNICO

## 2. Autoridad del contrato

Este documento constituye el contrato arquitectónico de Stream Health para ENG-013B.

Define:

-  semántica;
-  responsabilidades;
-  invariantes;
-  relaciones entre subsistemas;
-  límites arquitectónicos;
-  estrategia de evolución;
-  estrategia de implementación;
-  criterios de aceptación;
-  criterios de validación;
-  trazabilidad.

No pretende congelar prematuramente la estructura exacta de clases Python.

Cuando el contrato establezca conceptos como:

```
```

```
Client Health
Protocol Health
Service Health
Global Stream Health
```

estos deberán interpretarse primero como **responsabilidades y niveles semánticos**.

No implican automáticamente la creación de clases:

```
```

```
ClientHealth
ProtocolHealth
ServiceHealth
GlobalStreamHealth
```

si el dominio existente puede evolucionar para representar correctamente esas responsabilidades.

---

## 3. Autoridad del dominio

La autoridad sobre el estado de Health reside en el dominio y en los servicios responsables de evaluarlo.

No reside en:

```
```

```
Dashboard
renderer
color
texto mostrado
terminal
web UI
```

El Dashboard representa el estado.

No lo determina.

Queda prohibido introducir reglas de severidad exclusivamente dentro de la capa de presentación.

---

## 4. Estado de partida

La plataforma ya dispone de una base funcional sobre la cual evolucionará Stream Health.

Existen actualmente conceptos como:

```
```

```
HealthStatus
StreamingConnectionHealth
StreamingPathHealth
StreamingHealth
SessionProtocol
SessionSnapshot
```

y existe infraestructura de sesiones capaz de observar múltiples protocolos.

El modelo de sesiones contempla actualmente:

```
```

```
SRT
RTMP
RTSP
HLS
WebRTC
```

Stream Health, sin embargo, mantiene actualmente una semántica y evaluación predominantemente centrada en SRT.

Por tanto:

```
```

```
MULTIPROTOCOL SESSION OBSERVABILITY
                ✓

COMPLETE MULTIPROTOCOL STREAM HEALTH
                ✗
```

El objetivo de este contrato es cerrar progresivamente esa diferencia.

---

## 5. Baseline operacional

Antes de formalizar este contrato se verificó el sistema real en operación.

El NOC Terminal se encontraba ejecutándose sobre el servidor real y observando:

```
```

```
MediaMTX       ONLINE
MediaMTX API   ONLINE

Paths          3
Readers        3

ejtv           ACTIVE / AVAILABLE
enlace         ACTIVE / AVAILABLE
impact         ACTIVE / AVAILABLE

Stream Health  HEALTHY
Node Health    HEALTHY
Active Alarms  0
```

El sistema observaba clientes SRT activos y, simultáneamente, Events asociados a conexiones RTMP.

Esto demuestra que la observabilidad multiprotocolo ya existe parcialmente aunque la evaluación de Stream Health todavía no sea completamente multiprotocolo.

---

# PARTE II — PRINCIPIOS FUNDAMENTALES

## 6. Principio arquitectónico principal

La cadena canónica será:

```
```

```
RAW TELEMETRY / METRICS
          │
          ▼
PROTOCOL ADAPTER / NORMALIZATION
          │
          ▼
HEALTH EVALUATION
          │
          ▼
CURRENT HEALTH
          │
          ▼
STATE TRANSITION
          │
          ▼
NOC EVENT
          │
          ▼
ALARM POLICY
          │
          ▼
NOC ALARM
          │
          ▼
HISTORY / EVIDENCE
```

La regla fundamental es:

> **Stream Health determina estado. Events registran transiciones y hechos operacionales. Alarm Policies determinan cuáles condiciones requieren intervención. History conserva la memoria operacional.**

---

## 7. Relación prohibida

Queda prohibida como arquitectura general:

```
```

```
bad metric
    │
    ▼
  ALARM
```

La relación correcta será:

```
```

```
metric
  ↓
semantic evaluation
  ↓
health state
  ↓
transition
  ↓
event
  ↓
alarm policy
  ↓
alarm when applicable
```

---

## 8. Separación de dominios

Los siguientes conceptos deberán permanecer diferenciados:

```
```

```
Node Health
Stream Health
Availability
Session State
Event
Alarm
History
Dashboard
```

No son sinónimos.

No deberán sustituirse entre sí.

---

# PARTE III — NODE HEALTH, STREAM HEALTH, AVAILABILITY Y SESSIONS

## 9. Node Health

Node Health describe la condición operacional del Node y su infraestructura.

Puede considerar dominios como:

```
```

```
System
Network
Storage
CPU
Memory
Interfaces
```

según la arquitectura del Node.

---

## 10. Stream Health

Stream Health describe la condición operacional de los servicios multimedia observados.

Puede evaluar:

```
```

```
servicios
protocolos
sesiones
conexiones
publishers
readers
ingest
distribution
traffic
protocol metrics
```

---

## 11. Node Health no es Stream Health

Se establece:

```
```

```
NODE HEALTH != STREAM HEALTH
```

Una condición crítica del Node puede afectar el streaming.

Pero esa relación deberá expresarse como correlación operacional.

No mediante sustitución automática de estados.

---

## 12. Precedente físico

La validación física de ENG-013B demostró:

```
```

```
enp9s0 DOWN
       ↓
Network Health = CRITICAL
       ↓
Node Health = CRITICAL
       ↓
Media ingest unavailable
       ↓
Paths / Readers / Traffic = 0
       ↓
Stream Health = UNKNOWN
```

Esta conducta se considera arquitectónicamente correcta.

Por tanto:

```
```

```
Node Health = CRITICAL
```

no autoriza automáticamente:

```
```

```
Stream Health = CRITICAL
```

sin evidencia propia del dominio de streaming.

---

## 13. Availability

Availability responde principalmente:

```
```

```
¿Está disponible?
```

Health responde:

```
```

```
¿Qué tan correctamente está funcionando?
```

Por tanto puede existir:

```
```

```
Availability = AVAILABLE
Health       = DEGRADED
```

---

## 14. Session State

Session State describe existencia o actividad de una sesión.

Ejemplo:

```
```

```
CONNECTED
```

no implica necesariamente:

```
```

```
HEALTHY
```

Una sesión puede estar conectada mientras presenta:

```
```

```
packet loss
high RTT
jitter
retransmissions
traffic stalled
protocol errors
buffer problems
```

Por tanto:

```
```

```
SESSION STATE != HEALTH
```

---

# PARTE IV — MODELO OPERACIONAL MULTIPROTOCOLO

## 15. Jerarquía semántica

El modelo objetivo será:

```
```

```
GLOBAL STREAM HEALTH
          │
          ▼
       SERVICES
          │
          ▼
    SERVICE HEALTH
          │
          ▼
      PROTOCOLS
          │
          ▼
    PROTOCOL HEALTH
          │
          ▼
CLIENTS / CONNECTIONS
          │
          ▼
CLIENT / CONNECTION HEALTH
```

Desde el punto de vista de evaluación ascendente:

```
```

```
CLIENT / CONNECTION HEALTH
             │
             ▼
       PROTOCOL HEALTH
             │
             ▼
        SERVICE HEALTH
             │
             ▼
  GLOBAL STREAM HEALTH
```

---

## 16. Service

Un Service representa una unidad lógica multimedia observada por la plataforma.

Ejemplos actuales:

```
```

```
ejtv
enlace
impact
```

son datos operacionales.

No son elementos del dominio codificados de forma estática.

Queda prohibido introducir lógica como:

```
```

```
if service == "impact":
    ...
```

para determinar comportamiento estructural de Health.

---

## 17. Escalabilidad de servicios

El sistema deberá soportar:

```
```

```
service-001
service-002
...
service-N
```

sin modificación del núcleo de Health.

---

## 18. Protocol

Protocol constituye una dimensión independiente de Service.

Se establece:

```
```

```
SERVICE != PROTOCOL
```

Un mismo servicio puede participar en diferentes protocolos.

Conceptualmente:

```
```

```
impact
├── SRT
├── RTMP
├── RTSP
├── HLS
└── WebRTC
```

---

## 19. Protocolos actuales

El contrato contempla inicialmente:

```
```

```
SRT
RTMP
RTSP
HLS
WebRTC
```

La arquitectura deberá permitir protocolos futuros.

---

## 20. Soporte de sesión no implica soporte completo de Health

Debe distinguirse:

```
```

```
PROTOCOL OBSERVABLE
```

de:

```
```

```
PROTOCOL HEALTH FULLY EVALUATED
```

Por ejemplo:

```
```

```
RTMP session observed
        ↓
Session Event
```

puede existir antes de disponer de:

```
```

```
complete RTMP Health evaluator
```

Esto es válido.

---

# PARTE V — CLIENT / CONNECTION

## 21. Connection

Una Connection representa una relación operacional concreta entre un servicio y un endpoint.

Deberá conservar tanta identidad como permita la evidencia disponible.

Conceptualmente:

```
```

```
node
service
protocol
session_id / connection_id
role
direction
remote endpoint
metadata
```

---

## 22. Identidad estable

La IP remota no deberá utilizarse como única identidad cuando exista información más específica.

Dos conexiones pueden compartir:

```
```

```
IP
service
protocol
```

y seguir siendo conexiones diferentes.

Cuando MediaMTX u otra fuente proporcione:

```
```

```
connection_id
session_id
```

deberá preservarse cuando sea operacionalmente útil.

---

## 23. Remote endpoint

El endpoint remoto constituye contexto operacional.

No necesariamente constituye identidad lógica permanente del cliente.

Se deberá distinguir entre:

```
```

```
client identity
```

y:

```
```

```
current network endpoint
```

cuando exista información suficiente.

---

# PARTE VI — ROLE Y DIRECTION

## 24. Rol

La arquitectura deberá poder representar semánticamente roles como:

```
```

```
INGEST
PUBLISHER
READER
DISTRIBUTION
UNKNOWN
```

La representación exacta deberá reutilizar o evolucionar el dominio existente.

---

## 25. UNKNOWN role

Cuando no exista evidencia suficiente para determinar el rol:

```
```

```
role = UNKNOWN
```

Nunca deberá inferirse arbitrariamente.

---

## 26. Importancia operacional del rol

No todas las conexiones tienen el mismo impacto.

Ejemplo:

```
```

```
1 READER CRITICAL
```

puede afectar solamente un consumidor.

Mientras:

```
```

```
PRIMARY INGEST CRITICAL
```

puede afectar a todos los consumidores de un servicio.

Por tanto, role/direction podrá participar en:

```
```

```
Health aggregation
impact calculation
alarm policy
diagnostics
```

---

# PARTE VII — CANONICAL HEALTH STATES

## 27. Estados

Se reutilizará el `HealthStatus` canónico existente:

```
```

```
HEALTHY
DEGRADED
CRITICAL
UNKNOWN
```

Queda prohibido crear innecesariamente otro enum equivalente para Stream Health.

---

## 28. HEALTHY

HEALTHY significa:

> Existe evidencia suficiente y confiable para determinar que el objeto evaluado se encuentra dentro de condiciones operacionales aceptables.

No significa simplemente:

```
```

```
no error detected
```

si tampoco existe evidencia suficiente.

---

## 29. DEGRADED

DEGRADED significa:

> Existe evidencia de deterioro operacional significativo, pero el objeto continúa prestando una función útil o parcialmente funcional.

---

## 30. CRITICAL

CRITICAL significa:

> Existe evidencia suficiente de una condición severa que compromete materialmente el funcionamiento del objeto evaluado.

La severidad deberá interpretarse considerando:

```
```

```
protocol
role
direction
scope
persistence
impact
```

---

## 31. UNKNOWN

UNKNOWN significa:

> No existe evidencia suficiente o confiable para determinar el estado.

Regla contractual:

```
```

```
INSUFFICIENT EVIDENCE != HEALTHY
```

y:

```
```

```
INSUFFICIENT EVIDENCE = UNKNOWN
```

UNKNOWN no significa automáticamente falla.

---

# PARTE VIII — TELEMETRÍA Y EVALUADORES DE PROTOCOLO

## 32. Evaluación específica por protocolo

Cada protocolo podrá necesitar evidencia diferente.

Arquitectura conceptual:

```
```

```
                RAW TELEMETRY
                     │
      ┌──────────────┼──────────────┐
      │              │              │
     SRT            RTMP          WebRTC ...
      │              │              │
      ▼              ▼              ▼
 SRT Adapter    RTMP Adapter    WebRTC Adapter
      │              │              │
      ▼              ▼              ▼
 SRT Evaluator  RTMP Evaluator  WebRTC Evaluator
      │              │              │
      └──────────────┼──────────────┘
                     ▼
             COMMON HEALTH MODEL
```

---

## 33. Responsabilidad del adapter

El Adapter obtiene y normaliza evidencia.

No deberá convertirse innecesariamente en la autoridad de severidad.

Conceptualmente:

```
```

```
Adapter:
    "RTT = 8 ms"

Evaluator:
    "esta evidencia corresponde a HEALTHY"
```

---

## 34. Responsabilidad del evaluator

El evaluator interpreta evidencia dentro de la semántica del protocolo.

Produce:

```
```

```
status
reason
diagnostics
evidence
```

según el modelo disponible.

---

# PARTE IX — SRT HEALTH V2

## 35. SRT como primera implementación vertical

SRT será el primer protocolo que evolucionará bajo este contrato porque ya dispone de:

```
```

```
telemetry
real clients
real operational traffic
tests
physical evidence
existing evaluator
```

No se reemplazará innecesariamente el evaluador existente.

Se evolucionará.

---

## 36. Señales SRT

Podrán evaluarse, previa validación semántica:

```
```

```
RTT
packet loss
packet loss rate
retransmissions
drops
send rate
receive rate
buffers
ACK/NAK
traffic continuity
```

y otras métricas verificadas.

---

## 37. Una métrica disponible no implica una señal de severidad

La existencia de una métrica en MediaMTX no significa que deba participar automáticamente en Health.

Toda métrica que afecte severidad deberá tener:

```
```

```
semantic justification
test coverage
operational evidence
```

---

## 38. Precedente link\_capacity

El incidente real observado demostró que:

```
```

```
send_rate / estimated_link_capacity > 100 %
```

puede coexistir con:

```
```

```
low RTT
zero meaningful loss
stable operational stream
```

Por tanto:

```
```

```
link_capacity
```

se conserva como **diagnostic telemetry**.

No será por sí sola señal autónoma de:

```
```

```
DEGRADED
CRITICAL
```

---

## 39. Trazabilidad link\_capacity

Esta decisión está consolidada por:

```
```

```
412b17c
fix(streaming): treat SRT link capacity as diagnostic
```

y deberá mantenerse protegida por regresión.

---

# PARTE X — COUNTERS, RATES Y TIME

## 40. Contadores acumulativos

Un contador acumulativo no expresa automáticamente severidad.

Ejemplo:

```
```

```
retransmissions = 3000
```

carece de suficiente contexto.

Podría representar:

```
```

```
3000 / 20 days
```

o:

```
```

```
3000 / 20 seconds
```

con significados completamente diferentes.

---

## 41. Deltas

Cuando corresponda, deberán utilizarse:

```
```

```
delta counter
```

entre observaciones.

---

## 42. Rates

Cuando corresponda, deberán derivarse:

```
```

```
events / second
packets / second
loss %
retransmission rate
```

en lugar de interpretar directamente el total acumulado.

---

## 43. Ventanas temporales

La evaluación podrá operar sobre ventanas.

Ejemplo:

```
```

```
t0 HEALTHY
t1 anomaly
t2 HEALTHY
```

no deberá necesariamente generar:

```
```

```
HEALTHY
CRITICAL
HEALTHY
```

---

## 44. Persistence

Una condición podrá requerir persistencia antes de modificar Health.

Conceptualmente:

```
```

```
anomaly
   ↓
observation
   ↓
persists
   ↓
DEGRADED
```

---

## 45. Hysteresis

La recuperación podrá requerir estabilidad suficiente.

Conceptualmente:

```
```

```
CRITICAL
   ↓
metrics recover
   ↓
stability window
   ↓
HEALTHY
```

Esto evita:

```
```

```
HEALTHY
DEGRADED
HEALTHY
DEGRADED
HEALTHY
```

en períodos cortos.

---

## 46. Umbrales

No se incorporarán umbrales arbitrarios sin evidencia.

Los umbrales deberán ser:

```
```

```
explicit
testable
justifiable
traceable
configurable when appropriate
```

---

# PARTE XI — DIAGNOSTICS

## 47. Health debe explicar su resultado

Un estado sin explicación tiene utilidad operacional limitada.

El objetivo será producir conceptualmente:

```
```

```
STATUS
+
REASON
+
EVIDENCE
+
SCOPE
+
IMPACT
```

---

## 48. Diagnóstico estructurado

Cuando exista evidencia, el diagnóstico podrá contener:

```
```

```
node
service
protocol
connection/session
role
direction
remote endpoint
previous health
current health
reason
observed_at
metrics
duration
scope
impact
```

---

## 49. Reason codes

Se favorecerán razones estructuradas.

Ejemplo:

```
```

```
reason_code = sustained_packet_loss
```

acompañadas de explicación humana:

```
```

```
Sustained SRT packet loss detected
```

---

## 50. Estabilidad de reason codes

Cuando un reason code sea utilizado en:

```
```

```
Events
History
API
Tests
Alarm Policies
```

deberá considerarse parte del contrato y modificarse mediante change control.

---

# PARTE XII — AGGREGATION

## 51. La agregación no será ingenua

Queda prohibido establecer universalmente:

```
```

```
worst child wins
```

sin analizar la semántica del nivel agregado.

---

## 52. Factores de agregación

La agregación podrá considerar:

```
```

```
role
direction
scope
impact
affected population
service availability
protocol importance
persistence
dependency
```

---

## 53. Client Health no determina automáticamente Service Health

Ejemplo:

```
```

```
Service IMPACT

Reader A = HEALTHY
Reader B = CRITICAL
Reader C = HEALTHY
```

no obliga automáticamente:

```
```

```
Service IMPACT = CRITICAL
```

---

## 54. Primary source failure

En contraste:

```
```

```
Primary publisher = CRITICAL
```

puede justificar:

```
```

```
Service = CRITICAL
```

cuando la dependencia operacional lo demuestre.

---

# PARTE XIII — PROTOCOL HEALTH

## 55. Protocol Health

Protocol Health representa la condición de un protocolo dentro del contexto de un servicio.

Ejemplo:

```
```

```
IMPACT

SRT      HEALTHY
RTMP     DEGRADED
HLS      HEALTHY
WebRTC   UNKNOWN
```

Esta es una semántica requerida.

No constituye obligación de crear una clase `ProtocolHealth`.

---

# PARTE XIV — SERVICE HEALTH

## 56. Service Health

Service Health representa la condición operacional de un servicio multimedia.

Puede considerar:

```
```

```
sources
publishers
protocols
clients
availability
impact
dependencies
```

sin fusionar indebidamente esos conceptos.

---

# PARTE XV — GLOBAL STREAM HEALTH

## 57. Global Stream Health

Representa la visión agregada del dominio multimedia observado.

Ejemplo:

```
```

```
ejtv      HEALTHY
enlace    HEALTHY
impact    DEGRADED
service-N HEALTHY
```

produce un estado global conforme a la política de agregación.

---

## 58. Trazabilidad descendente

Global Stream Health nunca deberá convertirse en un indicador opaco.

El operador deberá poder navegar:

```
```

```
GLOBAL
  ↓
SERVICE
  ↓
PROTOCOL
  ↓
CLIENT / CONNECTION
  ↓
REASON / EVIDENCE
```

---

# PARTE XVI — SCOPE E IMPACT

## 59. Scope

Una condición deberá poder expresar su alcance cuando sea determinable.

Conceptualmente:

```
```

```
CONNECTION
PROTOCOL
SERVICE
PLATFORM
```

---

## 60. Impact

Impact responde:

```
```

```
¿A quién afecta?
```

Ejemplos:

```
```

```
1 reader
5 readers
all clients of service
primary ingest
entire service
multiple services
platform
```

---

## 61. Scope e Impact no son lo mismo

Una condición puede originarse en:

```
```

```
CONNECTION
```

pero tener impacto:

```
```

```
SERVICE
```

si dicha conexión corresponde a una dependencia primaria.

---

# PARTE XVII — HEALTH TRANSITIONS

## 62. Current State

Health describe el estado actual.

---

## 63. Transition

Transition describe un cambio semántico.

Ejemplos:

```
```

```
UNKNOWN  → HEALTHY
HEALTHY  → DEGRADED
DEGRADED → CRITICAL
CRITICAL → DEGRADED
CRITICAL → HEALTHY
HEALTHY  → UNKNOWN
```

---

## 64. Observación sin transición

Si:

```
```

```
HEALTHY → HEALTHY
```

no existe necesariamente una transición operacional que deba convertirse en Event.

---

# PARTE XVIII — EVENTS

## 65. Events existentes son la autoridad

No se creará:

```
```

```
StreamEventDatabase
StreamEventService
StreamEventHistory
```

como sistema paralelo al NOC.

Stream Health utilizará la infraestructura de Events existente.

---

## 66. Pipeline de Events

La relación será:

```
```

```
Health Evaluation
       ↓
State Transition
       ↓
NOC Event
```

---

## 67. Infraestructura existente

Antes de crear nuevas abstracciones deberán reutilizarse o evolucionarse, cuando corresponda:

```
```

```
HealthTransitionDetector
HealthTransitionEventService
HealthTransitionEventFactory
SessionTransitionDetector
SessionTransitionEventService
SessionTransitionEventFactory
EventService
```

---

## 68. Contexto del Event

Un Event de Stream Health deberá poder conservar, cuando exista evidencia:

```
```

```
node
service
protocol
connection/session
role
direction
remote endpoint
previous health
current health
reason
scope
impact
observed_at
```

---

## 69. Events son hechos

Un Event registra:

```
```

```
algo ocurrió
```

No implica automáticamente:

```
```

```
el operador debe intervenir
```

Esa responsabilidad corresponde a Alarm Policy.

---

# PARTE XIX — ALARMS

## 70. Alarm infrastructure existente

No se creará un sistema paralelo:

```
```

```
StreamAlarmSystem
```

Se reutilizará la infraestructura existente.

---

## 71. Pipeline de Alarm

La relación será:

```
```

```
Health
  ↓
Transition
  ↓
Event
  ↓
Alarm Policy
  ↓
Alarm
```

---

## 72. Servicios existentes

Antes de crear equivalentes deberán reutilizarse o evolucionarse:

```
```

```
AlarmService
HealthTransitionAlarmService
SessionAlarmRuntime
```

junto con las políticas existentes relevantes.

---

## 73. Health no implica Alarm

Regla fundamental:

> Un estado DEGRADED o CRITICAL no implica necesariamente, por sí mismo, la creación de una alarma.

---

## 74. Alarm Policy

Alarm Policy podrá considerar:

```
```

```
health
role
direction
scope
impact
persistence
affected population
operational importance
```

---

## 75. Ejemplo de condición sin alarma

```
```

```
1 READER
DEGRADED
temporary/localized
```

puede generar:

```
```

```
Health Transition
Event
No Alarm
```

---

## 76. Ejemplo de condición con alarma

```
```

```
PRIMARY INGEST
CRITICAL
persistent
all service clients affected
```

puede generar:

```
```

```
Health Transition
Event
Alarm OPEN
```

---

# PARTE XX — ALARM STORM PREVENTION

## 77. Problema

Con N clientes:

```
```

```
primary ingest fails
        ↓
1000 clients affected
```

una arquitectura ingenua podría producir:

```
```

```
1000 client alarms
```

---

## 78. Comportamiento objetivo

El NOC deberá poder representar:

```
```

```
PRIMARY INGEST FAILURE
          ↓
SERVICE CRITICAL
          ↓
1000 clients affected
          ↓
1 primary operational alarm
```

manteniendo evidencia individual cuando resulte necesaria.

---

## 79. Deduplicación y correlación

Alarm Policy podrá utilizar:

```
```

```
scope
common cause
service
protocol
role
dependency
```

para evitar alarmas redundantes.

La estrategia exacta deberá implementarse incrementalmente y mediante pruebas.

---

# PARTE XXI — ALARM LIFECYCLE

## 80. Reutilización

Stream Health reutilizará el lifecycle existente.

No redefinirá innecesariamente:

```
```

```
OPENED
ACKNOWLEDGED
RESOLVED
CLOSED
```

ni las transiciones adicionales ya soportadas por el NOC.

---

## 81. Recovery

La recuperación deberá ser observable.

Ejemplo:

```
```

```
CRITICAL
   ↓
HEALTHY
```

produce conceptualmente:

```
```

```
Health Recovery Transition
          ↓
Recovery Event
          ↓
Alarm Policy
          ↓
RESOLVED when applicable
```

---

## 82. Recuperación no borra historia

La recuperación no deberá eliminar la condición previa.

History deberá permitir reconstruir:

```
```

```
HEALTHY
↓
DEGRADED
↓
CRITICAL
↓
HEALTHY
```

---

# PARTE XXII — DURABLE HISTORY

## 83. Historia existente

No se creará una base de datos independiente de Stream Health si la historia durable existente puede representar correctamente los hechos.

---

## 84. SQLite

SQLite continuará funcionando como memoria operacional durable y consultable del NOC conforme a la arquitectura existente.

---

## 85. Events y Alarms de Stream Health

Las transiciones que produzcan Events y Alarms deberán entrar en esa misma infraestructura.

---

# PARTE XXIII — EVIDENCE

## 86. Evidencia histórica

Cuando corresponda, Stream Health utilizará la infraestructura existente:

```
```

```
SQLite operational history
        ↓
daily JSONL evidence
        ↓
SHA-256
        ↓
manifest
```

---

## 87. No crear evidencia paralela

No se creará:

```
```

```
stream-health-history/
```

como autoridad independiente salvo que exista una necesidad arquitectónica futura explícitamente aprobada.

---

## 88. Current Health versus History

Ejemplo:

```
```

```
CURRENT

impact/SRT = HEALTHY
```

puede coexistir con:

```
```

```
HISTORY

18:00 HEALTHY → DEGRADED
18:03 DEGRADED → CRITICAL
18:05 CRITICAL → HEALTHY
```

Son responsabilidades diferentes.

---

# PARTE XXIV — DASHBOARD

## 89. Dashboard no se implementará primero

La secuencia será:

```
```

```
DOMAIN
↓
EVALUATION
↓
TRANSITIONS
↓
EVENTS
↓
ALARMS
↓
AGGREGATION
↓
DASHBOARD
```

---

## 90. Navegación objetivo

El NOC deberá evolucionar hacia:

```
```

```
GLOBAL STREAM HEALTH
          │
          ▼
       SERVICES
          │
          ▼
        SERVICE
          │
          ▼
       PROTOCOLS
          │
          ▼
        PROTOCOL
          │
          ▼
CLIENTS / CONNECTIONS
          │
          ▼
         DETAIL
```

---

## 91. Detail

La vista detallada deberá poder responder:

```
```

```
identity
protocol
role
remote
status
reason
metrics
duration
scope
impact
events
alarm
history
```

cuando esos datos estén disponibles.

---

# PARTE XXV — COMPATIBILITY MAP

## 92. Regla general

Se deberá preferir:

```
```

```
REUSE
```

o:

```
```

```
EVOLVE
```

antes que:

```
```

```
REPLACE
```

cuando la arquitectura existente sea compatible.

---

## 93. Mapa inicial de compatibilidad

| Componente existenteAcción contractual |                    |
| -------------------------------------- | ------------------ |
| `HealthStatus`                         | **REUSE**          |
| `HEALTHY`                              | **REUSE**          |
| `DEGRADED`                             | **REUSE**          |
| `CRITICAL`                             | **REUSE**          |
| `UNKNOWN`                              | **REUSE**          |
| `StreamingConnectionHealth`            | **EVOLVE**         |
| `StreamingPathHealth`                  | **EVOLVE**         |
| `StreamingHealth`                      | **EVOLVE**         |
| `SessionProtocol`                      | **REUSE**          |
| `SessionSnapshot`                      | **REUSE**          |
| MediaMTX session adapters              | **REUSE / EXTEND** |
| multiprotocol session observation      | **REUSE**          |
| `HealthTransitionDetector`             | **REUSE / EVOLVE** |
| `HealthTransitionEventService`         | **REUSE / EVOLVE** |
| `HealthTransitionEventFactory`         | **REUSE / EVOLVE** |
| `SessionTransitionDetector`            | **REUSE**          |
| `SessionTransitionEventService`        | **REUSE**          |
| `EventService`                         | **REUSE**          |
| `AlarmService`                         | **REUSE**          |
| `HealthTransitionAlarmService`         | **REUSE / EVOLVE** |
| `SessionAlarmRuntime`                  | **REUSE**          |
| Existing Alarm Policies                | **REUSE / EXTEND** |
| SQLite History                         | **REUSE**          |
| JSONL Evidence                         | **REUSE**          |
| SHA-256 / manifests                    | **REUSE**          |
| Terminal Dashboard                     | **EVOLVE LATER**   |

---

## 94. Nueva abstracción requiere justificación

No se creará una nueva abstracción solamente porque el contrato utilice un nuevo término conceptual.

Antes deberá demostrarse que las estructuras actuales no pueden representar correctamente la semántica requerida.

---

# PARTE XXVI — PROHIBICIONES ARQUITECTÓNICAS

## 95. Hardcoding

Queda prohibido hardcodear:

```
```

```
ejtv
enlace
impact
```

como estructura del dominio.

---

## 96. Cantidades fijas

Queda prohibido asumir:

```
```

```
3 services
1 reader per service
3 clients
```

---

## 97. SRT-only architecture

Queda prohibido diseñar el nuevo núcleo suponiendo que:

```
```

```
Streaming == SRT
```

---

## 98. Missing evidence as HEALTHY

Queda prohibido:

```
```

```
no telemetry
    ↓
HEALTHY
```

cuando la evaluación requiere esa evidencia.

---

## 99. Metric-to-alarm

Queda prohibido:

```
```

```
metric threshold
      ↓
alarm
```

sin la política semántica correspondiente.

---

## 100. Parallel Events

Queda prohibido duplicar Events exclusivamente para Stream Health.

---

## 101. Parallel Alarms

Queda prohibido duplicar Alarm lifecycle exclusivamente para Stream Health.

---

## 102. Parallel History

Queda prohibido crear una historia durable paralela sin necesidad demostrada.

---

## 103. UI authority

Queda prohibido que Dashboard determine Health.

---

## 104. Universal worst-child-wins

Queda prohibido aplicar universalmente:

```
```

```
worst child wins
```

sin considerar scope e impact.

---

## 105. Alarm storms

Queda prohibido considerar correcto un diseño que transforme una causa común de gran alcance en una cantidad indiscriminada de alarmas redundantes.

---

# PARTE XXVII — IMPLEMENTACIÓN VERTICAL

## 106. Diseñar globalmente, implementar verticalmente

El contrato contempla:

```
```

```
SRT
RTMP
RTSP
HLS
WebRTC
future protocols
```

pero no se implementarán simultáneamente.

---

## 107. Secuencia general

La evolución se divide inicialmente en:

```
```

```
BLOCK 0
Contract

BLOCK 1
SRT Health v2 — domain/evaluator

BLOCK 2
SRT temporal evaluation / hysteresis

BLOCK 3
Health transitions

BLOCK 4
Events integration

BLOCK 5
Alarm Policy integration

BLOCK 6
Service / Protocol / Client aggregation

BLOCK 7
Dashboard evolution

BLOCK 8
RTMP Health

BLOCK 9
RTSP Health

BLOCK 10
HLS Health

BLOCK 11
WebRTC Health

BLOCK 12
Full multiprotocol regression

BLOCK 13
Physical operational validation

BLOCK 14
ENG-013B closure evidence
```

Este orden podrá ajustarse si la inspección de cada bloque demuestra dependencias diferentes.

El contrato semántico no deberá alterarse silenciosamente para acomodar la implementación.

---

# PARTE XXVIII — BLOCK 0: CONTRACT

## 108. Objetivo

Formalizar este documento.

---

## 109. Cierre

BLOCK 0 sólo se considera cerrado después de:

```
```

```
document created
README updated
git diff --check
document review
commit
push
origin verification
```

---

# PARTE XXIX — BLOCK 1: SRT HEALTH V2

## 110. Objetivo

Evolucionar el evaluador SRT actual sin romper comportamiento válido.

---

## 111. Mantener RTT

RTT continuará siendo señal operacional válida conforme a las reglas existentes mientras no exista evidencia para modificar su semántica.

---

## 112. Mantener link\_capacity diagnóstica

La regresión del commit `412b17c` deberá preservarse.

---

## 113. Investigar métricas adicionales

Antes de incorporarlas a severidad deberán inspeccionarse:

```
```

```
packet loss rate
retransmission behavior
drops
traffic continuity
buffers
ACK/NAK
```

---

## 114. No inventar thresholds

No se seleccionarán thresholds solamente por intuición.

---

# PARTE XXX — BLOCK 2: TEMPORAL HEALTH

## 115. Objetivo

Evitar clasificación excesivamente sensible a muestras individuales.

---

## 116. Estado temporal

Se investigará la mínima abstracción necesaria para conservar contexto entre evaluaciones.

---

## 117. Persistence

Se probarán condiciones persistentes.

---

## 118. Hysteresis

Se probará recuperación estable.

---

## 119. Flapping

Se deberá demostrar que una anomalía breve no genera oscilaciones injustificadas.

---

# PARTE XXXI — BLOCK 3: HEALTH TRANSITIONS

## 120. Objetivo

Detectar exactamente una transición semántica por cambio real de Health.

---

## 121. Reutilización

Se inspeccionará primero `HealthTransitionDetector`.

No se implementará un detector paralelo sin demostrar necesidad.

---

# PARTE XXXII — BLOCK 4: EVENTS

## 122. Objetivo

Convertir transiciones significativas en Events existentes del NOC.

---

## 123. Contexto

Se ampliará contexto solamente cuando sea necesario y compatible.

---

## 124. No duplicación

El resultado deberá continuar siendo parte de la memoria cronológica uniforme del NOC.

---

# PARTE XXXIII — BLOCK 5: ALARM POLICIES

## 125. Objetivo

Determinar qué condiciones de Stream Health requieren atención.

---

## 126. Casos iniciales

Deberán existir tests que diferencien al menos:

```
```

```
single reader degradation
```

de:

```
```

```
primary source/service-impacting failure
```

---

## 127. Persistencia

Alarm Policy podrá exigir persistencia cuando corresponda.

---

## 128. Alarm storm protection

Se deberán probar múltiples clientes afectados por una causa común.

---

# PARTE XXXIV — BLOCK 6: AGGREGATION

## 129. Objetivo

Formalizar agregación:

```
```

```
connection
→ protocol
→ service
→ global
```

sin perder contexto.

---

## 130. Multi-client

Deberán probarse servicios con:

```
```

```
0
1
2
N
```

clientes.

---

## 131. Multi-protocol

Deberá probarse un mismo servicio con múltiples protocolos.

---

# PARTE XXXV — BLOCK 7: DASHBOARD

## 132. Objetivo

Representar el nuevo dominio sin introducir lógica operacional en UI.

---

## 133. Compatibilidad

La pantalla actual deberá evolucionar incrementalmente.

No se requiere reescribir el Dashboard completo.

---

# PARTE XXXVI — BLOCKS 8–11: PROTOCOLOS ADICIONALES

## 134. RTMP

RTMP deberá definir sus propias evidencias válidas.

No copiará automáticamente thresholds SRT.

---

## 135. RTSP

RTSP deberá definir semántica conforme a sus sesiones y telemetría disponible.

---

## 136. HLS

HLS deberá considerar su naturaleza particular.

La semántica de sesiones HLS no deberá forzarse artificialmente a ser idéntica a conexiones persistentes como SRT.

---

## 137. WebRTC

WebRTC deberá considerar, cuando exista evidencia:

```
```

```
peer connection
ICE
RTT
loss
jitter
bitrate
```

u otras señales verificadas.

---

## 138. Protocol independence

Cada protocolo deberá producir resultados compatibles con:

```
```

```
HEALTHY
DEGRADED
CRITICAL
UNKNOWN
```

sin exigir métricas idénticas.

---

# PARTE XXXVII — TEST STRATEGY

## 139. Test first

Cada nueva regla deberá comenzar mediante un test que exprese el comportamiento esperado cuando sea razonablemente posible.

---

## 140. HEALTHY

Debe existir cobertura de condiciones saludables.

---

## 141. DEGRADED

Debe existir cobertura de degradación verificable.

---

## 142. CRITICAL

Debe existir cobertura de condiciones críticas.

---

## 143. UNKNOWN

Debe existir cobertura explícita de evidencia insuficiente.

---

## 144. Recovery

Debe existir cobertura de recuperación.

---

## 145. Temporal behavior

Debe existir cobertura de:

```
```

```
persistence
hysteresis
flapping prevention
```

cuando se implemente.

---

## 146. Multi-client

Debe existir cobertura de múltiples conexiones simultáneas.

---

## 147. Multi-service

Debe demostrarse ausencia de dependencia de nombres concretos.

---

## 148. Multi-protocol

La regresión final deberá incluir múltiples protocolos.

---

# PARTE XXXVIII — REGRESSION STRATEGY

## 149. Targeted tests

Cada cambio ejecutará primero tests focalizados.

---

## 150. Related regression

Después deberán ejecutarse los tests del subsistema relacionado.

---

## 151. Full regression

Los hitos mayores deberán ejecutar la regresión completa del backend antes de cierre.

---

## 152. No regression by assumption

Un test nuevo en verde no demuestra por sí solo ausencia de regresión.

---

# PARTE XXXIX — PHYSICAL VALIDATION

## 153. Principio

Cuando un comportamiento pueda comprobarse razonablemente sobre infraestructura real:

```
```

```
AUTOMATED TESTS
       +
PHYSICAL VALIDATION
```

serán utilizados antes de declarar cerrado el bloque.

---

## 154. Validación no destructiva primero

Se preferirán observaciones y condiciones reales no destructivas.

No se interrumpirá infraestructura de producción innecesariamente.

---

## 155. Evidencia

Las pruebas físicas significativas deberán documentarse cuando agreguen evidencia arquitectónica nueva.

---

# PARTE XL — MÉTODO DE CAMBIO

## 156. Secuencia obligatoria

El método de trabajo para este objetivo será:

```
```

```
INSPECTION
    ↓
DESIGN / CONTRACT
    ↓
TEST
    ↓
SMALL CHANGE
    ↓
TARGETED REGRESSION
    ↓
RELATED REGRESSION
    ↓
PHYSICAL VALIDATION
    ↓
DOCUMENTATION
    ↓
COMMIT
    ↓
PUSH
    ↓
ORIGIN VERIFICATION
```

---

## 157. Cambios pequeños

Un commit deberá representar una unidad razonable y verificable.

---

## 158. No giant refactor

No se realizará un refactor masivo de Stream Health, Sessions, Events, Alarms, History y Dashboard en un solo cambio.

---

## 159. No avance sin evidencia

No se considerará cerrado un bloque solamente porque el código compile.

---

# PARTE XLI — CHANGE CONTROL

## 160. Cambio de semántica

Cambios futuros en:

```
```

```
Health states
aggregation
reason codes
alarm semantics
protocol evaluation
```

deberán:

```
```

```
be explicit
be tested
be documented
be traceable
```

---

## 161. Backward compatibility

Se conservará compatibilidad hacia atrás cuando sea razonablemente posible.

Cuando no lo sea, la incompatibilidad deberá documentarse explícitamente.

---

# PARTE XLII — CRITERIOS SRT V2

## 162. Healthy transport

Deberá demostrarse:

```
```

```
low RTT
+
healthy transport evidence
        ↓
HEALTHY
```

---

## 163. Missing evidence

Cuando la evidencia necesaria sea insuficiente:

```
```

```
UNKNOWN
```

---

## 164. Temporary anomaly

Una anomalía temporal no deberá producir flapping injustificado.

---

## 165. Persistent degradation

Una condición de degradación persistente deberá poder producir:

```
```

```
DEGRADED
```

---

## 166. Persistent severe degradation

Una condición severa persistente deberá poder producir:

```
```

```
CRITICAL
```

---

## 167. Recovery

La recuperación suficientemente estable deberá producir:

```
```

```
HEALTHY
```

---

## 168. Link capacity regression

Debe mantenerse:

```
```

```
estimated utilization > 100 %
+
low RTT
+
no meaningful loss
+
operational stream
        ↓
NO autonomous severity escalation
```

---

# PARTE XLIII — CRITERIOS MULTIPROTOCOLO

## 169. Dynamic services

Agregar un nuevo servicio no deberá requerir modificar el evaluador central.

---

## 170. Dynamic clients

Agregar clientes no deberá requerir modificar el modelo.

---

## 171. Dynamic protocols

Agregar un protocolo deberá seguir conceptualmente:

```
```

```
Adapter
   ↓
Normalized Evidence
   ↓
Protocol Evaluation
   ↓
Common Health Semantics
   ↓
Existing Events
   ↓
Existing Alarm Policies
```

---

## 172. Unknown protocol Health

Un protocolo observable pero todavía no evaluable completamente deberá poder permanecer:

```
```

```
UNKNOWN
```

sin desaparecer del NOC.

---

# PARTE XLIV — CRITERIOS EVENTS

## 173. Exactly meaningful transitions

Una transición significativa deberá poder generar exactamente el hecho operacional correspondiente.

---

## 174. No event flood from unchanged state

Observaciones repetidas del mismo estado no deberán producir Events equivalentes indefinidamente sin razón operacional.

---

## 175. Context

Los Events deberán transportar contexto suficiente para investigación.

---

# PARTE XLV — CRITERIOS ALARMS

## 176. Alarm policy separation

Debe demostrarse que:

```
```

```
CRITICAL Health
```

no produce necesariamente Alarm sin evaluación de política.

---

## 177. Role-aware policy

Debe poder distinguirse operacionalmente entre:

```
```

```
reader problem
```

y:

```
```

```
primary publisher/ingest problem
```

cuando exista evidencia.

---

## 178. Alarm storm resistance

Una causa común que afecte N clientes no deberá generar automáticamente N alarmas primarias equivalentes.

---

# PARTE XLVI — CRITERIOS HISTORY/EVIDENCE

## 179. Durable lifecycle

Events y Alarms derivados de Stream Health deberán sobrevivir conforme a las garantías existentes de historia durable.

---

## 180. Restart

El reinicio del runtime no deberá inventar ni destruir incorrectamente el lifecycle operacional existente.

---

## 181. Evidence

Los hechos históricos relevantes deberán poder incorporarse a las proyecciones de evidencia existentes.

---

# PARTE XLVII — CRITERIOS DASHBOARD

## 182. Current state

El operador deberá poder conocer el estado actual.

---

## 183. Localization

Deberá poder localizar progresivamente:

```
```

```
service
protocol
connection/client
```

---

## 184. Explanation

Deberá poder conocer:

```
```

```
reason
evidence
scope
impact
```

cuando existan.

---

## 185. Events and Alarms

La navegación deberá permitir relacionar Health con Events y Alarms sin convertirlos en el mismo concepto.

---

# PARTE XLVIII — TRAZABILIDAD

## 186. Precedente Node Health / Stream Health

La evidencia física existente que demuestra:

```
```

```
Node Health   = CRITICAL
Stream Health = UNKNOWN
```

constituye precedente contractual para preservar separación semántica.

---

## 187. Precedente SRT link capacity

El commit:

```
```

```
412b17c
fix(streaming): treat SRT link capacity as diagnostic
```

constituye precedente contractual.

---

## 188. Arquitectura de Events y Alarms

La infraestructura existente de:

```
```

```
transition detection
EventService
AlarmService
Alarm Policies
durable history
```

constituye autoridad de integración.

Stream Health deberá evolucionar dentro de ella.

---

# PARTE XLIX — DEFINITION OF DONE POR BLOQUE

## 189. Un bloque no está terminado cuando se escribe código

Un bloque se considerará cerrado únicamente cuando, según corresponda, exista:

```
```

```
contract/invariant identified
test created or updated
implementation completed
targeted tests PASS
related regression PASS
physical validation PASS
documentation updated
git diff clean
commit created
push completed
origin synchronized
```

---

## 190. Evidencia antes de porcentaje

No se incrementará el estado de avance de ENG-013B por expectativa.

El avance deberá corresponder a evidencia concreta.

---

# PARTE L — LÍMITE DE ENG-013B

## 191. ENG-014

Este trabajo pertenece a ENG-013B.

No se iniciará ENG-014 como consecuencia de este contrato.

ENG-014 deberá permanecer fuera de alcance hasta el cierre formal de ENG-013B.

---

# PARTE LI — RESULTADO OPERACIONAL OBJETIVO

## 192. Caso localizado

El NOC deberá poder evolucionar hacia una explicación equivalente a:

```
```

```
STREAM HEALTH: DEGRADED

Service:
    impact

Protocol:
    SRT

Connection:
    id: <connection-id>
    role: READER
    remote: <endpoint>

Health:
    HEALTHY → DEGRADED

Reason:
    sustained_packet_loss

Duration:
    47 s

Scope:
    CONNECTION

Impact:
    1 of 18 readers

Event:
    STREAM_CLIENT_HEALTH_DEGRADED

Alarm:
    none
```

---

## 193. Caso de alto impacto

Y deberá poder representar una condición equivalente a:

```
```

```
STREAM HEALTH: CRITICAL

Service:
    impact

Protocol:
    SRT

Connection:
    role: PUBLISHER

Health:
    HEALTHY → CRITICAL

Reason:
    primary_ingest_unavailable

Scope:
    SERVICE

Impact:
    primary ingest unavailable
    18 readers affected

Event:
    STREAM_SERVICE_HEALTH_CRITICAL

Alarm:
    OPEN
```

Los nombres concretos de Events y reason codes deberán definirse y validarse durante la implementación; los anteriores son ejemplos semánticos y no se consideran todavía identificadores canónicos.

---

# PARTE LII — NORTH STAR

## 194. Objetivo final

Stream Health no existe para producir un color.

Existe para transformar:

```
```

```
telemetry
```

en:

```
```

```
operational knowledge
```

El flujo completo objetivo es:

```
```

```
                         NOC
                          │
          ┌───────────────┼────────────────┐
          │               │                │
     CURRENT HEALTH      EVENTS          ALARMS
          ▲               ▲                ▲
          │               │                │
          │        state transitions       │
          │               └────────┬───────┘
          │                        │
          │                   Alarm Policy
          │                        ▲
          │                        │
          └──────────── HEALTH ENGINE
                                   ▲
                                   │
                         NORMALIZED EVIDENCE
                                   ▲
                 ┌─────────────────┼──────────────────┐
                 │                 │                  │
                SRT               RTMP              RTSP
                 │                 │                  │
                 ├─────────────────┼──────────────────┤
                 │                 │                  │
                HLS             WebRTC             FUTURE
```

Y jerárquicamente:

```
```

```
                    GLOBAL STREAM HEALTH
                             │
                ┌────────────┼────────────┐
                │            │            │
             SERVICE      SERVICE      SERVICE
                │
        ┌───────┼────────┐
        │       │        │
       SRT     HLS     WebRTC
        │
    ┌───┼───┐
    │   │   │
   C1  C2  C3 ... Cn
```

---

# PARTE LIII — REGLA FINAL

## 195. Contrato de responsabilidades

La regla arquitectónica definitiva es:

```
```

```
TELEMETRY
    ↓
provides evidence

PROTOCOL EVALUATOR
    ↓
determines Health

HEALTH TRANSITION
    ↓
represents change

EVENT
    ↓
records what happened

ALARM POLICY
    ↓
determines whether operator attention is required

ALARM
    ↓
manages operational intervention lifecycle

HISTORY / EVIDENCE
    ↓
preserves operational memory

DASHBOARD
    ↓
presents the system to the operator
```

Ninguna de estas responsabilidades deberá sustituir indebidamente a las demás.

---

# PARTE LIV — PLAN DE EJECUCIÓN

## 196. Estado de partida

Al aprobar este contrato:

```
```

```
ENG-013A                         CLOSED

ENG-013B
├── Existing NOC Core            IMPLEMENTED / EVOLVING
├── Node Health                  IMPLEMENTED
├── Sessions                     MULTIPROTOCOL FOUNDATION PRESENT
├── Events                       IMPLEMENTED
├── Alarms                       IMPLEMENTED
├── Durable History              IMPLEMENTED
├── Evidence                     IMPLEMENTED
├── Stream Health SRT            IMPLEMENTED / BASELINE
└── Stream Health Multiprotocol  TO IMPLEMENT
```

---

## 197. Ejecución controlada

La evolución se realizará:

```
```

```
CONTRACT
   ↓
SRT v2
   ↓
TEMPORAL HEALTH
   ↓
TRANSITIONS
   ↓
EVENTS
   ↓
ALARMS
   ↓
AGGREGATION
   ↓
DASHBOARD
   ↓
RTMP
   ↓
RTSP
   ↓
HLS
   ↓
WEBRTC
   ↓
MULTIPROTOCOL REGRESSION
   ↓
PHYSICAL VALIDATION
   ↓
ENG-013B CLOSURE
```

---

## 198. Principio de conservación

Durante toda la evolución deberá mantenerse:

```
```

```
working system
+
small controlled changes
+
continuous regression
```

No se sacrificará el sistema operacional actual para alcanzar la arquitectura objetivo.

---

## 199. Criterio final de éxito

ENG-013B Stream Health será considerado arquitectónicamente maduro cuando el NOC pueda determinar de manera dinámica, trazable y explicable:

```
```

```
WHAT
WHERE
WHO
WHY
WHEN
SCOPE
IMPACT
EVENT
ALARM
HISTORY
```

para servicios multimedia observados sobre múltiples protocolos y múltiples conexiones, reutilizando la arquitectura común del NOC.

---

## 200. Declaración final

**Stream Health determina estado.**

**Events registran transiciones y hechos operacionales.**

**Alarm Policies determinan cuáles condiciones requieren intervención.**

**Alarms administran el ciclo de vida de dicha intervención.**

**History/Evidence conserva la memoria operacional.**

**Dashboard presenta esa información al operador.**

**Node Health, Stream Health, Availability y Session State conservan sus propias semánticas.**

**La arquitectura deberá soportar N servicios, N protocolos y N clientes sin hardcoding.**

**La implementación será incremental, testeada, regresionada, validada físicamente cuando corresponda, documentada, versionada y trazable.**

---
