from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import AbstractUser
import uuid


class TimestampMixin(models.Model):
    
    data_criacao = models.DateTimeField(auto_now_add=True, null=True, verbose_name=_("Data de Criação"))
    data_actualizacao = models.DateTimeField(auto_now=True,null=True, verbose_name=_("Data de Actualização"))

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):

    activo = models.BooleanField(default=True, verbose_name=_("Activo"), db_index=True)
    data_desactivacao = models.DateTimeField(null=True, blank=True, verbose_name=_("Data de Desactivação"))

    class Meta:
        abstract = True

    def desactivar(self):
        self.activo = False
        self.data_desactivacao = timezone.now()
        self.save(update_fields=["activo", "data_desactivacao"])

    def activar(self):
        self.activo = True
        self.data_desactivacao = None
        self.save(update_fields=["activo", "data_desactivacao"])


class Utilizador(AbstractUser):

    class Genero(models.TextChoices):
        MASCULINO = "M", _("Masculino")
        FEMININO = "F", _("Feminino")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(
        "academico.TenantEscola",
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name="utilizadores",
        verbose_name=_("Escola"),
    )
    nome_completo = models.CharField(
        max_length=200, blank=True, null=True,
        db_index=True,
        verbose_name=_("Nome Completo"),
    )

    verificado_email = models.BooleanField(
        default=False,
        verbose_name=_("E-mail Verificado"),
    )
    verificado_telefone = models.BooleanField(
        default=False,
        verbose_name=_("Telefone Verificado"),
    )
    ultimo_acesso = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_("Último Acesso"),
    )
    criado_por = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="utilizadores_criados",
        verbose_name=_("Criado por"),
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name=_("Data de Criação"))
    data_actualizacao = models.DateTimeField(auto_now=True, verbose_name=_("Data de Actualização"))

    REQUIRED_FIELDS = ["email", "nome_completo"]

    class Meta:
        db_table = "utilizador"
        verbose_name = _("Utilizador")
        verbose_name_plural = _("Utilizadores")
        ordering = ["nome_completo"]
        indexes = [
            models.Index(fields=["escola"], name="idx_util_escola"),
            models.Index(fields=["escola", "is_active"], name="idx_util_escola_activo"),
            models.Index(fields=["email"], name="idx_util_email"),
            models.Index(fields=["username"], name="idx_util_username"),
            models.Index(fields=["nome_completo"], name="idx_util_nome"),
            models.Index(fields=["ultimo_acesso"], name="idx_util_ultimo_acesso"),
        ]

    def __str__(self) -> str:
        return self.nome_completo or self.username

    @property
    def esta_verificado(self) -> bool:
     
        return self.verificado_email and self.verificado_telefone

    def registar_acesso(self) -> None:
    
        self.ultimo_acesso = timezone.now()
        self.save(update_fields=["ultimo_acesso"])



class EscolaMixin(models.Model):
    escola = models.ForeignKey(
        "TenantEscola",
        on_delete=models.CASCADE,
        verbose_name=_("Escola"),
        db_index=True,
    )

    class Meta:
        abstract = True

class Role(TimestampMixin):

    class NomeRole(models.TextChoices):
        ADMIN = "admin", _("Administrador")
        ESTUDANTE = "estudante", _("Estudante")
        DIRECTOR = "director", _("Director")
        PROFESSOR = "professor", _("Professor")
        SECRETARIO = "secretario", _("Secretário")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(
        max_length=50,
        unique=True,
        choices=NomeRole.choices,
        verbose_name=_("Nome"),
    )
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Activo"))

    class Meta:
        db_table = "roles"
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["nome", "is_active"], name="idx_role_nome_activo"),
        ]
     

    def __str__(self) -> str:
        return self.get_nome_display()


class Permissao(TimestampMixin):

    class Recurso(models.TextChoices):
        USUARIO = "usuario", _("Utilizador")
        FUNCIONARIO = "funcionario", _("Funcionário")
        INSCRICAO = "inscricao", _("Inscrição")
        MATRICULA = "matricula", _("Matrícula")
        NOTA = "nota", _("Notas")
        DISCIPLINA = "disciplina", _("Disciplina")
        TURMA = "turma", _("Turma")
        FREQUENCIA = "frequencia", _("Frequência")
        ANO_LETIVO = "ano_letivo", _("Ano Lectivo")
        CURSO = "curso", _("Curso")
        SEMESTRE = "semestres", _("Semestres")
        PERIODO = "periodo", _("Período")

    class Acao(models.TextChoices):
        CRIAR = "criar", _("Criar")
        VISUALIZAR = "visualizar", _("Visualizar")
        ATUALIZAR = "atualizar", _("Editar")
        DELETAR = "deletar", _("Eliminar")
        PROCESSO_INSCRICAO = "processo_inscricao", _("Processar Inscrição")
        LANCAR_NOTA_CANDIDATO = "lancar_nota_candidato", _("Lançar Nota do Candidato")
        REALIZAR_MATRICULA = "realizar_matricula", _("Realizar Matrícula")
        ATRIBUIR_CARGA_HORARIA = "atribuir_carga_horaria", _("Atribuir Carga Horária")
        LANCAR_NOTA = "lancar_nota", _("Lançar Notas")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=50, choices=Recurso.choices, verbose_name=_("Recurso"))
    acao = models.CharField(max_length=50, choices=Acao.choices, verbose_name=_("Acção"))

    class Meta:
        db_table = "permissoes"
        unique_together = [["nome", "acao"]]
        verbose_name = _("Permissão")
        verbose_name_plural = _("Permissões")
        indexes = [
            models.Index(fields=["nome", "acao"], name="idx_permissao_recurso_acao"),
        ]

    def __str__(self) -> str:
        return f"{self.get_acao_display()} {self.get_nome_display()}"


class RolePermissao(models.Model):
    

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE,
        related_name="role_permissoes", verbose_name=_("Role"),
    )
    permissao = models.ForeignKey(
        Permissao, on_delete=models.CASCADE,
        related_name="role_permissoes", verbose_name=_("Permissão"),
    )
    atribuido_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "role_permissao"
        unique_together = [["role", "permissao"]]
        verbose_name = _("Permissão do Role")
        verbose_name_plural = _("Permissões dos Roles")
        indexes = [
            models.Index(fields=["role"], name="idx_rolepermissao_role"),
            models.Index(fields=["permissao"], name="idx_rolepermissao_permissao"),
        ]

    def __str__(self) -> str:
        return f"{self.role} → {self.permissao}"


class UsuarioRole(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilizador = models.ForeignKey(
        Utilizador, on_delete=models.CASCADE,
        related_name="usuario_roles", verbose_name=_("Utilizador"),
    )
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE,
        related_name="usuario_roles", verbose_name=_("Role"),
    )
    atribuido_em = models.DateTimeField(auto_now_add=True)
    atribuido_por = models.ForeignKey(
        Utilizador, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="roles_atribuidos", verbose_name=_("Atribuído por"),
    )

    class Meta:
        db_table = "role_usuario"
        unique_together = [["utilizador", "role"]]
        verbose_name = _("Role do Utilizador")
        verbose_name_plural = _("Roles dos Utilizadores")
        indexes = [
            models.Index(fields=["utilizador"], name="idx_usuariorole_utilizador"),
            models.Index(fields=["role"], name="idx_usuariorole_role"),
        ]

    def __str__(self) -> str:
        return f"{self.utilizador} — {self.role}"


class PlanoSubscricao(TimestampMixin, SoftDeleteMixin):

    class TipoPlano(models.TextChoices):
        BASICO = "basico", _("Básico")
        PLUS = "plus", _("Plus")


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=100, choices=TipoPlano.choices, default=TipoPlano.BASICO, unique=True, verbose_name=_("Nome"))
    descricao = models.TextField(verbose_name=_("Descrição"))
    preco_mensal = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Preço Mensal"),
    )
    preco_anual = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Preço Anual"),
    )
    max_alunos = models.IntegerField(validators=[MinValueValidator(1)], verbose_name=_("Máx. Alunos"))
    max_professores = models.IntegerField(validators=[MinValueValidator(1)], verbose_name=_("Máx. Professores"))
    max_turmas = models.IntegerField(validators=[MinValueValidator(1)], verbose_name=_("Máx. Turmas"))

    class Meta:
        db_table = "plano_subscricao"
        verbose_name = _("Plano de Subscrição")
        verbose_name_plural = _("Planos de Subscrição")
        ordering = ["preco_mensal"]
        constraints = [
            models.CheckConstraint(condition=models.Q(preco_mensal__gte=0), name="chk_plano_preco_mensal_positivo"),
            models.CheckConstraint(condition=models.Q(preco_anual__gte=0), name="chk_plano_preco_anual_positivo"),
            models.CheckConstraint(condition=models.Q(max_alunos__gte=1), name="chk_plano_max_alunos"),
        ]

    def __str__(self):
        return self.get_nome_display()


