from django.urls import path
from . import views

app_name = 'recursos_humanos'

urlpatterns = [
    path('', views.home_rh, name='home_rh'),
]
