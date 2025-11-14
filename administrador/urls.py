from django.urls import path
from .views import *



urlpatterns = [
    path('', index, name='index'),
    path('lista_professor/', lista_professor, name='lista_professor'),
    path('criar_professor/', criar_professor, name='criar_professor'),

]