class TenantEscola(TimestampMixin, SoftDeleteMixin):

    class TipoEnsino(models.TextChoices):
        PRIVADO = "Privado", _("Privado")
        PUBLICO = "Público", _("Público")

    class StatusEnsino(models.TextChoices):
        PENDENTE = "pendente", _("Pendente")
        ACTIVA = "activa", _("Activa")
        INACTIVA = "inactiva", _("Inactiva")

    nif_validator = RegexValidator(
        regex=r"^\d{9,14}$",
        message=_("NIF inválido. Deve conter entre 9 e 14 dígitos."),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200, verbose_name=_("Nome"))
    nif = models.CharField(
        max_length=20, unique=True,
        validators=[nif_validator],
        verbose_name=_("NIF"),
    )
    email = models.EmailField(max_length=100, verbose_name=_("E-mail"))
    telefone = models.CharField(max_length=20, verbose_name=_("Telefone"))
    telefone_alternativo = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Telefone Alternativo"))
    logotipo = models.ImageField(upload_to="escolas/logos/", blank=True, null=True, verbose_name=_("Logótipo"))
    endereco_completo = models.TextField(verbose_name=_("Endereço Completo"))
    provincia = models.CharField(max_length=50, verbose_name=_("Província"))
    municipio = models.CharField(max_length=50, verbose_name=_("Município"))
    bairro = models.CharField(max_length=100, verbose_name=_("Bairro"))
    tipo_ensino = models.CharField(max_length=10, choices=TipoEnsino.choices, verbose_name=_("Tipo de Ensino"))
    status_ensino = models.CharField(max_length=10, choices=StatusEnsino.choices, verbose_name=_("Status de Ensino"))
    numero_alvara = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Número de Alvará"))
    plano_subscricao = models.ForeignKey(
        PlanoSubscricao, on_delete=models.PROTECT,
        verbose_name=_("Plano de Subscrição"),
    )
    data_expiracao_plano = models.DateField(verbose_name=_("Expiração do Plano"))

    class Meta:
        db_table = "tenant_escola"
        verbose_name = _("Escola")
        verbose_name_plural = _("Escolas")
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["nif"], name="idx_escola_nif"),
            models.Index(fields=["activo"], name="idx_escola_activo"),
            models.Index(fields=["provincia", "municipio"], name="idx_escola_localizacao"),
            models.Index(fields=["data_expiracao_plano"], name="idx_escola_expiracao"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(data_expiracao_plano__gte=models.F("data_criacao__date")),
                name="chk_escola_expiracao_futura",
            )
        ]

    def __str__(self):
        return self.nome

    @property
    def plano_expirado(self) -> bool:
        return self.data_expiracao_plano < timezone.now().date()


class Periodo(EscolaMixin):

    class Turno(models.TextChoices):
        MANHA = "manha", _("Manhã")
        TARDE = "tarde", _("Tarde")
        NOITE = "noite", _("Noite")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designacao = models.CharField(
        max_length=60,
        choices=Turno.choices,
        unique=True,
        verbose_name=_("Designação"),
    )

    class Meta:
        verbose_name = _("Período")
        verbose_name_plural = _("Períodos")

    def __str__(self) -> str:
        return self.get_designacao_display()


class Trimestre(EscolaMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designacao = models.CharField(max_length=50, unique=True, verbose_name=_("Designação"))
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)

    activo = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Trimestre")
        verbose_name_plural = _("Trimestres")
        ordering = ["designacao"]

    def __str__(self) -> str:
        return self.designacao

class AnoLectivo(EscolaMixin, TimestampMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designacao = models.CharField(max_length=50, verbose_name=_("Designação"))
    data_inicio = models.DateField(verbose_name=_("Data de Início"))
    data_fim = models.DateField(verbose_name=_("Data de Fim"))
    e_atual = models.BooleanField(default=False, db_index=True, verbose_name=_("É Actual"))

    class Meta:
        db_table = "ano_lectivo"
        verbose_name = _("Ano Lectivo")
        verbose_name_plural = _("Anos Lectivos")
        unique_together = [["escola", "designacao"]]
        indexes = [
            models.Index(fields=["escola", "e_atual"], name="idx_anolectivo_escola_atual"),
            models.Index(fields=["data_inicio", "data_fim"], name="idx_anolectivo_periodo"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(data_fim__gt=models.F("data_inicio")),
                name="chk_anolectivo_datas_validas",
            )
        ]

    def __str__(self):
        return self.designacao

    def clean(self):
        if self.data_inicio and self.data_fim and self.data_fim <= self.data_inicio:
            raise ValidationError(_("A data de fim deve ser posterior à data de início."))


class PeriodoAvaliativo(TimestampMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ano_lectivo = models.ForeignKey(
        AnoLectivo, on_delete=models.CASCADE,
        related_name="periodos", verbose_name=_("Ano Lectivo"),
    )
    numero_periodo = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        verbose_name=_("Número do Período"),
    )
    designacao = models.CharField(max_length=50, verbose_name=_("Designação"))
    data_inicio = models.DateField(verbose_name=_("Data de Início"))
    data_fim = models.DateField(verbose_name=_("Data de Fim"))
    activo = models.BooleanField(default=False, db_index=True, verbose_name=_("Activo"))

    class Meta:
        db_table = "periodo_avaliativo"
        verbose_name = _("Período Avaliativo")
        verbose_name_plural = _("Períodos Avaliativos")
        unique_together = [["ano_lectivo", "numero_periodo"]]
        indexes = [
            models.Index(fields=["ano_lectivo", "activo"], name="idx_periodo_activo"),
            models.Index(fields=["data_inicio", "data_fim"], name="idx_periodo_datas"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(data_fim__gt=models.F("data_inicio")),
                name="chk_periodo_datas_validas",
            ),
            models.CheckConstraint(
                condition=models.Q(numero_periodo__gte=1) & models.Q(numero_periodo__lte=3),
                name="chk_periodo_numero_valido",
            ),
        ]

    def __str__(self):
        return self.designacao

    def clean(self):
        if self.data_inicio and self.data_fim and self.data_fim <= self.data_inicio:
            raise ValidationError(_("A data de fim deve ser posterior à data de início."))


class TenantConfiguracao(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.OneToOneField(
        TenantEscola, on_delete=models.CASCADE,
        related_name="configuracao", verbose_name=_("Escola"),
    )
    ano_lectivo_activo = models.ForeignKey(
        AnoLectivo, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", verbose_name=_("Ano Lectivo Activo"),
    )
    periodo_activo = models.ForeignKey(
        PeriodoAvaliativo, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+", verbose_name=_("Período Activo"),
    )
    nota_minima_aprovacao = models.DecimalField(
        max_digits=4, decimal_places=2, default=10,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name=_("Nota Mínima de Aprovação"),
    )
    percentual_faltas_reprovacao = models.DecimalField(
        max_digits=5, decimal_places=2, default=25,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("% Faltas para Reprovação"),
    )
    permite_recuperacao = models.BooleanField(default=True, verbose_name=_("Permite Recuperação"))
    formato_numero_processo = models.CharField(
        max_length=50, default="ES-{ano}-{sequencia}",
        verbose_name=_("Formato Nº Processo"),
    )
    prefixo_factura = models.CharField(max_length=10, default="FT", verbose_name=_("Prefixo Factura"))
    moeda = models.CharField(max_length=3, default="AOA", verbose_name=_("Moeda"))
    dia_vencimento_propina = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        verbose_name=_("Dia Vencimento Propina"),
    )

    email_smtp_host = models.CharField(max_length=200, blank=True, verbose_name=_("SMTP Host"))
    email_smtp_port = models.IntegerField(default=587, verbose_name=_("SMTP Port"))
    email_remetente = models.EmailField(max_length=100, blank=True, verbose_name=_("E-mail Remetente"))
    # SMS
    sms_provider = models.CharField(max_length=50, blank=True, verbose_name=_("Provedor SMS"))
    sms_api_key = models.CharField(max_length=200, blank=True, verbose_name=_("SMS API Key"))
    # Pagamentos
    multicaixa_entity = models.CharField(max_length=20, blank=True, verbose_name=_("Multicaixa Entidade"))
    multicaixa_api_key = models.CharField(max_length=200, blank=True, verbose_name=_("Multicaixa API Key"))

    class Meta:
        db_table = "tenant_configuracao"
        verbose_name = _("Configuração da Escola")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nota_minima_aprovacao__gte=0) & models.Q(nota_minima_aprovacao__lte=20),
                name="chk_config_nota_aprovacao_valida",
            ),
            models.CheckConstraint(
                condition=models.Q(percentual_faltas_reprovacao__gte=0) & models.Q(percentual_faltas_reprovacao__lte=100),
                name="chk_config_percentual_faltas_valido",
            ),
        ]

    def __str__(self):
        return f"Config — {self.escola}"

