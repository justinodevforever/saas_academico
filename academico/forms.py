
from django import forms
from .models import *
from django.db.models import Q
from django.core.exceptions import ValidationError
from datetime import date

import string, secrets

from django.shortcuts import get_list_or_404

from authenticate.models import Utilizador
from .models import *

class ProfessorForm(forms.Form):

    nome_completo = forms.CharField(
        required=True,
        widget= forms.TextInput(attrs={
            'oninput': 'this.value=this.value.toUpperCase()',
            'placeholder': 'Nome completo'
        })
    )
    data_nascimento = forms.DateField(
        required=True,
        widget= forms.DateInput(attrs={'type': 'date'})
    )
    genero = forms.ChoiceField(
        choices= Professor.GENERO,
        required=True,
        widget= forms.Select()
    )
    telefone = forms.CharField(
        max_length=9,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Número de telefone'})
    )
    categoria = forms.ModelChoiceField(
        queryset= Categoria.objects.all(),
        required=True,
        widget= forms.Select()
    )
    numero_agente = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Número de agente'})
    )
    bi = forms.CharField(
        required=True,
        max_length=14,
        widget= forms.TextInput(attrs={
            'oninput': 'this.value=this.value.toUpperCase()',
            'placeholder': 'Número de B.I'
        })
    )
    especialidade = forms.CharField(
        required=True,
        max_length=100,
        widget= forms.TextInput(attrs={
            'oninput': 'this.value=this.value.toUpperCase()',
            'placeholder': 'especialidade'
        })
    )
    nivel_academico = forms.ChoiceField(
        required=True,
        choices=Professor.NIVEL_ACADEMICO,
        widget= forms.Select()
    )
    instituicao_formacao = forms.CharField(
        required=False,
        max_length=200,
        widget= forms.TextInput(attrs={
            'oninput': 'this.value=this.value.toUpperCase()',
            'placeholder': 'Instituição de formação'
        })
    )
    anos_experiencia = forms.IntegerField(
        required=False,
        widget= forms.NumberInput(attrs={
            'oninput': 'this.value=this.value.toUpperCase()',
        }),
    )
    email = forms.EmailField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'type': 'email',
            'placeholder': 'Email'
        })
    )
    endereco = forms.CharField(
        required=False,
        widget= forms.Textarea(attrs={
            'id': 'textarea',
            'oninput': 'this.value=this.value.toUpperCase()',
            'placeholder': 'Instituição de formação'
        })
    )
    tipo_contrato = forms.ChoiceField(
        required=False,
        choices=Professor.TIPO_CONTRATO,
        widget=forms.Select()
    )
    carga_horaria_semanal = forms.IntegerField(
        required=False,
        widget=forms.NumberInput()
    )
   

    def save(self):


        professor = Professor(
            nome_completo = self.cleaned_data['nome_completo'],
            categoria = self.cleaned_data['categoria'],
            telefone = self.cleaned_data['telefone'],
            genero = self.cleaned_data['genero'],
            data_nascimento = self.cleaned_data['data_nascimento'],
            numero_agente = self.cleaned_data['numero_agente'],
            bi = self.cleaned_data['bi'],
            especialidade = self.cleaned_data['especialidade'],
            nivel_academico = self.cleaned_data['nivel_academico'],
            instituicao_formacao = self.cleaned_data['instituicao_formacao'],
            anos_experiencia = self.cleaned_data['anos_experiencia'],
            email = self.cleaned_data['email'],
            endereco = self.cleaned_data['endereco'],
            tipo_contrato = self.cleaned_data['tipo_contrato'],
            carga_horaria_semanal = self.cleaned_data['carga_horaria_semanal'],
        )

        return professor
        
        
        
