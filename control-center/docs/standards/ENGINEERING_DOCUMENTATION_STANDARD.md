# Engineering Documentation Standard (EDS-001)

**Proyecto:**
EJTV Broadcast Platform

**Subproyecto:**
EJTV Control Center

**Versión**
1.0

**Estado**
Vigente

**Autor**
Gerardo Araya Fallas

---

# 1. Introducción

El presente documento establece el estándar oficial para la elaboración de toda la documentación técnica del proyecto EJTV Broadcast Platform y del EJTV Control Center.

Su propósito es garantizar que cualquier documento producido durante el desarrollo del proyecto mantenga una estructura uniforme, un nivel técnico consistente y un enfoque eminentemente didáctico.

La documentación no constituye un requisito administrativo. Forma parte integral del proceso de ingeniería.

Todo conocimiento adquirido durante el desarrollo deberá documentarse de manera que pueda ser comprendido por un ingeniero que no haya participado en el proyecto.

---

# 2. Filosofía

La documentación constituye un producto de ingeniería.

El software y la documentación poseen el mismo nivel de importancia.

El código implementa capacidades.

La documentación preserva conocimiento.

Una funcionalidad sin documentación adecuada se considera una funcionalidad incompleta.

---

# 3. Objetivos

Este estándar busca:

- preservar el conocimiento generado;
- facilitar el mantenimiento futuro;
- reducir la curva de aprendizaje;
- justificar las decisiones técnicas;
- mejorar la trazabilidad;
- permitir la transferencia de conocimiento;
- convertir el proyecto en una referencia de ingeniería.

---

# 4. Principios Fundamentales

Toda documentación deberá cumplir los siguientes principios.

## Principio 1

Escribir para enseñar.

Nunca asumir que el lector conoce un concepto.

Todo término nuevo deberá explicarse antes de utilizarse.

---

## Principio 2

Del concepto a la implementación.

El orden natural será:

Problema

↓

Concepto

↓

Diseño

↓

Implementación

↓

Pruebas

↓

Resultados

↓

Lecciones aprendidas

---

## Principio 3

Cada documento responde una única pregunta.

No mezclar múltiples temas dentro de un mismo documento.

---

## Principio 4

Justificar todas las decisiones.

Nunca indicar únicamente qué se hizo.

Explicar siempre por qué se tomó esa decisión.

---

## Principio 5

Documentar antes de programar.

La implementación inicia únicamente cuando el problema y el diseño se encuentran claramente definidos.

---

## Principio 6

Toda misión deja una capacidad.

Cada Sprint debe producir una nueva capacidad funcional permanente.

---

## Principio 7

Toda misión deja conocimiento.

Al finalizar una misión deberá existir documentación suficiente para comprender completamente el trabajo realizado.

---

## Principio 8

Pensar siempre en el mantenimiento futuro.

La documentación se escribe para el ingeniero que trabajará sobre el proyecto dentro de cinco años.

---

# 5. Estilo de Escritura

Toda la documentación deberá cumplir las siguientes reglas.

## Escritura técnica

Utilizar lenguaje profesional.

Evitar frases ambiguas.

Evitar lenguaje coloquial.

Evitar opiniones personales.

---

## Escritura didáctica

Explicar conceptos nuevos.

Utilizar ejemplos.

Construir el conocimiento paso a paso.

No asumir experiencia previa.

---

## Longitud de línea

Las líneas deberán mantenerse relativamente cortas para facilitar su lectura tanto en Visual Studio Code como en GitHub.

Se recomienda una longitud aproximada entre 80 y 100 caracteres.

---

## Párrafos

Preferir párrafos cortos.

Cada párrafo deberá desarrollar una única idea.

---

## Listas

Utilizar listas cuando mejoren la comprensión.

No abusar de ellas.

---

# 6. Uso de Diagramas

Siempre que un diagrama permita explicar mejor un concepto deberá preferirse sobre largos bloques de texto.

Se recomienda utilizar diagramas SVG por su escalabilidad y facilidad de mantenimiento.

---

# 7. Código Fuente

El código incluido en la documentación deberá ser mínimo.

Nunca utilizar grandes bloques de código cuando un diagrama o una explicación sean suficientes.

El objetivo de la documentación no es reemplazar al código fuente.

---

# 8. Evidencias

Toda misión deberá incluir evidencias verificables.

Ejemplos:

- capturas de pantalla;
- resultados de pruebas;
- respuestas HTTP;
- registros de ejecución;
- archivos de configuración;
- diagramas;
- tablas.

---

# 9. Pruebas

Toda funcionalidad deberá documentar:

- qué se probó;
- cómo se probó;
- resultado esperado;
- resultado obtenido.

---

# 10. Lecciones Aprendidas

Cada misión finalizará con una sección denominada:

Lecciones Aprendidas

En esta sección se documentará el conocimiento adquirido durante la misión.

No constituye un resumen.

Constituye experiencia acumulada.

---

# 11. Organización de una Misión

Cada misión utilizará la siguiente estructura documental.

README.md

OBJECTIVE.md

PROBLEM.md

GLOSSARY.md

ARCHITECTURE.md

DESIGN.md

IMPLEMENTATION.md

TESTS.md

EVIDENCE.md

LESSONS.md

REFERENCES.md

CHANGELOG.md

BL-XXX.md

---

# 12. Documentación Permanente

Los siguientes documentos describen el sistema completo.

architecture/

api/

standards/

tutorials/

decisions/

Estos documentos evolucionan lentamente.

---

# 13. Documentación Evolutiva

Cada misión posee su propio expediente.

Los expedientes documentan únicamente el desarrollo de una capacidad específica.

---

# 14. Trazabilidad

Toda decisión importante deberá poder rastrearse.

Cuando corresponda deberá referenciarse:

- ADR
- ROADMAP
- CHANGELOG
- MISSION correspondiente

---

# 15. Criterio de Finalización

Una misión se considera terminada únicamente cuando:

✓ el código funciona;

✓ las pruebas pasan satisfactoriamente;

✓ la documentación está completa;

✓ las evidencias fueron incorporadas;

✓ el CHANGELOG fue actualizado;

✓ el ROADMAP fue actualizado;

✓ el Baseline fue generado;

✓ el repositorio puede ser comprendido por otro ingeniero.

---

# 16. Filosofía Final

El objetivo del proyecto no consiste únicamente en desarrollar software.

El objetivo consiste en construir conocimiento reutilizable.

El código implementa capacidades.

La documentación preserva conocimiento.

Ambos poseen exactamente el mismo nivel de importancia.

---

# 17. Frase Institucional

La filosofía oficial del proyecto queda resumida en las siguientes expresiones.

> Donde hay orden, está Dios.

> No estamos desarrollando funciones; estamos construyendo capacidades.

> Administrar infraestructura multimedia profesional desde una plataforma unificada.

> Todo módulo deja código.

> Toda misión deja conocimiento.

> Toda decisión deja una justificación.

> Todo Sprint deja un legado.