class PessoaMixin(models.Model):

    class Genero(models.TextChoices):
        MASCULINO = "M", _("Masculino")
        FEMININO = "F", _("Feminino")

    class NivelAcademico(models.TextChoices):
        TECNICO_MEDIO = "Tecnico_medio", _("Técnico Médio")
        BACHAREL = "Bacharel", _("Bacharel")
        LICENCIADO = "Licenciado", _("Licenciado")
        MESTRE = "Mestre", _("Mestre")
        DOUTOR = "Doutor", _("Doutor")

    nome_completo = models.CharField(max_length=200, verbose_name=_("Nome Completo"), db_index=True)
    bi = models.CharField(max_length=20, verbose_name=_("Bilhete de Identidade"))
    data_nascimento = models.DateField(null=True, blank=True, verbose_name=_("Data de Nascimento"))
    genero = models.CharField(max_length=1, choices=Genero.choices, blank=True, null=True, verbose_name=_("Género"))
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Telefone"))
    email = models.EmailField(max_length=100, blank=True, null=True, verbose_name=_("E-mail"))
    endereco = models.TextField(blank=True, null=True, verbose_name=_("Endereço"))

    class Meta:
        abstract = True

    @property
    def idade(self) -> int | None:
        if not self.data_nascimento:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.data_nascimento.year - (
            (today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )


class Diretor(EscolaMixin, PessoaMixin, TimestampMixin):

    class Status(models.TextChoices):
        ACTIVO = "Activo", _("Activo")
        INACTIVO = "Inactivo", _("Inactivo")
        LICENCA = "Licença", _("Licença")
        DEMITIDO = "Demitido", _("Demitido")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilizador = models.OneToOneField(
        Utilizador, on_delete=models.CASCADE,
        verbose_name=_("Utilizador"), related_name="director"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVO, db_index=True, verbose_name=_("Estado"))

    class Meta:
        db_table = "diretor"
        verbose_name = _("Director")
        verbose_name_plural = _("Directores")
        indexes = [
            models.Index(fields=["escola", "status"], name="idx_diretor_escola_status"),
        ]

    def __str__(self):
        return self.nome_completo


class Categoria(EscolaMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    categoria = models.CharField(max_length=100, verbose_name=_("Categoria"))

    class Meta:
        db_table = "categoria"
        verbose_name = _("Categoria")
        verbose_name_plural = _("Categorias")
        unique_together = [["escola", "categoria"]]

    def __str__(self):
        return self.categoria


class Funcionario(EscolaMixin, PessoaMixin, TimestampMixin):

    class TipoContrato(models.TextChoices):
        EFECTIVO = "Efectivo", _("Efectivo")
        CONTRATADO = "Contratado", _("Contratado")
        ESTAGIARIO = "Estagiário", _("Estagiário")

    class TipoFuncionario(models.TextChoices):
        ADMINISTRATIVO = "Administrativo", _("Administrativo")
        PROFESSOR = "Professor", _("Professor")

    class Status(models.TextChoices):
        ACTIVO = "Activo", _("Activo")
        INACTIVO = "Inactivo", _("Inactivo")
        LICENCA = "Licença", _("Licença")
        DEMITIDO = "Demitido", _("Demitido")


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilizador = models.OneToOneField(
        Utilizador, on_delete=models.SET_NULL,
        blank=True, null=True, verbose_name=_("Utilizador"), related_name="funcionario"
    )
    numero_agente = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name=_("Nº Agente"))
    especialidade = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Especialidade"))
    nivel_academico = models.CharField(max_length=20, choices=PessoaMixin.NivelAcademico.choices, verbose_name=_("Nível Académico"))
    instituicao_formacao = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("Instituição de Formação"))
    anos_experiencia = models.IntegerField(default=0, blank=True, null=True, validators=[MinValueValidator(0)], verbose_name=_("Anos de Experiência"))
    tipo_contrato = models.CharField(max_length=20, choices=TipoContrato.choices, blank=True, null=True, verbose_name=_("Tipo de Contrato"))
    tipo_funcionario = models.CharField(max_length=20, choices=TipoFuncionario.choices, blank=True, null=True, verbose_name=_("Tipo de Funcionário"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVO, db_index=True, verbose_name=_("Estado"))
    carga_horaria_semanal = models.IntegerField(
        default=0, blank=True, null=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Carga Horária Semanal"),
    )

    class Meta:
        db_table = "funcionario"
        verbose_name = _("Funcionário")
        verbose_name_plural = _("Funcionários")
        indexes = [
            models.Index(fields=["escola", "status"], name="idx_funcionario_escola_status"),
            models.Index(fields=["nome_completo"], name="idx_funcionario_nome"),
        ]

    def __str__(self):
        return self.nome_completo


class Curso(EscolaMixin, TimestampMixin, SoftDeleteMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200, verbose_name=_("Nome"))
    nome_abreviado = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Nome Abreviado"))
    duracao_anos = models.IntegerField(
        default=3, blank=True, null=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name=_("Duração (anos)"),
    )

    class Meta:
        db_table = "curso"
        verbose_name = _("Curso")
        verbose_name_plural = _("Cursos")
        unique_together = [["escola", "nome"]]
        indexes = [
            models.Index(fields=["escola", "activo"], name="idx_curso_escola_activo"),
        ]

    def __str__(self):
        return self.nome


class Classe(EscolaMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.IntegerField(
        blank=True, null=True, verbose_name=_("Número"),
    )
    designacao = models.CharField(max_length=50, verbose_name=_("Designação"))
    ordem = models.IntegerField(blank=True, null=True, verbose_name=_("Ordem"))

    class Meta:
        db_table = "classe"
        verbose_name = _("Classe")
        verbose_name_plural = _("Classes")
        ordering = ["ordem"]
        unique_together = [["escola", "designacao"]]
        indexes = [
            models.Index(fields=["escola", "numero"], name="idx_classe_escola_numero"),
        ]

    def __str__(self):
        return self.designacao


class Disciplina(EscolaMixin, TimestampMixin, SoftDeleteMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200, verbose_name=_("Nome"))
    nome_abreviado = models.CharField(max_length=10, verbose_name=_("Abreviatura"))

    class Meta:
        db_table = "disciplina"
        verbose_name = _("Disciplina")
        verbose_name_plural = _("Disciplinas")
        indexes = [
            models.Index(fields=["escola", "activo"], name="idx_disciplina_escola_activo"),
            models.Index(fields=["nome"], name="idx_disciplina_nome"),
        ]

    def __str__(self):
        return self.nome



class Turma(EscolaMixin, TimestampMixin, SoftDeleteMixin):


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    designacao = models.CharField(max_length=60, verbose_name=_("Designação"))
    ano_lectivo = models.ForeignKey(AnoLectivo, on_delete=models.CASCADE, verbose_name=_("Ano Lectivo"), related_name='turmas')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, verbose_name=_("Curso"), related_name='turmas')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, verbose_name=_("Classe"), related_name='turmas')
    periodo = models.ForeignKey(Periodo, on_delete=models.PROTECT, verbose_name=_("Período"), related_name='turmas')
    sala = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Sala"))
    capacidade_maxima = models.IntegerField(
        default=40, blank=True, null=True,
        validators=[MinValueValidator(1)],
        verbose_name=_("Capacidade Máxima"),
    )
    vagas_disponiveis = models.IntegerField(
        default=40, blank=True, null=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Vagas Disponíveis"),
    )
    classificacao_positiva = models.CharField(max_length=40, verbose_name=_("Classificação positiva"))
    classificacao_negativa = models.CharField(max_length=40, verbose_name=_("Classificação negativa"))
    valor_minimo = models.PositiveIntegerField(default=0, verbose_name=_("Valor mínimo"))
    valor_maximo = models.PositiveIntegerField(default=20, verbose_name=_("Valor máximo"))

    preco_matricula = models.DecimalField(max_digits=12, blank=True, null=True, decimal_places=2, verbose_name=_("Preço matrícula"))
    preco_propina = models.DecimalField(max_digits=12, blank=True, null=True, decimal_places=2, verbose_name=_("Preço propina"))
    preco_confirmacao = models.DecimalField(max_digits=12, blank=True, null=True, decimal_places=2, verbose_name=_("Preço confirmação"))

    class Meta:
        db_table = "turma"
        verbose_name = _("Turma")
        verbose_name_plural = _("Turmas")
        unique_together = [["escola", "ano_lectivo", "classe", "designacao"]]
        indexes = [
            models.Index(fields=["escola", "ano_lectivo"], name="idx_turma_escola_ano"),
            models.Index(fields=["escola", "ano_lectivo", "activo"], name="idx_turma_activa"),
            models.Index(fields=["curso", "classe"], name="idx_turma_curso_classe"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(vagas_disponiveis__lte=models.F("capacidade_maxima")),
                name="chk_turma_vagas_nao_excedem_capacidade",
            )
        ]

    def __str__(self):
        return f"{self.curso.nome_abreviado} — {self.classe.designacao} {self.designacao}"


class TurmaDisciplina(EscolaMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    turma = models.ForeignKey(Turma, on_delete=models.PROTECT, verbose_name=_("Turma"), related_name='turma_disciplinas')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.PROTECT, verbose_name=_("Disciplina"),related_name='turma_disciplinas')
    professor = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Professor"), related_name='turma_disciplinas')
    carga_horaria = models.PositiveIntegerField(default=0, verbose_name=_("Carga Horária (h)"))

    class Meta:
        db_table = "turma_disciplina"
        verbose_name = _("Atribuição de Disciplina")
        verbose_name_plural = _("Atribuições de Disciplinas")
        unique_together = [["turma", "disciplina"]]
        indexes = [
            models.Index(fields=["turma"], name="idx_tdp_turma"),
            models.Index(fields=["professor"], name="idx_tdp_professor"),
        ]

    def __str__(self):
        return f"{self.turma} | {self.disciplina} | {self.professor}"


