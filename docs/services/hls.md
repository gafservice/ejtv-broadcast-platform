1. Introducción
2. Arquitectura HLS en EJTV
3. Configuración de MediaMTX
4. Publicación de un flujo mediante FFmpeg
5. Validación del servicio
   5.1 Verificación del puerto
   5.2 Verificación del index.m3u8
   5.3 Reproducción en VLC
   5.4 Reproducción en navegador

6. Observación técnica   
## Observación técnica

Durante las pruebas de validación del servicio HLS se observó un comportamiento propio de la implementación utilizada por MediaMTX v1.19.0 cuando opera en modo **Low-Latency HLS (LL-HLS)**.

El servidor genera correctamente el archivo principal de reproducción (`index.m3u8`), el cual contiene las referencias hacia las listas de reproducción de audio y video que serán utilizadas posteriormente por el cliente para solicitar los segmentos multimedia correspondientes.

Durante las pruebas también se comprobó que MediaMTX administra internamente la sesión de reproducción mediante mecanismos HTTP basados en cookies y otros parámetros asociados a la conexión del cliente. Este procedimiento forma parte del funcionamiento normal del servidor y permite mantener la sincronización entre las diferentes listas de reproducción y los segmentos generados dinámicamente.

Como consecuencia de este mecanismo, herramientas de línea de comandos como **curl** permiten verificar la disponibilidad y el contenido del archivo principal (`index.m3u8`), pero no necesariamente reproducen el comportamiento completo del protocolo cuando se intenta acceder directamente a las listas de reproducción internas (`video1_stream.m3u8` y `audio2_stream.m3u8`). En estos casos el servidor puede responder con mensajes de autenticación asociados al control interno de la sesión, aun cuando el servicio esté funcionando correctamente.

Por esta razón, la validación funcional del servicio HLS debe realizarse utilizando clientes compatibles con el protocolo, tales como **VLC**, navegadores web modernos o reproductores HLS equivalentes, ya que estos administran automáticamente las redirecciones HTTP, las cookies de sesión y las solicitudes sucesivas necesarias para la reproducción continua del contenido.

Durante la presente misión se verificó satisfactoriamente la generación del archivo `index.m3u8`, la creación dinámica de las listas de reproducción correspondientes y la reproducción continua del flujo tanto desde **VLC** como desde un navegador web. Estas evidencias permiten concluir que el servicio HLS quedó correctamente implementado e integrado dentro de la infraestructura de la **EJTV Broadcast Platform**.


## Revisión técnica final

La MISSION-014 permitió incorporar oficialmente el servicio HTTP Live Streaming (HLS) dentro de la infraestructura de la EJTV Broadcast Platform, utilizando las capacidades nativas de MediaMTX v1.19.0.

Durante la revisión técnica se verificó que el servicio HLS se encuentra habilitado en la configuración principal de MediaMTX, escuchando en el puerto `8888/tcp` y operando bajo la variante `lowLatency`. Esta configuración permite que los flujos publicados hacia MediaMTX puedan ser distribuidos posteriormente mediante HTTP, sin modificar los servicios previamente validados de RTSP, RTMP y SRT.

La publicación del flujo de prueba se realizó mediante FFmpeg, utilizando RTMP como protocolo de ingesta hacia MediaMTX. A partir de este flujo, MediaMTX generó automáticamente el recurso HLS correspondiente, incluyendo el archivo principal `index.m3u8` y las listas de reproducción asociadas al contenido multimedia.

La validación funcional confirmó que el archivo `index.m3u8` fue generado correctamente y que contenía una estructura HLS válida, identificada mediante las etiquetas `#EXTM3U`, `#EXT-X-VERSION`, `#EXT-X-MEDIA` y `#EXT-X-STREAM-INF`. Adicionalmente, se comprobó la reproducción satisfactoria del flujo desde VLC y desde un navegador web, demostrando que el servicio puede ser consumido por clientes HLS estándar.

Durante las pruebas también se identificó que MediaMTX administra internamente las sesiones Low-Latency HLS mediante mecanismos HTTP asociados a cookies y control de sesión. Por esta razón, la validación completa del servicio no debe depender únicamente del acceso directo a listas internas mediante `curl`, sino de la reproducción efectiva mediante clientes compatibles con HLS.

Como parte de la misión se incorporó el script de mantenimiento `scripts/maintenance/hls-status.sh`, el cual permite verificar de forma rápida el estado del servicio MediaMTX, la disponibilidad del puerto HLS, la respuesta HTTP del recurso `index.m3u8` y la validez básica de la playlist generada.

Con base en las pruebas realizadas, se concluye que el servicio HLS quedó correctamente implementado, validado, documentado e integrado dentro de la arquitectura de la EJTV Broadcast Platform. La misión no introdujo cambios que afectaran los servicios previamente validados y mantiene la compatibilidad con la arquitectura existente.




7. Acceptance Test

8. Conclusiones