# Principios de ingeniería

---

## Introducción

Toda decisión técnica tomada durante este proyecto deberá respetar los
principios definidos en este documento.

Estos principios representan la identidad de **EJTV Broadcast Platform** y
servirán como guía durante toda su evolución.

---

# 1. La estabilidad prevalece sobre la novedad

La incorporación de nuevas funcionalidades nunca tendrá prioridad sobre la
estabilidad del sistema.

Una plataforma estable siempre tendrá mayor valor que una plataforma con muchas
funciones difíciles de mantener.

---

# 2. Cada servicio tendrá una única responsabilidad

Cada componente deberá realizar una tarea específica.

Evitar que un mismo servicio asuma múltiples responsabilidades facilita el
mantenimiento, simplifica el diagnóstico y mejora la confiabilidad del sistema.

---

# 3. La seguridad forma parte del diseño

La seguridad no será incorporada al finalizar el proyecto.

Será considerada desde las primeras etapas del diseño y acompañará todas las
decisiones relacionadas con la plataforma.

---

# 4. Toda decisión debe poder justificarse

No incorporaremos una tecnología únicamente porque sea reciente o popular.

Cada componente deberá responder claramente dos preguntas.

- ¿Por qué fue seleccionado?
- ¿Qué ventaja aporta a la plataforma?

---

# 5. La documentación forma parte del sistema

La documentación tendrá el mismo nivel de importancia que la implementación.

Toda modificación importante deberá quedar registrada y explicada.

Creemos que una plataforma bien documentada puede mantenerse durante muchos
años.

---

# 6. La simplicidad es una ventaja

Siempre preferiremos la solución más sencilla que cumpla correctamente los
objetivos del proyecto.

La simplicidad reduce errores, facilita el mantenimiento y acelera la
capacitación de nuevos ingenieros.

---

# 7. Primero comprender, después implementar

Antes de modificar la plataforma debemos comprender completamente el problema.

Implementar una solución sin comprender su fundamento suele generar problemas
difíciles de mantener.

---

# 8. Nunca dejar de aprender

Este proyecto ha sido concebido como una plataforma de aprendizaje continuo.

Cada documento deberá enseñar.

Cada decisión deberá aportar conocimiento.

Cada etapa del proyecto deberá enriquecer la experiencia de quienes participen
en su desarrollo.

---

## Nuestro principio fundamental

> **Construimos plataformas que pueden entenderse.**

Creemos que una plataforma que solamente funciona depende de las personas que
la construyeron.

Una plataforma que puede comprenderse puede mantenerse, evolucionar y mejorar
durante muchos años.

Ese será siempre el objetivo de **EJTV Broadcast Platform**.    



# Principios de Ingeniería para el ENGINEERING NOC

Los siguientes principios complementan los principios generales del proyecto y establecen las reglas que regirán el desarrollo del ENGINEERING NOC y de todas las futuras capacidades de ingeniería de la plataforma.

---

## La observabilidad precede al diagnóstico

No es posible diagnosticar correctamente aquello que no puede observarse.

Antes de emitir conclusiones, el sistema deberá recopilar y modelar toda la información técnica disponible.

El ENGINEERING NOC priorizará siempre la adquisición de información antes que la interpretación.

---

## Toda la información técnica debe preservarse

La plataforma conservará toda la información técnica disponible proveniente del sistema operativo, del motor de streaming y de los protocolos soportados.

La interfaz decidirá qué información mostrar según el contexto operativo.

El modelo interno nunca eliminará información únicamente por razones de presentación.

Este principio garantiza que futuras capacidades puedan desarrollarse sin rediseñar el modelo de datos.

---

## Separación entre adquisición, dominio y presentación

La arquitectura deberá mantener claramente separadas las siguientes responsabilidades:

- Descubrimiento y adquisición de información.
- Modelado del dominio.
- Lógica de negocio.
- Diagnóstico.
- Presentación.

Cada componente deberá cumplir una única responsabilidad claramente definida.

---

## La portabilidad forma parte del diseño

La plataforma deberá poder instalarse sobre diferentes infraestructuras sin requerir modificaciones en el código fuente.

Durante su inicialización descubrirá automáticamente las capacidades disponibles del entorno donde se ejecuta.

Nunca deberá depender de:

- nombres específicos de interfaces;
- cantidad fija de procesadores;
- cantidad fija de discos;
- hardware determinado;
- proveedor específico de infraestructura.

---

## Configuración y capacidades son conceptos diferentes

La configuración representa las decisiones del administrador.

Las capacidades representan los recursos disponibles del sistema.

Ambos conceptos deberán permanecer completamente separados dentro de la arquitectura.

---

## Evolución mediante expansión

Las nuevas funcionalidades deberán incorporarse mediante nuevos módulos especializados.

Siempre que sea posible se evitará reemplazar componentes estables previamente validados.

La evolución de la plataforma deberá realizarse de manera incremental y compatible con versiones anteriores.

---

## Compatibilidad hacia atrás

Toda mejora deberá preservar el comportamiento observable de las funcionalidades existentes.

Las nuevas capacidades deberán integrarse sin afectar el funcionamiento previamente validado.

---

## Diagnóstico basado en evidencia

Las conclusiones emitidas por el ENGINEERING NOC deberán sustentarse exclusivamente en información objetiva obtenida del sistema.

El motor de diagnóstico no realizará inferencias basadas en supuestos no verificables.

---

## La resiliencia se construye sobre el conocimiento

Las capacidades de redundancia, sincronización y recuperación automática se implementarán únicamente cuando el comportamiento del sistema haya sido completamente comprendido mediante los módulos de observabilidad.

La alta disponibilidad será consecuencia de una plataforma previamente instrumentada y validada.

---

## La documentación forma parte del producto

Toda decisión arquitectónica relevante deberá quedar documentada mediante Architecture Decision Records (ADR).

La documentación técnica será considerada un componente permanente del proyecto y evolucionará junto con el código fuente.

---

## La calidad prevalece sobre la velocidad

El desarrollo privilegiará siempre:

- estabilidad;
- mantenibilidad;
- claridad arquitectónica;
- pruebas automatizadas;
- documentación;
- evolución incremental.

El crecimiento del proyecto nunca deberá comprometer la calidad alcanzada en las etapas anteriores.

## El software evoluciona sin perder estabilidad

Cada nueva funcionalidad deberá integrarse preservando la estabilidad de la plataforma.

La incorporación de nuevas capacidades nunca justificará la pérdida de funcionalidades previamente implementadas.

El crecimiento del sistema deberá producirse mediante evolución controlada, manteniendo la compatibilidad, la trazabilidad y la confiabilidad alcanzadas en las etapas anteriores.