class HorarioAula(EscolaMixin):

    class DiaSemana(models.TextChoices):
        SEGUNDA = "Segunda", _("Segunda-feira")
        TERCA = "Terça", _("Terça-feira")
        QUARTA = "Quarta", _("Quarta-feira")
        QUINTA = "Quinta", _("Quinta-feira")
        SEXTA = "Sexta", _("Sexta-feira")
        SABADO = "Sábado", _("Sábado")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name="horarios", verbose_name=_("Turma"))
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, verbose_name=_("Disciplina"))
    professor = models.ForeignKey(Funcionario, on_delete=models.CASCADE, verbose_name=_("Professor"))
    dia_semana = models.CharField(max_length=10, choices=DiaSemana.choices, verbose_name=_("Dia da Semana"))
    hora_inicio = models.TimeField(verbose_name=_("Hora de Início"))
    hora_fim = models.TimeField(verbose_name=_("Hora de Fim"))
    sala = models.CharField(max_length=50, blank=True, verbose_name=_("Sala"))

    class Meta:
        db_table = "horario_aula"
        verbose_name = _("Horário de Aula")
        verbose_name_plural = _("Horários de Aulas")
        indexes = [
            models.Index(fields=["turma", "dia_semana"], name="idx_horario_turma_dia"),
            models.Index(fields=["professor", "dia_semana"], name="idx_horario_professor_dia"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(hora_fim__gt=models.F("hora_inicio")),
                name="chk_horario_horas_validas",
            )
        ]

    def __str__(self):
        return f"{self.dia_semana} {self.hora_inicio}–{self.hora_fim} | {self.turma}"

    def clean(self):
        if self.hora_inicio and self.hora_fim and self.hora_fim <= self.hora_inicio:
            raise ValidationError(_("A hora de fim deve ser posterior à hora de início."))

class Aluno(EscolaMixin, PessoaMixin, TimestampMixin):

    class Status(models.TextChoices):
        MATRICULADO = "Matriculado", _("Matriculado")
        TRANSFERIDO = "Transferido", _("Transferido")
        DESISTENTE = "Desistente", _("Desistente")
        CONCLUIDO = "Concluído", _("Concluído")
        SUSPENSO = "Suspenso", _("Suspenso")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilizador = models.OneToOneField(
        'Utilizador', on_delete=models.SET_NULL,
        blank=True, null=True, verbose_name=_("Utilizador"), related_name="aluno"
    )
    numero_processo = models.CharField(
        max_length=50, unique=True, blank=True, null=True, verbose_name=_("Nº Processo"),
    )
    nome_pai = models.CharField(max_length=200, verbose_name=_("Nome do Pai"))
    nome_mae = models.CharField(max_length=200, verbose_name=_("Nome da Mãe"))
    naturalidade = models.CharField(max_length=100, verbose_name=_("Naturalidade"))
    data_emissao_bi = models.DateField(null=True, blank=True, verbose_name=_("Data de Emissão do BI"))
    necessidades_especiais = models.TextField(blank=True, verbose_name=_("Necessidades Especiais"))
    foto = models.ImageField(upload_to="alunos/fotos/", blank=True, null=True, verbose_name=_("Foto"))
    endereco_completo = models.TextField(blank=True, null=True, verbose_name=_("Endereço Completo"))
    provincia = models.CharField(max_length=50, verbose_name=_("Província"))
    municipio = models.CharField(max_length=50, verbose_name=_("Município"))
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Bairro"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.MATRICULADO, db_index=True, verbose_name=_("Estado"))
    criado_por = models.ForeignKey(
        Utilizador, on_delete=models.SET_NULL, null=True,
        related_name="alunos_criado", verbose_name=_("Criado por"),
    )

    class Meta:
        db_table = "aluno"
        verbose_name = _("Aluno")
        verbose_name_plural = _("Alunos")
        indexes = [
            models.Index(fields=["escola", "status"], name="idx_aluno_escola_status"),
            models.Index(fields=["nome_completo"], name="idx_aluno_nome"),
            models.Index(fields=["numero_processo"], name="idx_aluno_processo"),
            models.Index(fields=["bi"], name="idx_aluno_bi"),
        ]

    def __str__(self):
        return self.nome_completo


class EncarregadoEducacao(EscolaMixin, TimestampMixin):

    class Parentesco(models.TextChoices):
        PAI = "Pai", _("Pai")
        MAE = "Mãe", _("Mãe")
        AVO_M = "Avô", _("Avô")
        AVO_F = "Avó", _("Avó")
        TIO = "Tio", _("Tio")
        TIA = "Tia", _("Tia")
        IRMAO = "Irmão", _("Irmão")
        IRMA = "Irmã", _("Irmã")
        TUTOR = "Tutor", _("Tutor")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilizador = models.OneToOneField(
        Utilizador, on_delete=models.SET_NULL,
        blank=True, null=True, verbose_name=_("Utilizador"),
    )
    nome_completo = models.CharField(max_length=200, db_index=True, verbose_name=_("Nome Completo"))
    bi = models.CharField(max_length=20, verbose_name=_("BI"))
    genero = models.CharField(max_length=1, choices=PessoaMixin.Genero.choices, verbose_name=_("Género"))
    parentesco = models.CharField(max_length=20, choices=Parentesco.choices, verbose_name=_("Parentesco"))
    profissao = models.CharField(max_length=100, blank=True, verbose_name=_("Profissão"))
    local_trabalho = models.CharField(max_length=200, blank=True, verbose_name=_("Local de Trabalho"))
    telefone_principal = models.CharField(max_length=20, blank=True, verbose_name=_("Telefone Principal"))
    telefone_alternativo = models.CharField(max_length=20, blank=True, verbose_name=_("Telefone Alternativo"))
    e_contacto_emergencia = models.BooleanField(default=True, verbose_name=_("É Contacto de Emergência"))

    class Meta:
        db_table = "encarregado_educacao"
        verbose_name = _("Encarregado de Educação")
        verbose_name_plural = _("Encarregados de Educação")
        indexes = [
            models.Index(fields=["escola"], name="idx_encarregado_escola"),
        ]

    def __str__(self):
        return self.nome_completo


class AlunoEncarregado(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="encarregados", verbose_name=_("Aluno"))
    encarregado = models.ForeignKey(EncarregadoEducacao, on_delete=models.CASCADE, related_name="alunos", verbose_name=_("Encarregado"))

    class Meta:
        db_table = "aluno_encarregado"
        verbose_name = _("Encarregado do Aluno")
        verbose_name_plural = _("Encarregados dos Alunos")
        unique_together = [["aluno", "encarregado"]]
        indexes = [
            models.Index(fields=["aluno"], name="idx_alunoenc_aluno"),
            models.Index(fields=["encarregado"], name="idx_alunoenc_encarregado"),
        ]


# ==============================================================================
# INSCRIÇÃO & MATRÍCULA
# ==============================================================================

class Candidato(EscolaMixin, PessoaMixin, TimestampMixin):

    class Status(models.TextChoices):
        MATRICULADO = "Matriculado", _("Matriculado")
        TRANSFERIDO = "Transferido", _("Transferido")
        DESISTENTE = "Desistente", _("Desistente")
        CONCLUIDO = "Concluído", _("Concluído")
        SUSPENSO = "Suspenso", _("Suspenso")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilizador = models.OneToOneField(
        Utilizador, on_delete=models.SET_NULL,
        blank=True, null=True, verbose_name=_("Utilizador"), related_name="candidato"
    )
    nome_pai = models.CharField(max_length=200, verbose_name=_("Nome do Pai"))
    nome_mae = models.CharField(max_length=200, verbose_name=_("Nome da Mãe"))
    naturalidade = models.CharField(max_length=100, verbose_name=_("Naturalidade"))
    data_emissao_bi = models.DateField(null=True, blank=True, verbose_name=_("Data de Emissão do BI"))
    necessidades_especiais = models.TextField(blank=True, verbose_name=_("Necessidades Especiais"))
    endereco_completo = models.TextField(blank=True, null=True, verbose_name=_("Endereço Completo"))
    provincia = models.CharField(max_length=50, verbose_name=_("Província"))
    municipio = models.CharField(max_length=50, verbose_name=_("Município"))
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Bairro"))
    criado_por = models.ForeignKey(
        Utilizador, on_delete=models.SET_NULL, null=True,
        related_name="alunos_criados", verbose_name=_("Criado por"),
    )

    class Meta:
        db_table = "candidato"
        verbose_name = _("Candidato")
        verbose_name_plural = _("Candidatos")
        indexes = [
            models.Index(fields=["escola"], name="idx_candidato_escola"),
            models.Index(fields=["nome_completo"], name="idx_candidato_nome"),
            models.Index(fields=["bi"], name="idx_candidato_bi"),
        ]

    def __str__(self):
        return self.nome_completo

