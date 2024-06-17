from typing import Any
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render,redirect
from heimdallapp.models import *
from django.views.generic import * 
from .forms import *
from django.urls import reverse_lazy
from django.db.models import Count, Min
import random
from datetime import datetime
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordChangeDoneView
from django.contrib import messages
from django.http import JsonResponse

#FUNCION SUBCATEGORIAS
def obtener_subcategorias(request):
    categoria_id = request.GET.get('categoria_id')
    subcategorias = Sub_categoria.objects.filter(categoria=categoria_id).values('id', 'subcategoria')
    return JsonResponse({'subcategorias': list(subcategorias)})

# PERFILES

class Perfiles(LoginRequiredMixin,DetailView):
    model = Trabajador
    template_name = "registration/perfil.html"
    slug_field = "username"
    slug_url_kwarg  ="username"

    def get_success_url(self):
        return reverse('heim:perfiles', kwargs={'username': self.request.user.username})

class RedirectPasswordResetDoneView(PasswordResetDoneView):
    def dispatch(self, *args, **kwargs):
        return redirect('dash:dashboard')

class RedirectPasswordChangeDoneView(PasswordChangeDoneView):
    def dispatch(self, *args, **kwargs):
        return redirect('heim:perfiles', username=self.request.user.username)
    
# PARTE TRABAJADORES

class CrearTicket(UserPassesTestMixin,CreateView):
    model = Ticket
    form_class = FormTicket
    template_name = "componentes/trabajador/crear-confirmar.html"
    success_url = reverse_lazy("heim:confirmar_ticket")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context["pagina"] = "CREAR"
        if self.request.method == 'POST' and 'categoria' in self.request.POST:
            categoria_id = int(self.request.POST.get('categoria'))
            context['form'].fields['subcategoria'].queryset = Sub_categoria.objects.filter(categoria_id=categoria_id).order_by('subcategoria')
        
        return context

    def form_valid(self, form):
        form.instance.subcategoria = form.cleaned_data['subcategoria']
        form.instance.estado = "Creado"
        form.instance.trabajador = Trabajador.objects.get(id=self.request.user.id)

        self.object = form.save()
        return HttpResponseRedirect(reverse('heim:confirmar_ticket', kwargs={'pk': self.object.pk}))
    
    def test_func(self):
        return self.request.user.is_authenticated
    
class ConfirmacionTicket(UserPassesTestMixin,UpdateView):
    model = Ticket
    form_class = FormTicket
    template_name = "componentes/trabajador/crear-confirmar.html"
    success_url = reverse_lazy("heim:listado_ticket_trabajador")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pagina"] = "CONFIRMAR"
        if self.request.method == 'POST' and 'categoria' in self.request.POST:

            categoria_id = int(self.request.POST.get('categoria'))
            context['form'].fields['subcategoria'].queryset = Sub_categoria.objects.filter(categoria_id=categoria_id).order_by('subcategoria')
        return context

    def form_valid(self, form):
        form.instance.subcategoria = form.cleaned_data['subcategoria']
        form.instance.estado = "Confirmado"

        # ASIGNAR TICKET A UN TÉCNICO

        tecnicos = Trabajador.objects.filter(Q(es_tecnico=True) & ~Q(pk=self.request.user.pk))
        
        categoria_ticket = form.instance.subcategoria.categoria.problema

        if categoria_ticket.lower() == 'hardware':
            empresa_ticket = form.instance.trabajador.empresa
            tecnicos = tecnicos.filter(empresa=empresa_ticket)

        if categoria_ticket.lower() == "incidencias locales":
            tecnicos = Trabajador.objects.filter(is_superuser=True)

        cantidad_minima = tecnicos.annotate(num_tickets=Count('tecnico__tecnico', filter=~Q(tecnico__estado='Resuelto'))).aggregate(min_tickets=Min('num_tickets'))['min_tickets']

        tecnicos_con_min_tickets = tecnicos.annotate(num_tickets=Count('tecnico__tecnico', filter=~Q(tecnico__estado='Resuelto'))).filter(num_tickets=cantidad_minima)

        tecnico_seleccionado = random.choice(tecnicos_con_min_tickets)

        form.instance.tecnico = tecnico_seleccionado

        return super().form_valid(form)

    def test_func(self):
        ticket = self.get_object()
        return self.request.user.is_authenticated and ticket.trabajador.id == self.request.user.id and ticket.estado == "Creado"

