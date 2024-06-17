from django.urls import path
from .views import *

urlpatterns = [
    # FUNCIONES
    path('informacion/obtener_subcategorias/', obtener_subcategorias, name='informacion_subcategorias'),
    # PERFILES
    path('perfil/<slug:username>', Perfiles.as_view(), name='perfiles'),

    #TRABAJADOR
    path('trabajador/', ListadoTrabajador.as_view(), name='listado_ticket_trabajador'),
    path('crear-ticket/', CrearTicket.as_view(), name='crear_ticket'),
    path('crear-ticket/confirmar/<int:pk>', ConfirmacionTicket.as_view(), name='confirmar_ticket'),
    path('eliminar-ticket/<int:pk>', EliminarTicket.as_view(), name='eliminar_ticket'),

    # VISTA DE TECNICOS
    path('tecnico/', ListadoTecnico.as_view(), name='listado_ticket_tecnico'),
    path('ticket/<int:pk>', DetalleTicket.as_view(), name='detalle_ticket_tecnico'),
    path('ticket/escalar/<int:pk>', EscalarTicket.as_view(), name='escalar_ticket_tecnico'),
    path('ticket/registro-cambios/<int:pk>', RegistroCambios.as_view(), name='registro_ticket_tecnico'),
    path('ticket/archivos/<int:pk>', ArchivosTicket.as_view(), name='archivos_ticket_tecnico'),
    path('tickets/', HistorialTicket.as_view(), name='historial_ticket'),
    path('ticket/cerrar/<int:pk>', CerrarTicket.as_view(), name='cerrar_ticket'),
    path('ticket/archivos/eliminar/<int:pk>', EliminarArchivo.as_view(), name='eliminar_archivo_ticket'),
    path('informacion/tecnicos/', InformacionTecnicos.as_view(), name='informacion_tecnicos'),
    # DOCUMENTOS
    path('manuales/', Documentos.as_view(), name='documentos'),
    path('manuales/subir/', SubirDocumentos.as_view(), name='subir_documentos'),

    #LISTADO ADMINISTRADORES
    path('administrador/', ListadoAdministrador.as_view(), name='listado_ticket_administrador'),
    path('manuales/gestion/', GestionarDocumentos.as_view(), name='gestionar_documentos'),
    path('tickets/gestion/', AdministrarTickets.as_view(), name='gestionar_tickets'),
    path('tickets/gestion/eliminar/<int:pk>', EliminarTicketAdmin.as_view(), name='gestionar_ticket_eliminar'),
    # path('usuarios/gestion/', GestionarUsuarios.as_view(), name='gestionar_usuarios'),

    # Agrega más URLS (CRUD, crear, listar, actualizar, eliminar)
]
