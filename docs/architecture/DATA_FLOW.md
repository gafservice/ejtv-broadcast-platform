# Flujo de Datos

> *"Comprender una plataforma no consiste únicamente en conocer sus componentes.
> Consiste en comprender cómo circula la información entre ellos."*

---

# Resumen Ejecutivo

Este documento describe el flujo de información dentro de **EJTV Broadcast Platform**.

Mientras `SYSTEM_OVERVIEW.md` explica qué es la plataforma y `ARCHITECTURE.md` define cómo está organizada, el presente documento se concentra en responder una pregunta específica:

**¿Cómo circulan los datos dentro de la plataforma?**

Para ello se identifican los principales tipos de flujo que existirán dentro del sistema:

* flujo audiovisual;
* flujo de administración;
* flujo de monitoreo;
* flujo de seguridad;
* flujo de configuración;
* flujo de almacenamiento.

Cada tipo de flujo posee una función diferente dentro de la plataforma y será representado mediante una convención gráfica propia, basada en colores y estilos de línea.

Esta separación facilita la comprensión del sistema, evita mezclar responsabilidades y permite analizar la plataforma desde diferentes perspectivas.

---

# Objetivo

Definir los principales flujos de información de **EJTV Broadcast Platform**, estableciendo cómo se transportan los contenidos audiovisuales, cómo se administra el sistema, cómo se monitorea su estado y cómo se protegen los accesos.

---

# Alcance

Este documento describe el flujo de datos desde una perspectiva arquitectónica.

No documenta comandos de configuración, reglas específicas de firewall, parámetros de MediaMTX ni procedimientos de instalación.

Los detalles de implementación serán desarrollados en documentos específicos dentro de:

* `docs/services/`
* `docs/network/`
* `docs/security/`
* `docs/operation/`

El propósito de este documento es definir cómo debe entenderse el movimiento de información dentro de la plataforma.

---

# Convención gráfica de flujos

Para mantener una documentación didáctica y visualmente consistente, todos los diagramas de **EJTV Broadcast Platform** utilizarán una convención de colores asociada a la función de cada flujo.

| Tipo de flujo                 | Color   | Código HEX | Significado                                   |
| ----------------------------- | ------- | ---------- | --------------------------------------------- |
| Video / contenido audiovisual | Azul    | `#1976D2`  | Transporte de señales audiovisuales           |
| Administración / control      | Verde   | `#2E7D32`  | Acceso administrativo y operación             |
| Monitoreo / observabilidad    | Naranja | `#F57C00`  | Métricas, logs y estado del sistema           |
| Seguridad / acceso            | Rojo    | `#C62828`  | Control de acceso, firewall y autenticación   |
| Infraestructura física        | Gris    | `#616161`  | Equipos, enlaces físicos y red base           |
| Configuración / políticas     | Morado  | `#7B1FA2`  | Archivos de configuración y reglas operativas |

Esta convención permitirá que los diagramas sean más fáciles de interpretar.

El lector podrá identificar rápidamente si una flecha representa video, administración, monitoreo, seguridad o configuración sin necesidad de leer todo el texto asociado.

---

# Tipos principales de flujo

La plataforma manejará varios tipos de información.

Aunque todos viajan sobre infraestructura de red, no todos representan lo mismo.

Por esta razón es importante distinguirlos desde el inicio.

```text
                EJTV Broadcast Platform

        ┌──────────────────────────────────────┐
        │                                      │
        │  🔵 Flujo audiovisual                │
        │  🟢 Flujo de administración          │
        │  🟠 Flujo de monitoreo               │
        │  🔴 Flujo de seguridad               │
        │  🟣 Flujo de configuración           │
        │  ⚪ Infraestructura física            │
        │                                      │
        └──────────────────────────────────────┘
```

Cada flujo cumple una responsabilidad distinta.

Mezclarlos conceptualmente dificultaría la comprensión de la plataforma.

Separarlos permite analizar el sistema de forma más clara y facilita su mantenimiento futuro.

---

# Flujo audiovisual

El flujo audiovisual representa el recorrido principal del contenido dentro de la plataforma.

Este flujo inicia en una fuente externa, como un encoder, un equipo Magewell u otro dispositivo capaz de entregar una señal previamente codificada.

La plataforma recibe ese contenido, lo administra y lo distribuye hacia clientes autorizados.

```text
🔵 Flujo audiovisual

Fuente de contenido
        │
        ▼
Recepción del flujo
        │
        ▼
Administración de flujos
        │
        ▼
Distribución multimedia
        │
        ▼
Cliente autorizado
```

Durante la primera etapa del proyecto, este flujo estará orientado principalmente a la distribución mediante SRT.

Sin embargo, la arquitectura no queda limitada a este protocolo.

En el futuro podrán incorporarse otros mecanismos de transporte sin modificar la lógica general del flujo audiovisual.

---

# Características del flujo audiovisual

El flujo audiovisual posee las siguientes características:

* transporta contenido ya codificado;
* requiere estabilidad y baja pérdida de paquetes;
* puede utilizar protocolos especializados;
* debe llegar únicamente a clientes autorizados;
* no debe mezclarse con tareas administrativas;
* debe poder monitorearse sin interferir con su transporte.

