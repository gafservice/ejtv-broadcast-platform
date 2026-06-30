# Arquitectura de Red

> *"La red no es solamente el camino por donde viaja la señal.
> Es la estructura que define quién puede entrar, quién puede salir y cómo se protege la plataforma."*

---

# Resumen Ejecutivo

Este documento describe la arquitectura de red propuesta para **EJTV Broadcast Platform**.

Su propósito consiste en definir cómo se conectará el servidor **ejtv-01** con las fuentes de contenido, la red local, Internet y los operadores autorizados que recibirán los flujos audiovisuales.

A diferencia de la arquitectura general de la plataforma, este documento se concentra en la organización de la conectividad, las zonas de red, los puertos, la segmentación, el firewall y las posibles ampliaciones futuras mediante VLAN, VPN o zonas DMZ.

La red será diseñada con tres objetivos principales:

* permitir la recepción y distribución de flujos audiovisuales;
* proteger el acceso a la plataforma;
* facilitar el crecimiento futuro sin rediseñar toda la infraestructura.

---

# Objetivo

Definir la arquitectura de red de **EJTV Broadcast Platform**, estableciendo la relación entre el servidor, la red local, Internet, los clientes autorizados y los mecanismos de seguridad que controlarán el acceso a los servicios.

---

# Alcance

Este documento describe la arquitectura de red desde una perspectiva conceptual y operativa.

No documenta todavía comandos específicos de configuración.

La configuración detallada de interfaces, firewall, rutas, puertos, VPN o servicios específicos será desarrollada posteriormente en los documentos correspondientes dentro de las carpetas:

* `docs/network/`
* `docs/security/`
* `docs/services/`

---

# Estado inicial de red

Durante la instalación inicial de **ejtv-01** se identificaron cuatro interfaces Ethernet físicas.

```text
ejtv-01

├── enp9s0   → Intel 82574L Gigabit
├── enp10s0  → Intel 82574L Gigabit
├── ens2f0   → Intel X540-AT2 10 GbE
└── ens2f1   → Intel X540-AT2 10 GbE
```

Durante la primera etapa del proyecto, la interfaz activa fue:

```text
enp9s0
```

con dirección IP asignada por DHCP:

```text
192.168.33.239/24
```

y puerta de enlace:

```text
192.168.33.1
```

---

# Interfaces disponibles

| Interfaz | Tipo           | Capacidad | Uso inicial propuesto                   |
| -------- | -------------- | --------- | --------------------------------------- |
| enp9s0   | Intel 82574L   | 1 GbE     | Administración inicial                  |
| enp10s0  | Intel 82574L   | 1 GbE     | Reserva / administración secundaria     |
| ens2f0   | Intel X540-AT2 | 10 GbE    | Producción / recepción de flujos        |
| ens2f1   | Intel X540-AT2 | 10 GbE    | Producción / distribución / redundancia |

Esta disponibilidad de interfaces permite separar físicamente diferentes funciones de red en etapas futuras.

---

# Modelo inicial de red

Durante la primera etapa, la plataforma utilizará una arquitectura simple.

```text
                   Internet
                       │
                       ▼
                Router / Firewall
                       │
                       ▼
                 Red local EJTV
                       │
                       ▼
              enp9s0 — ejtv-01
                       │
                       ▼
              Servicios iniciales
```

Este modelo permite instalar, actualizar y administrar el servidor mientras se desarrolla la plataforma.

---

# Modelo objetivo de red

A medida que la plataforma crezca, la red podrá separarse en zonas funcionales.

```text
                         Internet
                             │
                             ▼
                      Firewall / Router
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
      Red de gestión   Red de producción   Red de clientes
            │                │                │
            ▼                ▼                ▼
         SSH/Cockpit     Encoders/SRT IN    SRT OUT/VPN
            │                │                │
            └────────────────┼────────────────┘
                             ▼
                          ejtv-01
```

Este modelo permite separar administración, recepción de contenido y distribución hacia operadores autorizados.

---

# Zonas de red

La arquitectura considera tres zonas principales.

## 1. Red de administración

Esta red se utilizará para administrar el servidor y sus servicios.

Aquí se ubicarán accesos como:

* SSH;
* Cockpit;
* herramientas de monitoreo;
* tareas de mantenimiento.

Esta zona debe tener acceso restringido.

No debe estar expuesta directamente a Internet.

---

