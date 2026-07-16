# Testing Standard (EDS-005)

**Código del estándar:**
EDS-005

**Nombre:**
Testing Standard

**Proyecto:**
EJTV Broadcast Platform

**Subproyecto:**
EJTV Control Center

**Versión:**
1.0

**Estado:**
Vigente

**Autor:**
Gerardo Araya Fallas

---

# 1. Introducción

El presente documento establece el estándar oficial para el diseño, ejecución y documentación de las pruebas realizadas durante el desarrollo del proyecto EJTV Broadcast Platform y del EJTV Control Center.

Su propósito consiste en garantizar que cada nueva capacidad incorporada al sistema sea validada de manera objetiva, reproducible y documentada.

Las pruebas constituyen una evidencia técnica del funcionamiento del sistema.

No representan únicamente una herramienta para detectar errores.

Representan un mecanismo formal para validar que la arquitectura, la implementación y el comportamiento del sistema cumplen los objetivos definidos durante el diseño.

---

# 2. Objetivos

Este estándar busca:

- validar cada nueva capacidad;
- detectar errores tempranamente;
- proteger funcionalidades existentes;
- facilitar futuras modificaciones;
- garantizar la estabilidad del sistema;
- documentar evidencias verificables.

---

# 3. Filosofía

Toda capacidad desarrollada debe poder demostrarse.

La demostración se realiza mediante pruebas.

Si una capacidad no puede probarse, tampoco puede considerarse terminada.

Las pruebas forman parte del desarrollo.

No constituyen una actividad posterior.

---

# 4. Principios Fundamentales

Toda estrategia de pruebas deberá cumplir los siguientes principios.

## 4.1 Toda capacidad debe probarse

Cada nueva funcionalidad deberá disponer de pruebas apropiadas.

No existen excepciones.

---

## 4.2 Las pruebas deben ser reproducibles

Otra persona debe obtener exactamente el mismo resultado siguiendo el mismo procedimiento.

---

## 4.3 Las pruebas deben ser independientes

Una prueba nunca deberá depender del resultado producido por otra.

Cada prueba debe poder ejecutarse individualmente.

---

## 4.4 Las pruebas constituyen documentación

Las pruebas describen el comportamiento esperado del sistema.

Por esta razón forman parte permanente del proyecto.

---

# 5. Pirámide de Pruebas

El proyecto utiliza una estrategia de validación basada en varios niveles.

```
                Smoke Test

                     ▲

             Integration Test

                     ▲

            Architecture Test

                     ▲

               Service Test

                     ▲

               Domain Test

                     ▲

              Adapter Test
```

Cada nivel valida un aspecto diferente del sistema.

---

# 6. Adapter Tests

Los Adapter Tests verifican el comportamiento de los adaptadores.

Objetivos:

- validar llamadas al sistema operativo;
- validar lectura de información;
- verificar el aislamiento de infraestructura.

Los adaptadores constituyen la única capa autorizada para acceder a Linux.

---

# 7. Domain Tests

Los Domain Tests validan el comportamiento del modelo de dominio.

Se verifica:

- creación de objetos;
- validación de datos;
- invariantes;
- reglas del dominio.

El dominio nunca depende de infraestructura.

---

# 8. Service Tests

Los Service Tests validan las reglas de negocio.

Los Services coordinan la interacción entre el dominio y la infraestructura.

No realizan llamadas directas al sistema operativo.

---

# 9. Architecture Tests

Los Architecture Tests verifican el cumplimiento de las reglas arquitectónicas.

Ejemplos:

- API no accede a Linux.
- Domain no importa FastAPI.
- Services no utilizan subprocess.
- Sólo los Adapters conocen Linux.

Estas pruebas protegen la arquitectura del proyecto.

---

# 10. Integration Tests

Los Integration Tests validan el funcionamiento conjunto de múltiples componentes.

Ejemplos:

Adapter

↓

Service

↓

API

↓

Respuesta HTTP

