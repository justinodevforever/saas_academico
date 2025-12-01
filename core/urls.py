
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('academico.urls')),
    path('', include('administrador.urls')),
    path('', include('authenticate.urls')),
    path('', include('director.urls')),
    path('', include('relatorio.urls')),
    path('', include('secretario.urls')),
]
