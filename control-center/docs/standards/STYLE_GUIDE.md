# EJTV Control Center

# Guía de Estilo

**Versión:** 1.0

**Estado:** Diseño

**Misión:** MISSION-017

---

# 1. Introducción

La presente Guía de Estilo define las normas visuales y de interacción del EJTV Control Center.

Su objetivo consiste en garantizar que toda la plataforma mantenga una identidad uniforme, una experiencia de usuario consistente y una presentación profesional independientemente del módulo desarrollado.

Esta guía deberá ser utilizada por los equipos de desarrollo Frontend, Backend y Diseño.

---

# 2. Filosofía

El Control Center es una herramienta de operación profesional.

No pretende parecer una página web comercial.

Debe transmitir:

- estabilidad;
- claridad;
- rapidez;
- precisión;
- confianza.

El diseño nunca deberá distraer al operador.

La información es más importante que la decoración.

---

# 3. Principios de Diseño

Toda la interfaz deberá respetar los siguientes principios.

## Claridad

Cada elemento debe tener un propósito.

## Consistencia

Los mismos elementos siempre deberán comportarse igual.

## Simplicidad

Eliminar elementos innecesarios.

## Jerarquía

La información crítica debe destacar.

## Rapidez

Las operaciones frecuentes deben ejecutarse con pocos clics.

## Accesibilidad

Toda la información deberá ser fácilmente identificable.

---

# 4. Paleta de Colores

La plataforma utilizará una paleta sobria inspirada en centros de operación de red (NOC).

## Fondo principal

Azul muy oscuro.

## Paneles

Gris oscuro.

## Tarjetas

Gris ligeramente más claro.

## Texto principal

Blanco.

## Texto secundario

Gris claro.

---

## Estados

Normal

Verde.

Advertencia

Amarillo.

Error

Rojo.

Información

Azul.

Deshabilitado

Gris.

Mantenimiento

Naranja.

---

# 5. Tipografía

Se utilizará una única familia tipográfica.

Jerarquía:

Título principal

Subtítulo

Título de sección

Texto normal

Texto técnico

Código

Las métricas deberán utilizar números fácilmente legibles.

---

# 6. Iconografía

Los iconos deberán representar conceptos, no decoración.

Ejemplos:

Dashboard

Canal

Cliente

Servicio

Usuario

Nodo

Interfaz

Red

Seguridad

Configuración

Reporte

Logs

Alarma

Métrica

Protocolo

No deberán utilizarse iconos ambiguos.

---

# 7. Botones

Todos los botones deberán clasificarse según su propósito.

## Acción primaria

Guardar.

Aplicar.

Crear.

## Acción secundaria

Cancelar.

Volver.

Cerrar.

## Acción operativa

Iniciar.

Detener.

Reiniciar.

## Acción crítica

Eliminar.

Restaurar.

Aplicar configuración.

Las acciones críticas deberán diferenciarse claramente.

---

# 8. Tarjetas

Las tarjetas representan entidades del sistema.

Ejemplo

Canal

Cliente

Servicio

Nodo

Usuario

Toda tarjeta mostrará:

nombre

estado

acciones principales

indicadores relevantes

---

# 9. Tablas

Las tablas deberán ser uniformes.

Toda tabla permitirá:

ordenamiento

búsqueda

filtrado

paginación

exportación cuando corresponda

Las acciones se ubicarán al extremo derecho.

---

# 10. Formularios

Los formularios deberán presentar los campos agrupados por tema.

Toda validación deberá realizarse antes del envío.

Los errores deberán mostrarse junto al campo correspondiente.

Nunca deberán utilizarse mensajes genéricos.

---

# 11. Indicadores

Los indicadores deberán utilizar siempre las mismas unidades.

Ejemplos:

CPU %

RAM %

Disco %

Bitrate Mbps

Temperatura °C

Latencia ms

Pérdida %

Lectores

Conexiones

Nunca deberán mezclarse unidades.

---

# 12. Gráficos

Todos los gráficos deberán utilizar el mismo estilo.

Reglas:

leyendas visibles

ejes claros

unidades visibles

escala uniforme

colores consistentes

Evitar gráficos tridimensionales.

La prioridad será facilitar la interpretación.

---

# 13. Alarmas

Las alarmas utilizarán cinco niveles.

Informativa

Advertencia

Menor

Mayor

Crítica

Toda alarma mostrará:

origen

fecha

hora

descripción

estado

acción recomendada

---

# 14. Mensajes

Los mensajes deberán ser claros.

Ejemplo correcto

"El canal ENLACE fue reiniciado correctamente."

Ejemplo incorrecto

"Operación realizada."

Siempre deberá indicarse:

qué ocurrió

sobre qué recurso

resultado

cuando corresponda

acción sugerida

---

# 15. Confirmaciones

Toda operación crítica requerirá confirmación.

Ejemplos:

Eliminar cliente.

Detener canal.

Aplicar configuración.

Reiniciar servicio.

La confirmación deberá indicar claramente las consecuencias.

---

# 16. Nomenclatura

La interfaz utilizará lenguaje operativo.

Correcto

Canal

Cliente

Servicio

Nodo

Protocolo

Fuente

Configuración

Incorrecto

Path

Publisher

Reader

PID

YAML

Systemctl

La terminología técnica quedará reservada para vistas avanzadas.

---

# 17. Navegación

Todos los módulos compartirán la misma estructura.

Objeto

↓

Información

↓

Operación

↓

Histórico

↓

Configuración

Esto reducirá la curva de aprendizaje.

---

# 18. Diseño Adaptable

El Control Center deberá funcionar correctamente en:

escritorio

portátil

tableta

La información crítica deberá permanecer visible.

---

# 19. Accesibilidad

La plataforma deberá:

mantener suficiente contraste;

no depender únicamente del color;

utilizar iconografía consistente;

permitir navegación mediante teclado;

mostrar indicadores claros de foco.

---

# 20. Animaciones

Las animaciones deberán utilizarse únicamente cuando aporten información.

Ejemplos:

actualización de métricas;

aparición de alarmas;

progreso de operaciones.

No deberán utilizarse efectos decorativos.

---

# 21. Tiempo Real

Los datos dinámicos deberán actualizarse automáticamente.

El operador nunca deberá actualizar manualmente la página para conocer el estado actual.

---

# 22. Estados Vacíos

Cuando un módulo no posea información se mostrará un mensaje descriptivo.

Ejemplo

"No existen alarmas activas."

Nunca deberán mostrarse tablas vacías sin explicación.

---

# 23. Estados de Carga

Toda operación mostrará claramente:

cargando

procesando

completado

error

El operador deberá comprender qué está ocurriendo.

---

# 24. Identidad Visual

Toda la plataforma deberá transmitir:

ingeniería;

estabilidad;

precisión;

profesionalismo.

La apariencia deberá mantenerse uniforme durante toda la evolución del proyecto.

---

# 25. Evolución

Esta guía podrá ampliarse para incorporar:

modo claro;

modo oscuro;

temas corporativos;

personalización por cliente;

paneles especializados;

nuevos componentes visuales.

Toda incorporación deberá respetar las reglas establecidas en este documento.

---

# 26. Conclusión

La Guía de Estilo constituye el estándar visual del EJTV Control Center.

Su finalidad consiste en garantizar que todos los módulos de la plataforma presenten una apariencia coherente, una interacción consistente y una experiencia de usuario orientada a la operación profesional.

Toda nueva pantalla, componente o funcionalidad deberá cumplir las normas definidas en este documento antes de ser incorporada al sistema.