class ProfessorEditForm(forms.Form):

    nome_completo = forms.CharField(
        required=True,
        widget= forms.TextInput(attrs={
            'oninput': 'this.value=this.value.toUpperCase()',
            'placeholder': 'Nome completo'
        })
    )
    data_nascimento = forms.DateField(
        required=True,
        widget= forms.DateInput(attrs={'type': 'date'})
    )
    genero = forms.ChoiceField(
        choices= Professor.GENERO,
        required=True,
        widget= forms.Select()
    )
    telefone = forms.CharField(
        max_length=9,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Número de telefone'})
    )
    categoria = forms.ModelChoiceField(
        queryset= Categoria.objects.all(),
        required=True,
        widget= forms.Select()
    )
    numero_agente = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Número de agente'})
    )
    bi = forms.CharField(
        required=True,
        max_length=14,
        widget= forms.TextInput(attrs={
            'oninput': 'this.value=this.value.toUpperCase()',
            'placeholder': 'Número de B.I'
        })
    )
    especialidade = forms.CharField(
        required=True,
        max_length=100,
        widget= forms.TextInput(attrs={
            'oninput': 'this.value=this.value.toUpperCase()',
            'placeholder': 'especialidade'
        })
    )
    nivel_academico = forms.ChoiceField(
        required=True,
        choices=Professor.NIVEL_ACADEMICO,
        widget= forms.Select()
    )
    instituicao_formacao = forms.CharField(
        required=False,
        max_length=200,
        widget= forms.TextInput(attrs={
            'oninput': 'this.value=this.value.toUpperCase()',
            'placeholder': 'Instituição de formação'
        })
    )
    anos_experiencia = forms.IntegerField(
        required=False,
        widget= forms.NumberInput(attrs={
            'oninput': 'this.value=this.value.toUpperCase()',
        }),
    )
    email = forms.EmailField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'type': 'email',
            'placeholder': 'Email'
        })
    )
    endereco = forms.CharField(
        required=False,
        widget= forms.Textarea(attrs={
            'id': 'textarea',
            'oninput': 'this.value=this.value.toUpperCase()',
            'placeholder': 'Instituição de formação'
        })
    )
    tipo_contrato = forms.ChoiceField(
        required=False,
        choices=Professor.TIPO_CONTRATO,
        widget=forms.Select()
    )
    carga_horaria_semanal = forms.IntegerField(
        required=False,
        widget=forms.NumberInput()
    )

    def __init__(self, *args, **kwargs):

        self.professor = kwargs.pop('professor', None)
        super().__init__(*args, **kwargs)

        self.fields['nome_completo'].initial = self.professor.nome_completo
        self.fields['categoria'].initial = self.professor.categoria
        self.fields['telefone'].initial = self.professor.telefone
        self.fields['genero'].initial = self.professor.genero
        self.fields['data_nascimento'].initial = self.professor.data_nascimento
        self.fields['bi'].initial = self.professor.bi
        self.fields['especialidade'].initial = self.professor.especialidade
        self.fields['nivel_academico'].initial = self.professor.nivel_academico
        self.fields['instituicao_formacao'].initial = self.professor.instituicao_formacao
        self.fields['anos_experiencia'].initial = self.professor.anos_experiencia
        self.fields['email'].initial = self.professor.email
        self.fields['endereco'].initial = self.professor.endereco
        self.fields['tipo_contrato'].initial = self.professor.tipo_contrato
        self.fields['carga_horaria_semanal'].initial = self.professor.carga_horaria_semanal
        self.fields['numero_agente'].initial = self.professor.numero_agente
   

    def save(self):

        self.professor.nome_completo = self.cleaned_data['nome_completo']
        self.professor.categoria = self.cleaned_data['categoria']
        self.professor.telefone = self.cleaned_data['telefone']
        self.professor.genero = self.cleaned_data['genero']
        self.professor.data_nascimento = self.cleaned_data['data_nascimento']
        self.professor.numero_agente = self.cleaned_data['numero_agente']
        self.professor.bi = self.cleaned_data['bi']
        self.professor.especialidade = self.cleaned_data['especialidade']
        self.professor.nivel_academico = self.cleaned_data['nivel_academico']
        self.professor.instituicao_formacao = self.cleaned_data['instituicao_formacao']
        self.professor.anos_experiencia = self.cleaned_data['anos_experiencia']
        self.professor.email = self.cleaned_data['email']
        self.professor.endereco = self.cleaned_data['endereco']
        self.professor.tipo_contrato = self.cleaned_data['tipo_contrato']
        self.professor.carga_horaria_semanal = self.cleaned_data['carga_horaria_semanal']

        return self.professor

class AlunoForm(forms.Form):

    nome_completo = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Nome completo'})
    )
    nome_pai = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Nome do pai'})
    )
    nome_mae = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Nome da mãe'})
    )
    data_nascimento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
  
    naturalidade = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Naturalidade'})
    )
    bi = forms.CharField(
        max_length=14, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'B.I'})
    )
    data_emissao_bi = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    genero = forms.ChoiceField(choices=Aluno.GENERO)
    provincia = forms.CharField(
        max_length=50, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Província'})
        
    )
    telefone = forms.CharField(
        max_length=9, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Telefone', 'id': 'telefone'})
    )
    municipio = forms.CharField(
        max_length=50, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Município'})
    )
    bairro = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Bairro'})
    )
    endereco_completo = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'endereço completo'})
    )


    def clean(self):
        clean_data =  super().clean()

        telefone=self.cleaned_data['telefone']
        
        if telefone:
            telefone_validade = int(telefone[0])

            if telefone_validade != 9:
                self.add_error('telefone', 'Número de telefone inválido!')

        return clean_data

    def save(self):

        aluno = Aluno(
            nome_completo=self.cleaned_data['nome_completo'],
            nome_pai=self.cleaned_data['nome_pai'],
            nome_mae=self.cleaned_data['nome_mae'],
            data_nascimento=self.cleaned_data['data_nascimento'],
            naturalidade=self.cleaned_data['naturalidade'],
            telefone=self.cleaned_data['telefone'],
            bi=self.cleaned_data.get('bi'),
            data_emissao_bi=self.cleaned_data.get('data_emissao_bi'),
            genero=self.cleaned_data['genero'],
            provincia=self.cleaned_data['provincia'],
            municipio=self.cleaned_data['municipio'],
            bairro=self.cleaned_data['bairro'],
            endereco_completo=self.cleaned_data['endereco_completo'],
        )

        return aluno
    
