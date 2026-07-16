# SPRINT-003

# DESIGN

---

# Objetivo del diseño

Diseñar una solución que permitiera obtener información de los recursos
del servidor Linux sin comprometer la arquitectura limpia del
EJTV Control Center.

El diseño debía mantener la separación entre las diferentes capas del
backend y preservar el principio de inversión de dependencias.

---

# Principios de diseño

Durante este Sprint se mantuvieron los siguientes principios de
ingeniería:

- Arquitectura por capas.
- Inversión de dependencias.
- Separación de responsabilidades.
- Dominio independiente de la infraestructura.
- Bajo acoplamiento.
- Alta cohesión.
- Componentes fácilmente comprobables mediante pruebas.

---

# Arquitectura aplicada

La información del sistema sigue el siguiente flujo:

```text
                Linux
                  │
                  ▼
        LinuxSystemAdapter
                  │
                  ▼
          SystemAdapter
            (Contrato)
                  │
                  ▼
          SystemService
                  │
                  ▼
         SystemResources
                  │
                  ▼
        Endpoint REST API
                  │
                  ▼
               Cliente
```

Cada componente posee una única responsabilidad.

---

# Dominio

El dominio representa exclusivamente conceptos del negocio.

Durante este Sprint se incorporaron los siguientes modelos:

- CPUInfo
- MemoryInfo
- DiskInfo
- UptimeInfo
- SystemResources

Estos modelos no contienen llamadas al sistema operativo ni conocen la
existencia de Linux o de la biblioteca `psutil`.

---

# Contrato del adaptador

El acceso al sistema operativo permanece encapsulado mediante la
interfaz:

```text
SystemAdapter
```

La interfaz define las operaciones que el resto de la aplicación puede
utilizar sin conocer la implementación concreta.

Para este Sprint se agregaron los métodos:

- cpu_info()
- memory_info()
- disk_info()
- uptime_info()

---

# Adaptador Linux

La implementación concreta reside exclusivamente en:

```text
LinuxSystemAdapter
```

Este componente utiliza la biblioteca `psutil` para obtener información
real del sistema operativo.

Ninguna otra capa tiene acceso directo a dicha biblioteca.

---

# Servicio de aplicación

El componente:

```text
SystemService
```

coordina la obtención de la información y construye el objeto de dominio
`SystemResources`.

El servicio no realiza llamadas directas al sistema operativo.

Toda la información proviene del contrato `SystemAdapter`.

---

# API REST

La publicación de la información se realiza mediante:

```text
GET /api/v1/system/resources
```

El endpoint mantiene el formato estándar de respuestas definido para el
backend del EJTV Control Center.

---

# Beneficios del diseño

La solución adoptada ofrece las siguientes ventajas:

- independencia del dominio respecto a Linux;
- facilidad para realizar pruebas unitarias;
- reutilización del servicio con diferentes adaptadores;
- posibilidad de incorporar nuevos sistemas operativos;
- mantenimiento sencillo;
- escalabilidad para futuras capacidades.

---

# Escalabilidad

La arquitectura permite incorporar nuevas capacidades reutilizando el
mismo patrón.

Por ejemplo:

- monitoreo de procesos;
- interfaces de red;
- GPU;
- temperatura;
- servicios multimedia;
- MediaMTX;
- FFmpeg;
- Docker.

Cada nueva capacidad podrá implementarse mediante el mismo flujo:

```text
Sistema

↓

Adaptador

↓

Servicio

↓

Dominio

↓

API

↓

Frontend
```

---

# Conclusión

El diseño implementado durante el Sprint-003 mantiene la arquitectura
definida para el EJTV Control Center y establece la base técnica para el
desarrollo del futuro Dashboard de monitoreo del servidor.

---