class ListadoTrabajador(UserPassesTestMixin,TemplateView):
    template_name = "componentes/trabajador/ticket_list_trabajador.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["tickets"] = Ticket.objects.filter(trabajador=Trabajador.objects.get(id=self.request.user.id))[::-1]
        return context

    def test_func(self):
        return self.request.user.is_authenticated

class EliminarTicket(UserPassesTestMixin,DeleteView):
    model = Ticket
    template_name = "componentes/trabajador/ticket_eliminar.html"
    success_url = reverse_lazy("heim:listado_ticket_trabajador")

    def test_func(self):
        ticket = self.get_object()
        return self.request.user.is_authenticated and ticket.trabajador.id == self.request.user.id
    
# PARTE DE TÉCNICOS

class HistorialTicket(UserPassesTestMixin,ListView):
    model = Ticket
    template_name = "componentes/tecnico/busqueda.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["categorias"] = Categoria.objects.all()
        context["subcategorias"] = Sub_categoria.objects.all()
        context["prioridades"] = Sub_categoria.objects.values('prioridad').distinct()
        context["tecnicos"] = Trabajador.objects.filter(es_tecnico=True)
        return context
    

    def get_queryset(self) -> QuerySet[Any]:
        descripcion = self.request.GET.get("q")
        categoria = self.request.GET.get("cat")
        subcategoria = self.request.GET.get("subcat")
        prioridad = self.request.GET.get("prior")
        tecnico = self.request.GET.get("tec")
        estado = self.request.GET.get("est")
        queryset = Ticket.objects.all()

        if descripcion:
            queryset = queryset.filter(descripcion__icontains=descripcion)

        if categoria and categoria != "All":
            queryset = queryset.filter(subcategoria__categoria__problema=categoria)

        if subcategoria and subcategoria != "All":
            queryset = queryset.filter(subcategoria__subcategoria=subcategoria)

        if prioridad and prioridad != "All":
            queryset = queryset.filter(subcategoria__prioridad=prioridad)

        if tecnico and tecnico != "All":
            queryset = queryset.filter(tecnico=tecnico)

        if estado and estado != "All":
            queryset = queryset.filter(estado=estado)

        return queryset[::-1]
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.es_tecnico or self.request.user.is_superuser)
    
class ListadoTecnico(UserPassesTestMixin,TemplateView):
    template_name = "componentes/tecnico/ticket_list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["tickets"] = Ticket.objects.filter(tecnico=Trabajador.objects.get(id=self.request.user.id))[::-1]
        context["administrador"] = False
        return context
    
    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        # CAMBIAR EL ESTADO DEL TICKET
        ticket = Ticket.objects.get(id=int(request.POST["id"]))
        ticket.estado = "Aceptado"
        ticket.save()

        # AÑADIR EL USUARIO AL HISTORICO
        Historial.objects.create(
            ticket = ticket,
            tecnico = Trabajador.objects.get(id=request.user.id),
            operacion = "Aceptado"
        )

        return HttpResponseRedirect(reverse_lazy("heim:listado_ticket_tecnico"))
    
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.es_tecnico or self.request.user.is_superuser)
    
class DetalleTicket(UserPassesTestMixin,DetailView):
    model = Ticket
    template_name = "componentes/tecnico/ticket_detalle.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["aceptar"] = True 
        context["documentos"] = Documento.objects.filter(subcategoria=self.get_object().subcategoria)
        return context
    
    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        # CAMBIAR EL ESTADO DEL TICKET
        id_ticket = int(request.POST["id"])
        ticket = Ticket.objects.get(id=id_ticket)
        ticket.estado = "Aceptado"
        ticket.save()

        # AÑADIR EL USUARIO AL HISTORICO
        Historial.objects.create(
            ticket = ticket,
            tecnico = Trabajador.objects.get(id=request.user.id),
            operacion = "Aceptado"
        )

        return HttpResponseRedirect(reverse_lazy("heim:detalle_ticket_tecnico", kwargs={'pk': id_ticket}))
    
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.es_tecnico or self.request.user.is_superuser)
    