class Inscricao(EscolaMixin, TimestampMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidato = models.ForeignKey(Candidato, on_delete=models.PROTECT, related_name="inscricoes", verbose_name=_("candidato"))
    periodo = models.ForeignKey(Periodo, on_delete=models.PROTECT, related_name="inscricoes", verbose_name=_("Período"))
    ano_lectivo = models.ForeignKey(AnoLectivo, on_delete=models.PROTECT, verbose_name=_("Ano Lectivo"), related_name="inscricoes")
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Curso"), related_name="inscricoes")
    inscrito_por = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, null=True, verbose_name=_("Inscrito por"))
    data_inscricao = models.DateField(auto_now_add=True, verbose_name=_("Data de Inscrição"))
    documentos_entregues = models.JSONField(default=dict, verbose_name=_("Documentos Entregues"))

    class Meta:
        db_table = "inscricao"
        verbose_name = _("Inscrição")
        verbose_name_plural = _("Inscrições")
        indexes = [
            models.Index(fields=["escola", "ano_lectivo"], name="idx_inscricao_escola_ano"),
        ]

    def __str__(self):
        return f"{self.aluno} — {self.ano_lectivo}"


class Matricula(EscolaMixin, TimestampMixin):

    class TipoMatricula(models.TextChoices):
        NOVA = "Nova", _("Nova")
        RENOVACAO = "Renovação", _("Renovação")
        TRANSFERENCIA = "Transferência", _("Transferência")

    class Status(models.TextChoices):
        ACTIVA = "Activa", _("Activa")
        CANCELADA = "Cancelada", _("Cancelada")
        TRANSFERIDA = "Transferida", _("Transferida")
        CONCLUIDA = "Concluída", _("Concluída")
        TRANCAMENTO = "Trancamento", _("Trancamento")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="matriculas", verbose_name=_("Aluno"))
    ano_lectivo = models.ForeignKey(AnoLectivo, on_delete=models.CASCADE, verbose_name=_("Ano Lectivo"), related_name="matriculas")
    turma = models.ForeignKey(Turma, on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Turma"), related_name='matriculas')
    numero_matricula = models.CharField(
        max_length=50, unique=True, blank=True, null=True,
        db_index=True, verbose_name=_("Nº Matrícula"),
    )
    tipo_matricula = models.CharField(max_length=20, choices=TipoMatricula.choices, verbose_name=_("Tipo"))
    escola_origem = models.CharField(max_length=200, blank=True, verbose_name=_("Escola de Origem"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVA, db_index=True, verbose_name=_("Estado"))
    motivo_cancelamento = models.TextField(blank=True, null=True, verbose_name=_("Motivo de Cancelamento"))
    observacoes = models.TextField(blank=True, verbose_name=_("Observações"))
    documentos_entregues = models.JSONField(default=dict, verbose_name=_("Documentos Entregues"))
    matriculado_por = models.ForeignKey(
        Utilizador, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Matriculado por"), related_name="matriculas"
    )
    data_matricula = models.DateField(auto_now_add=True, verbose_name=_("Data de Matrícula"))

    class Meta:
        db_table = "matricula"
        verbose_name = _("Matrícula")
        verbose_name_plural = _("Matrículas")
        unique_together = [["aluno", "ano_lectivo"]]
        indexes = [
            models.Index(fields=["escola", "ano_lectivo", "status"], name="matricula_escola_ano_status"),
            models.Index(fields=["aluno", "ano_lectivo"], name="idx_matricula_aluno_ano"),
            models.Index(fields=["turma", "ano_lectivo"], name="idx_matricula_turma_ano"),
            models.Index(fields=["numero_matricula"], name="idx_matricula_numero"),
        ]

    def __str__(self):
        return f"{self.aluno.nome_completo} — {self.numero_matricula}"


class DocumentoAluno(EscolaMixin, TimestampMixin):

    class TipoDocumento(models.TextChoices):
        BI = "BI", _("Bilhete de Identidade")
        CERTIFICADO = "Certificado", _("Certificado")
        ATESTADO = "Atestado", _("Atestado Médico")
        FOTO = "Foto", _("Fotografia")
        BOLETIM = "Boletim", _("Boletim de Notas")
        OUTROS = "Outros", _("Outros")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="documentos", verbose_name=_("Aluno"))
    tipo_documento = models.CharField(max_length=20, choices=TipoDocumento.choices, verbose_name=_("Tipo"))
    titulo = models.CharField(max_length=200, verbose_name=_("Título"))
    arquivo = models.FileField(upload_to="alunos/documentos/", verbose_name=_("Arquivo"))
    data_upload = models.DateTimeField(auto_now_add=True, verbose_name=_("Data de Upload"))
    uploaded_por = models.ForeignKey(
        Utilizador, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Carregado por"),
    )

    class Meta:
        db_table = "documento_aluno"
        verbose_name = _("Documento do Aluno")
        verbose_name_plural = _("Documentos dos Alunos")
        indexes = [
            models.Index(fields=["aluno", "tipo_documento"], name="idx_docaluno_aluno_tipo"),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.aluno})"


class ContaAluno(EscolaMixin, TimestampMixin):

    class Status(models.TextChoices):
        EM_DIA = "Em Dia", _("Em Dia")
        PENDENTE = "Pendente", _("Pendente")
        ATRASADO = "Atrasado", _("Atrasado")
        BLOQUEADO = "Bloqueado", _("Bloqueado")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, verbose_name=_("Aluno"), related_name='conta_alunos')
    ano_lectivo = models.ForeignKey(AnoLectivo, on_delete=models.CASCADE, verbose_name=_("Ano Lectivo"), related_name='conta_alunos')
    saldo_devedor = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Saldo Devedor"),
    )
    total_pago = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Total Pago"),
    )
    total_devido = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Total Devido"),
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.EM_DIA, db_index=True, verbose_name=_("Estado"))
    ultima_actualizacao = models.DateTimeField(auto_now=True, verbose_name=_("Última Actualização"))

    class Meta:
        db_table = "conta_aluno"
        verbose_name = _("Conta do Aluno")
        verbose_name_plural = _("Contas dos Alunos")
        unique_together = [["aluno", "ano_lectivo"]]
        indexes = [
            models.Index(fields=["escola", "status"], name="idx_conta_escola_status"),
            models.Index(fields=["aluno", "ano_lectivo"], name="idx_conta_aluno_ano"),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(saldo_devedor__gte=0), name="chk_conta_saldo_nao_negativo"),
            models.CheckConstraint(condition=models.Q(total_pago__gte=0), name="chk_conta_total_pago_nao_negativo"),
        ]

    def __str__(self):
        return f"Conta {self.aluno} — {self.ano_lectivo}"

class Comunicado(EscolaMixin, TimestampMixin, SoftDeleteMixin):

    class Tipo(models.TextChoices):
        GERAL = "Geral", _("Geral")
        URGENTE = "Urgente", _("Urgente")
        EVENTO = "Evento", _("Evento")
        AVISO = "Aviso", _("Aviso")

    class Destinatario(models.TextChoices):
        TODOS = "Todos", _("Todos")
        ALUNOS = "Alunos", _("Alunos")
        PROFESSORES = "Professores", _("Professores")
        ENCARREGADOS = "Encarregados", _("Encarregados")
        TURMA_ESPECIFICA = "Turma Específica", _("Turma Específica")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=200, verbose_name=_("Título"))
    conteudo = models.TextField(verbose_name=_("Conteúdo"))
    tipo = models.CharField(max_length=20, choices=Tipo.choices, verbose_name=_("Tipo"))
    destinatario_tipo = models.CharField(max_length=50, choices=Destinatario.choices, verbose_name=_("Destinatário"))
    turma = models.ForeignKey(Turma, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Turma"))
    anexo = models.FileField(upload_to="comunicados/anexos/", null=True, blank=True, verbose_name=_("Anexo"))
    publicado_por = models.ForeignKey(
        Utilizador, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_("Publicado por"),
    )
    data_publicacao = models.DateTimeField(auto_now_add=True, verbose_name=_("Data de Publicação"))
    data_expiracao = models.DateTimeField(null=True, blank=True, verbose_name=_("Data de Expiração"))

    class Meta:
        db_table = "comunicado"
        verbose_name = _("Comunicado")
        verbose_name_plural = _("Comunicados")
        ordering = ["-data_publicacao"]
        indexes = [
            models.Index(fields=["escola", "activo", "data_publicacao"], name="idx_comunicado_activo"),
            models.Index(fields=["data_expiracao"], name="idx_comunicado_expiracao"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(data_expiracao__isnull=True) | models.Q(data_expiracao__gt=models.F("data_publicacao")),
                name="chk_comunicado_expiracao_valida",
            )
        ]

    def __str__(self):
        return self.titulo

    @property
    def expirado(self) -> bool:
        return self.data_expiracao is not None and self.data_expiracao < timezone.now()

class TipoAvaliacao(models.Model):
    """
    Tipos de avaliação para o II Ciclo de Angola.
 
    Tipos principais:
      - TESTE_1, TESTE_2: Testes escritos por trimestre
      - MAC: Média de Aptidão e Conhecimento (resultado trimestral)
      - EXAME_NORMAL: Exame de época normal (alunos com MAC < 10)
      - EXAME_RECURSO: Exame de recurso / época especial
      - PROVA_ORAL: Componente oral (línguas, etc.)
      - TRABALHO_GRUPO: Trabalhos em grupo
      - TESTE_DIAGNOSTICO: Avaliação diagnóstica
    """
 
    class Categoria(models.TextChoices):
        CONTINUA = "continua", _("Avaliação Contínua")
        TRIMESTRAL = "trimestral", _("Avaliação Trimestral (MAC)")
        EXAME = "exame", _("Exame")
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(
        "academico.TenantEscola",
        on_delete=models.CASCADE,
        verbose_name=_("Escola"),
        db_index=True,
    )
    designacao = models.CharField(max_length=100, verbose_name=_("Designação"))
    categoria = models.CharField(
        max_length=20,
        choices=Categoria.choices,
        default=Categoria.CONTINUA,
        verbose_name=_("Categoria"),
    )
    peso = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Peso (%)"),
        help_text=_("Peso percentual dentro do trimestre. Soma dos pesos deve ser 100%."),
    )
    conta_para_mac = models.BooleanField(
        default=True,
        verbose_name=_("Conta para MAC"),
        help_text=_("Se esta avaliação entra no cálculo da Média de Aptidão e Conhecimento."),
    )
    descricao = models.TextField(blank=True, verbose_name=_("Descrição"))
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_actualizacao = models.DateTimeField(auto_now=True)
 
    class Meta:
        db_table = "tipo_avaliacao"
        verbose_name = _("Tipo de Avaliação")
        verbose_name_plural = _("Tipos de Avaliação")
        unique_together = [["escola", "designacao"]]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(peso__gte=0) & models.Q(peso__lte=100),
                name="chk_tipoavaliacao_peso_valido",
            )
        ]
 
    def __str__(self):
        return f"{self.designacao} ({self.get_categoria_display()})"
 
 
