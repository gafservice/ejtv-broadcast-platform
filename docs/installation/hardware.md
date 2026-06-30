# Plataforma de Hardware

> *"Todo sistema informático comienza mucho antes de instalar el sistema operativo. Comienza con la selección del hardware sobre el cual se construirá toda la infraestructura."*

---

# Resumen Ejecutivo

La plataforma **EJTV Broadcast Platform** fue concebida para desarrollarse sobre una infraestructura física capaz de ofrecer estabilidad, capacidad de expansión y una larga vida útil.

La selección del hardware no respondió únicamente a criterios económicos ni a la disponibilidad inmediata de equipos. Representó una decisión de ingeniería orientada a construir una plataforma robusta, preparada para crecer y capaz de incorporar nuevas funcionalidades conforme evolucionen las necesidades del proyecto.

El servidor **ejtv-01** constituye el primer nodo físico de esta infraestructura. Sobre él se instalarán el sistema operativo, los servicios de distribución audiovisual, las herramientas de monitoreo, los mecanismos de administración y todos los componentes que conformarán la primera versión de la plataforma.

Este documento describe las características generales del hardware seleccionado, explica los criterios utilizados durante su elección y documenta el estado actual de la plataforma física sobre la cual continuará desarrollándose **EJTV Broadcast Platform**.

---

# Objetivo

Documentar la plataforma física utilizada para el desarrollo de **EJTV Broadcast Platform**, justificando las decisiones relacionadas con el hardware y estableciendo una referencia técnica para futuras ampliaciones de la infraestructura.

---

# Alcance

El presente documento describe el hardware desde una perspectiva arquitectónica.

No documenta procedimientos relacionados con la instalación del sistema operativo, configuración del firmware, particionado de discos ni instalación de controladores.

Estos procedimientos serán desarrollados posteriormente en los documentos correspondientes dentro de la sección **Installation**.

---

# Filosofía de selección del hardware

Toda plataforma tecnológica necesita una base física sobre la cual operar.

La calidad de esta base condiciona la estabilidad del sistema, su capacidad de crecimiento y la facilidad con la que podrán incorporarse nuevas funcionalidades durante los próximos años.

Por esta razón, la selección del servidor no se limitó a comparar especificaciones técnicas.

Se analizaron aspectos relacionados con la robustez de la plataforma, la capacidad de expansión, la disponibilidad de interfaces de comunicación, el almacenamiento interno, la facilidad de mantenimiento y la compatibilidad con Linux.

El objetivo consistió en seleccionar un equipo capaz de evolucionar junto con la plataforma sin requerir sustituciones prematuras del hardware principal.

---

# Plataforma seleccionada

El servidor utilizado para el desarrollo de **EJTV Broadcast Platform** corresponde a una estación de trabajo profesional **Apple Mac Pro 5,1**.

Aunque este equipo fue diseñado originalmente para aplicaciones de producción audiovisual, edición de video y procesamiento de contenido multimedia, sus características técnicas permiten reutilizarlo exitosamente como servidor Linux de propósito general.

Su arquitectura modular facilita la incorporación de nuevos discos, interfaces de red, tarjetas PCI Express y otros componentes especializados, proporcionando una plataforma especialmente adecuada para proyectos experimentales y de investigación.

---

# Justificación de la selección

La elección del Mac Pro respondió a criterios eminentemente técnicos.

Entre las principales razones destacan:

* arquitectura profesional diseñada para operación continua;
* procesadores Intel Xeon orientados a cargas de trabajo intensivas;
* soporte para memoria ECC (según la configuración instalada);
* múltiples bahías internas para almacenamiento;
* amplia capacidad de expansión mediante PCI Express;
* posibilidad de incorporar interfaces Ethernet de 10 Gigabits;
* excelente sistema de refrigeración;
* construcción robusta y facilidad de mantenimiento.

Estas características permiten construir una plataforma estable sin depender de hardware propietario especializado.

---

# Configuración general del servidor

El servidor constituye el nodo principal sobre el cual se desarrollará la infraestructura.

Su configuración será documentada y actualizada conforme evolucione el proyecto.

Actualmente la plataforma incorpora los siguientes componentes generales:

* Chasis Apple Mac Pro 5,1.
* Procesador Intel Xeon.
* Memoria principal instalada.
* Unidad SSD destinada al sistema operativo.
* Discos adicionales para almacenamiento de datos.
* Tarjeta gráfica dedicada.
* Interfaces Gigabit Ethernet.
* Interfaces Ethernet de 10 Gigabits.

Las características específicas de cada componente podrán ampliarse conforme se incorporen nuevas actualizaciones de hardware.

---

# Interfaces de red

Uno de los aspectos más importantes considerados durante la selección del servidor fue la disponibilidad de múltiples interfaces Ethernet.

Durante la etapa inicial del proyecto se identificaron cuatro interfaces físicas:

* dos interfaces Intel Gigabit Ethernet;
* dos interfaces Intel X540 de 10 Gigabits Ethernet.

Esta configuración permitirá separar progresivamente diferentes funciones de la plataforma, tales como:

* administración;
* producción audiovisual;
* distribución de contenido;
* monitoreo;
* redes dedicadas para respaldo.

La existencia de múltiples interfaces constituye una ventaja importante para futuras arquitecturas segmentadas mediante VLAN o enlaces físicos independientes.

---

# Subsistema de almacenamiento

La plataforma dispone de varias bahías internas destinadas al almacenamiento.

Esta característica permite separar físicamente el sistema operativo de la información generada durante la operación diaria.

Durante la primera etapa del proyecto se utilizará la siguiente organización:

* una unidad SSD dedicada al sistema operativo;
* un disco destinado al almacenamiento de datos;
* espacio reservado para futuras ampliaciones.