class EscalarTicket(UserPassesTestMixin,FormView):
    form_class = FormEscalar

    template_name = "componentes/tecnico/escalar.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["object"] = Ticket.objects.get(pk=self.request.path_info.split("/")[-1])
        return context
    
    def form_valid(self, form):
        ticket_pk = self.request.path_info.split("/")[-1]
        tk = Ticket.objects.get(pk=ticket_pk)

        # DATOS DEL TÉCNICO AL CUAL LE VAMOS A ESCALAR Y EL MOTIVO POR EL CUAL SE ESCALA
        tecnico = form.cleaned_data["tecnico"]
        motivo = form.cleaned_data["motivo"]

        Historial.objects.create(
                    ticket = tk,
                    tecnico = Trabajador.objects.get(pk=self.request.user.id),
                    operacion = "Escalado",
                    descripcion = motivo,
                    escalado_a = Trabajador.objects.get(username=tecnico)
                )
        
        # ASIGNAR EL TICKET AL NUEVO TECNICO Y CAMBIAR EL ESTADO
        tk.tecnico = tecnico
        tk.estado = "Escalado"
        tk.save()

        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('heim:detalle_ticket_tecnico', kwargs={'pk': self.request.path_info.split("/")[-1]})
    
    def test_func(self):
        ticket = self.get_context_data()["object"]
        return self.request.user.is_authenticated and ticket.tecnico.id == self.request.user.id and self.get_context_data()["object"].estado == "Aceptado"
    
class RegistroCambios(UserPassesTestMixin,TemplateView):
    
    template_name = "componentes/tecnico/ticket_registro.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        tk = Ticket.objects.get(pk=self.request.path_info.split("/")[-1])
        context["object"] = tk
        context["historial"] = Historial.objects.filter(ticket=tk)

        return context
    
    def test_func(self) -> bool | None:
        ticket = self.get_context_data()["object"]
        return self.request.user.is_authenticated and (self.request.user.es_tecnico or self.request.user.is_superuser)
    
class ArchivosTicket(UserPassesTestMixin,FormView):
    form_class = FormArchivos
    template_name = "componentes/tecnico/archivos_ticket.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tk = Ticket.objects.get(pk=self.request.path_info.split("/")[-1])
        context["object"] = tk
        context["archivos"] = Archivo.objects.filter(ticket=tk)
        return context
    
    def form_valid(self, form):
        archivo = form.cleaned_data["archivo"]
        archivo_nombre = archivo.name
        archivo_formato = archivo_nombre.split(".")[::-1][0]
        
        extensiones_permitidas = ["png","jpg","jpeg","mp4","mov","avi","pdf"]

        if self.get_context_data()["object"].estado == "Resuelto":
            mensaje = f"ERROR: El Ticket se encuentra en el estado 'Resuelto', no es posible realizar modificaciones sobre este."
            return render(self.request,'componentes/tecnico/archivos_ticket.html', {"mensaje":mensaje,
                                                                                    "object":Ticket.objects.get(pk=self.request.path_info.split("/")[-1]),
                                                                                    "form":form,
                                                                                    "archivos": Archivo.objects.filter(ticket=Ticket.objects.get(pk=self.request.path_info.split("/")[-1]))
                                                                                    })
        elif self.request.user.id  == self.get_context_data()["object"].tecnico.id:
            if archivo_formato in extensiones_permitidas:
                ruta_guardado = default_storage.save(f"{self.request.path_info.split('/')[-1]}/{archivo_nombre}", ContentFile(archivo.read()))

                Archivo.objects.create(
                    tecnico = Trabajador.objects.get(pk=self.request.user.id),
                    ticket = Ticket.objects.get(pk=self.request.path_info.split("/")[-1]),
                    archivo = ruta_guardado
                )

            else:

                mensaje = f"ERROR: La extensión '{archivo_formato}' no está permitida, debes de usar una de las siguientes: " + ", ".join(extensiones_permitidas)
                return render(self.request,'componentes/tecnico/archivos_ticket.html', {"mensaje":mensaje,
                                                                                    "object":Ticket.objects.get(pk=self.request.path_info.split("/")[-1]),
                                                                                    "form":form
                                                                                    })
                
        else:
            mensaje = f"ERROR: El Técnico asociado al ticket es {self.get_context_data()['object'].tecnico}."
            return render(self.request,'componentes/tecnico/archivos_ticket.html', {"mensaje":mensaje,
                                                                                    "object":Ticket.objects.get(pk=self.request.path_info.split("/")[-1]),
                                                                                    "form":form
                                                                                    })
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('heim:archivos_ticket_tecnico', kwargs={'pk': self.request.path_info.split("/")[-1]})
    
    def test_func(self) -> bool | None:
        return self.request.user.is_authenticated and (self.request.user.es_tecnico or self.request.user.is_superuser)