class Avaliacao(models.Model):
    """
    Avaliação (instrumento de avaliação) no II Ciclo.
 
    Cada avaliação está associada a:
      - Uma turma-disciplina
      - Um trimestre
      - Um tipo de avaliação (Teste 1, Teste 2, MAC, Exame, etc.)
    """
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(
        "academico.TenantEscola",
        on_delete=models.CASCADE,
        verbose_name=_("Escola"),
        db_index=True,
    )
    turma = models.ForeignKey(
        "academico.Turma",
        on_delete=models.CASCADE,
        verbose_name=_("Turma"),
        related_name="avaliacoes",
    )
    disciplina = models.ForeignKey(
        "academico.Disciplina",
        on_delete=models.CASCADE,
        verbose_name=_("Disciplina"),
        related_name="avaliacoes",
    )
    professor = models.ForeignKey(
        "academico.Funcionario",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Professor"),
        related_name="avaliacoes",
    )
    trimestre = models.ForeignKey(
        "academico.Trimestre",
        on_delete=models.CASCADE,
        verbose_name=_("Trimestre"),
        related_name="avaliacoes",
    )
    tipo_avaliacao = models.ForeignKey(
        TipoAvaliacao,
        on_delete=models.PROTECT,
        verbose_name=_("Tipo de Avaliação"),
        related_name="avaliacoes",
    )
    designacao = models.CharField(max_length=200, verbose_name=_("Designação"))
    data_realizacao = models.DateField(verbose_name=_("Data de Realização"))
    nota_maxima = models.DecimalField(
        max_digits=5, decimal_places=2, default=20,
        validators=[MinValueValidator(0)],
        verbose_name=_("Nota Máxima"),
    )
    observacoes = models.TextField(blank=True, verbose_name=_("Observações"))
    criado_por = models.ForeignKey(
        "academico.Utilizador",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Criado por"),
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_actualizacao = models.DateTimeField(auto_now=True)
 
    class Meta:
        db_table = "avaliacao"
        verbose_name = _("Avaliação")
        verbose_name_plural = _("Avaliações")
        indexes = [
            models.Index(fields=["turma", "disciplina", "trimestre"], name="avaliacao_turma_disc_trim"),
            models.Index(fields=["escola", "data_realizacao"], name="idx_avaliacao_escola_data"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nota_maxima__gt=0),
                name="chk_avaliacao_nota_maxima_positiva",
            ),
        ]
 
    def __str__(self):
        return f"{self.designacao} — {self.turma} | {self.disciplina}"
 
 
class Nota(models.Model):
    """Nota individual de um aluno numa avaliação."""
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(
        "academico.TenantEscola",
        on_delete=models.CASCADE,
        verbose_name=_("Escola"),
        db_index=True,
    )
    avaliacao = models.ForeignKey(
        Avaliacao,
        on_delete=models.CASCADE,
        related_name="notas",
        verbose_name=_("Avaliação"),
    )
    aluno = models.ForeignKey(
        "academico.Aluno",
        on_delete=models.CASCADE,
        related_name="notas",
        verbose_name=_("Aluno"),
    )
    nota = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Nota"),
    )
    faltou = models.BooleanField(
        default=False,
        verbose_name=_("Faltou"),
        help_text=_("Marcar se o aluno faltou à avaliação (nota = 0)."),
    )
    observacao = models.TextField(blank=True, verbose_name=_("Observação"))
    lancado_por = models.ForeignKey(
        "academico.Funcionario",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Lançado por"),
        related_name="notas_lancadas",
    )
    data_lancamento = models.DateTimeField(auto_now_add=True, verbose_name=_("Data de Lançamento"))
    data_actualizacao = models.DateTimeField(auto_now=True, verbose_name=_("Data de Actualização"))
 
    class Meta:
        db_table = "nota"
        verbose_name = _("Nota")
        verbose_name_plural = _("Notas")
        unique_together = [["avaliacao", "aluno"]]
        indexes = [
            models.Index(fields=["avaliacao", "aluno"], name="idx_nota_avaliacao_aluno"),
            models.Index(fields=["aluno"], name="idx_nota_aluno"),
            models.Index(fields=["escola", "data_lancamento"], name="idx_nota_escola_data"),
        ]
 
    def __str__(self):
        return f"{self.aluno} — {self.avaliacao}: {self.nota}"
 
    def clean(self):
        if self.avaliacao_id and self.nota is not None:
            if self.nota > self.avaliacao.nota_maxima:
                raise ValidationError(
                    _("A nota %(nota)s excede a nota máxima %(max)s.") % {
                        "nota": self.nota,
                        "max": self.avaliacao.nota_maxima,
                    }
                )
 
 
class ResultadoTrimestral(models.Model):
    """
    MAC (Média de Aptidão e Conhecimento) por disciplina por trimestre.
    Calculado automaticamente com base nas Notas das avaliações contínuas.
    """
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(
        "academico.TenantEscola",
        on_delete=models.CASCADE,
        verbose_name=_("Escola"),
    )
    aluno = models.ForeignKey(
        "academico.Aluno",
        on_delete=models.CASCADE,
        related_name="resultados_trimestrais",
        verbose_name=_("Aluno"),
    )
    turma = models.ForeignKey(
        "academico.Turma",
        on_delete=models.CASCADE,
        related_name="resultados_trimestrais",
        verbose_name=_("Turma"),
    )
    disciplina = models.ForeignKey(
        "academico.Disciplina",
        on_delete=models.CASCADE,
        related_name="resultados_trimestrais",
        verbose_name=_("Disciplina"),
    )
    trimestre = models.ForeignKey(
        "academico.Trimestre",
        on_delete=models.CASCADE,
        related_name="resultados_trimestrais",
        verbose_name=_("Trimestre"),
    )
    ano_lectivo = models.ForeignKey(
        "academico.AnoLectivo",
        on_delete=models.CASCADE,
        related_name="resultados_trimestrais",
        verbose_name=_("Ano Lectivo"),
    )
    mac = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name=_("MAC"),
        help_text=_("Média de Aptidão e Conhecimento (0-20)."),
    )
    aprovado_trimestre = models.BooleanField(
        default=False,
        verbose_name=_("Aprovado no Trimestre"),
    )
    observacao = models.TextField(blank=True, verbose_name=_("Observação"))
    calculado_em = models.DateTimeField(auto_now=True, verbose_name=_("Calculado em"))
 
    class Meta:
        db_table = "resultado_trimestral"
        verbose_name = _("Resultado Trimestral")
        verbose_name_plural = _("Resultados Trimestrais")
        unique_together = [["aluno", "disciplina", "trimestre", "ano_lectivo"]]
        indexes = [
            models.Index(fields=["aluno", "ano_lectivo"], name="idx_restrim_aluno_ano"),
            models.Index(fields=["turma", "trimestre"], name="idx_restrim_turma_trim"),
        ]
 
    def __str__(self):
        return f"{self.aluno} | {self.disciplina} | {self.trimestre}: {self.mac}"
 
    def save(self, *args, **kwargs):
        self.aprovado_trimestre = self.mac >= 10
        super().save(*args, **kwargs)
 
 
