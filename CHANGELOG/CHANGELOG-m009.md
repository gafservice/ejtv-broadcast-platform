# CHANGELOG

Todos los cambios relevantes realizados sobre la plataforma **EJTV Broadcast Platform** se registran en este documento siguiendo un criterio cronológico.

---

# 2026-06-29 — MISSION-009

## Tipo

Implementación de servicio base.

---

## Resumen

Se implementó y validó el servicio oficial de sincronización horaria de la plataforma **EJTV Broadcast Platform**, estableciendo una referencia temporal única para el servidor y para los servicios que serán incorporados durante las siguientes etapas del proyecto.

La sincronización precisa del reloj constituye un requisito fundamental para garantizar la correcta correlación de eventos, registros del sistema, servicios multimedia y procesos de monitoreo.

---

## Implementación

Se adoptó **systemd-timesyncd** como servicio oficial de sincronización horaria del servidor.

La implementación se realizó utilizando la solución nativa de Ubuntu Server, manteniendo la arquitectura del sistema lo más simple posible y evitando la incorporación de componentes adicionales innecesarios.

---

## Infraestructura

Se verificó el correcto funcionamiento de:

* Ubuntu Server 24.04.4 LTS.
* systemd.
* systemd-timesyncd.
* Configuración regional y zona horaria del servidor.
* Servidores oficiales NTP de Ubuntu.

---

## Validación técnica

Se verificó satisfactoriamente:

* sincronización correcta del reloj del sistema;
* estado operativo del servicio `systemd-timesyncd`;
* integración con `systemd`;
* utilización de los servidores oficiales `ntp.ubuntu.com`;
* correcta configuración de la zona horaria;
* estabilidad del servicio después del reinicio del sistema.

---

## Decisiones técnicas

Durante esta misión se evaluó la utilización de soluciones alternativas para sincronización horaria, incluyendo **Chrony**.

Después del análisis correspondiente se decidió mantener **systemd-timesyncd** como solución oficial de la plataforma, al cumplir plenamente los requerimientos técnicos del proyecto y ofrecer una integración nativa con Ubuntu Server.

---

## Documentación incorporada

Se incorporó la documentación correspondiente a la misión:

* `docs/services/ntp.md`
* actualización de `docs/network/ports.md`
* actualización de la línea base del sistema.

---

## Compatibilidad

La implementación del servicio de sincronización horaria mantiene compatibilidad completa con los componentes existentes y proporciona una referencia temporal estable para las siguientes fases del proyecto, particularmente para los servicios multimedia y los mecanismos de registro de eventos.

---

## Incidentes

No se registraron incidentes durante la implementación ni durante las pruebas funcionales.

---

## Estado de la misión

**MISSION-009 finalizada satisfactoriamente.**

La plataforma incorpora un servicio oficial de sincronización horaria completamente validado, proporcionando una base temporal consistente para la operación de todos los componentes que integran la **EJTV Broadcast Platform**.
