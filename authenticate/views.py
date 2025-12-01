from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.db.models import Q
from django.contrib import messages
from .models import Utilizador


def auth_user(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        try: 
            user_obj = Utilizador.objects.get(
                Q(username=username) |
                Q(password=password)
            )

        except Utilizador.DoesNotExist:
            messages.error(request,  "Credenciais inválidas!")
            return render(request, 'login.html', {
                'next': request.POST.get('next')
            })

        user = authenticate(request, 
            username=user_obj.username, 
            password=password
        )

        if user:
            login(request, user) 

            if remember:

                request.session.set_expiry(60 * 60 * 24 * 30)

            else:
                request.session.set_expiry(60*60) 

            next_url = request.GET.get('next') or request.POST.get('next') or '/'

            return redirect(next_url)

        else:

            messages.error(request,  "Credenciais inválidas!")
            return render(request, 'login.html', {
                'next': request.POST.get('next')
            })
    else:
        return render(request, 'login.html', {
            'next': request.GET.get('next', '/')
        })

def view_logaout(request):

    

    next_url = request.GET.get('next', '/')

    logout(request)

    return redirect(f'/accounts/login/?next={next_url}')
