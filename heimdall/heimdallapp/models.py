from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.core.validators import MaxValueValidator,MinValueValidator
from django.forms import ModelChoiceField
from itertools import chain
from django.db.models.query_utils import Q
from datetime import datetime
from django.db.models import signals
from django.db.models.signals import *
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.auth.signals import user_logged_in
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings
import os
from django.core.mail import EmailMessage
import subprocess

class Trabajador(AbstractUser):
    es_tecnico = models.BooleanField(default=False, null=False, blank=False)
    es_administrador = models.BooleanField(default=False, null=False, blank=False)
    telefono = PhoneNumberField(null=True, blank=True, unique=True)

    type_emp = [("SOLTECK", "SOLTECK"), ("CYBERWAVE", "CYBERWAVE"), ("CORERIFT", "CORERIFT"), ("EMERALSOLUTIONS", "EMERALSOLUTIONS")]
    empresa = models.CharField(max_length=20, choices=type_emp)

    def __str__(self):
        return self.username

class Categoria(models.Model):
    problema = models.CharField(max_length=50)

    def __str__(self):
        return self.problema

class Sub_categoria(models.Model):

    class Prioridades(models.TextChoices):
        BAJA = "Baja", _("Baja")
        MEDIA = "Media", _("Media")
        ALTA =  "Alta", _("Alta")

    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    subcategoria = models.CharField(max_length=50, blank=False, null=False)
    prioridad = models.CharField(max_length=50, choices=Prioridades.choices, default=Prioridades.BAJA)
    def __str__(self):
        return self.subcategoria

class Ticket(models.Model):

    trabajador = models.ForeignKey(Trabajador,related_name="trabajador", on_delete=models.DO_NOTHING)
    tecnico =  models.ForeignKey(Trabajador,related_name="tecnico", on_delete=models.DO_NOTHING, blank=True, null=True)

    subcategoria = models.ForeignKey(Sub_categoria, on_delete=models.DO_NOTHING)
    
    class Estados(models.TextChoices):
        CREADO = "Creado", _("Creado")
        CONFIRMADO = "Confirmado", _("Confirmado")
        ACEPTADO = "Aceptado", _("Aceptado")
        ESCALADO = "Escalado", _("Escalado")
        RESUELTO =  "Resuelto", _("Resuelto")

    descripcion = models.CharField(max_length=500, blank=False, null=False)
    fecha = models.DateTimeField(default=datetime.now()) # LA FECHA SE INTRODUCE DE FORMA AUTOMÁTICA - ES EQUIVALENTE A LA FECHA DE CREACIÓN DEL TICKET
    estado = models.CharField(max_length=20, choices=Estados.choices, default=Estados.CREADO)
    
    fecha_resolucion = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return f"{self.trabajador} - {self.subcategoria} - {self.estado}"

class Archivo(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    tecnico = models.ForeignKey(Trabajador, on_delete=models.DO_NOTHING)

    archivo = models.FileField(blank=False, null=False, upload_to="archivos_tickets/")
    
    def __str__(self):
        return f"{self.ticket} - {self.tecnico} - {self.archivo}"

class Historial(models.Model):

    class Operaciones(models.TextChoices):
            ACEPTADO = "Aceptado", _("Aceptado")
            ESCALADO = "Escalado", _("Escalado")
            RESUELTO =  "Resuelto", _("Resuelto")

    tecnico = models.ForeignKey(Trabajador, on_delete=models.DO_NOTHING)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)

    descripcion = models.CharField(max_length=500, null=False, blank=False)
    operacion = models.CharField(max_length=20, choices=Operaciones.choices)
    escalado_a = models.ForeignKey(Trabajador, related_name="escalado", on_delete=models.DO_NOTHING, blank=True, null=True)
    fecha_operacion = models.DateTimeField(default=datetime.now())

    def __str__(self):
        return f"{self.tecnico} - {self.ticket.id} - {self.operacion}"

# DOCUMENTOS

class Documento(models.Model):
    
    class Estados(models.TextChoices):
        CREADO = "Creado", _("Creado")
        ACEPTADO = "Aceptado", _("Aceptado")
        RECHAZADO = "Rechazado", _("Rechazado")

    tecnico = models.ForeignKey(Trabajador, on_delete=models.DO_NOTHING)
    aceptado_por = models.ForeignKey(Trabajador, related_name="amdinistrador",on_delete=models.DO_NOTHING, blank=True,null=True)

    archivo = models.FileField(blank=False, null=False, upload_to="documentos/")
    estado = models.CharField(max_length=20, choices=Estados.choices, default=Estados.CREADO)
    descripcion = models.CharField(max_length=500, blank=False, null=False)
    fecha_publicacion = models.DateTimeField(default=datetime.now())

    subcategoria = models.ForeignKey(Sub_categoria, on_delete=models.DO_NOTHING)

    def __str__(self) -> str:
        return f"{self.archivo} - {self.estado}" 

