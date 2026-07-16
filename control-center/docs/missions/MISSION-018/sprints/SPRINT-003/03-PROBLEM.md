# SPRINT-003

# PROBLEM

---

# Situación inicial

Al finalizar el Sprint-002, el EJTV Control Center era capaz de
identificar el servidor administrado mediante la obtención de:

- hostname;
- sistema operativo;
- versión del kernel.

Esta información permitía conocer la identidad del servidor, pero no
proporcionaba ninguna indicación sobre su estado operativo.

---

# Problema identificado

El backend carecía de mecanismos para consultar los recursos actuales
del sistema.

No era posible conocer, mediante la API, información como:

- utilización del procesador;
- memoria disponible;
- utilización del almacenamiento;
- tiempo de actividad del servidor.

Como consecuencia, el Control Center no disponía de información
suficiente para evaluar el estado general del servidor.

---

# Impacto sobre la plataforma

La ausencia de esta capacidad impedía construir funcionalidades propias
de un sistema de monitoreo, tales como:

- paneles de estado;
- indicadores de salud del servidor;
- alertas por consumo elevado;
- supervisión de recursos;
- diagnóstico operativo.

El backend únicamente podía responder **quién era el servidor**, pero no
**cómo estaba funcionando**.

---

# Restricciones de diseño

La incorporación de esta capacidad debía respetar la arquitectura del
proyecto.

En particular, era indispensable evitar que:

- el dominio dependiera de Linux;
- los servicios accedieran directamente a `psutil`;
- la API conociera detalles del sistema operativo.

Todo acceso al sistema debía permanecer encapsulado dentro del adaptador
Linux mediante el contrato `SystemAdapter`.

---

# Riesgos identificados

Durante el diseño se identificaron los siguientes riesgos:

- acoplamiento entre la lógica de negocio y el sistema operativo;
- incorporación de dependencias Linux en capas superiores;
- pérdida de la capacidad de realizar pruebas unitarias;
- dificultad para incorporar adaptadores futuros para otros sistemas.

La solución debía mantener el principio de inversión de dependencias y
la separación estricta entre capas.

---

# Necesidad del Sprint

Se requería incorporar una capacidad permanente que permitiera obtener,
consolidar y publicar información real sobre los recursos del servidor,
sin comprometer la arquitectura existente.

Esta capacidad constituye el primer paso hacia la construcción de un
Dashboard operativo capaz de supervisar continuamente el estado del
servidor EJTV.

---

# Resultado esperado

Al finalizar el Sprint, el backend debía ser capaz de exponer mediante
una API REST información actualizada del estado del servidor,
manteniendo la independencia entre el dominio, la lógica de aplicación y
la infraestructura del sistema operativo.

---