# ENG-012 — Bootstrap del Subsistema Identity

---

# Objetivo

El proceso de **Bootstrap** tiene como finalidad preparar el subsistema
Identity para operar de forma segura y consistente antes de que la
aplicación comience a aceptar solicitudes HTTP.

Durante esta fase se inicializan los componentes fundamentales del
subsistema, se sincroniza el catálogo canónico de identidad y se valida
que el estado persistido sea coherente con las reglas definidas por el
dominio.

El bootstrap constituye la primera línea de defensa contra
configuraciones incompletas, inconsistencias de datos o instalaciones
parciales.

---

# Filosofía del Bootstrap

El proceso de bootstrap fue diseñado bajo cuatro principios
fundamentales.

## Inicialización automática

La plataforma debe ser capaz de preparar el subsistema Identity sin
intervención manual durante el arranque normal.

---

## Idempotencia

El bootstrap puede ejecutarse repetidamente sin producir efectos
secundarios inesperados.

Ejecutarlo una o cien veces debe producir exactamente el mismo estado
funcional.

---

## Integridad

Antes de aceptar tráfico HTTP, el sistema debe comprobar que los datos
persistidos cumplen con el catálogo oficial del dominio.

---

## Seguridad

La aplicación nunca debe iniciar con un catálogo incompleto o
inconsistente.

Ante una falla crítica de integridad, el arranque debe detenerse.

---

# Secuencia general

Durante el inicio de la aplicación se ejecuta la siguiente secuencia.

```text
Inicio de FastAPI
        │
        ▼
Inicialización de la base de datos
        │
        ▼
Construcción del IdentityBootstrapService
        │
        ▼
Sincronización del catálogo canónico
        │
        ▼
Verificación de integridad
        │
        ▼
Identity listo para operar
```

Cada etapa posee una responsabilidad claramente definida.

---

# Inicialización de la base de datos

El primer paso consiste en garantizar la existencia de la estructura de
persistencia requerida por Identity.

Durante esta fase se:

- crea el motor de base de datos;
- inicializan las tablas necesarias;
- prepara la fábrica de sesiones SQLAlchemy.

Esta operación es transparente para el resto del sistema.

---

# Construcción del Bootstrap Service

Una vez disponible la persistencia, se construye una instancia de
`IdentityBootstrapService`.

Este servicio recibe mediante inyección de dependencias los componentes
necesarios para ejecutar el bootstrap.

Entre ellos:

- UserRepository;
- IdentityCatalogRepository;
- AuditRepository;
- PasswordHasher.

De esta forma el dominio permanece desacoplado de la infraestructura.

---

# Sincronización del catálogo

La sincronización constituye una de las responsabilidades principales
del bootstrap.

Su propósito es garantizar que la base de datos refleje exactamente el
catálogo canónico definido por el dominio.

Durante esta fase se ejecuta:

```python
synchronize_catalog()
```

La sincronización realiza automáticamente las siguientes operaciones.

## Crear roles faltantes

Si un rol oficial no existe en la base de datos, se crea
automáticamente.

---

## Actualizar permisos

Si un rol existe pero su conjunto de permisos no coincide con el
catálogo oficial, éste se actualiza.

---

## Conservar roles correctos

Los roles que ya coinciden exactamente con el catálogo permanecen sin
modificaciones.

---

# Catálogo canónico

El catálogo oficial reside en el dominio Identity.

Representa la definición única de:

- roles;
- permisos;
- relaciones entre ambos.

Actualmente incluye, entre otros:

```text
administrator

operator

viewer
```

La sincronización convierte este catálogo en el estado persistido del
sistema.

Esto evita divergencias entre instalaciones.

---

# Verificación de integridad

Una vez sincronizado el catálogo, el bootstrap ejecuta una validación
completa.

```python
verify_integrity()
```

Su propósito es comprobar que la persistencia refleja exactamente el
modelo definido por el dominio.

La validación verifica:

- roles faltantes;
- roles inesperados;
- permisos inconsistentes.

El resultado se representa mediante un objeto
`CatalogIntegrityResult`.

---

# Resultado de la verificación

La validación puede producir tres tipos de diferencias.

## Missing Roles

Roles definidos por el dominio pero ausentes en la base de datos.

---

## Unexpected Roles

Roles presentes en la base de datos pero inexistentes en el catálogo
canónico.

---

## Mismatched Roles

Roles cuyo conjunto de permisos no coincide con la definición oficial.

---

# Política de fallo

Si la verificación determina que el catálogo no es íntegro, la
aplicación interrumpe el proceso de arranque.

Este comportamiento evita que la plataforma opere con un modelo de
seguridad inconsistente.

---

# Bootstrap del administrador inicial

Además de preparar el catálogo, Identity permite crear el primer
administrador del sistema.

Este proceso se ejecuta mediante:

```bash
python -m app.identity.bootstrap_admin
```

Su objetivo es facilitar la instalación inicial de la plataforma.

---

# Variables de configuración

El bootstrap utiliza la configuración definida en el entorno.

Entre las variables principales se encuentran:

```text
BOOTSTRAP_ADMIN_USERNAME

BOOTSTRAP_ADMIN_EMAIL

BOOTSTRAP_ADMIN_PASSWORD
```

La contraseña sólo debe existir durante el proceso de instalación.

Una vez verificado el acceso inicial, debe eliminarse del entorno.

---

# Idempotencia del administrador

El bootstrap del administrador es completamente idempotente.

Si el usuario administrador ya existe:

- no se modifica la contraseña;
- no se modifica el correo;
- no se reemplazan los roles;
- no se altera el estado del usuario.

El proceso simplemente informa que el administrador ya se encuentra
registrado.

---

# Auditoría

Las operaciones relevantes del bootstrap generan registros de auditoría.

Entre ellos:

```text
identity.bootstrap.catalog_synchronized

identity.bootstrap.integrity_verified

identity.bootstrap.administrator_created

identity.bootstrap.skipped
```

Estos eventos permiten reconstruir posteriormente el proceso de
inicialización del sistema.

---

# Integración con FastAPI

El bootstrap forma parte del ciclo de vida de la aplicación.

Durante el evento de inicio se ejecuta automáticamente:

```text
application_startup()

↓

build_bootstrap_service()

↓

synchronize_catalog()

↓

verify_integrity()
```

De esta forma ningún endpoint queda disponible antes de que Identity
haya sido validado.

---

# Beneficios del diseño

La estrategia implementada proporciona múltiples ventajas.

Entre ellas:

- instalaciones reproducibles;
- despliegues consistentes;
- detección temprana de errores;
- eliminación de configuraciones manuales;
- recuperación sencilla ante instalaciones nuevas;
- reducción del riesgo operativo.

---

# Conclusión

El proceso de Bootstrap constituye el mecanismo mediante el cual el
subsistema Identity garantiza que todas las instancias de la plataforma
comiencen desde un estado conocido, consistente y verificable.

Gracias a la sincronización automática del catálogo, la validación de
integridad y la creación idempotente del administrador inicial, el
arranque de la aplicación se convierte en un proceso seguro,
determinístico y alineado con las reglas del dominio.