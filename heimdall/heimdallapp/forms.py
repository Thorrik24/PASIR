from .models import *
from django.forms import *
from django.utils.translation import gettext_lazy as _
from django import forms

class FormTicket(forms.ModelForm):

    CATEGORIAS_PERMITIDAS = ['Hardware', 'Software', 'Incidencias Locales','Otro']

    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(problema__in=CATEGORIAS_PERMITIDAS),
        required=True,
        label="Categoría",
        initial=Categoria.objects.get(problema='Hardware'),  # Categoría por defecto
        widget=forms.Select(attrs={'id': 'id_categoria'})
    )

    subcategoria = forms.ModelChoiceField(
        queryset=Sub_categoria.objects.filter(categoria__problema="Hardware"),
        required=True,
        label="Subcategoría",
        initial=Sub_categoria.objects.filter(categoria__problema="Hardware")[0],
        widget=forms.Select(attrs={'id': 'id_subcategoria'})
    )

    class Meta:
        model = Ticket
        fields = ['categoria', 'subcategoria', 'descripcion']

    def __init__(self, *args, **kwargs):
        super(FormTicket, self).__init__(*args, **kwargs)
        self.fields['descripcion'].widget = forms.Textarea(attrs={'rows': 7, 'cols': 60})

        if self.instance and self.instance.pk:
            self.fields['categoria'].initial = self.instance.subcategoria.categoria
            self.fields['subcategoria'].queryset = Sub_categoria.objects.filter(categoria=self.instance.subcategoria.categoria)
            self.fields['subcategoria'].initial = self.instance.subcategoria
        if 'categoria' in self.data:
            try:
                categoria_id = int(self.data.get('categoria'))
                self.fields['subcategoria'].queryset = Sub_categoria.objects.filter(categoria_id=categoria_id)
            except (ValueError, TypeError):
                self.fields['subcategoria'].queryset = Sub_categoria.objects.none()
        elif self.instance.pk:
            self.fields['subcategoria'].queryset = Sub_categoria.objects.filter(categoria=self.instance.subcategoria.categoria)
        else:
            self.fields['subcategoria'].queryset = Sub_categoria.objects.filter(categoria__problema="Hardware")
    
class FormEscalar(forms.Form):
    tecnico = forms.ModelChoiceField(
        queryset=Trabajador.objects.filter(es_tecnico=True),
        required=True,
        label="Técnico")
    
    motivo = forms.CharField(max_length=500,required=True,
                             widget=forms.Textarea(attrs={'rows': 4, 'cols': 60}))

class FormArchivos(forms.Form):
    archivo = forms.FileField(required=True)


class FormCerrar(forms.Form):
    solucion = forms.CharField(max_length=500,required=True, label="Solución",
                             widget=forms.Textarea(attrs={'rows': 4, 'cols': 60}))
    

class FormUsuarios(forms.Form):
    CARGOS =( 
    ("Administrador", "Administrador"), 
    ("Tecnico", "Técnico"), 
    ) 
    OPERACIONES =( 
    ("Añadir", "Añadir"), 
    ("Eliminar", "Eliminar"), 
    ) 
  

    tecnico = forms.ModelChoiceField(
        queryset=Trabajador.objects.all(),
        required=True,
        label="Técnico",
        widget=forms.Select(attrs={'id': 'id_tecnico'})
    )

    cargo = forms.ChoiceField(choices = CARGOS, required=True) 

    operacion = forms.ChoiceField(choices = OPERACIONES, required=True) 
