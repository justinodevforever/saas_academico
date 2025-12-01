
from django import forms
from .models import *
from django.db.models import Q
import string, secrets

from django.shortcuts import get_list_or_404



class UsuarioForm(forms.Form):
    


    nome_completo = forms.CharField(
        required=True, 
        widget= forms.TextInput(attrs={'id': 'nome_completo', 'placeholder': 'Nome completo'})
    )

    email = forms.CharField(
        required=True,
        widget= forms.TextInput(attrs={'id': 'email', 'placeholder': 'E-mail'})
    )

    username = forms.CharField(
        required=True,
        widget= forms.TextInput(attrs={'id': 'username', 'placeholder': 'Nome do usuário'})
    )

    password = forms.CharField(
        required=True,
        widget= forms.PasswordInput(attrs={'id': 'password', 'placeholder': 'Senha'})
    )

    is_active = forms.BooleanField(
        required=False,
        widget= forms.CheckboxInput()
    )

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('instance', None)

        super().__init__(*args, **kwargs)

        if self.usuario:

            self.fields['username'].initial = self.usuario.username
            self.fields['nome_completo'].initial = self.usuario.nome_completo
            self.fields['email'].initial = self.usuario.email
            self.fields['role'].initial = self.usuario.role


    def save(self):

        if self.usuario is None:

            usuario = Utilizador(
                username = self.cleaned_data['username'],
                nome_completo = self.cleaned_data['nome_completo'],
                role = self.cleaned_data['role'],
                email = self.cleaned_data['email'],
                is_active = True,
            )

            if self.cleaned_data['role'].nome == 1:
                usuario.is_staff = True
                usuario.is_superuser = True
            
            usuario.set_password(self.cleaned_data['password'])

            usuario.save()

            return usuario
        
        else:

            self.usuario.username = self.cleaned_data['username']
            self.usuario.nome_completo = self.cleaned_data['nome_completo']
            self.usuario.role = self.cleaned_data['role']
            self.usuario.email = self.cleaned_data['email']
            self.usuario.is_active = self.cleaned_data['is_active']

            if self.cleaned_data['role'].nome == 1:

                self.usuario.is_staff = True
                self.usuario.is_superuser = True

            else:
                self.usuario.is_staff = False
                self.usuario.is_superuser = False

            
            self.usuario.save()


            return self.usuario
        

