from django.shortcuts import render

from .models import *

def index(request):

    return render(request, 'index.html')


def criar_professor(request):


    return render(request, 'professor/criar_professor.html')

def lista_professor(request):
    professores = Professor.objects.all()


    context = {
        'professores': professores
    }
    return render(request, 'professor/lista_professor.html', context)