class AlunoEditForm(forms.Form):

    nome_completo = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Nome completo'})
    )
    nome_pai = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Nome do pai'})
    )
    nome_mae = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Nome da mãe'})
    )
    data_nascimento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
  
    naturalidade = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Naturalidade'})
    )
    bi = forms.CharField(
        max_length=14, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'B.I'})
    )
    data_emissao_bi = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    genero = forms.ChoiceField(choices=Aluno.GENERO)
    provincia = forms.CharField(
        max_length=50, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Província'})
        
    )
    telefone = forms.CharField(
        max_length=9, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Telefone', 'id': 'telefone'})
    )
    municipio = forms.CharField(
        max_length=50, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Município'})
    )
    bairro = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Bairro'})
    )
    endereco_completo = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'endereço completo'})
    )

    def __init__(self, *args, **kwargs):
        self.aluno = kwargs.pop("aluno")
        super().__init__(*args, **kwargs)

        if self.aluno:
            self.fields['nome_completo'].initial = self.aluno.nome_completo
            self.fields['nome_pai'].initial = self.aluno.nome_pai
            self.fields['nome_mae'].initial = self.aluno.nome_mae
            self.fields['data_nascimento'].initial = self.aluno.data_nascimento
            self.fields['naturalidade'].initial = self.aluno.naturalidade
            self.fields['telefone'].initial = self.aluno.telefone
            self.fields['bi'].initial = self.aluno.bi
            self.fields['data_emissao_bi'].initial = self.aluno.data_emissao_bi
            self.fields['genero'].initial = self.aluno.genero
            self.fields['provincia'].initial = self.aluno.provincia
            self.fields['municipio'].initial = self.aluno.municipio
            self.fields['endereco_completo'].initial = self.aluno.endereco_completo
            self.fields['bairro'].initial = self.aluno.bairro
           
    def clean(self):
        clean_data =  super().clean()

        telefone=self.cleaned_data['telefone']
        
        if telefone:
            telefone_validade = int(telefone[0])

            if telefone_validade != 9:
                self.add_error('telefone', 'Número de telefone inválido!')

        return clean_data

    def save(self):

        
        self.aluno.nome_completo=self.cleaned_data['nome_completo']
        self.aluno.nome_pai=self.cleaned_data['nome_pai']
        self.aluno.nome_mae=self.cleaned_data['nome_mae']
        self.aluno.data_nascimento=self.cleaned_data['data_nascimento']
        self.aluno.naturalidade=self.cleaned_data['naturalidade']
        self.aluno.telefone=self.cleaned_data['telefone']
        self.aluno.bi=self.cleaned_data.get('bi')
        self.aluno.data_emissao_bi=self.cleaned_data.get('data_emissao_bi')
        self.aluno.genero=self.cleaned_data['genero']
        self.aluno.provincia=self.cleaned_data['provincia']
        self.aluno.municipio=self.cleaned_data['municipio']
        self.aluno.endereco_completo=self.cleaned_data['endereco_completo']
        self.aluno.bairro=self.cleaned_data['bairro']
        

        return self.aluno