Una decisión importante del proyecto consiste en que el servidor no realizará procesos de codificación ni transcodificación durante la primera etapa.

Esta decisión reduce el consumo de CPU, simplifica la operación y permite concentrar la plataforma en su responsabilidad principal: administrar y distribuir contenido.

---

# Flujo de administración

El flujo de administración representa las acciones utilizadas para operar, configurar y mantener la plataforma.

Incluye conexiones realizadas por administradores, acceso remoto, revisión de servicios, edición de archivos de configuración y tareas de mantenimiento.

```text
🟢 Flujo de administración

Administrador
      │
      ▼
Acceso seguro
      │
      ▼
Herramientas administrativas
      │
      ▼
Servicios del sistema
      │
      ▼
Plataforma EJTV
```

Este flujo no transporta contenido audiovisual.

Su función consiste en permitir que el personal autorizado pueda administrar la plataforma de manera segura y controlada.

---

# Características del flujo de administración

El flujo de administración debe cumplir las siguientes condiciones:

* debe estar restringido a usuarios autorizados;
* preferiblemente debe operar sobre redes internas o VPN;
* no debe exponerse libremente a Internet;
* debe utilizar mecanismos seguros de autenticación;
* debe quedar documentado;
* debe poder auditarse.

Ejemplos de tecnologías asociadas a este flujo incluyen SSH, Cockpit y herramientas de administración remota.

La configuración específica de estos servicios será documentada en sus respectivos archivos dentro de `docs/services/`.

---

# Flujo de monitoreo

El flujo de monitoreo permite observar el estado de la plataforma.

No modifica el contenido audiovisual ni administra directamente los servicios.

Su función consiste en recopilar información sobre el comportamiento del sistema.

```text
🟠 Flujo de monitoreo

Servicios
   │
   ▼
Logs y métricas
   │
   ▼
Sistema de monitoreo
   │
   ▼
Alertas / paneles
   │
   ▼
Operador técnico
```

Este flujo es fundamental para detectar problemas, analizar rendimiento y realizar mantenimiento preventivo.

Una plataforma que no puede observarse resulta difícil de mantener.

---

# Información asociada al monitoreo

El monitoreo puede incluir:

* estado de servicios;
* consumo de CPU;
* consumo de memoria;
* uso de disco;
* disponibilidad de red;
* errores de transmisión;
* conexiones activas;
* eventos de seguridad;
* disponibilidad de flujos;
* registros del sistema.

Estos datos permiten comprender cómo se comporta la plataforma durante su operación normal y facilitan la detección temprana de fallas.

---

# Flujo de seguridad

El flujo de seguridad representa los mecanismos que controlan el acceso hacia la plataforma.

Incluye autenticación, autorización, firewall, reglas de acceso, certificados, VPN y registros de eventos de seguridad.

```text
🔴 Flujo de seguridad

Origen externo
      │
      ▼
Firewall / control de acceso
      │
      ▼
Autenticación
      │
      ▼
Autorización
      │
      ▼
Servicio permitido
```

Este flujo existe para garantizar que únicamente usuarios, clientes o sistemas autorizados puedan acceder a los recursos de la plataforma.

---

# Características del flujo de seguridad

El flujo de seguridad debe cumplir los siguientes principios:

* bloquear por defecto;
* permitir únicamente servicios documentados;
* restringir accesos por origen cuando sea posible;
* separar administración de distribución;
* registrar intentos relevantes;
* utilizar autenticación robusta;
* evitar exposición innecesaria de servicios.

La seguridad no se considera un componente agregado posteriormente.

Forma parte del diseño desde las primeras etapas del proyecto.

---

# Flujo de configuración

El flujo de configuración representa la forma en que las decisiones operativas se convierten en comportamiento del sistema.

Incluye archivos de configuración, políticas de servicio, reglas de firewall, listas de acceso y parámetros de operación.

```text
🟣 Flujo de configuración

Decisión técnica
        │
        ▼
Archivo de configuración
        │
        ▼
Servicio
        │
        ▼
Comportamiento operativo
        │
        ▼
Validación
```

Este flujo conecta la ingeniería con la operación.

Una configuración no debe aplicarse sin comprender qué modifica, por qué se realiza y cómo se valida.

---

# Características del flujo de configuración

Toda configuración deberá cumplir estas condiciones:

* tener un propósito claro;
* estar documentada;
* poder validarse;
* poder revertirse;
* estar asociada a una decisión técnica;
* evitar cambios no trazables.

Este principio será especialmente importante conforme la plataforma incorpore nuevos servicios.

---

# Flujo de almacenamiento

El flujo de almacenamiento representa el movimiento de información hacia discos, respaldos, registros o archivos persistentes.

Puede incluir logs, configuraciones, grabaciones, respaldos o reportes generados por la plataforma.

```text
⚪ / 🟠 Flujo de almacenamiento

Servicio
   │
   ▼
Datos generados
   │
   ▼
Sistema de archivos
   │
   ▼
Respaldo / archivo
   │
   ▼
Recuperación futura
```