## 2. Red de producción

Esta red transportará los flujos audiovisuales entre los equipos de origen y la plataforma.

Aquí se ubicarán:

* encoders;
* equipos Magewell;
* fuentes SRT;
* servicios de recepción.

Esta red debe priorizar estabilidad, ancho de banda y baja pérdida de paquetes.

---

## 3. Red de clientes

Esta red permitirá entregar los flujos audiovisuales hacia operadores autorizados.

Puede implementarse mediante:

* acceso directo controlado por firewall;
* túneles VPN;
* enlaces dedicados;
* conexiones SRT autenticadas.

Esta zona debe estar protegida mediante reglas estrictas de acceso.

---

# Separación lógica inicial

En la primera versión no se implementarán VLAN obligatoriamente.

Sin embargo, la arquitectura se diseñará para permitir su incorporación posterior.

```text
Etapa 1

Red única
192.168.33.0/24

    ├── Administración
    ├── Pruebas
    └── Servicios iniciales
```

En esta etapa se prioriza la simplicidad para validar el funcionamiento de la plataforma.

---

# Separación futura mediante VLAN

Cuando la plataforma crezca, se recomienda separar el tráfico mediante VLAN.

```text
VLAN 10 — Administración
VLAN 20 — Producción audiovisual
VLAN 30 — Clientes autorizados
VLAN 40 — Monitoreo
VLAN 50 — Respaldo / almacenamiento
```

Representación conceptual:

```text
                     Switch administrable
                              │
      ┌───────────────┬────────┼────────┬───────────────┐
      ▼               ▼        ▼        ▼               ▼
  VLAN 10         VLAN 20   VLAN 30  VLAN 40        VLAN 50
 Gestión        Producción Clientes Monitoreo      Backups
```

Esta separación reduce riesgos, mejora el control del tráfico y facilita la aplicación de políticas de seguridad.

---

# Firewall

El firewall será el componente encargado de controlar qué tráfico puede ingresar o salir de la plataforma.

En una primera etapa se utilizará un modelo restrictivo.

```text
Bloquear todo por defecto
        │
        ▼
Permitir solo servicios necesarios
        │
        ▼
Registrar intentos relevantes
        │
        ▼
Revisar y ajustar reglas
```

---

# Política general de firewall

La política general será:

```text
Entrada:
    Denegar por defecto.

Salida:
    Permitir según necesidad operativa.

Excepciones:
    Solo servicios documentados.
```

Ejemplo conceptual:

| Servicio   | Puerto                | Protocolo | Exposición           |
| ---------- | --------------------- | --------- | -------------------- |
| SSH        | 22                    | TCP       | Solo administración  |
| Cockpit    | 9090                  | TCP       | Solo administración  |
| SRT        | Definido por servicio | UDP       | Clientes autorizados |
| HTTP/HTTPS | 80/443                | TCP       | Según necesidad      |
| NTP        | 123                   | UDP       | Salida               |

Los puertos definitivos se documentarán en:

```text
docs/network/ports.md
```

---

# Acceso desde Internet

El acceso desde Internet deberá tratarse como una zona no confiable.

Ningún servicio administrativo deberá exponerse directamente a Internet sin un mecanismo adicional de protección.

La exposición de servicios hacia operadores autorizados deberá realizarse mediante una de las siguientes opciones:

* reglas de firewall por dirección IP;
* autenticación propia del protocolo;
* VPN;
* certificados;
* túneles seguros;
* listas de acceso.

---

# VPN

La VPN se considera una opción recomendada para acceso administrativo remoto y para conexiones con operadores que requieran un canal seguro.

Modelo conceptual:

```text
Administrador remoto
        │
        ▼
      VPN
        │
        ▼
 Red de administración
        │
        ▼
     ejtv-01
```

La VPN permite que los servicios administrativos no estén directamente expuestos a Internet.

---

# DMZ

Una zona DMZ puede ser necesaria si la plataforma expone servicios hacia Internet de manera permanente.

En una arquitectura futura, la DMZ podría alojar componentes expuestos al exterior, mientras que la red interna conserva los servicios críticos.

```text
Internet
    │
    ▼
Firewall perimetral
    │
    ├── DMZ
    │     └── Servicios expuestos
    │
    └── Red interna
          └── Servicios administrativos
```

En la primera etapa no se implementará una DMZ obligatoria.

