from django.shortcuts import render, redirect
from academico.permissions import *
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    user = request.user
    
    if is_admin(user):
        return redirect('dashboard_admin')
    elif is_professor(user):
        return redirect('dashboard_professor')
    elif is_secretario(user):
        return redirect('dashboard_secretario')
    elif is_director(user):
        return redirect('dashboard_diretor')
    elif is_estudante(user):
   
        return redirect('estudante:dashboard_estudante')
    else:
        messages.warning(request, 'Seu perfil não tem um dashboard específico.')
        return redirect('home')