class CerrarTicket(UserPassesTestMixin,FormView):
    form_class = FormCerrar
    template_name = "componentes/tecnico/cerrar.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["object"] = Ticket.objects.get(pk=self.request.path_info.split("/")[-1])
        return context
    
    def form_valid(self, form: Any) -> HttpResponse:

        ticket_pk = self.request.path_info.split("/")[-1]
        tk = Ticket.objects.get(pk=ticket_pk)
        tecnico = tk.tecnico

        solucion = form.cleaned_data["solucion"]

        Historial.objects.create(
                    ticket = tk,
                    tecnico = tecnico,
                    operacion = "Resuelto",
                    descripcion = solucion
                )
        
        tk.estado = "Resuelto"
        tk.fecha_resolucion = datetime.now()

        tk.save()
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('heim:detalle_ticket_tecnico', kwargs={'pk': self.request.path_info.split("/")[-1]})
    
    def test_func(self):
        ticket = self.get_context_data()["object"]
        return self.request.user.is_authenticated and self.request.user.id == ticket.tecnico.id and self.get_context_data()["object"].estado == "Aceptado" and self.get_context_data()["object"].estado != 'Resuelto'

class EliminarArchivo(UserPassesTestMixin,DeleteView):
    model = Archivo
    template_name = "componentes/tecnico/eliminar_archivo.html"
    
    def get_success_url(self) -> str:
        return reverse('heim:archivos_ticket_tecnico', kwargs={'pk': self.get_object().ticket.id})
    
    def test_func(self):
        archivo = self.get_object()
        return self.request.user.is_authenticated and self.request.user.id == archivo.tecnico.id and archivo.ticket.estado != 'Resuelto'

class InformacionTecnicos(UserPassesTestMixin,ListView):
    model = Trabajador
    template_name = "componentes/tecnico/listado_tecnicos.html"

    def get_queryset(self) -> QuerySet[Any]:
        return Trabajador.objects.filter(Q(es_tecnico=True) | Q(es_administrador=True) | Q(is_superuser=True))
    
    def test_func(self) -> bool | None:
        return self.request.user.es_tecnico or self.request.user.es_administrador or self.request.user.is_superuser
# DOCUMENTOS

class Documentos(UserPassesTestMixin,ListView):
    model = Documento
    template_name = "componentes/tecnico/listado_documentos.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["categorias"] = Categoria.objects.all()
        context["subcategorias"] = Sub_categoria.objects.all()

        mensaje = messages.get_messages(self.request)
        for message in mensaje:
            context["mensaje"] = message.message
            break

        return context
    
    def get_queryset(self) -> QuerySet[Any]:

        categoria = self.request.GET.get("cat")
        subcategoria = self.request.GET.get("subcat")
        queryset = Documento.objects.all()

        if categoria and categoria != "All":
            queryset = queryset.filter(subcategoria__categoria__problema=categoria)

        if subcategoria and subcategoria != "All":
            queryset = queryset.filter(subcategoria__subcategoria=subcategoria)

        return queryset[::-1]

    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.es_tecnico or self.request.user.es_administrador or self.request.user.is_superuser)
    
