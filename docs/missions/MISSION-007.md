# MISSION-007
# Instalación y validación de Cockpit

## Objetivo

Instalar Cockpit como plataforma de administración web del servidor EJTV Broadcast Platform, verificando su correcta integración con Ubuntu Server 24.04.4 LTS y documentando el procedimiento completo de instalación, validación y acceso.

---

## Fecha

2026-06-26

---

## Estado inicial

Durante el diagnóstico previo se verificó que el sistema no disponía de Cockpit.

### Ubuntu

Ubuntu 24.04.4 LTS

### Kernel

6.17.0-35-generic

### Estado inicial

- Cockpit no instalado.
- No existía cockpit.service.
- El puerto TCP 9090 no se encontraba en escucha.
- Firewall UFW aún no configurado.
- Repositorio oficial disponible.

---

## Instalación

Se actualizó la información de paquetes.

```bash
sudo apt update