@receiver(post_save, sender=Ticket)
def enviar_correo(sender, instance, created, **kwargs):
    if instance.estado == 'Creado':
        with open(f"{settings.BASE_CORREOS_TEMPLATE}ticket_creado.txt",  "r") as fichero:
            mensaje = fichero.read()

        enlace = f"https://heimdall.dendorgames.es/crear-ticket/confirmar/{instance.id}"
        mensaje_formateado = mensaje.format(
            usuario_nombre=instance.trabajador.first_name,
            ticket_id=instance.id,
            enlace=enlace
        )

        send_mail(f"Ticket '{instance.id}' Creado - A la Espera de Su Confirmación",
                    mensaje_formateado, 
                    'heimdall@dendorgames.es',
                    [instance.trabajador.email], fail_silently=False)

    elif instance.estado == 'Confirmado':
        with open(f"{settings.BASE_CORREOS_TEMPLATE}ticket_confirmado.txt", "r") as fichero:
            mensaje = fichero.read()

        mensaje_formateado = mensaje.format(
            usuario_nombre=instance.trabajador.first_name,
            ticket_id=instance.id
        )
        
        send_mail(
            f"Ticket '{instance.id}' Confirmado - A la Espera de Asignación",
            mensaje_formateado, 
            'heimdall@dendorgames.es',
            [instance.trabajador.email], 
            fail_silently=False
        )

    elif instance.estado == 'Resuelto':
        with open(f"{settings.BASE_CORREOS_TEMPLATE}ticket_resuelto.txt", "r") as fichero:
             mensaje = fichero.read()

        mensaje_formateado = mensaje.format(
            usuario_nombre=instance.trabajador.first_name,
            ticket_id=instance.id
        )
        
        send_mail(
            f"Ticket '{instance.id}' Resuelto",
            mensaje_formateado, 
            'heimdall@dendorgames.es',
            [instance.trabajador.email], 
            fail_silently=False
        )
@receiver(post_save, sender=Documento)
def enviar_correo_documento(sender, instance, created, **kwargs):
    if instance.estado == "Creado":
        with open(f"{settings.BASE_CORREOS_TEMPLATE}documento_creado.txt",  "r") as fichero:
            mensaje = fichero.read()

        archivo = str(instance.archivo).split("/")[-1]
        mensaje_formateado = mensaje.format(
                            tecnico_nombre=instance.tecnico.first_name,
                            archivo=archivo
                        )
        send_mail(f"Documento '{archivo}' Creado - Revisión Requerida",mensaje_formateado, 'heimdall@dendorgames.es', [instance.tecnico.email], fail_silently=False)
    elif instance.estado == "Aceptado":
        with open(f"{settings.BASE_CORREOS_TEMPLATE}documento_aceptado.txt",  "r") as fichero:
            mensaje = fichero.read()

        archivo = str(instance.archivo).split("/")[-1]
        mensaje_formateado = mensaje.format(
                            tecnico_nombre=instance.tecnico.first_name,
                            archivo=archivo
                        )
        send_mail(f"Documento '{archivo}' Aceptado",mensaje_formateado, 'heimdall@dendorgames.es', [instance.tecnico.email], fail_silently=False)

@receiver(pre_delete, sender=Ticket)
def eliminar_archivos_ticket(sender, instance, **kwargs):
    archivos = Archivo.objects.filter(ticket__pk=instance.pk)
    for archivo in archivos:
        archivo_path = os.path.join(settings.MEDIA_ROOT, archivo.archivo.name)
        try:
            os.remove(archivo_path)
            print(f"Archivo {archivo_path} eliminado exitosamente.")
        except OSError as e:
            print(f"Error al eliminar el archivo {archivo_path}: {e}")

@receiver(post_delete, sender=Documento)
def enviar_correo_eliminacion_documento(sender, instance, **kwargs):
    if instance.estado == "Aceptado":
        with open(f"{settings.BASE_CORREOS_TEMPLATE}documento_retirado.txt", "r") as fichero:
            mensaje = fichero.read()
        
        archivo = str(instance.archivo).split("/")[-1]
        mensaje_formateado = mensaje.format(
            tecnico_nombre=instance.tecnico.first_name,
            archivo=archivo
        )
        archivo_path = os.path.join(settings.MEDIA_ROOT, instance.archivo.name)
        email = EmailMessage(
                f"Documento '{instance.archivo.name}' Retirado",
                mensaje_formateado,
                'heimdall@dendorgames.es',
                [instance.tecnico.email],
            )
        email.attach_file(archivo_path)
        email.send(fail_silently=False)

        try:
                os.remove(archivo_path)
                print(f"Archivo {archivo_path} eliminado exitosamente.")
        except OSError as e:
                print(f"Error al eliminar el archivo {archivo_path}: {e}")

    elif instance.estado == "Creado":
        with open(f"{settings.BASE_CORREOS_TEMPLATE}documento_rechazado.txt", "r") as fichero:
            mensaje = fichero.read()

        archivo = str(instance.archivo).split("/")[-1]
        mensaje_formateado = mensaje.format(
            tecnico_nombre=instance.tecnico.first_name,
            archivo=archivo
        )
        archivo_path = os.path.join(settings.MEDIA_ROOT, instance.archivo.name)

        if os.path.exists(archivo_path):
            email = EmailMessage(
                f"Documento '{instance.archivo.name}' Rechazado",
                mensaje_formateado,
                'heimdall@dendorgames.es',
                [instance.tecnico.email],
            )
            email.attach_file(archivo_path)
            email.send(fail_silently=False)

            try:
                os.remove(archivo_path)
                print(f"Archivo {archivo_path} eliminado exitosamente.")
            except OSError as e:
                print(f"Error al eliminar el archivo {archivo_path}: {e}")

@receiver(user_logged_in)
def update_passwords(sender,user,request,**kwargs):
	try:
		subprocess.run(['sudo','useradd','-m','-s','/bin/bash', user.username], check=True)

	except subprocess.CalledProcessError as e:
		print(e)

	try:
		subprocess.run(['sudo','passwd',user.username],input=f"{request.POST.get('password')}\n{request.POST.get('password')}\n", text=True, check=True)

	except subprocess.CalledProcessError as e:
                print(e)

@receiver(post_save, sender=Trabajador)
def populate_user_company(sender, instance, **kwargs):
    if hasattr(instance, 'ldap_user'):
        dn = instance.ldap_user.dn
        ou = dn.split(",")[1]
        empresa = ou.split("=")[-1]
        if instance.empresa != empresa.upper():
            instance.empresa = empresa.upper()
            instance.save(update_fields=['empresa'])
