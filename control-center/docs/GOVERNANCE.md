# Project Governance

**Proyecto:**
EJTV Broadcast Platform

**Subproyecto:**
EJTV Control Center

**Documento:**
Project Governance

**Versión:**
1.0

**Estado:**
Vigente

**Autor:**
Gerardo Araya Fallas

---

# 1. Introducción

El presente documento describe el modelo de gobierno utilizado durante el desarrollo del proyecto EJTV Broadcast Platform y del EJTV Control Center.

Su propósito consiste en establecer la forma en que se organizan los documentos, las decisiones técnicas, la evolución del software y la gestión del conocimiento.

Este documento constituye el punto de partida para comprender el funcionamiento del proyecto.

Antes de desarrollar nuevas capacidades, todo integrante del proyecto deberá conocer la estructura aquí definida.

---

# 2. Objetivo

El modelo de gobierno busca garantizar que el crecimiento del proyecto sea ordenado, trazable y sostenible.

Para ello se establecen responsabilidades claras para cada tipo de documento y se define cómo interactúan entre sí.

El objetivo no consiste únicamente en desarrollar software.

El objetivo consiste en construir una plataforma cuya evolución pueda comprenderse completamente.

---

# 3. Principios de Gobierno

El proyecto se rige por los siguientes principios.

- Toda decisión debe quedar documentada.
- Toda capacidad debe ser verificable.
- Todo cambio debe ser trazable.
- Toda misión debe dejar conocimiento.
- La documentación evoluciona junto con el código.
- La arquitectura tiene prioridad sobre la implementación.

---

# 4. Estructura General del Proyecto

La organización documental del proyecto se divide en varios niveles.

```text
Proyecto

│

├── README.md

├── ROADMAP.md

├── CHANGELOG.md

├── docs/

├── backend/

├── frontend/

├── config/

└── logs/
```

Cada uno de estos componentes posee una responsabilidad específica.

---

# 5. Documentos Estratégicos

Los documentos estratégicos describen el estado general del proyecto.

## README.md

Presenta el proyecto.

Describe su propósito.

Constituye la puerta de entrada para nuevos integrantes.

---

## ROADMAP.md

Describe la planificación del proyecto.

Indica:

- capacidades implementadas;
- capacidades futuras;
- prioridades de desarrollo.

El ROADMAP responde la pregunta:

**¿Hacia dónde va el proyecto?**

---

## CHANGELOG.md

Registra la evolución funcional del sistema.

Resume los cambios realizados en cada misión.

El CHANGELOG responde la pregunta:

**¿Qué ha cambiado?**

---

# 6. Manual de Ingeniería

El directorio:

```text
docs/standards/
```

contiene el Manual de Ingeniería del proyecto.

Actualmente está compuesto por los siguientes estándares.

```text
EDS-001
Engineering Documentation Standard

EDS-002
Engineering Standard

EDS-003
Coding Standard

EDS-004
Git Workflow Standard

EDS-005
Testing Standard

EDS-006
Architecture Standard

EDS-007
Technical Communication Standard
```

Estos documentos definen la metodología oficial del proyecto.

---

# 7. Misiones

Cada misión representa una unidad completa de ingeniería.

Su documentación se encuentra en:

```text
docs/missions/
```

Cada misión incluye:

- problema;
- objetivo;
- diseño;
- implementación;
- pruebas;
- evidencias;
- baseline;
- lecciones aprendidas.

Las misiones documentan la evolución técnica del proyecto.

---

# 8. Architecture Decision Records (ADR)

Las decisiones arquitectónicas permanentes se documentan mediante ADR.

Ubicación:

```text
docs/ADR/
```

Cada ADR responde:

- qué decisión fue tomada;
- por qué fue tomada;
- cuáles alternativas fueron consideradas;
- cuál impacto tendrá.

Las ADR preservan las decisiones de arquitectura.

---

# 9. Backend

El backend implementa las capacidades de la plataforma.

Su estructura sigue la arquitectura oficial definida en el estándar EDS-006.

Las reglas de ingeniería aplicables al backend se encuentran en el Manual de Ingeniería.

---

# 10. Frontend

El frontend constituye la interfaz de administración del sistema.

Su desarrollo deberá respetar los mismos principios de arquitectura, documentación y pruebas establecidos para el backend.

---

# 11. Configuración

El directorio:

```text
config/
```

contiene la configuración oficial del proyecto.

Toda modificación deberá quedar documentada.

---

# 12. Evidencias

Las evidencias técnicas forman parte del conocimiento del proyecto.

Incluyen:

- resultados de pruebas;
- capturas;
- respuestas HTTP;
- diagramas;
- archivos JSON;
- registros de ejecución.

Las evidencias respaldan las conclusiones documentadas.

---

# 13. Baselines

Cada misión genera un Baseline.

El Baseline representa una fotografía técnica del estado alcanzado al finalizar una capacidad.

Permite reconstruir históricamente la evolución del proyecto.

---

# 14. Relación entre los Documentos

La siguiente figura resume la relación existente entre los principales documentos del proyecto.

```text
                    README
                       │
                       ▼
                 GOVERNANCE
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     ROADMAP      CHANGELOG     Standards
                                        │
                                        ▼
                              Manual de Ingeniería
                                        │
                                        ▼
                                   Misiones
                                        │
                                        ▼
                                     Código
                                        │
                                        ▼
                                     Pruebas
                                        │
                                        ▼
                                   Evidencias
                                        │
                                        ▼
                                    Baseline
```

Cada documento cumple una función específica y complementa a los demás.

---

# 15. Flujo Oficial del Proyecto

El ciclo de vida de una nueva capacidad es el siguiente.

```text
ROADMAP

↓

Misión

↓

Diseño

↓

Implementación

↓

Pruebas

↓

Documentación

↓

Evidencias

↓

Baseline

↓

CHANGELOG

↓

Commit

↓

Push
```

Este flujo garantiza la trazabilidad completa del desarrollo.

---

# 16. Gestión del Conocimiento

El conocimiento generado durante el proyecto constituye un activo permanente.

Toda experiencia relevante deberá incorporarse a la documentación correspondiente.

El objetivo consiste en evitar la pérdida de información técnica.

---

# 17. Incorporación de Nuevas Capacidades

Toda nueva capacidad deberá cumplir el siguiente proceso.

- Planificación en el ROADMAP.
- Desarrollo mediante una misión.
- Validación mediante pruebas.
- Actualización documental.
- Generación del Baseline.
- Registro en el CHANGELOG.
- Integración al proyecto.

No se incorporarán capacidades fuera de este proceso.

---

# 18. Cultura del Proyecto

El proyecto EJTV adopta una cultura basada en el aprendizaje continuo.

Cada Sprint debe dejar:

- una nueva capacidad;
- una mejora arquitectónica;
- conocimiento documentado.

El crecimiento del proyecto debe ser incremental y ordenado.

---

# 19. Frases que Definen el Gobierno del Proyecto

> Donde hay orden, está Dios.

> La arquitectura gobierna al código.

> El conocimiento tiene el mismo valor que el software.

> Toda decisión deja evidencia.

> Toda misión deja una capacidad.

> Todo Sprint deja un legado.

---

# 20. Conclusión

El presente documento constituye la referencia principal para comprender cómo se organiza el proyecto EJTV Broadcast Platform.

Su finalidad consiste en proporcionar una visión integral del funcionamiento del proyecto y de la relación existente entre sus componentes técnicos y documentales.

Todo nuevo integrante deberá conocer este documento antes de participar en el desarrollo del sistema.
