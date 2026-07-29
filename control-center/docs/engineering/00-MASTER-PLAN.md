# Engineering NOC — Master Plan

## Propósito

Transformar `control-center/` en una plataforma de observabilidad, operación,
diagnóstico y automatización para infraestructura Broadcast IP.

## Visión

```text
Broadcast Infrastructure
        ↓
Control Center
        ↓
Engineering NOC
        ↓
Enterprise NOC
```

## Alcance

El Engineering NOC integrará:

- observabilidad del sistema;
- observabilidad de red;
- observabilidad de streaming;
- inspección de sesiones;
- gestión de eventos;
- gestión de alarmas;
- diagnóstico y correlación;
- reportes e históricos;
- automatización operativa;
- capacidades futuras de AI Operations.

## Modelo de organización

- Las `MISSION-xxx` continúan representando hitos mayores del producto.
- Los módulos `ENG-xxx` representan capacidades permanentes.
- Los sprints representan incrementos verificables dentro de cada módulo.
- Las capacidades compartidas pueden enlazar una misión con uno o más módulos ENG.

## Regla principal

El Engineering NOC no reemplaza `control-center/`; es la evolución funcional de
ese componente.