class ResultadoAnual(models.Model):
    """
    Resultado final anual por disciplina de um aluno.
 
    No II Ciclo:
      - Nota Final = (MAC_T1 + MAC_T2 + MAC_T3) / 3  →  MAC Anual
      - Se MAC Anual >= 10: Aprovado (sem exame)
      - Se MAC Anual entre 7 e 9: Admitido a exame
      - Se MAC Anual < 7: Reprovado (sem direito a exame)
      - Nota Final com Exame = (MAC_Anual * 2 + Nota_Exame) / 3
    """
 
    class SituacaoFinal(models.TextChoices):
        APROVADO = "Aprovado", _("Aprovado")
        APROVADO_EXAME = "Aprovado por Exame", _("Aprovado por Exame")
        REPROVADO = "Reprovado", _("Reprovado")
        REPROVADO_EXAME = "Reprovado em Exame", _("Reprovado em Exame")
        ADMITIDO_EXAME = "Admitido a Exame", _("Admitido a Exame")
        TRANSFERIDO = "Transferido", _("Transferido")
        DESISTENTE = "Desistente", _("Desistente")
 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(
        "academico.TenantEscola",
        on_delete=models.CASCADE,
        verbose_name=_("Escola"),
    )
    aluno = models.ForeignKey(
        "academico.Aluno",
        on_delete=models.CASCADE,
        related_name="resultados_anuais",
        verbose_name=_("Aluno"),
    )
    turma = models.ForeignKey(
        "academico.Turma",
        on_delete=models.CASCADE,
        related_name="resultados_anuais",
        verbose_name=_("Turma"),
    )
    disciplina = models.ForeignKey(
        "academico.Disciplina",
        on_delete=models.CASCADE,
        related_name="resultados_anuais",
        verbose_name=_("Disciplina"),
    )
    ano_lectivo = models.ForeignKey(
        "academico.AnoLectivo",
        on_delete=models.CASCADE,
        related_name="resultados_anuais",
        verbose_name=_("Ano Lectivo"),
    )
    # MACs por trimestre
    mac_1_trimestre = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name=_("MAC 1º Trimestre"),
    )
    mac_2_trimestre = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name=_("MAC 2º Trimestre"),
    )
    mac_3_trimestre = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name=_("MAC 3º Trimestre"),
    )
    mac_anual = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name=_("MAC Anual"),
        help_text=_("Média dos 3 MACs trimestrais."),
    )
    nota_exame = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name=_("Nota de Exame"),
    )
    nota_final = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name=_("Nota Final"),
        help_text=_("Nota final: MAC anual (sem exame) ou (MAC*2 + Exame)/3 (com exame)."),
    )
    situacao = models.CharField(
        max_length=30,
        choices=SituacaoFinal.choices,
        verbose_name=_("Situação Final"),
    )
    calculado_em = models.DateTimeField(auto_now=True, verbose_name=_("Calculado em"))
 
    class Meta:
        db_table = "resultado_anual"
        verbose_name = _("Resultado Anual")
        verbose_name_plural = _("Resultados Anuais")
        unique_together = [["aluno", "disciplina", "ano_lectivo"]]
        indexes = [
            models.Index(fields=["aluno", "ano_lectivo"], name="idx_resanual_aluno_ano"),
            models.Index(fields=["turma", "ano_lectivo"], name="idx_resanual_turma_ano"),
            models.Index(fields=["situacao"], name="idx_resanual_situacao"),
        ]
 
    def __str__(self):
        return f"{self.aluno} | {self.disciplina} | {self.ano_lectivo}: {self.nota_final}"
 
    def calcular(self):
        """Calcula MAC anual e nota final segundo regras do II Ciclo de Angola."""
        from decimal import Decimal, ROUND_HALF_UP
 
        macs = [m for m in [self.mac_1_trimestre, self.mac_2_trimestre, self.mac_3_trimestre] if m is not None]
        if macs:
            self.mac_anual = (sum(macs) / len(macs)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
 
        if self.mac_anual is not None:
            if self.nota_exame is not None:
                # Aluno fez exame: (MAC * 2 + Exame) / 3
                self.nota_final = ((self.mac_anual * 2 + self.nota_exame) / 3).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            else:
                self.nota_final = self.mac_anual
 
            # Determinar situação final
            if self.nota_exame is not None:
                if self.nota_final >= 10:
                    self.situacao = self.SituacaoFinal.APROVADO_EXAME
                else:
                    self.situacao = self.SituacaoFinal.REPROVADO_EXAME
            elif self.mac_anual >= 10:
                self.situacao = self.SituacaoFinal.APROVADO
            elif self.mac_anual >= 7:
                self.situacao = self.SituacaoFinal.ADMITIDO_EXAME
            else:
                self.situacao = self.SituacaoFinal.REPROVADO
 
    def save(self, *args, **kwargs):
        if not self.situacao:
            self.calcular()
        super().save(*args, **kwargs)
 

class MaterialDidatico(EscolaMixin, TimestampMixin, SoftDeleteMixin):
    """Material didáctico partilhado por professores."""

    class Tipo(models.TextChoices):
        APOSTILA = "Apostila", _("Apostila")
        EXERCICIO = "Exercício", _("Exercício")
        SLIDE = "Slide", _("Slide")
        VIDEO = "Vídeo", _("Vídeo")
        AUDIO = "Áudio", _("Áudio")
        LINK = "Link", _("Link")
        OUTRO = "Outro", _("Outro")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=200, verbose_name=_("Título"))
    descricao = models.TextField(blank=True, verbose_name=_("Descrição"))
    tipo = models.CharField(max_length=50, choices=Tipo.choices, verbose_name=_("Tipo"))
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, verbose_name=_("Disciplina"))
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, verbose_name=_("Classe"))
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Curso"))
    arquivo = models.FileField(upload_to="materiais/arquivos/", null=True, blank=True, verbose_name=_("Arquivo"))
    url_externa = models.CharField(max_length=500, blank=True, verbose_name=_("URL Externa"))
    tamanho_arquivo = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)], verbose_name=_("Tamanho (bytes)"))
    visualizacoes = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name=_("Visualizações"))
    downloads = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name=_("Downloads"))
    publicado_por = models.ForeignKey(
        Funcionario, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_("Publicado por"),
    )
    data_publicacao = models.DateTimeField(auto_now_add=True, verbose_name=_("Data de Publicação"))

    class Meta:
        db_table = "material_didatico"
        verbose_name = _("Material Didáctico")
        verbose_name_plural = _("Materiais Didácticos")
        ordering = ["-data_publicacao"]
        indexes = [
            models.Index(fields=["escola", "activo"], name="idx_material_escola_activo"),
            models.Index(fields=["disciplina", "classe"], name="idx_material_disc_classe"),
            models.Index(fields=["publicado_por"], name="idx_material_professor"),
        ]

    def __str__(self):
        return self.titulo


class AcessoMaterial(models.Model):

    class TipoAcesso(models.TextChoices):
        VISUALIZACAO = "Visualização", _("Visualização")
        DOWNLOAD = "Download", _("Download")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    material = models.ForeignKey(MaterialDidatico, on_delete=models.CASCADE, related_name="acessos", verbose_name=_("Material"))
    utilizador = models.ForeignKey(Utilizador, on_delete=models.CASCADE, verbose_name=_("Utilizador"))
    tipo_acesso = models.CharField(max_length=20, choices=TipoAcesso.choices, verbose_name=_("Tipo de Acesso"))
    data_acesso = models.DateTimeField(auto_now_add=True, verbose_name=_("Data de Acesso"))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_("Endereço IP"))

    class Meta:
        db_table = "acesso_material"
        verbose_name = _("Acesso a Material")
        verbose_name_plural = _("Acessos a Materiais")
        indexes = [
            models.Index(fields=["material", "tipo_acesso"], name="idx_acesso_material_tipo"),
            models.Index(fields=["utilizador", "data_acesso"], name="idx_acesso_utilizador_data"),
            models.Index(fields=["data_acesso"], name="idx_acesso_data"),
        ]

    def __str__(self):
        return f"{self.utilizador} — {self.material} ({self.tipo_acesso})"
    

