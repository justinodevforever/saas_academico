
from django import forms
from academico.models import *
from django.db.models import Q
import string, secrets

from django.shortcuts import get_list_or_404

from django import forms
from django.utils import timezone


PROVINCIAS_ANGOLA = [
    ('', 'Selecione a província…'),
    ('Bengo', 'Bengo'),
    ('Benguela', 'Benguela'),
    ('Bié', 'Bié'),
    ('Cabinda', 'Cabinda'),
    ('Cuando Cubango', 'Cuando Cubango'),
    ('Cuanza Norte', 'Cuanza Norte'),
    ('Cuanza Sul', 'Cuanza Sul'),
    ('Cunene', 'Cunene'),
    ('Huambo', 'Huambo'),
    ('Huíla', 'Huíla'),
    ('Luanda', 'Luanda'),
    ('Lunda Norte', 'Lunda Norte'),
    ('Lunda Sul', 'Lunda Sul'),
    ('Malanje', 'Malanje'),
    ('Moxico', 'Moxico'),
    ('Namibe', 'Namibe'),
    ('Uíge', 'Uíge'),
    ('Zaire', 'Zaire'),
]

class CriarDirectorForm(forms.Form):

    nome_completo = forms.CharField(
        max_length=2000,
        required=True,
        widget=forms.TextInput(attrs={'class':'form-control-custom', 'placeholder': 'Nome completo'})
    )

    bi = forms.CharField(
        max_length=14,
        min_length=14,
        required=True,
        widget=forms.TextInput(attrs={'class':'form-control-custom', 'placeholder': 'Nº de Bilhete'})
    )
    data_nascimento = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class':'form-control-custom', 'type': 'date'})
    )
    genero = forms.ChoiceField(
        choices=Diretor.Genero.choices,
        required=True,
        widget=forms.Select(attrs={'class':'form-control-custom', 'placeholder': 'Preço anual'})
    )
    telefone = forms.CharField(
        required=True,
        max_length=9,
        min_length=9,
        widget=forms.TextInput(attrs={'class':'form-control-custom', 'placeholder': 'Ex.: 938 775 839'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class':'form-control-custom', 'placeholder': 'Ex.: chitombi@gmail.com'})
    )
    endereco = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class':'form-control-custom', 'placeholder': 'Ex.: Luena, Bairro 4 de Fevereio'})
    )
 
    def save(self):

        director = Diretor(
            nome_completo=self.cleaned_data.get('nome_completo'),
            bi=self.cleaned_data.get('bi'),
            genero=self.cleaned_data.get('genero'),
            data_nascimento=self.cleaned_data.get('data_nascimento'),
            telefone=self.cleaned_data.get('telefone'),
            email=self.cleaned_data.get('email'),
            endereco=self.cleaned_data.get('endereco'),
        )

        return director


class EditarDirectorForm(forms.Form):

    nome_completo = forms.CharField(
        max_length=2000,
        required=True,
        widget=forms.TextInput(attrs={'class':'form-control-custom', 'placeholder': 'Nome completo'})
    )



    bi = forms.CharField(
        max_length=14,
        min_length=14,
        required=True,
        widget=forms.TextInput(attrs={'class':'form-control-custom', 'placeholder': 'Nº de Bilhete'})
    )
    data_nascimento = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class':'form-control-custom', 'type': 'date'})
    )
    genero = forms.ChoiceField(
        choices=Diretor.Genero.choices,
        required=True,
        widget=forms.Select(attrs={'class':'form-control-custom', 'placeholder': 'Preço anual'})
    )
    telefone = forms.CharField(
        required=True,
        max_length=9,
        min_length=9,
        widget=forms.TextInput(attrs={'class':'form-control-custom', 'placeholder': 'Ex.: 938 775 839'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class':'form-control-custom', 'placeholder': 'Ex.: chitombi@gmail.com'})
    )
    endereco = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class':'form-control-custom', 'placeholder': 'Ex.: Luena, Bairro 4 de Fevereio'})
    )

    def __init__(self, *args, **kwargs):
        self.director = kwargs.pop('director', None)
        super().__init__(*args, **kwargs)


        if self.director:
            self.fields['nome_completo'].initial = self.director.nome_completo
            self.fields['bi'].initial = self.director.bi
            self.fields['genero'].initial = self.director.genero
            self.fields['data_nascimento'].initial = self.director.data_nascimento
            self.fields['telefone'].initial = self.director.telefone
            self.fields['email'].initial = self.director.email
            self.fields['endereco'].initial = self.director.endereco
 
    def save(self):

        self.director.nome_completo=self.cleaned_data.get('nome_completo')
        self.director.bi=self.cleaned_data.get('bi')
        self.director.genero=self.cleaned_data.get('genero')
        self.director.data_nascimento=self.cleaned_data.get('data_nascimento')
        self.director.telefone=self.cleaned_data.get('telefone')
        self.director.email=self.cleaned_data.get('email')

        return self.director


class CriarPlanoForm(forms.Form):

    nome = forms.ChoiceField(
        choices=PlanoSubscricao.TipoPlano.choices,
        required=True,
        widget=forms.Select(attrs={'class':'form-control-custom'})
    )

    descricao = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class':'form-control-custom', 'placeholder': 'Descreva alguma coisa'})
    )
    preco_mensal = forms.DecimalField(
        required=True,
        widget=forms.NumberInput(attrs={'class':'form-control-custom', 'placeholder': 'Preço mensal'})
    )
    preco_anual = forms.DecimalField(
        required=True,
        widget=forms.NumberInput(attrs={'class':'form-control-custom', 'placeholder': 'Preço anual'})
    )
    max_alunos = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class':'form-control-custom', 'placeholder': 'Máximo de alunos'})
    )
    max_professores = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class':'form-control-custom', 'placeholder': 'Máximo de professores'})
    )
    max_turmas = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class':'form-control-custom', 'placeholder': 'Máximo de turmas'})
    )


    def save(self):

        plano = PlanoSubscricao(
            nome=self.cleaned_data.get('nome'),
            descricao=self.cleaned_data.get('descricao'),
            max_turmas=self.cleaned_data.get('max_turmas'),
            max_alunos=self.cleaned_data.get('max_alunos'),
            max_professores=self.cleaned_data.get('max_professores'),
            preco_mensal=self.cleaned_data.get('preco_mensal'),
            preco_anual=self.cleaned_data.get('preco_anual'),
        )

        return plano