Este flujo se relaciona tanto con la infraestructura física como con el monitoreo y la operación.

Por esta razón se documentará con mayor detalle dentro de la arquitectura de almacenamiento y los procedimientos de respaldo.

---

# Flujo completo de operación

Desde una perspectiva integrada, la plataforma puede entenderse como la interacción de varios flujos simultáneos.

```text
                         🔵 Contenido audiovisual
Fuente / Encoder ───────────────────────────────────► Cliente autorizado
        │                                                     ▲
        │                                                     │
        ▼                                                     │
  Recepción del flujo                                  Distribución

                         🟢 Administración
Administrador ─────────► Herramientas administrativas ───────► Servicios

                         🟠 Monitoreo
Servicios ─────────────► Logs / Métricas ────────────────────► Operador

                         🔴 Seguridad
Cliente / Admin ───────► Firewall / Autenticación ───────────► Servicio

                         🟣 Configuración
Decisión técnica ──────► Configuración ──────────────────────► Comportamiento
```

Este diagrama muestra que la plataforma no posee un único flujo.

El contenido audiovisual es el flujo principal, pero depende de otros flujos complementarios para operar de manera segura, administrable y mantenible.

---

# Relación entre los flujos

Los diferentes flujos no deben entenderse como sistemas aislados.

Cada uno cumple una función específica, pero todos interactúan dentro de la plataforma.

Por ejemplo:

* el flujo audiovisual transporta contenido;
* el flujo de seguridad decide quién puede acceder;
* el flujo de monitoreo informa si el servicio funciona;
* el flujo de administración permite intervenir el sistema;
* el flujo de configuración modifica el comportamiento operativo;
* el flujo de almacenamiento preserva información útil para diagnóstico o recuperación.

La estabilidad de la plataforma depende de que cada flujo cumpla su función sin invadir la responsabilidad de los demás.

---

# Separación de tráfico

Cuando la plataforma crezca, será recomendable separar ciertos flujos mediante redes, interfaces o VLAN diferentes.

Por ejemplo:

```text
VLAN 10 — Administración      🟢
VLAN 20 — Producción video    🔵
VLAN 30 — Clientes            🔵 / 🔴
VLAN 40 — Monitoreo           🟠
VLAN 50 — Respaldo            ⚪
```

Esta separación permitirá aplicar políticas de seguridad más claras, reducir interferencias y facilitar el diagnóstico de problemas.

Durante la primera etapa del proyecto esta separación podrá ser lógica y documental.

En etapas posteriores podrá implementarse mediante configuración real de red.

---

# Prioridad de los flujos

No todos los flujos tienen la misma prioridad operativa.

| Flujo          | Prioridad    | Justificación                                      |
| -------------- | ------------ | -------------------------------------------------- |
| Audiovisual    | Alta         | Representa el servicio principal de la plataforma. |
| Seguridad      | Alta         | Protege el acceso y evita uso no autorizado.       |
| Administración | Media / Alta | Permite operar y corregir el sistema.              |
| Monitoreo      | Media        | Permite detectar fallas y analizar comportamiento. |
| Configuración  | Media        | Modifica el comportamiento del sistema.            |
| Almacenamiento | Variable     | Depende del tipo de dato almacenado.               |

Esta clasificación permite tomar mejores decisiones cuando existan restricciones de red, CPU, almacenamiento o seguridad.

---

# Principios del flujo de datos

Toda implementación futura deberá respetar los siguientes principios:

* el flujo audiovisual no debe mezclarse innecesariamente con administración;
* los accesos administrativos deben estar protegidos;
* todo flujo expuesto debe estar documentado;
* el monitoreo no debe interferir con la distribución;
* los cambios de configuración deben ser trazables;
* los logs deben facilitar diagnóstico y auditoría;
* los datos críticos deben poder respaldarse;
* la seguridad debe acompañar todos los flujos.

---

# Documentos relacionados

Este documento se complementa con:

* `docs/architecture/SYSTEM_OVERVIEW.md`
* `docs/architecture/ARCHITECTURE.md`
* `docs/architecture/NETWORK_ARCHITECTURE.md`
* `docs/architecture/SECURITY_ARCHITECTURE.md`
* `docs/network/ports.md`
* `docs/services/mediamtx.md`
* `docs/services/logging.md`
* `docs/security/authentication.md`
* `docs/operation/troubleshooting.md`

---

# Conclusión

El flujo de datos de **EJTV Broadcast Platform** no se limita al transporte de contenido audiovisual.

La plataforma también debe administrar accesos, registrar eventos, monitorear servicios, aplicar configuraciones y preservar información útil para su operación.

Comprender estos flujos desde las primeras etapas del proyecto permite diseñar una arquitectura más clara, segura y mantenible.

La separación entre flujo audiovisual, administración, monitoreo, seguridad, configuración y almacenamiento será uno de los principios fundamentales para mantener la plataforma ordenada conforme continúe creciendo.

Una plataforma que comprende sus flujos puede operar con mayor estabilidad, diagnosticar problemas con mayor rapidez y evolucionar sin perder control sobre su propia complejidad.
