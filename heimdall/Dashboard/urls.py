from django.urls import path
from .views import *

urlpatterns = [
    #DASHBOARD
    path('', Dash.as_view(), name='dashboard'),

]