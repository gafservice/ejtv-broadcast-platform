# ENG-011 — IAM Test Strategy

> Estado: estructura inicial creada. Contenido pendiente de desarrollo.

# ENG-011 — Test Strategy

---

# Introducción

Este documento define la estrategia de pruebas para el módulo Identity & Access Management (IAM).

El objetivo es garantizar que cada componente del subsistema de identidad sea verificable, reproducible y mantenible durante toda la vida del proyecto.

Las pruebas constituyen un requisito obligatorio para todas las funcionalidades implementadas dentro del módulo.

---

# Objetivos

La estrategia de pruebas busca garantizar:

- Correctitud funcional.
- Seguridad.
- Estabilidad.
- Regresión controlada.
- Compatibilidad con futuras versiones.
- Alta cobertura del dominio.

---

# Pirámide de pruebas

La distribución de pruebas seguirá la siguiente estrategia.

```text
                End-to-End
              ───────────────
             Integration Tests
        ───────────────────────────
              Unit Tests
```

La mayor parte de las pruebas corresponderán al dominio.

---

# Tipos de pruebas

## Unitarias

Validan el comportamiento interno del dominio.

Se probarán:

- User
- Role
- Permission
- Identity
- Value Objects
- Reglas de negocio

Estas pruebas no utilizarán:

- Base de datos
- JWT
- FastAPI
- Argon2
- HTTP

---

## Integración

Verifican la interacción con la infraestructura.

Incluyen:

- UserRepository
- PasswordHasher
- JWT Provider
- Audit Repository

---

## API

Validan el comportamiento expuesto mediante FastAPI.

Se probarán:

- Login
- Logout
- Refresh Token
- Protección de endpoints
- HTTP 401
- HTTP 403

---

## End-to-End

Simulan el comportamiento completo del usuario.

Ejemplos:

- Inicio de sesión.
- Acceso al Dashboard.
- Cambio de contraseña.
- Cierre de sesión.
- Acceso denegado.

---

# Cobertura esperada

| Capa | Cobertura mínima |
|------|------------------:|
| Domain | 100 % |
| Application | 95 % |
| Infrastructure | 90 % |
| API | 90 % |

---

# Casos de prueba del dominio

## User

- Crear usuario válido.
- Usuario deshabilitado.
- Usuario bloqueado.
- Cambio de contraseña.
- Cambio de estado.

---

## Role

- Crear rol.
- Agregar permiso.
- Eliminar permiso.
- Comparación de roles.

---

## Permission

- Crear permiso.
- Comparación.
- Igualdad.
- Serialización.

---

## Identity

- Usuario autenticado.
- Usuario anónimo.
- Usuario expirado.

---

# Casos de autenticación

Se validarán escenarios como:

- Usuario inexistente.
- Contraseña incorrecta.
- Usuario deshabilitado.
- Usuario bloqueado.
- Credenciales válidas.
- Token expirado.
- Token inválido.
- Token alterado.

---

# Casos de autorización

Se validarán escenarios como:

- Acceso permitido.
- Acceso denegado.
- Rol inexistente.
- Permiso insuficiente.
- Recurso inexistente.

---

# Casos de auditoría

Se verificará el registro de:

- Login exitoso.
- Login fallido.
- Cambio de contraseña.
- Creación de usuarios.
- Eliminación de usuarios.
- Reinicio de servicios.
- Modificación de configuraciones.

---

# Automatización

Todas las pruebas deberán ejecutarse automáticamente mediante Pytest.

La ejecución deberá integrarse con el pipeline de desarrollo del proyecto.

Cada cambio funcional deberá incorporar sus respectivas pruebas antes de ser aceptado.

---

# Regresión

Toda corrección de errores deberá incluir una prueba que reproduzca el problema detectado.

Una vez corregido el defecto, la prueba permanecerá en el repositorio para evitar regresiones futuras.

---

# Rendimiento

También se verificarán aspectos relacionados con:

- Tiempo de autenticación.
- Tiempo de validación de permisos.
- Emisión de tokens.
- Consumo de memoria.

---

# Criterios de aceptación

Una funcionalidad será considerada terminada únicamente cuando:

- Todas las pruebas unitarias pasen.
- Todas las pruebas de integración pasen.
- Todas las pruebas de API pasen.
- No existan regresiones.
- Se mantenga la cobertura mínima definida.

---

# Herramientas

Las pruebas utilizarán:

- Pytest
- pytest-cov
- httpx
- FastAPI TestClient
- Mocks y Fakes cuando corresponda

---

# Conclusión

La estrategia de pruebas definida para ENG-011 garantiza que el subsistema IAM evolucione de forma segura, manteniendo un alto nivel de calidad y permitiendo detectar de manera temprana errores funcionales, regresiones y problemas de integración.