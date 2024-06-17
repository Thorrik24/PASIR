
# HEIMDALL

Durante el periodo de prácticas en un entorno real como parte de mi Formación en Centros de Trabajo (FCT), hemos decidido desarrollar una aplicación web utilizando Django. Esta iniciativa tiene como objetivo principal mejorar la gestión de incidencias dentro de la organización mediante un sistema integral de gestión de tickets y comunicación interna.

Para lograr esto, la aplicación permitirá a los usuarios registrar incidencias de manera estructurada, asignar prioridades, dar seguimiento al estado de cada ticket y registrar las acciones tomadas para su resolución. Se implementará un flujo de trabajo automatizado que mejorará la eficiencia operativa, reduciendo los tiempos de respuesta y aumentando la satisfacción del cliente interno.

Un componente clave de la aplicación será un panel de control interactivo creado con Plotly, que proporcionará análisis detallados de estadísticas como el número de tickets abiertos, resueltos y los tiempos de resolución promedio. Este panel de control permitirá a los administradores y responsables tomar decisiones informadas mediante la visualización en tiempo real de tendencias de incidencias por departamento o área específica, facilitando así la identificación proactiva de problemas y la implementación de soluciones preventivas.

Además de la gestión de tickets, la aplicación integrará un sistema de correo electrónico interno utilizando tecnologías como Postfix, Dovecot y Roundcube. Esto mejorará significativamente la comunicación entre los equipos dentro de la organización, facilitando el intercambio rápido de información crucial para la resolución efectiva de incidencias y la colaboración entre departamentos.

Desde el punto de vista de la infraestructura, tanto la aplicación Django como el servidor de correos se desplegarán en un entorno Linux. Esto garantizará la estabilidad y seguridad necesarias para operaciones críticas. Para la gestión centralizada de usuarios, se utilizará un servidor Windows Server con Active Directory (AD), aprovechando LDAP para la sincronización automática de credenciales entre el AD y la aplicación Django. Esta integración asegurará un acceso seguro y eficiente a la plataforma, simplificando la administración de usuarios y manteniendo la coherencia en los permisos de acceso.

En resumen, el proyecto tiene como resultado esperado la implementación de una solución integral que no solo optimice la gestión de incidencias y la comunicación interna, sino que también promueva una cultura organizacional más colaborativa y eficiente. Al proporcionar herramientas avanzadas para la toma de decisiones basadas en datos y mejorar la eficiencia operativa, la aplicación contribuirá directamente a la mejora continua y al éxito a largo plazo de la organización.


## Instalación

Para instalar la aplicación de Tickets se debe descargar los archivos que encontramos en este repositorio y una vez llevado a cabo debemos de instalar los distintos módulos.

```bash
  pip3 install -r requeriments.txt
```

Deberá de disponer de un servidor de Nginx y previamente uWSGI configurado (toda la documentación en la memoria). Movemos el proyecto a la ruta deseada y le damos permisos al usuario www-data.

Para no tener que hacer uso de la base de datos MySQL solamente debe cambiar la configuración en settings.py:

```bash
DATABASES = {
'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

Una vez hecho estos pasos simplemente reiniciar los servicios y acceder a través de la dirección asignada.

Para más información como la configuración del servidor de correo o Active Directory consultar la memoria de proytecto.
## Authors

- [@albertomave](https://www.github.com/thorrik24)

