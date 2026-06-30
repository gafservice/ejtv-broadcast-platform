# Arquitectura de Seguridad

> *"La seguridad no consiste únicamente en impedir el acceso. Consiste en permitir que cada componente interactúe únicamente con aquello para lo que fue diseñado."*

---

# Resumen Ejecutivo

La seguridad constituye uno de los pilares fundamentales de **EJTV Broadcast Platform**.

Desde las primeras etapas del proyecto, la plataforma ha sido concebida bajo el principio de **seguridad por diseño** (*Security by Design*), incorporando mecanismos de protección como parte de la arquitectura y no como elementos añadidos posteriormente.

Este documento presenta el modelo conceptual de seguridad adoptado por la plataforma, describiendo las zonas de confianza, los mecanismos generales de control de acceso y los principios que orientarán la protección de los servicios durante toda la evolución del proyecto.

No se documentan configuraciones específicas ni procedimientos de instalación.

Su propósito consiste en definir la filosofía de seguridad que deberá respetar toda implementación futura.

---

# Objetivo

Definir la arquitectura de seguridad de **EJTV Broadcast Platform**, estableciendo los principios de protección, las zonas de confianza, los mecanismos generales de autenticación y las políticas que permitirán preservar la integridad, disponibilidad y confidencialidad de la plataforma.

---

# Alcance

Este documento describe la seguridad desde una perspectiva arquitectónica.

Los procedimientos específicos relacionados con firewall, SSH, VPN, certificados, autenticación o endurecimiento del sistema serán desarrollados posteriormente dentro de los documentos correspondientes.

La presente arquitectura constituye únicamente el modelo conceptual que guiará dichas implementaciones.

---

# La Seguridad como Parte de la Arquitectura

En numerosos proyectos la seguridad se incorpora únicamente cuando el sistema ya se encuentra en funcionamiento.

Como consecuencia aparecen configuraciones improvisadas, reglas inconsistentes y una creciente complejidad operacional.

En **EJTV Broadcast Platform** se adopta una estrategia diferente.

La seguridad forma parte de la arquitectura desde el inicio del proyecto.

Cada componente será diseñado considerando quién puede acceder a él, desde dónde podrá hacerlo y bajo qué condiciones se permitirá dicha interacción.

Este enfoque reduce considerablemente la superficie de ataque y facilita la administración de la plataforma conforme aumente su complejidad.

---

# Principios de Seguridad

Toda decisión relacionada con la seguridad deberá respetar los siguientes principios.

## Mínimo privilegio

Cada usuario, servicio o componente dispondrá únicamente de los permisos estrictamente necesarios para cumplir su función.

La reducción de privilegios limita el impacto potencial de errores o accesos no autorizados.

---

## Denegar por defecto

Todo acceso será considerado no autorizado hasta que exista una regla explícita que lo permita.

Este principio será aplicado tanto al firewall como a los diferentes servicios de la plataforma.

---

## Defensa en profundidad

La protección no dependerá de un único mecanismo.

La seguridad será implementada mediante múltiples capas complementarias, incluyendo segmentación de red, autenticación, firewall, registros de eventos y monitoreo.

La falla de una capa no deberá comprometer completamente el sistema.

---

## Separación de responsabilidades

Los mecanismos de administración no deberán compartir innecesariamente los mismos canales utilizados para la distribución del contenido audiovisual.

Esta separación facilita el control del acceso y reduce el riesgo de exposición accidental de servicios críticos.

---

## Trazabilidad

Toda acción relevante relacionada con la seguridad deberá poder registrarse y auditarse posteriormente.

La disponibilidad de registros confiables permitirá analizar incidentes y mejorar continuamente las políticas de protección.

---

# Zonas de Confianza

La arquitectura distingue diferentes niveles de confianza dentro de la plataforma.

Cada zona representa un conjunto de componentes con requisitos de seguridad similares.

```text
                    Internet
                        │
                        ▼
            Zona No Confiable
                        │
                        ▼
                 Firewall Perimetral
                        │
        ┌───────────────┼────────────────┐
        ▼                                ▼
Zona de Producción               Zona de Administración
        │                                │
        └───────────────┬────────────────┘
                        ▼
                  Plataforma EJTV
```

La comunicación entre zonas deberá realizarse únicamente mediante mecanismos previamente autorizados.

---

# Zona No Confiable

Internet representa la zona de menor confianza dentro de la arquitectura.

Toda conexión proveniente de esta zona será considerada potencialmente riesgosa.

Ningún servicio administrativo deberá exponerse directamente sin mecanismos adicionales de protección.

---

# Zona de Producción

La zona de producción aloja los servicios encargados de recibir y distribuir contenido audiovisual.

Su prioridad consiste en mantener la continuidad operativa del servicio.

Los accesos permitidos estarán limitados a los protocolos estrictamente necesarios para la operación de la plataforma.

---

# Zona de Administración

Esta zona concentra las herramientas utilizadas para operar la plataforma.

Aquí se ubicarán los mecanismos de acceso remoto, administración del servidor, monitoreo y mantenimiento.

El acceso a esta zona deberá restringirse a personal autorizado y, preferiblemente, realizarse mediante redes internas o túneles VPN.

---

# Control de Acceso

Todo acceso a la plataforma deberá cumplir un proceso de validación antes de llegar al servicio solicitado.

```text
Solicitud
    │
    ▼
Firewall
    │
    ▼
Autenticación
    │
    ▼
Autorización
    │
    ▼
Servicio
```

Cada etapa reduce progresivamente el riesgo asociado al acceso no autorizado.