Esta separación reduce el impacto de tareas de mantenimiento sobre la información operativa y facilita la administración del almacenamiento.

---

# Compatibilidad con Linux

Uno de los factores evaluados durante el proceso de selección fue la compatibilidad del hardware con distribuciones modernas de Linux.

Las pruebas realizadas demostraron que Ubuntu reconoce correctamente los principales componentes del servidor, incluyendo:

* interfaces de red;
* dispositivos PCI Express;
* controladoras de almacenamiento;
* tarjeta gráfica;
* dispositivos USB.

Esta compatibilidad simplifica la administración del sistema y reduce la dependencia de controladores propietarios.

---

# Capacidad de expansión

El servidor fue seleccionado considerando también su potencial de crecimiento.

Entre las posibilidades de ampliación disponibles destacan:

* incremento de la memoria principal;
* incorporación de nuevas unidades de almacenamiento;
* instalación de interfaces de red adicionales;
* tarjetas PCI Express especializadas;
* incorporación de nuevas tecnologías de comunicación.

Esta capacidad permitirá adaptar la infraestructura conforme evolucionen las necesidades operativas sin modificar la arquitectura general del sistema.

---

# Limitaciones conocidas

Como toda plataforma tecnológica, el servidor presenta algunas limitaciones que deben documentarse desde las primeras etapas del proyecto.

Entre ellas destacan:

* arquitectura con varios años de antigüedad;
* ausencia de algunas tecnologías presentes en plataformas modernas;
* soporte limitado para determinadas funciones avanzadas de firmware;
* consumo energético superior al de equipos contemporáneos.

Estas limitaciones fueron consideradas durante la etapa de análisis y se estimó que no comprometen los objetivos planteados para la primera versión de **EJTV Broadcast Platform**.

---

# Estado actual de la plataforma

Al concluir la etapa inicial de preparación del servidor, la plataforma presenta el siguiente estado general:

* Sistema operativo Ubuntu 24.04 LTS instalado.
* Kernel Linux actualizado.
* Nombre del servidor configurado como **ejtv-01**.
* Acceso remoto mediante SSH habilitado.
* Visual Studio Code instalado como entorno de desarrollo.
* Repositorio Git inicializado.
* Documentación técnica organizada dentro del proyecto.

Este estado constituye el punto de partida para la instalación progresiva de los servicios que conformarán la plataforma.

---

# Evolución prevista

La arquitectura del servidor permitirá incorporar nuevos recursos conforme aumenten las necesidades del proyecto.

Entre las ampliaciones previstas se consideran:

* incremento de la capacidad de almacenamiento;
* implementación de mecanismos de redundancia;
* incorporación de almacenamiento dedicado para respaldos;
* ampliación de la infraestructura de red;
* integración de nuevos servicios de monitoreo y administración.

Cada una de estas modificaciones será documentada conforme se implemente.

---

# Ficha técnica del servidor

| Parámetro              | Valor                                         |
| ---------------------- | --------------------------------------------- |
| Nombre del servidor    | **ejtv-01**                                   |
| Plataforma             | Apple Mac Pro 5,1                             |
| Función                | Servidor principal de EJTV Broadcast Platform |
| Sistema operativo      | Ubuntu 24.04 LTS                              |
| Kernel                 | Linux 6.17                                    |
| Interfaces de red      | 2 × 1 GbE + 2 × 10 GbE                        |
| Almacenamiento inicial | SSD para sistema + disco de datos             |
| Estado                 | Operativo                                     |
| Rol                    | Nodo principal de desarrollo                  |

---

# Relación con otros documentos

Este documento se complementa con:

* `docs/installation/ubuntu.md`
* `docs/installation/network.md`
* `docs/installation/storage.md`
* `docs/architecture/NETWORK_ARCHITECTURE.md`
* `docs/architecture/STORAGE_ARCHITECTURE.md`
* `docs/journal/MISSION-001.md`

---

# Lecciones aprendidas

La experiencia obtenida durante la selección y preparación del hardware permitió confirmar varios principios que acompañarán el desarrollo de la plataforma.

Una infraestructura profesional no depende necesariamente del hardware más reciente, sino de una arquitectura bien planificada y de una adecuada capacidad de expansión.

La reutilización de equipos de clase profesional puede proporcionar una excelente relación entre desempeño, estabilidad y costo, siempre que exista compatibilidad con el sistema operativo y disponibilidad de recursos suficientes para soportar la evolución prevista del proyecto.

Asimismo, documentar detalladamente la plataforma física desde el inicio facilita futuras tareas de mantenimiento, simplifica la incorporación de nuevos integrantes al proyecto y preserva la trazabilidad de las decisiones de ingeniería adoptadas durante las primeras etapas de desarrollo.

---

# Conclusión

La selección del servidor **ejtv-01** constituye una de las primeras decisiones de ingeniería adoptadas durante el desarrollo de **EJTV Broadcast Platform**.

Más allá de sus especificaciones técnicas, la plataforma fue elegida por su capacidad para ofrecer estabilidad, flexibilidad y posibilidades de crecimiento a largo plazo.

La reutilización de una estación de trabajo profesional demuestra que es posible construir una infraestructura moderna aprovechando hardware confiable y ampliamente probado, siempre que exista una arquitectura bien definida y una estrategia clara de evolución.

El servidor no representa únicamente el equipo donde se instaló Ubuntu.

Representa el primer nodo físico sobre el cual comenzará a construirse toda la infraestructura tecnológica de **EJTV Broadcast Platform**, sirviendo como base para las siguientes etapas de desarrollo, integración de servicios y crecimiento de la plataforma.