class EditarPlanoForm(forms.Form):

    nome = forms.ChoiceField(
        choices=PlanoSubscricao.TipoPlano.choices,
        required=True,
        widget=forms.Select(attrs={'class':'form-control-custom'})
    )

    descricao = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class':'form-control-custom', 'placeholder': 'Descreva alguma coisa'})
    )
    preco_mensal = forms.DecimalField(
        required=True,
        widget=forms.NumberInput(attrs={'class':'form-control-custom', 'placeholder': 'Preço mensal'})
    )
    preco_anual = forms.DecimalField(
        required=True,
        widget=forms.NumberInput(attrs={'class':'form-control-custom', 'placeholder': 'Preço anual'})
    )
    max_alunos = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class':'form-control-custom', 'placeholder': 'Máximo de alunos'})
    )
    max_professores = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class':'form-control-custom', 'placeholder': 'Máximo de professores'})
    )
    max_turmas = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class':'form-control-custom', 'placeholder': 'Máximo de turmas'})
    )
 

    def __init__(self, *args, **kwargs):
        self.plano = kwargs.pop('plano', None)
        super().__init__(*args,**kwargs)

        if self.plano:

            self.fields['nome'].initial = self.plano.nome
            self.fields['descricao'].initial = self.plano.descricao
            self.fields['max_turmas'].initial = self.plano.max_turmas
            self.fields['max_alunos'].initial = self.plano.max_alunos
            self.fields['max_professores'].initial = self.plano.max_professores
            self.fields['preco_mensal'].initial = self.plano.preco_mensal
            self.fields['preco_anual'].initial = self.plano.preco_anual

    def save(self):

        self.plano.nome=self.cleaned_data.get('nome')
        self.plano.descricao=self.cleaned_data.get('descricao')
        self.plano.max_turmas=self.cleaned_data.get('max_turmas')
        self.plano.max_alunos=self.cleaned_data.get('max_alunos')
        self.plano.max_professores=self.cleaned_data.get('max_professores')
        self.plano.preco_mensal=self.cleaned_data.get('preco_mensal')
        self.plano.preco_anual=self.cleaned_data.get('preco_anual')

        return self.plano