class MatriculaForm(forms.Form):

    STATUS = [
        ('ativa', 'Ativa'),
        ('finalizada', 'Finalizada'),
    ]

    turma = forms.ModelChoiceField(
        queryset=Turma.objects.none(),
        label="Turma",
        widget=forms.Select(attrs={
            'required': True
        })
    )

    tipo_matricula = forms.ChoiceField(
        choices=Matricula.TIPO_MATRICULA,
        label="Tipo de Matrícula",
        widget=forms.Select(attrs={
            'required': True,
            'id': 'tipo_matricula'
        })
    )

    escola_origem = forms.CharField(
        max_length=200,
        required=False,
        label="Escola de Origem",
        widget=forms.TextInput(attrs={
            'placeholder': 'Apenas para transferências',
            'id': 'escola_origem'
        })
    )
    
    documentos_entregues = forms.MultipleChoiceField(
        choices=[
            ('BI', 'Bilhete de Identidade'),
            ('Certidao', 'Certidão de Nascimento'),
            ('Foto', 'Fotografias'),
            ('Atestado', 'Atestado Médico'),
            ('Boletim', 'Boletim de Notas'),
            ('Declaracao', 'Declaração da Escola Anterior')
        ],
        required=False,
        label="Documentos Entregues",
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input d-inline-block'
        })
    )

    nome_completo = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Nome completo'})
    )
    nome_pai = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Nome do pai'})
    )
    nome_mae = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Nome da mãe'})
    )
    data_nascimento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
  
    naturalidade = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Naturalidade'})
    )
    bi = forms.CharField(
        max_length=14, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'B.I'})
    )
    data_emissao_bi = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    genero = forms.ChoiceField(choices=Aluno.GENERO)
    provincia = forms.CharField(
        max_length=50, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Província'})
        
    )
    telefone = forms.CharField(
        max_length=9, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Telefone'})
    )
    municipio = forms.CharField(
        max_length=50, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Município'})
    )
    bairro = forms.CharField(
        max_length=14, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Bairro'})
    )

    def __init__(self, *args, escola=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.escola = escola

        if escola:
           
            
            self.fields['ano_lectivo'].queryset = AnoLectivo.objects.filter(
                escola=escola
            ).order_by('-activo', '-data_inicio')
            
            self.fields['turma'].queryset = Turma.objects.filter(
                escola=escola,
                activo=True
            ).select_related('curso', 'classe').order_by('classe__ordem', 'designacao')

    def clean(self):

        cleaned_data = super().clean()

        aluno = cleaned_data.get('aluno')
        ano_lectivo = cleaned_data.get('ano_lectivo')
        turma = cleaned_data.get('turma')
        tipo_matricula = cleaned_data.get('tipo_matricula')
        escola_origem = cleaned_data.get('escola_origem')

        if aluno and ano_lectivo:
            if Matricula.objects.filter(aluno=aluno, ano_lectivo=ano_lectivo).exists():
                return self.add_error('ano_lectivo','Este aluno já possui matrícula neste ano lectivo.')

        if turma and turma.vagas_disponiveis <= 0:
            return self.add_error('turma',f'A turma {turma.designacao} não possui vagas disponíveis.')

        if tipo_matricula == 'Transferência' and not escola_origem:
            return self.add_error('tipo_matricula','Para transferências, é obrigatório informar a escola de origem.')

        return cleaned_data
    
    def save(self):

        try:
            ano_letivo = AnoLectivo.objects.get(activo=True)

            aluno = Aluno(
                escola=self.escola,
                nome_completo=self.cleaned_data['nome_completo'],
                nome_pai=self.cleaned_data['nome_pai'],
                nome_mae=self.cleaned_data['nome_mae'],
                data_nascimento=self.cleaned_data['data_nascimento'],
                naturalidade=self.cleaned_data['naturalidade'],
                telefone=self.cleaned_data['telefone'],
                bi=self.cleaned_data.get('bi'),
                data_emissao_bi=self.cleaned_data.get('data_emissao_bi'),
                genero=self.cleaned_data['genero'],
                provincia=self.cleaned_data['provincia'],
                municipio=self.cleaned_data['municipio'],
                bairro=self.cleaned_data['bairro'],
            )


            matricula = Matricula(
                turma = self.cleaned_data['turma'],
                ano_lectivo = self.cleaned_data['ano_lectivo'],
                tipo_matricula = ano_letivo,
                escola_origem = self.cleaned_data['escola_origem'],
                documentos_entregues = self.cleaned_data['documentos_entregues'],
            )

            return matricula, aluno
        
        except AnoLectivo.DoesNotExist:
            raise ValidationError('Erro ao matricular o estudante')
    
class MatriculaEditForm(forms.Form):

    turma = forms.ModelChoiceField(
        queryset=Turma.objects.none(),
        label="Turma",
        widget=forms.Select(attrs={
            'required': True
        })
    )

    tipo_matricula = forms.ChoiceField(
        choices=Matricula.TIPO_MATRICULA,
        label="Tipo de Matrícula",
        widget=forms.Select(attrs={
            'required': True,
            'id': 'tipo_matricula'
        })
    )

    escola_origem = forms.CharField(
        max_length=200,
        required=False,
        label="Escola de Origem",
        widget=forms.TextInput(attrs={
            'placeholder': 'Apenas para transferências',
            'id': 'escola_origem'
        })
    )
    
    documentos_entregues = forms.MultipleChoiceField(
        choices=[
            ('BI', 'Bilhete de Identidade'),
            ('Certidao', 'Certidão de Nascimento'),
            ('Foto', 'Fotografias'),
            ('Atestado', 'Atestado Médico'),
            ('Boletim', 'Boletim de Notas'),
            ('Declaracao', 'Declaração da Escola Anterior')
        ],
        required=False,
        label="Documentos Entregues",
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input d-inline-block'
        })
    )

    nome_completo = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Nome completo'})
    )
    nome_pai = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Nome do pai'})
    )
    nome_mae = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Nome da mãe'})
    )
    data_nascimento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
  
    naturalidade = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Naturalidade'})
    )
    bi = forms.CharField(
        max_length=14, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'B.I'})
    )
    data_emissao_bi = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    genero = forms.ChoiceField(choices=Aluno.GENERO)
    provincia = forms.CharField(
        max_length=50, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Província'})
        
    )
    telefone = forms.CharField(
        max_length=9, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Telefone'})
    )
    municipio = forms.CharField(
        max_length=50, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Município'})
    )
    bairro = forms.CharField(
        max_length=14, 
        required=True,
        widget=forms.TextInput(attrs={'oninput': 'this.value=this.value.toUpperCase()', 'placeholder': 'Bairro'})
    )

    def __init__(self, *args, **kwargs):
        self.matricula = kwargs.pop('matricula', None)
        super().__init__(*args, **kwargs)


    
        if self.matricula:
            
            self.fields['turma'].queryset = Turma.objects.filter(
                escola=self.matricula.escola,
                activo=True
            ).select_related('curso', 'classe').order_by('classe__ordem', 'designacao')


            self.fields['nome_completo'].initial= self.matricula.aluno.nome_completo
            self.fields['nome_pai'].initial= self.matricula.aluno.nome_pai
            self.fields['nome_mae'].initial= self.matricula.aluno.nome_mae
            self.fields['data_nascimento'].initial= self.matricula.aluno.data_nascimento
            self.fields['naturalidade'].initial= self.matricula.aluno.naturalidade
            self.fields['telefone'].initial= self.matricula.aluno.telefone
            self.fields['bi'].initial= self.matricula.aluno.bi
            self.fields['data_emissao_bi'].initial= self.matricula.aluno.data_emissao_bi
            self.fields['genero'].initial= self.matricula.aluno.genero
            self.fields['provincia'].initial= self.matricula.aluno.provincia
            self.fields['municipio'].initial= self.matricula.aluno.municipio
            self.fields['bairro'].initial= self.matricula.aluno.bairro

            self.fields['turma'].initial= self.matricula.turma
            self.fields['tipo_matricula'].initial= self.matricula.tipo_matricula
            self.fields['escola_origem'].initial= self.matricula.escola_origem
            self.fields['documentos_entregues'].initial= self.matricula.documentos_entregues

    def clean(self):
        tipo_matricula = self.cleaned_data['tipo_matricula']

        if tipo_matricula == 'Transferência':
            self.add_error('escola_origem', 'Opção Transferência foi selecionada, e este campo é Obrigatório!')


    def save(self):

        self.matricula.aluno.nome_completo=self.cleaned_data['nome_completo']
        self.matricula.aluno.nome_pai=self.cleaned_data['nome_pai']
        self.matricula.aluno.nome_mae=self.cleaned_data['nome_mae']
        self.matricula.aluno.data_nascimento=self.cleaned_data['data_nascimento']
        self.matricula.aluno.naturalidade=self.cleaned_data['naturalidade']
        self.matricula.aluno.telefone=self.cleaned_data['telefone']
        self.matricula.aluno.bi=self.cleaned_data.get('bi')
        self.matricula.aluno.data_emissao_bi=self.cleaned_data.get('data_emissao_bi')
        self.matricula.aluno.genero=self.cleaned_data['genero']
        self.matricula.aluno.provincia=self.cleaned_data['provincia']
        self.matricula.aluno.municipio=self.cleaned_data['municipio']
        self.matricula.aluno.bairro=self.cleaned_data['bairro']

        self.matricula.turma = self.cleaned_data['turma']
        self.matricula.tipo_matricula = self.cleaned_data['tipo_matricula']
        self.matricula.escola_origem = self.cleaned_data['escola_origem']
        self.matricula.documentos_entregues = self.cleaned_data['documentos_entregues']


        return self.matricula, self.matricula.aluno