class SubirDocumentos(UserPassesTestMixin,CreateView):
    model = Documento
    template_name = "componentes/tecnico/subir_documento.html"
    fields = ["archivo","subcategoria","descripcion"]

    def form_valid(self, form):
        archivo = form.cleaned_data["archivo"]
        archivo_nombre = archivo.name
        archivo_formato = archivo_nombre.split(".")[::-1][0]
        
        extensiones_permitidas = ["pdf"]

        if archivo_formato not in extensiones_permitidas:
            mensaje = f"ERROR: La extensión '{archivo_formato}' no está permitida, debes de usar una de las siguientes: " + ", ".join(extensiones_permitidas)
            
            return render(self.request,"componentes/tecnico/subir_documento.html", {"mensaje":mensaje,
                                                                                    "form":form})
        else:

            form.instance.tecnico = Trabajador.objects.get(pk=self.request.user.pk)
            form.instance.estado = "Creado"
            form.save()

            mensaje = f"COMPLETADO: Su documento se ha enviado, estará a la espera de que un administrador lo acepte."
            messages.success(self.request, mensaje)

            if self.request.user.es_administrador or self.request.user.is_superuser:
                 return redirect('heim:gestionar_documentos')
            else:
                return redirect('heim:documentos')
            

    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.es_tecnico or self.request.user.es_administrador or self.request.user.is_superuser)

# PARTE ADMINISTRADORES y ADMINISTRADOR JEFE

class GestionarDocumentos(UserPassesTestMixin,ListView):
    model = Documento
    template_name = "componentes/tecnico/gestion_documentos.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["object"] = Documento.objects.all()
        context["categorias"] = Categoria.objects.all()
        context["subcategorias"] = Sub_categoria.objects.all()
        return context
    
    def get_queryset(self) -> QuerySet[Any]:
        categoria = self.request.GET.get("cat")
        subcategoria = self.request.GET.get("subcat")
        queryset = Documento.objects.all()

        if categoria and categoria != "All":
            queryset = queryset.filter(subcategoria__categoria__problema=categoria)

        if subcategoria and subcategoria != "All":
            queryset = queryset.filter(subcategoria__subcategoria=subcategoria)

        return queryset[::-1]
    
    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        # CAMBIAR EL ESTADO DEL TICKET
        if "id_aceptar" in request.POST:
            documento = Documento.objects.get(id=int(request.POST["id_aceptar"]))
            documento.estado = "Aceptado"
            documento.aceptado_por = Trabajador.objects.get(pk=self.request.user.pk)
            documento.save()
        elif "id_rechazar" in request.POST:
            documento = Documento.objects.get(id=int(request.POST["id_rechazar"]))
            documento.delete()

        return HttpResponseRedirect(reverse_lazy("heim:gestionar_documentos"))

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.es_administrador

class ListadoAdministrador(UserPassesTestMixin,ListView):
    model = Ticket
    template_name = "componentes/tecnico/ticket_list_admin.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["administrador"] = True
        context["categorias"] = Categoria.objects.all()
        context["subcategorias"] = Sub_categoria.objects.all()
        context["prioridades"] = Sub_categoria.objects.values('prioridad').distinct()
        context["tecnicos"] = Trabajador.objects.filter(es_tecnico=True)
        return context
    
    def get_queryset(self) -> QuerySet[Any]:
        descripcion = self.request.GET.get("q")
        categoria = self.request.GET.get("cat")
        subcategoria = self.request.GET.get("subcat")
        prioridad = self.request.GET.get("prior")
        tecnico = self.request.GET.get("tec")
        estado = self.request.GET.get("est")
        queryset = Ticket.objects.filter(trabajador__empresa=self.request.user.empresa)

        if descripcion:
            queryset = queryset.filter(descripcion__icontains=descripcion)

        if categoria and categoria != "All":
            queryset = queryset.filter(subcategoria__categoria__problema=categoria)

        if subcategoria and subcategoria != "All":
            queryset = queryset.filter(subcategoria__subcategoria=subcategoria)

        if prioridad and prioridad != "All":
            queryset = queryset.filter(subcategoria__prioridad=prioridad)

        if tecnico and tecnico != "All":
            queryset = queryset.filter(tecnico=tecnico)

        if estado and estado != "All":
            queryset = queryset.filter(estado=estado)

        return queryset[::-1]
    
    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        # CAMBIAR EL ESTADO DEL TICKET
        ticket = Ticket.objects.get(id=int(request.POST["id"]))
        ticket.estado = "Aceptado"
        ticket.save()

        # AÑADIR EL USUARIO AL HISTORICO
        Historial.objects.create(
            ticket = ticket,
            tecnico = Trabajador.objects.get(id=request.user.id),
            operacion = "Aceptado"
        )

        return HttpResponseRedirect(reverse_lazy("heim:listado_ticket_administrador"))
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.es_administrador
  
