
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
        widget= forms.TextInput()
    )
    data_nascimento = forms.DateField(
        required=True,
        widget= forms.DateInput()
    )
    genero = forms.ChoiceField(
        choices= Professor.GENERO,
        required=True,
        widget= forms.Select()
    )
    telefone = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )
    categoria = forms.ModelChoiceField(
        queryset= Categoria.objects.all(),
        required=True,
        widget= forms.Select()
    )

    def save(self, professor=None):

        if professor is None: 

            professor = Professor(
                nome_completo = self.cleaned_data['nome_completo'],
                categoria = self.cleaned_data['categoria'],
                telefone = self.cleaned_data['telefone'],
                genero = self.cleaned_data['genero'],
                data_nascimento = self.cleaned_data['data_nascimento'],
            )

            return professor
        
        else:
            professor.nome_completo = self.cleaned_data['nome_completo']
            professor.categoria = self.cleaned_data['categoria']
            professor.telefone = self.cleaned_data['telefone']
            professor.genero = self.cleaned_data['genero']
            professor.data_nascimento = self.cleaned_data['data_nascimento']

            return professor

class AlunoForm(forms.Form):

    nome_completo = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Nome completo'})
    )
    nome_pai = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Nome do pai'})
    )
    nome_mae = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Nome da mãe'})
    )
    data_nascimento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
  
    naturalidade = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Naturalidade'})
    )
    bi = forms.CharField(
        max_length=14, 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'B.I'})
    )
    data_emissao_bi = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    genero = forms.ChoiceField(choices=Aluno.GENERO)
    provincia = forms.CharField(
        max_length=50, 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Província'})
        
    )
    telefone = forms.CharField(
        max_length=9, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Telefone'})
    )
    municipio = forms.CharField(
        max_length=50, 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Município'})
    )
    bairro = forms.CharField(
        max_length=14, 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Bairro'})
    )


    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, "escola"):
            self.fields["escola"].queryset = TenantEscola.objects.filter(id=user.escola.id)

            self.fields["escola"].initial = user.escola

    def seve(self):

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
        )

        aluno.save()

        return aluno


class MatriculaForm(forms.Form):

    STATUS = [
        ('ativa', 'Ativa'),
        ('finalizada', 'Finalizada'),
    ]

    
    turma = forms.ModelChoiceField(
        queryset=Turma.objects.all(),
        required=True, 
        widget= forms.Select()
    )

    ano_letivo = forms.ModelChoiceField(
        queryset=AnoLectivo.objects.all(),
        required=True, 
        widget= forms.Select()
    )

    data_cancelamento = forms.DateField(
        required=False,
        widget= forms.DateInput()
    )

    status_matricula = forms.ChoiceField(
        choices= STATUS,
        required=False,
        widget= forms.Select()
    )

    motivo_cancelamento = forms.CharField(
        required=False,
        widget= forms.Textarea()
    )


    nome_completo = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )

    nome_mae = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )
    nome_pai = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )

    provincia = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )
    municipio = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )
    natural = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )

    emitido_em = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )
    endereco = forms.CharField(
        required=False,
        widget= forms.TextInput()
    )

    data_emissao = forms.DateField(
        required=True,
        widget= forms.DateInput()
    )
    data_nascimento = forms.DateField(
        required=True,
        widget= forms.DateInput()
    )
    genero = forms.ChoiceField(
        choices= Aluno.GENERO,
        required=True,
        widget= forms.Select()
    )
    telefone = forms.CharField(
        required=False,
        widget= forms.TextInput()
    )
    bi = forms.CharField(
        required=False,
        widget= forms.TextInput()
    )

    def save(self):

        

        aluno = Aluno(
            nome_completo = self.cleaned_data['nome_completo'],
            nome_mae = self.cleaned_data['nome_mae'],
            nome_pai = self.cleaned_data['nome_pai'],
            endereco = self.cleaned_data['endereco'],
            emitido_em = self.cleaned_data['emitido_em'],
            data_emissao = self.cleaned_data['data_emissao'],
            bi = self.cleaned_data['bi'],
            telefone = self.cleaned_data['telefone'],
            genero = self.cleaned_data['genero'],
            data_nascimento = self.cleaned_data['data_nascimento'],
            provincia = self.cleaned_data['provincia'],
            municipio = self.cleaned_data['municipio'],
            natural = self.cleaned_data['natural'],
        )

        matricula = Matricula(
            turma = self.cleaned_data['turma'],
            ano_letivo = self.cleaned_data['ano_letivo'],
            status_matricula = self.cleaned_data['status_matricula'],
        )

        return matricula, aluno
    