class CriarEscolaForm(forms.Form):

    # ── 1. IDENTIFICAÇÃO ──────────────────────────────────────────
    nome = forms.CharField(
        max_length=200,
        label='Nome Completo',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Escola Secundária do Kilamba',
            'class': 'form-control-custom',
            'autofocus': True,
        }),
        error_messages={
            'required': 'O nome da escola é obrigatório.',
            'max_length': 'O nome não pode ter mais de 200 caracteres.',
        },
    )

    nif = forms.CharField(
        max_length=20,
        label='NIF',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: 5000123456LA041',
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'O NIF é obrigatório.',
        },
    )

    tipo_ensino = forms.ChoiceField(
        choices=[('', 'Selecione…')] + TenantEscola.TipoEnsino.choices,
        label='Tipo de Ensino',
        widget=forms.Select(attrs={
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'Selecione o tipo de ensino.',
            'invalid_choice': 'Selecione uma opção válida.',
        },
    )

    numero_alvara = forms.CharField(
        max_length=50,
        required=False,
        label='Número de Alvará',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: ALV-2024-001',
            'class': 'form-control-custom',
        }),
    )


    activo = forms.BooleanField(
        required=False,
        initial=True,
        label='Escola Activa',
        widget=forms.CheckboxInput(attrs={
            'id': 'activo',
        }),
    )

    # ── 2. CONTACTOS ─────────────────────────────────────────────
    email = forms.EmailField(
        max_length=100,
        label='Email Institucional',
        widget=forms.EmailInput(attrs={
            'placeholder': 'escola@dominio.ao',
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'O email é obrigatório.',
            'invalid': 'Introduza um endereço de email válido.',
        },
    )

    telefone = forms.CharField(
        max_length=9,
        min_length=9,
        label='Telefone Principal',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: +244 923 000 000',
            'class': 'form-control-custom',
            'type': 'tel',
        }),
        error_messages={
            'required': 'O telefone é obrigatório.',
        },
    )

    telefone_alternativo = forms.CharField(
        max_length=9,
        min_length=9,
        required=False,
        label='Telefone Alternativo',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: +244 912 000 000',
            'class': 'form-control-custom',
            'type': 'tel',
        }),
    )


    # ── 3. LOCALIZAÇÃO ────────────────────────────────────────────
    provincia = forms.ChoiceField(
        choices=PROVINCIAS_ANGOLA,
        label='Província',
        widget=forms.Select(attrs={
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'Selecione a província.',
            'invalid_choice': 'Selecione uma província válida.',
        },
    )

    municipio = forms.CharField(
        max_length=50,
        label='Município',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Belas',
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'O município é obrigatório.',
        },
    )

    bairro = forms.CharField(
        max_length=100,
        label='Bairro',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Kilamba',
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'O bairro é obrigatório.',
        },
    )

    endereco_completo = forms.CharField(
        label='Endereço Completo',
        widget=forms.Textarea(attrs={
            'placeholder': 'Rua, número, referências…',
            'class': 'form-control-custom',
            'rows': 3,
        }),
        error_messages={
            'required': 'O endereço completo é obrigatório.',
        },
    )

    # ── 4. SUBSCRIÇÃO ─────────────────────────────────────────────
    plano_subscricao = forms.ModelChoiceField(
        queryset=PlanoSubscricao.objects.all(),
        label='Plano de Subscrição',
        empty_label=None,
        widget=forms.RadioSelect(attrs={
            'class': 'plan-radio-input',
        }),
        error_messages={
            'required': 'Selecione um plano de subscrição.',
            'invalid_choice': 'Selecione um plano válido.',
        },
    )

    data_expiracao_plano = forms.DateField(
        label='Data de Expiração do Plano',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'A data de expiração é obrigatória.',
            'invalid': 'Introduza uma data válida.',
        },
    )

    # ── 5. LOGOTIPO ───────────────────────────────────────────────
    logotipo = forms.ImageField(
        required=False,
        label='Logotipo',
        widget=forms.FileInput(attrs={
            'id': 'logoInput',
            'accept': 'image/png,image/jpeg,image/svg+xml',
        }),
        error_messages={
            'invalid_image': 'O ficheiro enviado não é uma imagem válida.',
        },
    )

    status_ensino = forms.ChoiceField(
        choices=[('', 'Selecione…')] + TenantEscola.StatusEnsino.choices,
        required=True,
        label='Estado de Ensino',
        widget=forms.Select(attrs={
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'Selecione o estado de ensino.',
            'invalid_choice': 'Selecione uma opção válida.',
        },
    )


    def clean_nif(self):
        nif = self.cleaned_data.get('nif', '').strip().upper()
        if TenantEscola.objects.filter(nif=nif).exists():
            raise forms.ValidationError('Já existe uma escola registada com este NIF.')
        return nif

    def clean_nome_abreviado(self):
        return self.cleaned_data.get('nome_abreviado', '').strip().upper()

    def clean_email(self):
        return self.cleaned_data.get('email', '').strip().lower()

    def clean_data_fundacao(self):
        data = self.cleaned_data.get('data_fundacao')
        if data and data > timezone.now().date():
            raise forms.ValidationError('A data de fundação não pode ser uma data futura.')
        return data

    def clean_data_expiracao_plano(self):
        data = self.cleaned_data.get('data_expiracao_plano')
        if data and data <= timezone.now().date():
            raise forms.ValidationError('A data de expiração deve ser uma data futura.')
        return data

    def clean_logotipo(self):
        logotipo = self.cleaned_data.get('logotipo')
        if logotipo:
            max_size_mb = 2
            if logotipo.size > max_size_mb * 1024 * 1024:
                raise forms.ValidationError(
                    f'O ficheiro é demasiado grande. Tamanho máximo: {max_size_mb}MB.'
                )
        return logotipo

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone', '').strip()
        # Remove spaces for storage
        return telefone

    def clean_provincia(self):
        provincia = self.cleaned_data.get('provincia', '')
        if not provincia:
            raise forms.ValidationError('Selecione a província.')
        return provincia

    def clean_tipo_ensino(self):
        tipo = self.cleaned_data.get('tipo_ensino', '')
        if not tipo:
            raise forms.ValidationError('Selecione o tipo de ensino.')
        return tipo

    def clean(self):
        """Cross-field validations."""
        cleaned = super().clean()

        telefone   = cleaned.get('telefone', '')
        tel_alt    = cleaned.get('telefone_alternativo', '')

        if tel_alt and tel_alt == telefone:
            self.add_error(
                'telefone_alternativo',
                'O telefone alternativo não pode ser igual ao telefone principal.'
            )

        return cleaned
    
    def save(self):

        escola = TenantEscola(
            nome=self.cleaned_data.get('nome'),
            nif = self.cleaned_data.get('nif'),
            email = self.cleaned_data.get('email'),
            telefone = self.cleaned_data.get('telefone'),
            telefone_alternativo = self.cleaned_data.get('telefone_alternativo'),
            logotipo = self.cleaned_data.get('logotipo'),
            endereco_completo = self.cleaned_data.get('endereco_completo'),
            provincia = self.cleaned_data.get('provincia'),
            municipio = self.cleaned_data.get('municipio'),
            bairro = self.cleaned_data.get('bairro'),
            tipo_ensino = self.cleaned_data.get('tipo_ensino'),
            numero_alvara = self.cleaned_data.get('numero_alvara'),
            plano_subscricao = self.cleaned_data.get('plano_subscricao'),
            data_expiracao_plano = self.cleaned_data.get('data_expiracao_plano'),
            status_ensino = self.cleaned_data.get('status_ensino'),
        )

        return escola


class EditarEscolaForm(forms.Form):

    nome = forms.CharField(
        max_length=200,
        label='Nome Completo',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Escola Secundária do Kilamba',
            'class': 'form-control-custom',
            'autofocus': True,
        }),
        error_messages={
            'required': 'O nome da escola é obrigatório.',
            'max_length': 'O nome não pode ter mais de 200 caracteres.',
        },
    )

    nif = forms.CharField(
        max_length=20,
        label='NIF',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: 5000123456LA041',
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'O NIF é obrigatório.',
        },
    )

    tipo_ensino = forms.ChoiceField(
        choices=[('', 'Selecione…')] + TenantEscola.TipoEnsino.choices,
        label='Tipo de Ensino',
        widget=forms.Select(attrs={
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'Selecione o tipo de ensino.',
            'invalid_choice': 'Selecione uma opção válida.',
        },
    )

    status_ensino = forms.ChoiceField(
        choices=[('', 'Selecione…')] + TenantEscola.StatusEnsino.choices,
        required=True,
        label='Estado de Ensino',
        widget=forms.Select(attrs={
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'Selecione o estado de ensino.',
            'invalid_choice': 'Selecione uma opção válida.',
        },
    )

    numero_alvara = forms.CharField(
        max_length=50,
        required=False,
        label='Número de Alvará',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: ALV-2024-001',
            'class': 'form-control-custom',
        }),
    )

    activo = forms.BooleanField(
        required=False,
        initial=True,
        label='Escola Activa',
        widget=forms.CheckboxInput(attrs={
            'id': 'activo',
        }),
    )

    email = forms.EmailField(
        max_length=100,
        label='Email Institucional',
        widget=forms.EmailInput(attrs={
            'placeholder': 'escola@dominio.ao',
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'O email é obrigatório.',
            'invalid': 'Introduza um endereço de email válido.',
        },
    )

    telefone = forms.CharField(
        max_length=9,
        min_length=9,
        label='Telefone Principal',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: +244 923 000 000',
            'class': 'form-control-custom',
            'type': 'tel',
        }),
        error_messages={
            'required': 'O telefone é obrigatório.',
        },
    )

    telefone_alternativo = forms.CharField(
        max_length=9,
        min_length=9,
        required=False,
        label='Telefone Alternativo',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: +244 912 000 000',
            'class': 'form-control-custom',
            'type': 'tel',
        }),
    )

    provincia = forms.ChoiceField(
        choices=PROVINCIAS_ANGOLA,
        label='Província',
        widget=forms.Select(attrs={
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'Selecione a província.',
            'invalid_choice': 'Selecione uma província válida.',
        },
    )

    municipio = forms.CharField(
        max_length=50,
        label='Município',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Belas',
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'O município é obrigatório.',
        },
    )

    bairro = forms.CharField(
        max_length=100,
        label='Bairro',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Kilamba',
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'O bairro é obrigatório.',
        },
    )

    endereco_completo = forms.CharField(
        label='Endereço Completo',
        widget=forms.Textarea(attrs={
            'placeholder': 'Rua, número, referências…',
            'class': 'form-control-custom',
            'rows': 3,
        }),
        error_messages={
            'required': 'O endereço completo é obrigatório.',
        },
    )

    plano_subscricao = forms.ModelChoiceField(
        queryset=PlanoSubscricao.objects.all(),
        label='Plano de Subscrição',
        empty_label=None,
        widget=forms.RadioSelect(attrs={
            'class': 'plan-radio-input',
        }),
        error_messages={
            'required': 'Selecione um plano de subscrição.',
            'invalid_choice': 'Selecione um plano válido.',
        },
    )

    data_expiracao_plano = forms.DateField(
        label='Data de Expiração do Plano',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control-custom',
        }),
        error_messages={
            'required': 'A data de expiração é obrigatória.',
            'invalid': 'Introduza uma data válida.',
        },
    )

    logotipo = forms.ImageField(
        required=False,
        label='Logotipo',
        widget=forms.FileInput(attrs={
            'id': 'logoInput',
            'accept': 'image/png,image/jpeg,image/svg+xml',
        }),
        error_messages={
            'invalid_image': 'O ficheiro enviado não é uma imagem válida.',
        },
    )

    def __init__(self, *args, **kwargs):
        self.escola = kwargs.pop('escola', None)

        super().__init__(*args,**kwargs)

        self.fields['nome'].initial = self.escola.nome
        self.fields['nif'].initial = self.escola.nif
        self.fields['email'].initial = self.escola.email
        self.fields['telefone'].initial = self.escola.telefone 
        self.fields['telefone_alternativo'].initial = self.escola.telefone_alternativo 
        self.fields['logotipo'].initial = self.escola.logotipo
        self.fields['endereco_completo'].initial = self.escola.endereco_completo
        self.fields['provincia'].initial = self.escola.provincia
        self.fields['municipio'].initial = self.escola.municipio
        self.fields['bairro'].initial = self.escola.bairro 
        self.fields['tipo_ensino'].initial = self.escola.tipo_ensino
        self.fields['numero_alvara'].initial = self.escola.numero_alvara
        self.fields['plano_subscricao'].initial = self.escola.plano_subscricao
        self.fields['data_expiracao_plano'].initial = self.escola.data_expiracao_plano
        self.fields['status_ensino'].initial = self.escola.status_ensino


    def clean_nome_abreviado(self):
        return self.cleaned_data.get('nome_abreviado', '').strip().upper()

    def clean_email(self):
        return self.cleaned_data.get('email', '').strip().lower()

    def clean_data_fundacao(self):
        data = self.cleaned_data.get('data_fundacao')
        if data and data > timezone.now().date():
            raise forms.ValidationError('A data de fundação não pode ser uma data futura.')
        return data

    def clean_data_expiracao_plano(self):
        data = self.cleaned_data.get('data_expiracao_plano')
        if data and data <= timezone.now().date():
            raise forms.ValidationError('A data de expiração deve ser uma data futura.')
        return data

    def clean_logotipo(self):
        logotipo = self.cleaned_data.get('logotipo')
        if logotipo:
            max_size_mb = 2
            if logotipo.size > max_size_mb * 1024 * 1024:
                raise forms.ValidationError(
                    f'O ficheiro é demasiado grande. Tamanho máximo: {max_size_mb}MB.'
                )
        return logotipo

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone', '').strip()
        # Remove spaces for storage
        return telefone

    def clean_provincia(self):
        provincia = self.cleaned_data.get('provincia', '')
        if not provincia:
            raise forms.ValidationError('Selecione a província.')
        return provincia

    def clean_tipo_ensino(self):
        tipo = self.cleaned_data.get('tipo_ensino', '')
        if not tipo:
            raise forms.ValidationError('Selecione o tipo de ensino.')
        return tipo

    def clean(self):
        """Cross-field validations."""
        cleaned = super().clean()

        telefone   = cleaned.get('telefone', '')
        tel_alt    = cleaned.get('telefone_alternativo', '')

        if tel_alt and tel_alt == telefone:
            self.add_error(
                'telefone_alternativo',
                'O telefone alternativo não pode ser igual ao telefone principal.'
            )

        return cleaned
    
    def save(self):

        self.escola.nome=self.cleaned_data.get('nome')
        self.escola.nome_abreviado =self.cleaned_data.get('nome_abreviado')
        self.escola.nif = self.cleaned_data.get('nif')
        self.escola.email = self.cleaned_data.get('email')
        self.escola.telefone = self.cleaned_data.get('telefone')
        self.escola.telefone_alternativo = self.cleaned_data.get('telefone_alternativo')
        self.escola.logotipo = self.cleaned_data.get('logotipo')
        self.escola.endereco_completo = self.cleaned_data.get('endereco_completo')
        self.escola.provincia = self.cleaned_data.get('provincia')
        self.escola.municipio = self.cleaned_data.get('municipio')
        self.escola.bairro = self.cleaned_data.get('bairro')
        self.escola.tipo_ensino = self.cleaned_data.get('tipo_ensino')
        self.escola.data_fundacao = self.cleaned_data.get('data_fundacao')
        self.escola.numero_alvara = self.cleaned_data.get('numero_alvara')
        self.escola.plano_subscricao = self.cleaned_data.get('plano_subscricao')
        self.escola.data_expiracao_plano = self.cleaned_data.get('data_expiracao_plano')
        self.escola.status_ensino = self.cleaned_data.get('status_ensino')

        return self.escola


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
        

