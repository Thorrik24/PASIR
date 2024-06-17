from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from django.db.models import Count, Min
import random

# @receiver(post_save, sender=Ticket)
# def my_handler(sender, instance, created, **kwargs):
#     if created:
#         ticket = instance

        

#         ticket.tecnico = tecnico_seleccionado
        
#         print("Técnico seleccionado:", tecnico_seleccionado)
        
        

#     else:
#         print("ticket actualizado:", instance)