class MatriculaEditForm(forms.Form):

    
    turma = forms.ModelChoiceField(
        queryset=Turma.objects.all(),
        required=True, 
        widget= forms.Select()
    )

    ano_letivo = forms.ModelChoiceField(
        queryset=AnoLectivo.objects.all(),
        required=True, 
        widget= forms.Select()
    )

    data_cancelamento = forms.DateField(
        required=False,
        widget= forms.DateInput()
    )

    status_matricula = forms.ChoiceField(
        choices= Matricula.STATUS,
        required=False,
        widget= forms.Select(attrs={'id': 'status_matricula'})
    )

    motivo_cancelamento = forms.CharField(
        required=False,
        widget= forms.Textarea()
    )

    nome_completo = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )
    data_nascimento = forms.DateField(
        required=True,
        widget= forms.DateInput()
    )
    genero = forms.ChoiceField(
        choices= Aluno.GENERO,
        required=True,
        widget= forms.Select()
    )
    telefone = forms.CharField(
        required=False,
        widget= forms.TextInput()
    )
    bi = forms.CharField(
        required=False,
        widget= forms.TextInput()
    )

    nome_mae = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )
    nome_pai = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )
    emitido_em = forms.CharField(
        required=False,
        widget= forms.TextInput()
    )
    provincia = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )
    municipio = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )
    natural = forms.CharField(
        required=True,
        widget= forms.TextInput()
    )
    endereco = forms.CharField(
        required=False,
        widget= forms.TextInput()
    )

    data_emissao = forms.DateField(
        required=False,
        widget= forms.DateInput()
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

        ano = AnoLectivo.objects.get(id=self.instance.ano_letivo.id)
        turma = Turma.objects.get(id=self.instance.turma.id)

    
        if self.instance:
            self.fields['ano_letivo'].initial = ano

        if self.instance:
            self.fields['turma'].initial = turma

        if self.instance:
            self.fields['status_matricula'].initial = self.instance.status_matricula

        if self.instance.data_cancelamento:
            self.fields['data_cancelamento'].initial = self.instance.data_cancelamento

        if self.instance.motivo_cancelamento:
            self.fields['motivo_cancelamento'].initial = self.instance.motivo_cancelamento

    def clean(self):
        status_matricula = self.cleaned_data['status_matricula']
        data_cancelamento = self.cleaned_data['data_cancelamento']
        motivo_cancelamento = self.cleaned_data['motivo_cancelamento']

        if status_matricula == 'cancelada' and not data_cancelamento:
            self.add_error('data_cancelamento', 'Opção cancelada foi selecionada, e este campo é Obrigatório!')

        if status_matricula == 'cancelada' and not motivo_cancelamento:
            self.add_error('motivo_cancelamento', 'Opção cancelada, é Obrigatório!')

    def save(self):

        self.instance.estudante.nome_completo = self.cleaned_data['nome_completo']
        self.instance.estudante.bi = self.cleaned_data['bi']
        self.instance.estudante.telefone = self.cleaned_data['telefone']
        self.instance.estudante.genero = self.cleaned_data['genero']
        self.instance.estudante.data_nascimento = self.cleaned_data['data_nascimento']
        self.instance.estudante.nome_mae = self.cleaned_data['nome_mae']
        self.instance.estudante.provincia = self.cleaned_data['provincia']
        self.instance.estudante.municipio = self.cleaned_data['municipio']
        self.instance.estudante.natural = self.cleaned_data['natural']
        self.instance.estudante.nome_pai = self.cleaned_data['nome_pai']
        self.instance.estudante.endereco = self.cleaned_data['endereco']
        self.instance.estudante.emitido_em = self.cleaned_data['emitido_em']
        self.instance.estudante.data_emissao = self.cleaned_data['data_emissao']

        self.instance.estudante.save()

        self.instance.turma = self.cleaned_data['turma']
        self.instance.ano_letivo = self.cleaned_data['ano_letivo']
        self.instance.status_matricula = self.cleaned_data['status_matricula']
        self.instance.data_cancelamento = self.cleaned_data['data_cancelamento']
        self.instance.motivo_cancelamento = self.cleaned_data['motivo_cancelamento']

        self.instance.save()


        return self.instance
    
class DisciplinaForm(forms.Form):

    
    professor = forms.ModelChoiceField(
        queryset=Professor.objects.all(),
        required=True, 
        widget= forms.Select()
    )

    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        required=True, 
        widget= forms.Select()
    )

    nome = forms.CharField(
        required=True,
        widget= forms.TextInput(attrs={'id': 'nome'})
    )

    abreviatura = forms.CharField(
        required=False,
        widget= forms.TextInput(attrs={'id': 'abreviatura'})
    )


    def save(self):

        disciplina = Disciplina(
            nome = self.cleaned_data['nome'],
            professor = self.cleaned_data['professor'],
            classe = self.cleaned_data['classe'],
            abreviatura = self.cleaned_data['abreviatura'],
        )

        disciplina.save()

        return disciplina
    
