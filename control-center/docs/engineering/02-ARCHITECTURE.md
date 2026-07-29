# Engineering NOC — Arquitectura

## Relación con el repositorio

```text
ejtv-broadcast-platform/
├── docs/                         plataforma Broadcast
├── control-center/
│   ├── backend/                  aplicación y API
│   ├── frontend/                 interfaz web
│   ├── tests/                    pruebas
│   └── docs/
│       └── engineering/          documentación rectora del Engineering NOC
├── scripts/                      operación de plataforma
└── tests/                        pruebas integrales de plataforma
```

## Flujo funcional

```text
Linux / MediaMTX / FFmpeg / Network
                ↓
Adapters
                ↓
Domain Models and Snapshots
                ↓
Application Services
                ↓
API / Dashboard View Models
                ↓
Terminal Dashboard / Web Frontend
                ↓
Events / Alarms / Diagnostics / Automation
```

## Reglas arquitectónicas

- El dominio no depende de Rich, FastAPI, Linux ni MediaMTX.
- Los adaptadores traducen fuentes externas a modelos de dominio.
- Los servicios coordinan casos de uso.
- La presentación no contiene lógica de infraestructura.
- Toda acción automática debe ser auditable.
