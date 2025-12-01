from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.conf import settings

class PlanoSubscricao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    preco_mensal = models.DecimalField(max_digits=10, decimal_places=2)
    preco_anual = models.DecimalField(max_digits=10, decimal_places=2)
    max_alunos = models.IntegerField()
    max_professores = models.IntegerField()
    max_turmas = models.IntegerField()
    funcionalidades = models.JSONField(default=dict)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'plano_subscricao'
        verbose_name = 'Plano de Subscrição'
        verbose_name_plural = 'Planos de Subscrição'


class TenantEscola(models.Model):
    TIPO_ENSINO = [('Privado', 'Privado'), ('Público', 'Público')]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    nome = models.CharField(max_length=200)
    nome_abreviado = models.CharField(max_length=50)
    nif = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=100)
    telefone = models.CharField(max_length=20)
    telefone_alternativo = models.CharField(max_length=20, blank=True, null=True)
    site = models.URLField(max_length=200, blank=True, null=True)
    logotipo = models.ImageField(upload_to='escolas/logos/', blank=True, null=True)
    endereco_completo = models.TextField()
    provincia = models.CharField(max_length=50)
    municipio = models.CharField(max_length=50)
    bairro = models.CharField(max_length=100)
    tipo_ensino = models.CharField(max_length=10, choices=TIPO_ENSINO)
    data_fundacao = models.DateField(blank=True, null=True)
    numero_alvara = models.CharField(max_length=50, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_actualizacao = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    plano_subscricao = models.ForeignKey(PlanoSubscricao, on_delete=models.PROTECT)
    data_expiracao_plano = models.DateField()
    
    class Meta:
        db_table = 'tenant_escola'
        verbose_name = 'Escola'
        verbose_name_plural = 'Escolas'

class AnoLectivo(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(TenantEscola, on_delete=models.CASCADE)
    designacao = models.CharField(max_length=50)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    activo = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ano_lectivo'
        verbose_name = 'Ano Lectivo'
        verbose_name_plural = 'Anos Lectivos'
        unique_together = ['escola', 'designacao']


class PeriodoAvaliativo(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ano_lectivo = models.ForeignKey(AnoLectivo, on_delete=models.CASCADE, related_name='periodos')
    numero_periodo = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    designacao = models.CharField(max_length=50)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    activo = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'periodo_avaliativo'
        verbose_name = 'Período Avaliativo'
        verbose_name_plural = 'Períodos Avaliativos'
        unique_together = ['ano_lectivo', 'numero_periodo']

class TenantConfiguracao(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    escola = models.OneToOneField(TenantEscola, on_delete=models.CASCADE, related_name='configuracao')
    ano_lectivo_activo = models.ForeignKey(AnoLectivo, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    periodo_activo = models.ForeignKey(PeriodoAvaliativo, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    nota_minima_aprovacao = models.DecimalField(max_digits=4, decimal_places=2, default=10)
    percentual_faltas_reprovacao = models.DecimalField(max_digits=5, decimal_places=2, default=25)
    permite_recuperacao = models.BooleanField(default=True)
    formato_numero_processo = models.CharField(max_length=50, default='ES-{ano}-{sequencia}')
    prefixo_factura = models.CharField(max_length=10, default='FT')
    moeda = models.CharField(max_length=3, default='AOA')
    dia_vencimento_propina = models.IntegerField(default=10, validators=[MinValueValidator(1), MaxValueValidator(28)])
    email_smtp_host = models.CharField(max_length=200, blank=True)
    email_smtp_port = models.IntegerField(default=587)
    email_remetente = models.EmailField(max_length=100, blank=True)
    sms_provider = models.CharField(max_length=50, blank=True)
    sms_api_key = models.CharField(max_length=200, blank=True)
    multicaixa_entity = models.CharField(max_length=20, blank=True)
    multicaixa_api_key = models.CharField(max_length=200, blank=True)
    
    class Meta:
        db_table = 'tenant_configuracao'
        verbose_name = 'Configuração da Escola'


class Diretor(models.Model):
    GENERO = [('M', 'Masculino'), ('F', 'Feminino')]
    NIVEL_ACADEMICO = [
        ('Bacharel', 'Bacharel'),
        ('Licenciado', 'Licenciado'),
        ('Mestre', 'Mestre'),
        ('Doutor', 'Doutor')
    ]
    
    STATUS = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
        ('Licença', 'Licença'),
        ('Demitido', 'Demitido')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(TenantEscola, on_delete=models.CASCADE)
    utilizador = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nome_completo = models.CharField(max_length=200)
    bi = models.CharField(max_length=20)
    data_nascimento = models.DateField()
    genero = models.CharField(max_length=1, choices=GENERO)
    nacionalidade = models.CharField(max_length=50, default='Angolana')
    especialidade = models.CharField(max_length=100)
    nivel_academico = models.CharField(max_length=20, choices=NIVEL_ACADEMICO)
    instituicao_formacao = models.CharField(max_length=200)
    anos_experiencia = models.IntegerField(default=0)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(max_length=100)
    endereco = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='Activo')
    
    class Meta:
        db_table = 'diretor'
        verbose_name = 'Director'
        verbose_name_plural = 'Directores'


class Curso(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(TenantEscola, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20)
    nome = models.CharField(max_length=200)
    nome_abreviado = models.CharField(max_length=50)
    descricao = models.TextField(blank=True)
    duracao_anos = models.IntegerField(default=3)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'curso'
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        unique_together = ['escola', 'codigo']


class Classe(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.IntegerField(validators=[MinValueValidator(10), MaxValueValidator(12)])
    designacao = models.CharField(max_length=50)
    ciclo = models.CharField(max_length=20, default='II Ciclo')
    ordem = models.IntegerField()
    
    class Meta:
        db_table = 'classe'
        verbose_name = 'Classe'
        verbose_name_plural = 'Classes'
        ordering = ['ordem']


class Disciplina(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(TenantEscola, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20)
    nome = models.CharField(max_length=200)
    nome_abreviado = models.CharField(max_length=10)
    descricao = models.TextField(blank=True)
    carga_horaria_semanal = models.IntegerField()
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'disciplina'
        verbose_name = 'Disciplina'
        verbose_name_plural = 'Disciplinas'
        unique_together = ['escola', 'codigo']


class CursoClasseDisciplina(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    obrigatoria = models.BooleanField(default=True)
    carga_horaria = models.IntegerField()
    ordem_exibicao = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'curso_classe_disciplina'
        verbose_name = 'Grade Curricular'
        verbose_name_plural = 'Grades Curriculares'
        unique_together = ['curso', 'classe', 'disciplina']

class Categoria(models.Model):

    categoria = models.CharField(max_length=100)

    def __str__(self):
        return self.categoria
    
class Professor(models.Model):
    GENERO = [('M', 'Masculino'), ('F', 'Feminino')]
    NIVEL_ACADEMICO = [
        ('Bacharel', 'Bacharel'),
        ('Licenciado', 'Licenciado'),
        ('Mestre', 'Mestre'),
        ('Doutor', 'Doutor')
    ]
    TIPO_CONTRATO = [
        ('Efectivo', 'Efectivo'),
        ('Contratado', 'Contratado'),
        ('Estagiário', 'Estagiário')
    ]
    STATUS = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
        ('Licença', 'Licença'),
        ('Demitido', 'Demitido')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(TenantEscola, on_delete=models.CASCADE)
    utilizador = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    numero_agente = models.CharField(max_length=50, unique=True)
    nome_completo = models.CharField(max_length=200)
    bi = models.CharField(max_length=20)
    data_nascimento = models.DateField()
    genero = models.CharField(max_length=1, choices=GENERO)
    nacionalidade = models.CharField(max_length=50, default='Angolana')
    especialidade = models.CharField(max_length=100)
    nivel_academico = models.CharField(max_length=20, choices=NIVEL_ACADEMICO)
    instituicao_formacao = models.CharField(max_length=200, blank=True, null=True)
    anos_experiencia = models.IntegerField(default=0, blank=True, null=True)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(max_length=100)
    endereco = models.TextField()
    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CONTRATO, blank=True, null=True)
    data_admissao = models.DateField()
    data_saida = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Activo')
    carga_horaria_semanal = models.IntegerField(default=0)
    salario_base = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    foto = models.ImageField(upload_to='professores/fotos/', blank=True, null=True)
    cv = models.FileField(upload_to='professores/cvs/', blank=True, null=True)
    
    class Meta:
        db_table = 'professor'
        verbose_name = 'Professor'
        verbose_name_plural = 'Professores'


class FormacaoProfessor(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, related_name='formacoes')
    titulo = models.CharField(max_length=200)
    instituicao = models.CharField(max_length=200)
    area = models.CharField(max_length=100)
    nivel = models.CharField(max_length=50)
    ano_conclusao = models.IntegerField()
    certificado = models.FileField(upload_to='professores/certificados/', blank=True, null=True)
    
    class Meta:
        db_table = 'formacao_professor'
        verbose_name = 'Formação do Professor'
        verbose_name_plural = 'Formações dos Professores'


class DisciplinaProfessor(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, related_name='disciplinas_lecionadas')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    anos_experiencia = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'disciplina_professor'
        verbose_name = 'Disciplina do Professor'
        verbose_name_plural = 'Disciplinas dos Professores'
        unique_together = ['professor', 'disciplina']


class Turma(models.Model):
    TURNO = [('Manhã', 'Manhã'), ('Tarde', 'Tarde'), ('Noite', 'Noite')]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(TenantEscola, on_delete=models.CASCADE)
    ano_lectivo = models.ForeignKey(AnoLectivo, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    designacao = models.CharField(max_length=10)
    sala = models.CharField(max_length=50, blank=True)
    turno = models.CharField(max_length=10, choices=TURNO)
    capacidade_maxima = models.IntegerField(default=40)
    vagas_disponiveis = models.IntegerField(default=40)
    director_turma = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True, related_name='turmas_dirigidas')
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'turma'
        verbose_name = 'Turma'
        verbose_name_plural = 'Turmas'
        unique_together = ['escola', 'ano_lectivo', 'classe', 'designacao']


class TurmaDisciplinaProfessor(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    ano_lectivo = models.ForeignKey(AnoLectivo, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'turma_disciplina_professor'
        verbose_name = 'Atribuição de Professor'
        verbose_name_plural = 'Atribuições de Professores'
        unique_together = ['turma', 'disciplina', 'ano_lectivo']


class HorarioAula(models.Model):
    DIA_SEMANA = [
        ('Segunda', 'Segunda-feira'),
        ('Terça', 'Terça-feira'),
        ('Quarta', 'Quarta-feira'),
        ('Quinta', 'Quinta-feira'),
        ('Sexta', 'Sexta-feira'),
        ('Sábado', 'Sábado')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='horarios')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    dia_semana = models.CharField(max_length=10, choices=DIA_SEMANA)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    sala = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = 'horario_aula'
        verbose_name = 'Horário de Aula'
        verbose_name_plural = 'Horários de Aulas'


class Aluno(models.Model):
    GENERO = [('M', 'Masculino'), ('F', 'Feminino')]
    STATUS = [
        ('Matriculado', 'Matriculado'),
        ('Transferido', 'Transferido'),
        ('Desistente', 'Desistente'),
        ('Concluído', 'Concluído'),
        ('Suspenso', 'Suspenso')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(TenantEscola, on_delete=models.CASCADE)
    utilizador = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL , blank=True, null=True)
    numero_processo = models.CharField(max_length=50, unique=True, blank=True, null=True)
    nome_completo = models.CharField(max_length=200)
    nome_pai = models.CharField(max_length=200)
    nome_mae = models.CharField(max_length=200)
    data_nascimento = models.DateField()
    naturalidade = models.CharField(max_length=100)
    nacionalidade = models.CharField(max_length=50, default='Angolana')
    bi = models.CharField(max_length=20, blank=True)
    data_emissao_bi = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=1, choices=GENERO)
    tipo_sanguineo = models.CharField(max_length=5, blank=True)
    necessidades_especiais = models.TextField(blank=True)
    foto = models.ImageField(upload_to='alunos/fotos/', blank=True, null=True)
    endereco_completo = models.TextField(blank=True, null=True)
    provincia = models.CharField(max_length=50)
    municipio = models.CharField(max_length=50)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Matriculado')
    data_criacao = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='alunos_criados')
    
    @property
    def idade(self):
        from datetime import date
        today = date.today()
        return today.year - self.data_nascimento.year - ((today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day))
    
    class Meta:
        db_table = 'aluno'
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'


class EncarregadoEducacao(models.Model):
    GENERO = [('M', 'Masculino'), ('F', 'Feminino')]
    PARENTESCO = [
        ('Pai', 'Pai'),
        ('Mãe', 'Mãe'),
        ('Avô', 'Avô'),
        ('Avó', 'Avó'),
        ('Tio', 'Tio'),
        ('Tia', 'Tia'),
        ('Irmão', 'Irmão'),
        ('Irmã', 'Irmã'),
        ('Tutor', 'Tutor')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(TenantEscola, on_delete=models.CASCADE)
    utilizador = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    nome_completo = models.CharField(max_length=200)
    bi = models.CharField(max_length=20)
    genero = models.CharField(max_length=1, choices=GENERO)
    parentesco = models.CharField(max_length=20, choices=PARENTESCO)
    profissao = models.CharField(max_length=100, blank=True)
    local_trabalho = models.CharField(max_length=200, blank=True)
    telefone_principal = models.CharField(max_length=20)
    telefone_alternativo = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    endereco = models.TextField(blank=True, null=True)
    e_contacto_emergencia = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'encarregado_educacao'
        verbose_name = 'Encarregado de Educação'
        verbose_name_plural = 'Encarregados de Educação'


class AlunoEncarregado(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='encarregados')
    encarregado = models.ForeignKey(EncarregadoEducacao, on_delete=models.CASCADE, related_name='alunos')
    e_responsavel_financeiro = models.BooleanField(default=True)
    e_responsavel_pedagogico = models.BooleanField(default=True)
    prioridade_contacto = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'aluno_encarregado'
        verbose_name = 'Encarregado do Aluno'
        verbose_name_plural = 'Encarregados dos Alunos'
        unique_together = ['aluno', 'encarregado']


class Matricula(models.Model):
    TIPO_MATRICULA = [
        ('Nova', 'Nova'),
        ('Renovação', 'Renovação'),
        ('Transferência', 'Transferência')
    ]
    STATUS = [
        ('Activa', 'Activa'),
        ('Cancelada', 'Cancelada'),
        ('Transferida', 'Transferida'),
        ('Concluída', 'Concluída')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='matriculas')
    ano_lectivo = models.ForeignKey(AnoLectivo, on_delete=models.CASCADE)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    data_matricula = models.DateField()
    numero_matricula = models.CharField(max_length=50, unique=True)
    tipo_matricula = models.CharField(max_length=20, choices=TIPO_MATRICULA)
    escola_origem = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Activa')
    observacoes = models.TextField(blank=True)
    documentos_entregues = models.JSONField(default=dict)
    matriculado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'matricula'
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
        unique_together = ['aluno', 'ano_lectivo']


class DocumentoAluno(models.Model):
    TIPO_DOCUMENTO = [
        ('BI', 'Bilhete de Identidade'),
        ('Certificado', 'Certificado'),
        ('Atestado', 'Atestado Médico'),
        ('Foto', 'Fotografia'),
        ('Boletim', 'Boletim de Notas'),
        ('Outros', 'Outros')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='documentos')
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO)
    titulo = models.CharField(max_length=200)
    arquivo = models.FileField(upload_to='alunos/documentos/')
    data_upload = models.DateTimeField(auto_now_add=True)
    uploaded_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'documento_aluno'
        verbose_name = 'Documento do Aluno'
        verbose_name_plural = 'Documentos dos Alunos'

class ContaAluno(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    ano_lectivo = models.ForeignKey(AnoLectivo, on_delete=models.CASCADE)
    saldo_devedor = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_pago = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_devido = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    STATUS = [("Em Dia","Em Dia"),("Pendente","Pendente"),("Atrasado","Atrasado"),("Bloqueado","Bloqueado")]
    status = models.CharField(max_length=20, choices=STATUS, default="Em Dia")
    ultima_actualizacao = models.DateTimeField(auto_now=True)

class Comunicado(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    TIPOS = [("Geral","Geral"),("Urgente","Urgente"),("Evento","Evento"),("Aviso","Aviso")]
    DEST = [("Todos","Todos"),("Alunos","Alunos"),("Professores","Professores"),("Encarregados","Encarregados"),("Turma Específica","Turma Específica")]
    escola = models.ForeignKey(TenantEscola, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS)
    destinatario_tipo = models.CharField(max_length=50, choices=DEST)
    turma = models.ForeignKey(Turma, on_delete=models.SET_NULL, null=True, blank=True)
    anexo = models.FileField(upload_to="comunicados/anexos/", null=True, blank=True)
    publicado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    data_publicacao = models.DateTimeField(auto_now_add=True)
    data_expiracao = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

class TipoAvaliacao(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(TenantEscola, on_delete=models.CASCADE)
    designacao = models.CharField(max_length=100)
    peso = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    descricao = models.TextField(blank=True)

    def __str__(self):
        return self.designacao


class Avaliacao(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True)
    periodo = models.ForeignKey(PeriodoAvaliativo, on_delete=models.CASCADE)
    tipo_avaliacao = models.ForeignKey(TipoAvaliacao, on_delete=models.SET_NULL, null=True, blank=True)
    designacao = models.CharField(max_length=200)
    data_realizacao = models.DateField()
    nota_maxima = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    observacoes = models.TextField(blank=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)


class Nota(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.CASCADE)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    nota = models.DecimalField(max_digits=6, decimal_places=2)
    observacao = models.TextField(blank=True)
    lancado_por = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True)
    data_lancamento = models.DateTimeField(auto_now_add=True)
    data_actualizacao = models.DateTimeField(auto_now=True)



class MaterialDidatico(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    TIPOS = [("Apostila","Apostila"),("Exercício","Exercício"),("Slide","Slide"),("Vídeo","Vídeo"),("Áudio","Áudio"),("Link","Link"),("Outro","Outro")]
    escola = models.ForeignKey(TenantEscola, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=50, choices=TIPOS)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True)
    arquivo = models.FileField(upload_to="materiais/arquivos/", null=True, blank=True)
    url_externa = models.CharField(max_length=500, blank=True)
    tamanho_arquivo = models.IntegerField(null=True, blank=True)
    visualizacoes = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0)
    publicado_por = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True)
    data_publicacao = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)


class AcessoMaterial(models.Model):

    material = models.ForeignKey(MaterialDidatico, on_delete=models.CASCADE)
    utilizador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    TIPO = [("Visualização","Visualização"),("Download","Download")]
    tipo_acesso = models.CharField(max_length=20, choices=TIPO)
    data_acesso = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=45, blank=True)