class DisciplinaEditForm(forms.Form):

    
    professor = forms.ModelChoiceField(
        queryset=Professor.objects.all(),
        required=True, 
        widget= forms.Select()
    )

    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        required=True, 
        widget= forms.Select()
    )

    nome = forms.CharField(
        required=True,
        widget= forms.TextInput(attrs={'id': 'nome'})
    )

    abreviatura = forms.CharField(
        required=False,
        widget= forms.TextInput(attrs={'id': 'abreviatura'})
    )

    def __init__(self, *args, **kwargs):
        self.disciplina = kwargs.pop('instance', None)

        super().__init__(*args, **kwargs)
     
        self.fields['professor'].initial = self.disciplina.professor
        self.fields['classe'].initial = self.disciplina.classe


    def save(self):

        self.disciplina.nome = self.cleaned_data['nome']
        self.disciplina.professor = self.cleaned_data['professor']
        self.disciplina.classe = self.cleaned_data['classe']
        self.disciplina.abreviatura = self.cleaned_data['abreviatura']

        self.disciplina.save()

        return self.disciplina
    
class TurmaForm(forms.Form):
    
    ano_letivo = forms.ModelChoiceField(
        queryset=AnoLectivo.objects.all(),
        required=True, 
        widget= forms.Select()
    )

    

    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        required=True, 
        widget= forms.Select()
    )

    turma = forms.CharField(
        required=True,
        widget= forms.TextInput(attrs={
            'oninput': 'this.value=this.value.toUpperCase()',
            'placeholder': 'Nome da turma'
        })
    )


    def __init__(self, *args, **kwargs):
        self.turma = kwargs.pop('instance', None)

        super().__init__(*args, **kwargs)

        if self.turma is not None:

            self.fields['turma'].initial = self.turma.turma
            self.fields['ano_letivo'].initial = self.turma.ano_letivo
            self.fields['classe'].initial = self.turma.classe
            self.fields['periodo'].initial = self.turma.periodo
     
        
    def clean(self):
        turma=self.cleaned_data['turma']
        ano_letivo=self.cleaned_data['ano_letivo']
        classe=self.cleaned_data['classe']
        periodo=self.cleaned_data['periodo']

        if self.turma is None:
            try:

                if Turma.objects.filter( Q(turma=turma) & Q(ano_letivo=ano_letivo) & Q(classe=classe) & Q(periodo=periodo) ).exists():

                    self.add_error('turma', 'Está turma com essas informações já existe!')

            except Turma.DoesNotExist:
                pass

    def save(self):

        if self.turma is None:

            turma = Turma(
                turma=self.cleaned_data['turma'],
                ano_letivo=self.cleaned_data['ano_letivo'],
                classe=self.cleaned_data['classe'],
                periodo=self.cleaned_data['periodo'],
            )

            turma.save()

            return turma
       
        else:
           
            self.turma.turma=self.cleaned_data['turma']
            self.turma.ano_letivo=self.cleaned_data['ano_letivo']
            self.turma.classe=self.cleaned_data['classe']
            self.turma.periodo=self.cleaned_data['periodo']

            return self.turma
        
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


