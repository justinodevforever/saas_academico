from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(TenantEscola)
admin.site.register(Disciplina)
admin.site.register(TenantConfiguracao)
admin.site.register(Turma)
admin.site.register(Professor)
admin.site.register(Aluno)
admin.site.register(Diretor)
admin.site.register(PlanoSubscricao)
admin.site.register(AnoLectivo)
admin.site.register(PeriodoAvaliativo)