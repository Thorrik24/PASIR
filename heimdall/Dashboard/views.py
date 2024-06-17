from django.shortcuts import render
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from heimdallapp.models import *
import pandas as pd
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import *
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
# Create your views here.

#TICKETS CONFIRMADOS
#TICKETS RESUELTOS
#TIEMPO DE RESOLUCIÓN DE UN TICKET
#TOP CREADOR DE TICKETS
class Dash(UserPassesTestMixin, TemplateView):
    template_name = "componentes/dashboard/dashboard.html"
    no_permission_template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
            
        # GRÁFICOS TARJETA
        context['cantidad_tickets'] = Ticket.objects.filter(~Q(estado='Creado')).count()
        context['cantidad_tickets_resueltos'] = Ticket.objects.filter(estado='Resuelto').count()
        context['cantidad_tickets_no_resueltos'] = Ticket.objects.filter(~Q(estado='Resuelto') & ~Q(estado='Creado')).count()
        context['cantidad_tickets_sin_confirmar'] = Ticket.objects.filter(estado='Creado').count()

        # FILTROS
        rango1 = self.request.GET.get('rango1')
        rango2 = self.request.GET.get('rango2')
        if rango1 and rango2:
            rango1 = datetime.strptime(rango1, '%Y-%m-%dT%H:%M')
            rango2 = datetime.strptime(rango2, '%Y-%m-%dT%H:%M')
            tickets_resueltos = Ticket.objects.filter(estado='Resuelto',fecha__range=(rango1,rango2))
            top_empresa = Ticket.objects.filter(~Q(estado='Creado'),fecha__range=(rango1,rango2))
        else:
            tickets_resueltos = Ticket.objects.filter(estado='Resuelto')
            top_empresa = Ticket.objects.filter(~Q(estado='Creado'))

        
        # G1 TOP EMPRESAS
        
        data_empresa = []

        for ticket in top_empresa:
            empresa = ticket.trabajador.empresa
            fecha = f"{ticket.fecha.date()} {ticket.fecha.hour}:00"
            fechas_datetime = pd.to_datetime(fecha, format='%Y-%m-%d %H:%M')
            data_empresa.append({'Empresa': empresa, 'Fecha': fechas_datetime, 'Cantidad': 1})

        df_empresa = pd.DataFrame(data_empresa)
        
        if not df_empresa.empty:
            df_empresa = df_empresa.groupby(['Empresa', 'Fecha']).size().reset_index(name='Cantidad')

            fig_line_empresa_g1 = px.line(df_empresa, x='Fecha', y='Cantidad', color='Empresa', 
                                        title='Cantidad de Tickets por Empresa a lo Largo del Tiempo',
                                        markers=True,
                                        height=400)
            
            fig_line_empresa_g1.update_layout(showlegend=True,xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True))
            fig_line_empresa_g1.update_traces(textposition='top right')
        else:
            fig_line_empresa_g1 = px.line(title='Cantidad de Tickets por Empresa a lo Largo del Tiempo',
                                        height=400)
            
            fig_line_empresa_g1.update_layout(
                xaxis_title='Fecha',
                yaxis_title='Cantidad'
            )

        context['g1'] = fig_line_empresa_g1.to_html(full_html=False, include_plotlyjs=False)

        # G2 GRÁFICA RESUELTOS
        
        conteo_por_fecha = {}

        for ticket in tickets_resueltos:
            fecha = f"{ticket.fecha.date()} {ticket.fecha.hour}:00"
            if fecha in conteo_por_fecha:
                conteo_por_fecha[fecha] += 1
            else:
                conteo_por_fecha[fecha] = 1

        fechas = list(conteo_por_fecha.keys())
        fechas_datetime = pd.to_datetime(fechas, format='%Y-%m-%d %H:%M')
        cantidades = list(conteo_por_fecha.values())
        datos_g2 = {'Fecha': fechas_datetime, 'Cantidad': cantidades}
        df_g2 = pd.DataFrame(datos_g2)
        df_g2 = df_g2.sort_values(by='Fecha')

        fig_line_g2 = make_subplots(rows=1, cols=1)

        fig_line_g2.add_trace(
            go.Scatter(
                x=df_g2["Fecha"], 
                y=df_g2["Cantidad"], 
                mode='lines+markers+text', 
                text=df_g2["Cantidad"], 
                textposition='top center',
                name="Total de Tickets Resueltos",
                line=dict(color='green'),
            )
        )

        for i in range(len(df_g2)):
            fig_line_g2.add_trace(
                go.Scatter(x=[df_g2["Fecha"][i]], y=[df_g2["Cantidad"][i]], mode='markers', marker=dict(color='#1E5313', size=10), showlegend=False)
            )
        fig_line_g2.update_layout(title='Total de Tickets Resueltos', height=400, showlegend=False,xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True))

        fig_line_g2.update_layout(
                xaxis_title='Fecha',
                yaxis_title='Cantidad'
            )

        context['g2'] = fig_line_g2.to_html(full_html=False, include_plotlyjs=False)

        # G3 TOP TÉCNICOS
        top_tecnicos = Ticket.objects.filter(estado='Resuelto')
        tecnico_conteo = {}

        for ticket in top_tecnicos:
            tecnico = ticket.tecnico.username
            if tecnico in tecnico_conteo:
                tecnico_conteo[tecnico] += 1
            else:
                tecnico_conteo[tecnico] = 1

        df_tecnicos = pd.DataFrame(list(tecnico_conteo.items()), columns=['Tecnico', 'Cantidad'])
        df_tecnicos = df_tecnicos.sort_values(by='Cantidad', ascending=True)

        max_value = df_tecnicos['Cantidad'].max()

        df_tecnicos['EsMaximo'] = df_tecnicos['Cantidad'] == max_value

        fig_bar_tecnicos_g3 = px.bar(df_tecnicos, x='Cantidad', y='Tecnico', 
                              title='Cantidad de Tickets Resueltos por Técnico', 
                              labels={'Tecnico': 'Técnico', 'Cantidad': 'Cantidad de Tickets Resueltos'},
                              height=400,
                              color='EsMaximo',
                              color_discrete_map={True: '#299513', False: 'grey'})

        fig_bar_tecnicos_g3.update_layout(showlegend=False)
        

        context['g3'] = fig_bar_tecnicos_g3.to_html(full_html=False, include_plotlyjs=False)

        # G4 TOP PROBLEMAS CAT
        top_cat = Ticket.objects.filter(~Q(estado='Creado'))
        categoria_conteo = {}

        for ticket in top_cat:
            categoria = ticket.subcategoria.categoria.problema
            if categoria in categoria_conteo:
                categoria_conteo[categoria] += 1
            else:
                categoria_conteo[categoria] = 1

        df_categorias = pd.DataFrame(list(categoria_conteo.items()), columns=['Categoria', 'Cantidad'])
        df_categorias = df_categorias.sort_values(by='Cantidad', ascending=True)

        fig_pie_prioridad_g4 = px.pie(df_categorias, values="Cantidad", names="Categoria", 
                                      title='Tipo de problemas más comunes', height=400,hover_data=["Categoria"])
        
        fig_pie_prioridad_g4.update_traces(textinfo='label+percent ', textposition='outside')
        fig_pie_prioridad_g4.update_layout(showlegend=False)
        context['g4'] = fig_pie_prioridad_g4.to_html(full_html=False, include_plotlyjs=False)

        # G5 TOP PROBLEMAS SUBCAT
        subcategoria_conteo = {}

        for ticket in top_cat:
            subcategoria = ticket.subcategoria.subcategoria
            if subcategoria in subcategoria_conteo:
                subcategoria_conteo[subcategoria] += 1
            else:
                subcategoria_conteo[subcategoria] = 1

        df_subcategorias = pd.DataFrame(list(subcategoria_conteo.items()), columns=['SubCategoria', 'Cantidad'])
        df_subcategorias = df_subcategorias.sort_values(by='Cantidad', ascending=True)

        max_value_sub = df_subcategorias['Cantidad'].max()
        df_subcategorias['EsMaximo'] = df_subcategorias['Cantidad'] == max_value_sub

        fig_bar_subcategorias_g5 = px.bar(df_subcategorias, x='Cantidad', y='SubCategoria', 
                                          title='Incidencias más repetidas', 
                                          labels={'SubCategoria': 'SubCategoria', 'Cantidad': 'Cantidad'},
                                          height=400,
                                          color='EsMaximo',
                                      color_discrete_map={True: '#299513', False: 'grey'})

        fig_bar_subcategorias_g5.update_layout(showlegend=False)
        context['g5'] = fig_bar_subcategorias_g5.to_html(full_html=False, include_plotlyjs=False)

        # G6 PRIORIDAD DE INCIDENCIAS
        prioridad_conteo = {}

        for ticket in top_cat:
            prioridad = ticket.subcategoria.prioridad
            if prioridad in prioridad_conteo:
                prioridad_conteo[prioridad] += 1
            else:
                prioridad_conteo[prioridad] = 1

        df_prioridad = pd.DataFrame(list(prioridad_conteo.items()), columns=['Prioridad', 'Cantidad'])
        df_prioridad = df_prioridad.sort_values(by='Cantidad', ascending=True)

        max_value_prior = df_prioridad['Cantidad'].max()
        df_prioridad['EsMaximo'] = df_prioridad['Cantidad'] == max_value_prior

        fig_bar_prioridad_g6 = px.bar(df_prioridad, x='Cantidad', y='Prioridad', 
                                      title='Prioridad de Incidencias', 
                                      labels={'Prioridad': 'Prioridad', 'Cantidad': 'Cantidad'},
                                      height=400,
                                      color='EsMaximo',
                                      color_discrete_map={True: '#299513', False: 'grey'})

        fig_bar_prioridad_g6.update_layout(showlegend=False)

        context['g6'] = fig_bar_prioridad_g6.to_html(full_html=False, include_plotlyjs=False)

        return context
    
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.es_tecnico or self.request.user.is_superuser)
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return render(self.request, self.no_permission_template_name)
        else:
            return redirect(reverse("login"))