# ============= FORMS DE MATRÍCULA =============

class MatriculaForm(forms.Form):

    aluno = forms.ModelChoiceField(
        queryset=Aluno.objects.none(),
        label="Aluno",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    ano_lectivo = forms.ModelChoiceField(
        queryset=AnoLectivo.objects.none(),
        label="Ano Lectivo",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    turma = forms.ModelChoiceField(
        queryset=Turma.objects.none(),
        label="Turma",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    tipo_matricula = forms.ChoiceField(
        choices=[
            ('Nova', 'Nova'),
            ('Renovação', 'Renovação'),
            ('Transferência', 'Transferência')
        ],
        label="Tipo de Matrícula",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    escola_origem = forms.CharField(
        max_length=200,
        required=False,
        label="Escola de Origem",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apenas para transferências'
        })
    )
    observacoes = forms.CharField(
        required=False,
        label="Observações",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observações adicionais sobre a matrícula'
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
            'class': 'form-check-input'
        })
    )

    def __init__(self, *args, escola=None, **kwargs):
        super().__init__(*args, **kwargs)
        if escola:
            self.fields['aluno'].queryset = Aluno.objects.filter(
                escola=escola,
                status='Matriculado'
            ).order_by('nome_completo')
            
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




class TurmaForm(forms.Form):
    ano_lectivo = forms.ModelChoiceField(
        queryset=AnoLectivo.objects.none(),
        label="Ano Lectivo",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.none(),
        label="Curso",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        label="Classe",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    designacao = forms.CharField(
        max_length=10,
        label="Designação",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: A, B, C',
            'required': True
        })
    )
    sala = forms.CharField(
        max_length=50,
        required=False,
        label="Sala",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Sala 101'
        })
    )
    turno = forms.ChoiceField(
        choices=Turma.TURNO,
        label="Turno",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    capacidade_maxima = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=40,
        label="Capacidade Máxima",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    director_turma = forms.ModelChoiceField(
        queryset=Professor.objects.none(),
        required=False,
        label="Director de Turma",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    def __init__(self, *args, escola=None, **kwargs):
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

    def clean_designacao(self):
        designacao = self.cleaned_data.get('designacao')
        return designacao.upper()

class DisciplinaForm(forms.Form):
    codigo = forms.CharField(
        max_length=20,
        label="Código",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: MAT101',
            'required': True
        })
    )
    nome = forms.CharField(
        max_length=200,
        label="Nome",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Matemática',
            'required': True
        })
    )
    nome_abreviado = forms.CharField(
        max_length=10,
        label="Nome Abreviado",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: MAT',
            'required': True
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
        min_value=1,
        max_value=20,
        label="Carga Horária Semanal (horas)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'required': True
        })
    )

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        return codigo.upper()

    def clean_nome_abreviado(self):
        nome_abreviado = self.cleaned_data.get('nome_abreviado')
        return nome_abreviado.upper()



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
