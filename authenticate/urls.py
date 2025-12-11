from django.urls import path
from .views import *

urlpatterns = [
    path('accounts/login/', auth_user, name='login'),
    path('logout/', view_logaout, name='logout'),
]