Sin embargo, la arquitectura se mantendrá preparada para incorporarla si la operación lo requiere.

---

# Redundancia de red

El servidor **ejtv-01** dispone de múltiples interfaces Ethernet.

Esto permite diseñar escenarios de redundancia futura.

Posibles estrategias:

* interfaz primaria y secundaria;
* separación física entre administración y producción;
* enlaces dedicados para clientes;
* bonding de interfaces;
* rutas alternativas;
* segundo servidor en etapa futura.

Modelo futuro:

```text
                 Switch A
                    │
                    ▼
                 ens2f0
                  ejtv-01
                 ens2f1
                    ▲
                    │
                 Switch B
```

La redundancia no se implementará en la primera etapa, pero será considerada en el diseño de crecimiento.

---

# Flujo de red para SRT

Durante la primera versión, el flujo principal será SRT.

```text
Encoder / Magewell
        │
        ▼
   SRT hacia ejtv-01
        │
        ▼
 Plataforma de distribución
        │
        ▼
   SRT hacia cliente autorizado
```

El servidor no realizará transcodificación.

Su función será recibir y redistribuir flujos ya codificados.

Esto reduce el consumo de CPU y simplifica la operación.

---

# Principios de la arquitectura de red

Toda decisión de red deberá respetar los siguientes principios:

* no exponer servicios innecesarios;
* separar administración y producción cuando sea posible;
* documentar cada puerto abierto;
* restringir accesos por origen cuando sea posible;
* preparar la red para VLAN futuras;
* priorizar estabilidad sobre complejidad;
* evitar configuraciones difíciles de mantener;
* preservar la capacidad de crecimiento.

---

# Etapas de evolución

## Etapa 1 — Red simple

* Una interfaz activa.
* Una red local.
* Administración local.
* Pruebas iniciales.
* Firewall básico.

## Etapa 2 — Separación funcional

* Una interfaz para administración.
* Una interfaz para producción.
* Reglas de firewall más estrictas.
* Puertos documentados.
* Acceso remoto controlado.

## Etapa 3 — Segmentación

* VLAN de administración.
* VLAN de producción.
* VLAN de clientes.
* VPN para acceso remoto.
* Monitoreo separado.

## Etapa 4 — Redundancia

* Enlaces alternativos.
* Segundo servidor.
* Failover.
* Rutas alternativas.
* Alta disponibilidad.

---

# Documentos relacionados

Este documento se complementa con:

* `docs/architecture/SYSTEM_OVERVIEW.md`
* `docs/architecture/ARCHITECTURE.md`
* `docs/architecture/DATA_FLOW.md`
* `docs/architecture/SECURITY_ARCHITECTURE.md`
* `docs/network/addressing.md`
* `docs/network/firewall.md`
* `docs/network/ports.md`
* `docs/network/routing.md`
* `docs/security/hardening.md`
* `docs/services/ssh.md`

---

# Conclusión

La arquitectura de red de **EJTV Broadcast Platform** se diseñará de forma progresiva.

Durante la primera etapa se utilizará una configuración simple que permita validar el funcionamiento general de la plataforma.

Sin embargo, cada decisión se tomará considerando la posibilidad de incorporar segmentación, VPN, redundancia y mecanismos avanzados de seguridad en etapas posteriores.

La red no será tratada como un elemento secundario.

Será uno de los componentes fundamentales que determinará la estabilidad, seguridad y capacidad de crecimiento de la plataforma.


## Entornos de operación

La arquitectura de comunicaciones de EJTV Broadcast Platform fue concebida para operar en dos entornos claramente diferenciados.

El primero corresponde al entorno de desarrollo o banco de trabajo, utilizado durante la implementación, integración y validación del servidor. En esta etapa se empleó una configuración de red dinámica basada en DHCP, facilitando las tareas de instalación, actualización y pruebas de funcionamiento.

El segundo corresponde al entorno de producción, donde el servidor será instalado de forma permanente dentro de la infraestructura de comunicaciones del sitio de operación. En este escenario se implementará una configuración de red estática, adecuada a las políticas de administración y seguridad establecidas para la plataforma.

Aunque los parámetros de direccionamiento pueden variar entre ambos entornos, la arquitectura lógica del sistema, los servicios implementados y el funcionamiento interno del servidor permanecen inalterados, garantizando la portabilidad de la plataforma entre el ambiente de laboratorio y el entorno de producción.