class DisciplinaForm(forms.Form):

    codigo = forms.CharField(
        required=True,
        max_length=20,
        label="Código",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: MAT101',
            'oninput': 'this.value=this.value.toUpperCase()'
        })
    )
    nome = forms.CharField(
        required=True,
        max_length=200,
        label="Nome",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Matemática',
            'oninput': 'this.value=this.value.toUpperCase()'
        })
    )
    nome_abreviado = forms.CharField(
        required=True,
        max_length=10,
        label="Nome Abreviado",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: MAT',
            'oninput': 'this.value=this.value.toUpperCase()'
        })
    )
    descricao = forms.CharField(
        required=False,
        label="Descrição",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descrição da disciplina'
        })
    )
    carga_horaria_semanal = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=20,
        label="Carga Horária Semanal (horas)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
        })
    )

    def __init__(self, *args, escola = None, **kwargs):

        super().__init__(*args, **kwargs)

        self.escola = escola


    def clean(self):
        clean_data =  super().clean()

        codigo = self.cleaned_data.get('codigo')

        if Disciplina.objects.filter(escola=self.escola, codigo=codigo).exists():
            self.add_error('codigo', 'Já existe uma disciplina com este código.')

        return clean_data
    
    def save(self):

        disciplina = Disciplina(
            nome = self.cleaned_data['nome'],
            nome_abreviado = self.cleaned_data['nome_abreviado'],
            codigo = self.cleaned_data['codigo'],
            descricao = self.cleaned_data['descricao'],
            carga_horaria_semanal = self.cleaned_data['carga_horaria_semanal'],
        )


        return disciplina
    
class DisciplinaEditForm(forms.Form):


    nome = forms.CharField(
        required=True,
        widget= forms.TextInput(attrs={'id': 'nome'})
    )

    nome_abreviado = forms.CharField(
        required=False,
        widget= forms.TextInput(attrs={'id': 'nome_abreviado'})
    )

    codigo = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'id': 'codigo'})
    )
    descricao = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'id': 'descricao'})
    )
    carga_horaria_semanal = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'id': 'carga_horaria_semanal'})
    )

    def __init__(self, *args, **kwargs):
        self.disciplina = kwargs.pop('instance', None)

        super().__init__(*args, **kwargs)
     
        self.fields['nome'].initial = self.disciplina.nome
        self.fields['nome_abreviado'].initial = self.disciplina.nome_abreviado
        self.fields['codigo'].initial = self.disciplina.codigo
        self.fields['descricao'].initial = self.disciplina.descricao
        self.fields['carga_horaria_semanal'].initial = self.disciplina.carga_horaria_semanal


    def save(self):

        self.disciplina.nome = self.cleaned_data['nome']
        self.disciplina.nome_abreviado = self.cleaned_data['nome_abreviado']
        self.disciplina.codigo = self.cleaned_data['codigo']
        self.disciplina.descricao = self.cleaned_data['descricao']
        self.disciplina.carga_horaria_semanal = self.cleaned_data['carga_horaria_semanal']

        self.disciplina.save()

        return self.disciplina 
        
