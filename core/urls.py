
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.conf.urls import handler403, handler404
from django.shortcuts import render

def erro_403(request, exception):
    return render(request, '403.html', status=403)

def erro_404(request, exception):
    return render(request, '404.html', status=404)

urlpatterns = [

    path('admin/', admin.site.urls),
    path('', include('academico.urls')),
    path('administrator/', include('administrador.urls')),
    path('', include('authenticate.urls')),
    path('director/', include('director.urls')),
    path('', include('relatorio.urls')),
    path('', include('secretario.urls')),
    path('', include('home.urls')),
    path('', include('documentos.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler404 = erro_404
handler403 = erro_403