Estas pruebas demuestran que la capacidad funciona correctamente como un todo.

---

# 11. Smoke Tests

Los Smoke Tests constituyen la validación final del Sprint.

Su objetivo consiste en verificar que las capacidades principales continúan funcionando correctamente.

Los Smoke Tests se ejecutan antes del cierre oficial de cada misión.

---

# 12. Evidencias

Toda prueba deberá generar evidencia verificable.

Ejemplos:

- respuestas HTTP;
- capturas de pantalla;
- registros;
- archivos JSON;
- resultados de pytest;
- scripts de validación.

Las evidencias forman parte del expediente técnico de la misión.

---

# 13. Automatización

Siempre que sea posible las pruebas deberán automatizarse.

La automatización garantiza:

- repetibilidad;
- rapidez;
- confiabilidad;
- reducción de errores humanos.

---

# 14. Criterios de Calidad

Una prueba debe cumplir:

- claridad;
- independencia;
- repetibilidad;
- simplicidad;
- trazabilidad.

---

# 15. Criterios para una Nueva Capacidad

Ninguna capacidad podrá incorporarse oficialmente al proyecto sin cumplir las siguientes validaciones.

✓ Adapter Test.

✓ Domain Test.

✓ Service Test.

✓ Architecture Test.

✓ Integration Test.

✓ Smoke Test.

---

# 16. Relación con la Documentación

Toda misión deberá documentar:

- qué se probó;
- por qué se probó;
- cómo se probó;
- resultado esperado;
- resultado obtenido.

Las pruebas y la documentación constituyen un único proceso.

---

# 17. Relación con Git

El cierre de una misión requiere:

- pruebas satisfactorias;
- evidencias incorporadas;
- documentación actualizada.

Sólo entonces podrá realizarse el commit correspondiente.

---

# 18. Métricas

El proyecto prioriza la calidad de las pruebas sobre la cantidad.

No se establece una cobertura mínima obligatoria.

Se considera más importante validar correctamente cada capacidad que alcanzar un porcentaje arbitrario de cobertura.

---

# 19. Gestión de Errores

Cuando una prueba falle deberá documentarse:

- causa del fallo;
- análisis realizado;
- solución aplicada;
- evidencia de la corrección.

La resolución de errores también constituye conocimiento del proyecto.

---

# 20. Organización del Directorio de Pruebas

La estructura oficial será:

tests/

↓

adapters/

↓

domain/

↓

services/

↓

architecture/

↓

integration/

↓

smoke/

Cada carpeta agrupa pruebas de un único nivel.

---

# 21. Cierre de una Misión

Una misión sólo podrá considerarse finalizada cuando:

✓ Todas las pruebas pasen satisfactoriamente.

✓ Las evidencias hayan sido incorporadas.

✓ La documentación haya sido actualizada.

✓ El Baseline haya sido generado.

✓ El CHANGELOG haya sido actualizado.

✓ El ROADMAP haya sido actualizado.

---

# 22. Reglas de Oro

1.

Toda capacidad debe poder demostrarse.

2.

Una prueba sin evidencia no está completa.

3.

La arquitectura también se prueba.

4.

Los Adapters prueban infraestructura.

5.

Los Services prueban comportamiento.

6.

El Domain prueba conocimiento.

7.

Los Integration Tests prueban la capacidad completa.

8.

Los Smoke Tests validan el Sprint.

9.

Las pruebas documentan el sistema.

10.

Una misión termina cuando todas las pruebas son satisfactorias.

---

# 23. Conclusión

El presente estándar establece la metodología oficial para la validación del proyecto EJTV Broadcast Platform.

Las pruebas no constituyen una etapa independiente del desarrollo.

Constituyen un componente esencial del proceso de ingeniería.

Cada nueva capacidad deberá estar respaldada por pruebas reproducibles, evidencias verificables y documentación suficiente para garantizar la preservación del conocimiento y la evolución segura del sistema.