class ResultadoForm(forms.Form):
   
    estudante_id = forms.IntegerField(widget=forms.HiddenInput())

    not_Ev_Sist1 = forms.DecimalField(max_digits=5, decimal_places=2, required=True)
    not_Ev_Sist2 = forms.DecimalField(max_digits=5, decimal_places=2, required=True)
    not_Ev_Sist3 = forms.DecimalField(max_digits=5, decimal_places=2, required=True)
    not_Prov1 = forms.DecimalField(max_digits=5, decimal_places=2, required=True)
    not_Prov2 = forms.DecimalField(max_digits=5, decimal_places=2, required=True)
    not_Prov3 = forms.DecimalField(max_digits=5, decimal_places=2, required=True)
    not_examen = forms.DecimalField(max_digits=5, decimal_places=2, required=True)

class ClasseForm(forms.Form):
    
    denominacao = forms.CharField(
        required=False,
        widget= forms.TextInput(attrs={'id': 'denominacao', 'placeholder': 'Nome da classe'})
    )


    def __init__(self, *args, **kwargs):
        self.classe = kwargs.pop('instance', None)

        super().__init__(*args, **kwargs)

        if self.classe:

            self.fields['denominacao'].initial = self.classe.denominacao


    def save(self):

        if self.classe is None:
            

            classe = Classe(
                denominacao = self.cleaned_data['denominacao'],
            )



            classe.save()

            return classe
        
        else:

            self.classe.denominacao = self.cleaned_data['denominacao']

            return self.classe

class AnoLetivoForm(forms.Form):

    ano = forms.CharField(
        required=True, 
        widget= forms.TextInput(attrs={'id': 'ano'})
    )
    dataFim = forms.DateField(
        required=True, 
        widget= forms.DateInput(attrs={'id': 'dataFim'})
    )
    dataInicio = forms.DateField(
        required=True, 
        widget= forms.DateInput()
    )
    e_atual = forms.BooleanField(
        required=False, 
        widget= forms.CheckboxInput(attrs={'id': 'e_atual'})
    )

    def __init__(self, *args, **kwargs):
        self.ano_letivo = kwargs.pop('instance', None)

        super().__init__(*args, **kwargs)

        if self.ano_letivo:

            self.fields['ano'].initial = self.ano_letivo.ano
            self.fields['e_atual'].initial = self.ano_letivo.e_atual
            self.fields['dataInicio'].initial = self.ano_letivo.dataInicio
            self.fields['dataFim'].initial = self.ano_letivo.dataFim


    def save(self):

        if self.ano_letivo is None:

            ano_letivo = AnoLectivo(
                ano = self.cleaned_data['ano'],
                dataFim = self.cleaned_data['dataFim'],
                dataInicio = self.cleaned_data['dataInicio'],
                e_atual = self.cleaned_data['e_atual'],
            )

            ano_letivo.save()

            return ano_letivo
        
        else:

            self.ano_letivo.ano = self.cleaned_data['ano']
            self.ano_letivo.dataFim = self.cleaned_data['dataFim']
            self.ano_letivo.dataInicio = self.cleaned_data['dataInicio']
            self.ano_letivo.e_atual = self.cleaned_data['e_atual']

            self.ano_letivo.save()


            return self.ano_letivo


class HorarioAulaForm(forms.Form):

    turma = forms.ModelChoiceField(queryset=Turma.objects.all(), label="Turma")
    disciplina = forms.ModelChoiceField(queryset=Disciplina.objects.all(), label="Disciplina")
    professor = forms.ModelChoiceField(queryset=Professor.objects.all(), label="Professor")
    ano_letivo = forms.ModelChoiceField(queryset=AnoLectivo.objects.all(), label="Ano lectivo")
    dia_semana = forms.ChoiceField(
        choices=HorarioAula.DIA_SEMANA,
        label="Dia da Semana"
    )
    hora_inicio = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), label="Hora Início")
    hora_fim = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), label="Hora Fim")
    tipo = forms.ChoiceField(
        choices=[('prova', 'Prova'), ('aula', 'Aula')],
        label="Tipo",
    )
    data_prova = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label="Data da Prova"
    )
    sala = forms.CharField(max_length=50, label="Sala")

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        data_prova = cleaned_data.get('data_prova')

        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fim = cleaned_data.get('hora_fim')

        if hora_inicio > hora_fim:

            self.add_error('hora_inicio', 'Hora início não pode ser maior que hora final')

        if tipo == 'prova' and not data_prova:
            self.add_error('data_prova', 'A data da prova é obrigatória quando o tipo é Prova.')
            
        return cleaned_data
    

class ReconfirmacaoForm(forms.Form):

    
    turma = forms.ModelChoiceField(
        queryset=Turma.objects.all(),
        required=True, 
        widget= forms.Select()
    )
    bi = forms.CharField(
        required=True,
        widget= forms.TextInput(attrs={'placeholder': 'Digite B.I do estudante'})
    )

    def clean(self):
        clean_data =  super().clean()

        try:

            estudante = Aluno.objects.get(bi = self.cleaned_data['bi'])
        
        except Aluno.DoesNotExist:
            self.add_error('bi', 'Nenhum usuário encontrado com esse B.I')

        return clean_data
    
    def save(self):


        ano_letivo = AnoLectivo.objects.get(e_atual=True)

        try:

            estudante = Aluno.objects.get(bi = self.cleaned_data['bi'])

            matricula = Matricula(
                turma = self.cleaned_data['turma'],
                ano_letivo = ano_letivo,
                status_matricula = 'ativa',
                estudante=estudante
            )

            return matricula, estudante
        
        except Aluno.DoesNotExist:
            return self.add_error('bi', 'Nenhum usuário encontrado com esse B.I')