class LogAuditoria(models.Model):

    class Accao(models.TextChoices):
        CRIAR = "criar", _("Criar")
        ACTUALIZAR = "actualizar", _("Actualizar")
        ELIMINAR = "eliminar", _("Eliminar")
        LOGIN = "login", _("Login")
        LOGOUT = "logout", _("Logout")
        EXPORTAR = "exportar", _("Exportar")
        IMPRIMIR = "imprimir", _("Imprimir")
        OUTRO = "outro", _("Outro")

    class Modulo(models.TextChoices):
        ALUNO = "aluno", _("Aluno")
        PROFESSOR = "professor", _("Professor")
        MATRICULA = "matricula", _("Matrícula")
        INSCRICAO = "inscricao", _("Inscrição")
        NOTA = "nota", _("Nota")
        FINANCEIRO = "financeiro", _("Financeiro")
        UTILIZADOR = "utilizador", _("Utilizador")
        CONFIGURACAO = "configuracao", _("Configuração")
        TURMA = "turma", _("Turma")
        COMUNICADO = "comunicado", _("Comunicado")
        SISTEMA = "sistema", _("Sistema")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(
        "academico.TenantEscola",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="logs_auditoria",
        verbose_name=_("Escola"),
    )
    utilizador = models.ForeignKey(
        Utilizador,
        on_delete=models.SET_NULL,
        null=True,
        related_name="logs_auditoria",
        verbose_name=_("Utilizador"),
    )
    accao = models.CharField(
        max_length=100,
        choices=Accao.choices,
        verbose_name=_("Acção"),
    )
    modulo = models.CharField(
        max_length=50,
        choices=Modulo.choices,
        verbose_name=_("Módulo"),
    )
    descricao = models.TextField(verbose_name=_("Descrição"))
    objeto_id = models.CharField(
        max_length=100, blank=True, null=True,
        db_index=True,
        verbose_name=_("ID do Objecto"),
    )
    objeto_tipo = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name=_("Tipo do Objecto"),
    )
    ip_address = models.GenericIPAddressField(verbose_name=_("Endereço IP"))
    user_agent = models.TextField(blank=True, verbose_name=_("User Agent"))
    dados_antes = models.JSONField(null=True, blank=True, verbose_name=_("Dados Antes"))
    dados_depois = models.JSONField(null=True, blank=True, verbose_name=_("Dados Depois"))
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Timestamp"))

    class Meta:
        db_table = "log_auditoria"
        verbose_name = _("Log de Auditoria")
        verbose_name_plural = _("Logs de Auditoria")
        ordering = ["-timestamp"]
        # Logs nunca devem ser alterados — managed=True mas sem update
        indexes = [
            models.Index(fields=["escola", "timestamp"], name="idx_log_escola_timestamp"),
            models.Index(fields=["escola", "modulo", "timestamp"], name="idx_log_escola_modulo"),
            models.Index(fields=["utilizador", "timestamp"], name="idx_log_utilizador_timestamp"),
            models.Index(fields=["accao", "modulo"], name="idx_log_accao_modulo"),
            models.Index(fields=["objeto_id", "objeto_tipo"], name="idx_log_objeto"),
            models.Index(fields=["ip_address"], name="idx_log_ip"),
        ]

    def __str__(self) -> str:
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.utilizador} — {self.accao} em {self.modulo}"

    def save(self, *args, **kwargs):
        """Logs de auditoria são imutáveis — impede actualizações."""
        if self.pk and LogAuditoria.objects.filter(pk=self.pk).exists():
            raise ValidationError(_("Logs de auditoria não podem ser modificados."))
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Logs de auditoria não podem ser eliminados."""
        raise ValidationError(_("Logs de auditoria não podem ser eliminados."))


class BackupSistema(models.Model):
    """Registo de backups efectuados ao sistema."""

    class Tipo(models.TextChoices):
        MANUAL = "Manual", _("Manual")
        AUTOMATICO = "Automático", _("Automático")
        AGENDADO = "Agendado", _("Agendado")

    class Status(models.TextChoices):
        SUCESSO = "Sucesso", _("Sucesso")
        FALHA = "Falha", _("Falha")
        EM_PROGRESSO = "Em Progresso", _("Em Progresso")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(
        "academico.TenantEscola",
        on_delete=models.CASCADE,
        related_name="backups",
        verbose_name=_("Escola"),
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices, verbose_name=_("Tipo"))
    arquivo = models.CharField(max_length=500, verbose_name=_("Arquivo"))
    tamanho = models.BigIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Tamanho (bytes)"),
        help_text=_("Tamanho do arquivo em bytes"),
    )
    data_backup = models.DateTimeField(auto_now_add=True, verbose_name=_("Data do Backup"))
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.EM_PROGRESSO,
        db_index=True,
        verbose_name=_("Estado"),
    )
    duracao_segundos = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Duração (segundos)"),
    )
    observacoes = models.TextField(blank=True, verbose_name=_("Observações"))
    realizado_por = models.ForeignKey(
        Utilizador,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="backups_realizados",
        verbose_name=_("Realizado por"),
    )

    class Meta:
        db_table = "backup_sistema"
        verbose_name = _("Backup do Sistema")
        verbose_name_plural = _("Backups do Sistema")
        ordering = ["-data_backup"]
        indexes = [
            models.Index(fields=["escola", "status"], name="idx_backup_escola_status"),
            models.Index(fields=["escola", "data_backup"], name="idx_backup_escola_data"),
            models.Index(fields=["tipo", "status"], name="idx_backup_tipo_status"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tamanho__isnull=True) | models.Q(tamanho__gte=0),
                name="chk_backup_tamanho_nao_negativo",
            )
        ]

    def __str__(self) -> str:
        return f"Backup {self.tipo} — {self.escola} [{self.data_backup:%Y-%m-%d %H:%M}]"

    @property
    def tamanho_legivel(self) -> str:
        """Retorna o tamanho do backup em formato legível (KB, MB, GB)."""
        if not self.tamanho:
            return "—"
        for unidade in ("B", "KB", "MB", "GB", "TB"):
            if self.tamanho < 1024:
                return f"{self.tamanho:.1f} {unidade}"
            self.tamanho /= 1024
        return f"{self.tamanho:.1f} PB"


class ParametroSistema(models.Model):

    class TipoDado(models.TextChoices):
        STRING = "String", _("String")
        INTEGER = "Integer", _("Inteiro")
        BOOLEAN = "Boolean", _("Booleano")
        JSON = "JSON", _("JSON")
        DECIMAL = "Decimal", _("Decimal")

    class Categoria(models.TextChoices):
        ACADEMICO = "academico", _("Académico")
        FINANCEIRO = "financeiro", _("Financeiro")
        NOTIFICACOES = "notificacoes", _("Notificações")
        SEGURANCA = "seguranca", _("Segurança")
        INTEGRACAO = "integracao", _("Integração")
        GERAL = "geral", _("Geral")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey(
        "academico.TenantEscola",
        on_delete=models.CASCADE,
        related_name="parametros",
        verbose_name=_("Escola"),
    )
    chave = models.CharField(max_length=100, verbose_name=_("Chave"))
    valor = models.TextField(blank=True, verbose_name=_("Valor"))
    tipo_dado = models.CharField(
        max_length=20,
        choices=TipoDado.choices,
        default=TipoDado.STRING,
        verbose_name=_("Tipo de Dado"),
    )
    categoria = models.CharField(
        max_length=50,
        choices=Categoria.choices,
        default=Categoria.GERAL,
        blank=True,
        db_index=True,
        verbose_name=_("Categoria"),
    )
    descricao = models.TextField(blank=True, verbose_name=_("Descrição"))
    editavel = models.BooleanField(default=True, verbose_name=_("Editável"))
    data_actualizacao = models.DateTimeField(auto_now=True, verbose_name=_("Data de Actualização"))
    atualizado_por = models.ForeignKey(
        Utilizador,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="parametros_actualizados",
        verbose_name=_("Actualizado por"),
    )

    class Meta:
        db_table = "parametro_sistema"
        verbose_name = _("Parâmetro do Sistema")
        verbose_name_plural = _("Parâmetros do Sistema")
        unique_together = [["escola", "chave"]]
        ordering = ["categoria", "chave"]
        indexes = [
            models.Index(fields=["escola", "categoria"], name="idx_param_escola_categoria"),
            models.Index(fields=["escola", "chave"], name="idx_param_escola_chave"),
            models.Index(fields=["editavel"], name="idx_param_editavel"),
        ]

    def __str__(self) -> str:
        return f"{self.chave} = {self.valor[:50]}"

    def valor_tipado(self):
        """Retorna o valor convertido para o tipo de dado definido."""
        import json
        try:
            match self.tipo_dado:
                case self.TipoDado.INTEGER:
                    return int(self.valor)
                case self.TipoDado.BOOLEAN:
                    return self.valor.lower() in ("true", "1", "sim", "yes")
                case self.TipoDado.DECIMAL:
                    from decimal import Decimal
                    return Decimal(self.valor)
                case self.TipoDado.JSON:
                    return json.loads(self.valor)
                case _:
                    return self.valor
        except (ValueError, TypeError):
            return self.valor

    def clean(self):
        """Valida que o valor é compatível com o tipo de dado definido."""
        import json
        from decimal import Decimal, InvalidOperation

        if not self.valor:
            return

        try:
            match self.tipo_dado:
                case self.TipoDado.INTEGER:
                    int(self.valor)
                case self.TipoDado.DECIMAL:
                    Decimal(self.valor)
                case self.TipoDado.BOOLEAN:
                    if self.valor.lower() not in ("true", "false", "1", "0", "sim", "não", "yes", "no"):
                        raise ValueError
                case self.TipoDado.JSON:
                    json.loads(self.valor)
        except (ValueError, TypeError, json.JSONDecodeError):
            raise ValidationError(
                _("O valor '%(valor)s' não é compatível com o tipo '%(tipo)s'.") % {
                    "valor": self.valor,
                    "tipo": self.tipo_dado,
                }
            )