from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from administrador.models import *


class PerfilAcesso(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey('academico.TenantEscola', on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    permissoes = models.JSONField(default=dict)
    nivel_hierarquia = models.IntegerField(default=1)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'perfil_acesso'
        verbose_name = 'Perfil de Acesso'
        verbose_name_plural = 'Perfis de Acesso'


class Utilizador(AbstractUser):

    TIPO_UTILIZADOR = [
        ('admin', 'admin'),
        ('aluno', 'Aluno'),
        ('diretor', 'Director'),
        ('professor', 'Professor'),
        ('chefe_secretara', 'Chefe da secretaria'),
        ('ecarregado', 'Encarregado')
    ]

    GENERO = [('M', 'Masculino'), ('F', 'Feminino')]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey('academico.TenantEscola', on_delete=models.CASCADE, blank=True, null=True)
    tipo_utilizador = models.CharField(max_length=20, choices=TIPO_UTILIZADOR, blank=True, null=True)
    perfil = models.ForeignKey(PerfilAcesso, on_delete=models.PROTECT, null=True, blank=True)
    foto = models.ImageField(upload_to='utilizadores/fotos/', blank=True, null=True)
    verificado_email = models.BooleanField(default=False, blank=True, null=True)
    verificado_telefone = models.BooleanField(default=False, blank=True, null=True)
    ultimo_acesso = models.DateTimeField(null=True, blank=True)
    criado_por = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='utilizadores_criados')
    
    class Meta:
        db_table = 'utilizador'
        verbose_name = 'Utilizador'
        verbose_name_plural = 'Utilizadores'


class LogAuditoria(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey('academico.TenantEscola', on_delete=models.CASCADE)
    utilizador = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, null=True)
    accao = models.CharField(max_length=100)
    modulo = models.CharField(max_length=50)
    descricao = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    dados_antes = models.JSONField(null=True, blank=True)
    dados_depois = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'log_auditoria'
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']

class BackupSistema(models.Model):

    TIPO = [("Manual","Manual"),("Automático","Automático"),("Agendado","Agendado")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey('academico.TenantEscola', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO)
    arquivo = models.CharField(max_length=500)
    tamanho = models.IntegerField(null=True, blank=True)
    data_backup = models.DateTimeField(auto_now_add=True)
    STATUS = [("Sucesso","Sucesso"),("Falha","Falha"),("Em Progresso","Em Progresso")]
    status = models.CharField(max_length=20, choices=STATUS, default="Sucesso")
    observacoes = models.TextField(blank=True)
    realizado_por = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, null=True, blank=True)

class ParametroSistema(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escola = models.ForeignKey('academico.TenantEscola', on_delete=models.CASCADE)
    chave = models.CharField(max_length=100)
    valor = models.TextField(blank=True)
    TIPO = [("String","String"),("Integer","Integer"),("Boolean","Boolean"),("JSON","JSON"),("Decimal","Decimal")]
    tipo_dado = models.CharField(max_length=20, choices=TIPO, default="String")
    categoria = models.CharField(max_length=50, blank=True)
    descricao = models.TextField(blank=True)
    editavel = models.BooleanField(default=True)
    data_actualizacao = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(Utilizador, on_delete=models.SET_NULL, null=True, blank=True)