def gerar_senha():

    caracter = string.ascii_letters + string.digits + '@#$%!&%'


    return ''.join(secrets.choice(caracter) for _ in range(9))


class TurmaForm(forms.Form):

    ano_lectivo = forms.ModelChoiceField(
        queryset=AnoLectivo.objects.none(),
        required=True,
        widget=forms.Select()
    )
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.none(),
        required=True,
        widget=forms.Select()
    )
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        required=True,
        widget=forms.Select()
    )
    designacao = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: A, B, C',
            'oninput': 'this.value=this.value.toUpperCase()'
        })
    )
    sala = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Sala 101'
        })
    )
    turno = forms.ChoiceField(
        choices=Turma.TURNO,
        required=True,
        widget=forms.Select()
    )
    capacidade_maxima = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=40,
        required=False,
        widget=forms.NumberInput()
    )
    vagas_disponiveis = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=40,
        required=False,
        widget=forms.NumberInput()
    )
    director_turma = forms.ModelChoiceField(
        queryset=Professor.objects.none(),
        required=False,
        widget=forms.Select()
    )

    def __init__(self, *args, escola=None, **kwargs):
        self.escola = escola
        super().__init__(*args, **kwargs)
        if escola:
            self.fields['ano_lectivo'].queryset = AnoLectivo.objects.filter(
                escola=escola
            ).order_by('-activo', '-data_inicio')
            
            self.fields['curso'].queryset = Curso.objects.filter(
                escola=escola,
                activo=True
            ).order_by('nome')
            
            self.fields['director_turma'].queryset = Professor.objects.filter(
                escola=escola,
                status='Activo'
            ).order_by('nome_completo')
    
    def clean(self):
        designacao=self.cleaned_data['designacao']
        ano_lectivo=self.cleaned_data['ano_lectivo']
        classe=self.cleaned_data['classe']
        turno=self.cleaned_data['turno']
        curso=self.cleaned_data['curso']

        try:

            if Turma.objects.filter( 
                Q(designacao=designacao) & 
                Q(ano_lectivo=ano_lectivo) & 
                Q(classe=classe) & 
                Q(escola=self.escola) & 
                Q(curso=curso) & 
                Q(turno=turno) 
                
                ).exists():

                self.add_error('designacao', 'Está turma com essas informações já existe!')

        except Turma.DoesNotExist:
            pass

    def save(self):


        turma = Turma(
            designacao=self.cleaned_data['designacao'],
            ano_lectivo=self.cleaned_data['ano_lectivo'],
            classe=self.cleaned_data['classe'],
            turno=self.cleaned_data['turno'],
            director_turma=self.cleaned_data['director_turma'],
            curso=self.cleaned_data['curso'],
            sala=self.cleaned_data['sala'],
            escola=self.escola,
            capacidade_maxima=self.cleaned_data['capacidade_maxima'],
            vagas_disponiveis=self.cleaned_data['vagas_disponiveis'],
        )

        turma.save()

        return turma
    
class TurmaEditForm(forms.Form):

    ano_lectivo = forms.ModelChoiceField(
        queryset=AnoLectivo.objects.none(),
        required=True,
        widget=forms.Select()
    )
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.none(),
        required=True,
        widget=forms.Select()
    )
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.none(),
        required=True,
        widget=forms.Select()
    )
    designacao = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: A, B, C',
            'oninput': 'this.value=this.value.toUpperCase()'
        })
    )
    sala = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Sala 101'
        })
    )
    turno = forms.ChoiceField(
        choices=Turma.TURNO,
        required=True,
        widget=forms.Select()
    )
    capacidade_maxima = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=40,
        required=False,
        widget=forms.NumberInput()
    )
    vagas_disponiveis = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=40,
        required=False,
        widget=forms.NumberInput()
    )
    director_turma = forms.ModelChoiceField(
        queryset=Professor.objects.none(),
        required=False,
        widget=forms.Select()
    )

    def __init__(self, *args, escola=None, turma=None, **kwargs):
        self.escola = escola
        self.turma = turma
        super().__init__(*args, **kwargs)

        if escola:
            self.fields['ano_lectivo'].queryset = AnoLectivo.objects.filter(
                escola=escola
            ).order_by('-activo', '-data_inicio')
            
            self.fields['curso'].queryset = Curso.objects.filter(
                escola=escola,
                activo=True
            ).order_by('nome')

            self.fields['classe'].queryset = Classe.objects.filter(
                escola=escola,
            ).order_by('designacao')
            
            self.fields['director_turma'].queryset = Professor.objects.filter(
                escola=escola,
                status='Activo'
            ).order_by('nome_completo')
        
        if turma:
            self.fields['designacao'].initial = turma.designacao
            self.fields['sala'].initial = turma.sala
            self.fields['turno'].initial = turma.turno
            self.fields['sala'].initial = turma.sala
            self.fields['capacidade_maxima'].initial = turma.capacidade_maxima
            self.fields['vagas_disponiveis'].initial = turma.vagas_disponiveis
            self.fields['ano_lectivo'].initial = turma.ano_lectivo
            self.fields['curso'].initial = turma.curso
            self.fields['director_turma'].initial = turma.director_turma
            self.fields['classe'].initial = turma.classe
    

    def save(self):

        self.turma.designacao=self.cleaned_data['designacao']
        self.turma.classe=self.cleaned_data['classe']
        self.turma.ano_lectivo=self.cleaned_data['ano_lectivo']
        self.turma.turno=self.cleaned_data['turno']
        self.turma.director_turma=self.cleaned_data['director_turma']
        self.turma.curso=self.cleaned_data['curso']
        self.turma.sala=self.cleaned_data['sala']
        self.turma.capacidade_maxima=self.cleaned_data['capacidade_maxima']
        self.turma.vagas_disponiveis=self.cleaned_data['vagas_disponiveis']
    

        self.turma.save()

        return self.turma
       