---

# Firewall

El firewall constituye la primera línea de defensa de la plataforma.

Su responsabilidad consiste en controlar qué conexiones pueden ingresar o salir del sistema.

La política general será:

* bloquear por defecto;
* permitir únicamente servicios documentados;
* restringir accesos según origen cuando sea posible;
* registrar eventos relevantes;
* facilitar auditorías posteriores.

La configuración específica será documentada en `docs/network/firewall.md`.

---

# Acceso Administrativo

Las tareas administrativas representan uno de los activos más sensibles de la plataforma.

Por esta razón, el acceso remoto deberá cumplir criterios de seguridad más estrictos que los aplicados al tráfico audiovisual.

Se privilegiarán mecanismos seguros de administración, evitando la exposición innecesaria de interfaces de gestión hacia Internet.

El acceso administrativo deberá poder restringirse por dirección IP, autenticarse mediante credenciales robustas y registrar toda actividad relevante.

---

# SSH

El protocolo SSH será el mecanismo principal para la administración remota del servidor.

Su incorporación responde a criterios de seguridad ampliamente aceptados dentro de la industria.

Aunque la configuración específica será documentada en `docs/services/ssh.md`, desde la perspectiva arquitectónica SSH representa el canal oficial para la administración remota de la plataforma.

---

# VPN

A medida que la plataforma evolucione, el acceso remoto podrá realizarse mediante una red privada virtual.

La VPN permitirá establecer un canal cifrado entre los administradores autorizados y la infraestructura de EJTV, reduciendo significativamente la exposición de servicios administrativos.

Modelo conceptual:

```text
Administrador remoto
        │
        ▼
      VPN
        │
        ▼
Zona de Administración
        │
        ▼
Plataforma EJTV
```

La incorporación de la VPN no modifica la arquitectura.

Únicamente fortalece uno de los mecanismos utilizados para acceder a la plataforma.

---

# Autenticación

Toda interacción con servicios administrativos deberá realizarse mediante mecanismos de autenticación adecuados.

La autenticación constituye el proceso mediante el cual la plataforma verifica la identidad de un usuario o sistema antes de permitir cualquier operación.

En futuras etapas podrán incorporarse mecanismos adicionales como autenticación mediante claves, certificados digitales o autenticación multifactor.

---

# Exposición hacia Internet

Uno de los principios fundamentales de la arquitectura consiste en minimizar la exposición pública de servicios.

Únicamente aquellos componentes cuya operación lo requiera podrán aceptar conexiones provenientes de Internet.

Los servicios administrativos deberán permanecer protegidos detrás de mecanismos adicionales de control de acceso siempre que resulte posible.

Reducir la superficie de exposición constituye una de las estrategias más efectivas para disminuir riesgos de seguridad.

---

# Seguridad de los Servicios

Cada servicio incorporado a la plataforma deberá analizarse desde la perspectiva de seguridad antes de entrar en producción.

Entre otros aspectos, deberá definirse:

* quién puede acceder;
* desde qué redes;
* mediante qué protocolos;
* qué nivel de autenticación requiere;
* qué información registra;
* cómo puede auditarse.

Este análisis permitirá mantener criterios homogéneos de protección durante toda la evolución del proyecto.

---

# Observabilidad y Seguridad

La seguridad y el monitoreo constituyen disciplinas complementarias.

Los mecanismos de observabilidad permitirán detectar comportamientos anómalos, registrar eventos relevantes y facilitar la investigación de incidentes.

Los registros de autenticación, accesos, errores y eventos de firewall constituirán una fuente importante de información para comprender el estado de seguridad de la plataforma.

---

# Evolución de la Arquitectura de Seguridad

La seguridad evolucionará progresivamente junto con el crecimiento de la plataforma.

## Etapa 1

* Firewall básico.
* SSH seguro.
* Acceso administrativo restringido.
* Usuarios diferenciados.

## Etapa 2

* VPN para administración remota.
* Segmentación de red.
* Auditoría de accesos.
* Monitoreo de eventos.

## Etapa 3

* Certificados digitales.
* Autenticación reforzada.
* Alta disponibilidad.
* Automatización de políticas de seguridad.

Cada etapa incorpora nuevas capacidades sin modificar los principios arquitectónicos definidos en este documento.

---

# Relación con otros documentos

La presente arquitectura se complementa con:

* `SYSTEM_OVERVIEW.md`
* `ARCHITECTURE.md`
* `NETWORK_ARCHITECTURE.md`
* `DATA_FLOW.md`
* `docs/network/firewall.md`
* `docs/security/authentication.md`
* `docs/security/hardening.md`
* `docs/services/ssh.md`
* `docs/services/fail2ban.md`

---

# Conclusión

La arquitectura de seguridad de **EJTV Broadcast Platform** no se limita a proteger un servidor.

Su propósito consiste en establecer un modelo coherente que permita controlar el acceso, preservar la integridad de los servicios y facilitar la evolución futura de la plataforma.

La seguridad no depende exclusivamente del firewall, de un protocolo específico o de una aplicación determinada.

Depende de una arquitectura que distribuya correctamente las responsabilidades, reduzca la superficie de exposición y mantenga mecanismos consistentes de autenticación, autorización y auditoría.

A medida que la plataforma incorpore nuevos servicios y aumente su complejidad, estos principios continuarán guiando todas las decisiones relacionadas con la protección de la infraestructura.

Porque una plataforma profesional no se considera segura por la cantidad de mecanismos que incorpora.

Se considera segura cuando su arquitectura hace que la protección forme parte natural de su funcionamiento.
