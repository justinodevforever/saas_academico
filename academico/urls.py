from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/diretor/', views.dashboard_diretor, name='dashboard_diretor'),
    path('dashboard/professor/', views.dashboard_professor, name='dashboard_professor'),
    path('dashboard/aluno/', views.dashboard_aluno, name='dashboard_aluno'),
    path('dashboard/encarregado/', views.dashboard_encarregado, name='dashboard_encarregado'),
    
    path('alunos/', views.aluno_list, name='aluno_list'),
    path('alunos/criar/', views.aluno_create, name='aluno_create'),
    path('alunos/<uuid:aluno_id>/', views.aluno_detail, name='aluno_detail'),
    path('alunos/<uuid:aluno_id>/editar/', views.aluno_update, name='aluno_update'),
    path('alunos/<uuid:aluno_id>/excluir/', views.aluno_delete, name='aluno_delete'),
    
    path('professores/', views.professor_list, name='professor_list'),
    path('professores/<uuid:professor_id>/', views.professor_detail, name='professor_detail'),
    
    path('turmas/', views.turma_list, name='turma_list'),
    path('turmas/criar/', views.turma_create, name='turma_create'),
    path('turmas/<uuid:turma_id>/', views.turma_detail, name='turma_detail'),
    #path('turmas/<uuid:turma_id>/atribuir-professor/', views.turma_atribuir_professor, name='turma_atribuir_professor'),
    
    path('matriculas/', views.matricula_list, name='matricula_list'),
    path('matriculas/criar/', views.matricula_create, name='matricula_create'),
    path('matriculas/criar/<uuid:aluno_id>/', views.matricula_create, name='matricula_create_aluno'),
    #path('matriculas/<uuid:matricula_id>/cancelar/', views.matricula_cancelar, name='matricula_cancelar'),
    
    path('disciplinas/', views.disciplina_list, name='disciplina_list'),
    path('disciplinas/criar/', views.disciplina_create, name='disciplina_create'),
    path('disciplinas/<uuid:disciplina_id>/lancar-notas/', views.disciplina_detail, name='disciplina_detail'),
    #path('disciplinas/pauta/<uuid:turma_id>/<uuid:periodo_id>/', views.disciplina_pauta, name='disciplina_pauta'),

    path('avaliacoes/', views.avaliacao_list, name='avaliacao_list'),
    path('avaliacoes/criar/', views.avaliacao_create, name='avaliacao_create'),
    path('avaliacoes/<uuid:avaliacao_id>/lancar-notas/', views.avaliacao_lancar_notas, name='avaliacao_lancar_notas'),
    path('avaliacoes/pauta/<uuid:turma_id>/<uuid:periodo_id>/', views.avaliacao_pauta, name='avaliacao_pauta'),
    
    path('financeiro/', views.financeiro_dashboard, name='financeiro_dashboard'),
    path('financeiro/contas/', views.financeiro_contas_list, name='financeiro_contas_list'),
    path('financeiro/contas/<uuid:conta_id>/', views.financeiro_conta_detail, name='financeiro_conta_detail'),
    
    path('comunicados/', views.comunicado_list, name='comunicado_list'),
    path('comunicados/criar/', views.comunicado_create, name='comunicado_create'),
    path('comunicados/<uuid:comunicado_id>/', views.comunicado_detail, name='comunicado_detail'),
    path('comunicados/<uuid:comunicado_id>/toggle-status/', views.comunicado_toggle_status, name='comunicado_toggle_status'),
    
    path('materiais/', views.material_list, name='material_list'),
    path('materiais/criar/', views.material_create, name='material_create'),
    path('materiais/<uuid:material_id>/', views.material_detail, name='material_detail'),
    path('materiais/<uuid:material_id>/download/', views.material_download, name='material_download'),
    
    path('horarios/turma/<uuid:turma_id>/', views.horario_turma, name='horario_turma'),
    path('horarios/professor/', views.horario_professor, name='horario_professor'),
    path('horarios/professor/<uuid:professor_id>/', views.horario_professor, name='horario_professor_detail'),
    path('horarios/turma/<uuid:turma_id>/criar/', views.horario_create, name='horario_create'),
    
    path('relatorios/alunos/', views.relatorio_alunos, name='relatorio_alunos'),
    path('relatorios/professores/', views.relatorio_professores, name='relatorio_professores'),
    path('relatorios/turmas/', views.relatorio_turmas, name='relatorio_turmas'),
    
    path('configuracoes/escola/', views.configuracao_escola, name='configuracao_escola'),
    path('configuracoes/anos-lectivos/', views.ano_lectivo_list, name='ano_lectivo_list'),
    path('configuracoes/anos-lectivos/criar/', views.ano_lectivo_create, name='ano_lectivo_create'),
    path('configuracoes/anos-lectivos/<uuid:ano_id>/ativar/', views.ano_lectivo_ativar, name='ano_lectivo_ativar'),
    path('configuracoes/periodos/<uuid:ano_id>/', views.periodo_avaliativo_list, name='periodo_avaliativo_list'),
    path('configuracoes/periodos/<uuid:ano_id>/criar/', views.periodo_avaliativo_create, name='periodo_avaliativo_create'),
    path('configuracoes/cursos/', views.curso_list, name='curso_list'),
    path('configuracoes/disciplinas/', views.disciplina_list, name='disciplina_list'),
    path('configuracoes/tipos-avaliacao/', views.tipo_avaliacao_list, name='tipo_avaliacao_list'),
    
    path('api/turmas-por-classe/', views.api_turmas_por_classe, name='api_turmas_por_classe'),
    path('api/disciplinas-por-turma/', views.api_disciplinas_por_turma, name='api_disciplinas_por_turma'),
    path('api/alunos-por-turma/', views.api_alunos_por_turma, name='api_alunos_por_turma'),
    path('api/verificar-disponibilidade-turma/', views.api_verificar_disponibilidade_turma, name='api_verificar_disponibilidade_turma'),
    path('api/notas-aluno/<uuid:aluno_id>/', views.api_notas_aluno, name='api_notas_aluno'),
    path('api/estatisticas-dashboard/', views.api_estatisticas_dashboard, name='api_estatisticas_dashboard'),
    
    path('busca/aluno/', views.busca_aluno, name='busca_aluno'),
    path('busca/professor/', views.busca_professor, name='busca_professor'),
    
    path('exportar/alunos/', views.exportar_lista_alunos, name='exportar_lista_alunos'),
    path('exportar/pauta/<uuid:turma_id>/<uuid:periodo_id>/', views.exportar_pauta_pdf, name='exportar_pauta_pdf'),
    
    path('notificacoes/', views.notificacoes_list, name='notificacoes_list'),
    path('notificacoes/<int:notificacao_id>/marcar-lida/', views.marcar_notificacao_lida, name='marcar_notificacao_lida'),
    
    path('perfil/', views.meu_perfil, name='meu_perfil'),
    path('perfil/alterar-senha/', views.alterar_senha, name='alterar_senha'),
    
    path('ajuda/', views.ajuda_index, name='ajuda_index'),
    path('ajuda/<str:categoria>/', views.ajuda_categoria, name='ajuda_categoria'),
]