class AvaliacaoForm(forms.Form):
    turma = forms.ModelChoiceField(
        queryset=Turma.objects.none(),
        label="Turma",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    disciplina = forms.ModelChoiceField(
        queryset=Disciplina.objects.none(),
        label="Disciplina",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    periodo = forms.ModelChoiceField(
        queryset=PeriodoAvaliativo.objects.none(),
        label="Período Avaliativo",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    tipo_avaliacao = forms.ModelChoiceField(
        queryset=TipoAvaliacao.objects.none(),
        required=False,
        label="Tipo de Avaliação",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    designacao = forms.CharField(
        max_length=200,
        label="Designação",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Teste 1, Prova Trimestral',
            'required': True
        })
    )
    data_realizacao = forms.DateField(
        label="Data de Realização",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        })
    )
    nota_maxima = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=20,
        label="Nota Máxima",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'required': True
        })
    )
    observacoes = forms.CharField(
        required=False,
        label="Observações",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observações sobre a avaliação'
        })
    )

    def __init__(self, *args, escola=None, **kwargs):
        super().__init__(*args, **kwargs)
        if escola:
            self.fields['turma'].queryset = Turma.objects.filter(
                escola=escola,
                activo=True
            ).select_related('curso', 'classe').order_by('classe__ordem', 'designacao')
            
            self.fields['disciplina'].queryset = Disciplina.objects.filter(
                escola=escola,
                activo=True
            ).order_by('nome')
            
            self.fields['periodo'].queryset = PeriodoAvaliativo.objects.filter(
                ano_lectivo__escola=escola
            ).select_related('ano_lectivo').order_by('-ano_lectivo__activo', 'numero_periodo')
            
            self.fields['tipo_avaliacao'].queryset = TipoAvaliacao.objects.filter(
                escola=escola
            ).order_by('designacao')

    def clean_data_realizacao(self):
        data = self.cleaned_data.get('data_realizacao')
        if data and data > date.today():
            raise ValidationError('A data de realização não pode ser futura.')
        return data


class NotaForm(forms.Form):
    nota = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=0,
        label="Nota",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'required': True
        })
    )
    observacao = forms.CharField(
        required=False,
        label="Observação",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Observação sobre a nota'
        })
    )

    def __init__(self, *args, nota_maxima=20, **kwargs):
        super().__init__(*args, **kwargs)
        self.nota_maxima = nota_maxima
        self.fields['nota'].max_value = nota_maxima
        self.fields['nota'].widget.attrs['max'] = str(nota_maxima)

    def clean_nota(self):
        nota = self.cleaned_data.get('nota')
        if nota and nota > self.nota_maxima:
            raise ValidationError(f'A nota não pode ser superior a {self.nota_maxima}.')
        return nota


class LancamentoNotasForm(forms.Form):
    
    def __init__(self, *args, alunos=None, nota_maxima=20, notas_existentes=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if alunos:
            for aluno in alunos:
                # Campo de nota
                field_name = f'nota_{aluno.id}'
                self.fields[field_name] = forms.DecimalField(
                    max_digits=6,
                    decimal_places=2,
                    min_value=0,
                    max_value=nota_maxima,
                    required=False,
                    label=f"Nota - {aluno.nome_completo}",
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control form-control-sm',
                        'step': '0.01',
                        'max': str(nota_maxima),
                        'placeholder': '0.00'
                    })
                )
                
                # Campo de observação
                obs_field_name = f'obs_{aluno.id}'
                self.fields[obs_field_name] = forms.CharField(
                    required=False,
                    label=f"Obs - {aluno.nome_completo}",
                    widget=forms.TextInput(attrs={
                        'class': 'form-control form-control-sm',
                        'placeholder': 'Observação'
                    })
                )
                
                # Preencher com dados existentes
                if notas_existentes and aluno.id in notas_existentes:
                    nota_obj = notas_existentes[aluno.id]
                    self.initial[field_name] = nota_obj.nota
                    self.initial[obs_field_name] = nota_obj.observacao
