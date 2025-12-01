from django.urls import path
from .views import *

urlpatterns = [
    path('accounts/login/', auth_user, name='login'),
    path('view_logaout/', view_logaout, name='view_logaout'),
]