class AdministrarTickets(UserPassesTestMixin, ListView):
    model = Ticket
    template_name = "componentes/tecnico/gestion_tickets.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["empresas"] = Trabajador.objects.values('empresa').distinct()
        context["categorias"] = Categoria.objects.all()
        context["subcategorias"] = Sub_categoria.objects.all()
        context["prioridades"] = Sub_categoria.objects.values('prioridad').distinct()
        context["tecnicos"] = Trabajador.objects.filter(es_tecnico=True)
        return context
    
    def get_queryset(self) -> QuerySet[Any]:
        empresa = self.request.GET.get("empr")
        categoria = self.request.GET.get("cat")
        subcategoria = self.request.GET.get("subcat")
        prioridad = self.request.GET.get("prior")
        tecnico = self.request.GET.get("tec")
        estado = self.request.GET.get("est")
        queryset = Ticket.objects.filter(~Q(estado="Resuelto"))

        if empresa and empresa != "All":
            queryset = queryset.filter(trabajador__empresa=empresa)

        if categoria and categoria != "All":
            queryset = queryset.filter(subcategoria__categoria__problema=categoria)

        if subcategoria and subcategoria != "All":
            queryset = queryset.filter(subcategoria__subcategoria=subcategoria)

        if prioridad and prioridad != "All":
            queryset = queryset.filter(subcategoria__prioridad=prioridad)

        if tecnico and tecnico != "All":
            queryset = queryset.filter(tecnico=tecnico)

        if estado and estado != "All":
            queryset = queryset.filter(estado=estado)

        return queryset[::-1]
    
    def test_func(self) -> bool | None:
        return self.request.user.is_authenticated and self.request.user.is_superuser
    
class EliminarTicketAdmin(UserPassesTestMixin,DeleteView):
    model = Ticket
    template_name = "componentes/tecnico/eliminar_ticket.html"
    
    def get_success_url(self) -> str:
        if self.request.user.is_superuser:
            return reverse('heim:gestionar_tickets')
        elif self.request.user.es_administrador:
            return reverse('heim:listado_ticket_administrador')
    
    def test_func(self):
        return self.request.user.is_superuser or (self.request.user.empresa == self.get_object().trabajador.empresa and self.request.user.es_administrador)

# class GestionarUsuarios(UserPassesTestMixin,FormView):
#     form_class = FormUsuarios
#     template_name = "componentes/tecnico/gestion_usuarios.html"
#     reverse_lazy("heim:gestionar_usuarios")
#     def form_valid(self, form: Any) -> HttpResponse:

#         tecnico = form.cleaned_data["tecnico"]
#         cargo = form.cleaned_data["cargo"]
#         operacion = form.cleaned_data["operacion"]
#         if operacion == "Añadir":
#             mensaje = f"INFO: Se ha asignado el usuario {tecnico} al cargo {cargo}"
#             if cargo == "Administrador":
#                 tecnico.es_administrador = True
#                 tecnico.es_tecnico = True

#             elif cargo == "Tecnico":
#                 tecnico.es_tecnico = True
                
#         elif operacion == "Eliminar":
#             mensaje = f"INFO: Se ha eliminado a {tecnico} del cargo {cargo}"
#             if cargo == "Administrador":
#                 tecnico.es_administrador = False
#             elif cargo == "Tecnico":
#                 tecnico.es_tecnico = False
#                 tecnico.es_administrador = False

#         tecnico.save()

        

#         return render(self.request,"componentes/tecnico/gestion_usuarios.html", {"mensaje":mensaje,
#                                                                                     "form":form
#                                                                                 })

#     def test_func(self):
#         return self.request.user.is_authenticated and self.request.user.is_superuser
