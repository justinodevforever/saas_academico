from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import date, timedelta

from .models import (
    Diretor, TenantEscola, AnoLectivo, PeriodoAvaliativo,
    Aluno, Professor, Turma, Matricula, Inscricao,
    Curso, Classe, Disciplina, CursoClasseDisciplina,
    Nota, Avaliacao, TipoAvaliacao,
    ContaAluno, DocumentoAluno,
    Comunicado, HorarioAula, MaterialDidatico,
    TurmaDisciplinaProfessor, DisciplinaProfessor,
    EncarregadoEducacao, AlunoEncarregado,
    TenantConfiguracao,
)


# ──────────────────────────────────────────────
# UTILITÁRIO: obtém o director e a escola do
# utilizador autenticado (reutilizado em todas
# as views abaixo).
# ──────────────────────────────────────────────

def _get_diretor_escola(request):
    """
    Devolve (diretor, escola) para o utilizador autenticado.
    Levanta Http404 caso o utilizador não seja director.
    """
    diretor = get_object_or_404(Diretor, utilizador=request.user)
    return diretor, diretor.escola


# ══════════════════════════════════════════════
# 1. DASHBOARD PRINCIPAL DO DIRECTOR
# ══════════════════════════════════════════════

@login_required
def dashboard_diretor(request):
    """
    Painel principal da escola.  Apresenta KPIs, alertas,
    últimas matrículas e desempenho académico resumido.
    """
    diretor, escola = _get_diretor_escola(request)
    hoje = date.today()

    # ── Ano lectivo e período activos ──────────
    try:
        config = escola.configuracao
        ano_lectivo = config.ano_lectivo_activo
        periodo     = config.periodo_activo
    except TenantConfiguracao.DoesNotExist:
        ano_lectivo = AnoLectivo.objects.filter(escola=escola, e_atual=True).first()
        periodo     = None

    # ── KPIs principais ────────────────────────
    total_alunos        = Aluno.objects.filter(escola=escola, status='Matriculado').count()
    total_professores   = Professor.objects.filter(escola=escola, status='Activo').count()
    total_turmas        = Turma.objects.filter(escola=escola, activo=True).count()
    total_disciplinas   = Disciplina.objects.filter(escola=escola, activo=True).count()

    matriculas_ativas   = Matricula.objects.filter(escola=escola, status='Activa').count()
    inscricoes_pendentes = Inscricao.objects.filter(
        escola=escola, ano_lectivo=ano_lectivo
    ).count() if ano_lectivo else 0

    # ── Financeiro da escola ───────────────────
    financeiro = ContaAluno.objects.filter(escola=escola).aggregate(
        total_pago     = Sum('total_pago'),
        total_devido   = Sum('total_devido'),
        saldo_devedor  = Sum('saldo_devedor'),
    )
    contas_atrasadas  = ContaAluno.objects.filter(escola=escola, status='Atrasado').count()
    contas_bloqueadas = ContaAluno.objects.filter(escola=escola, status='Bloqueado').count()

    # ── Últimas matrículas (10) ─────────────────
    ultimas_matriculas = Matricula.objects.filter(escola=escola).select_related(
        'aluno', 'curso', 'turma', 'ano_lectivo'
    ).order_by('-data_matricula')[:10]

    # ── Comunicados activos da escola ──────────
    comunicados = Comunicado.objects.filter(
        escola=escola, activo=True
    ).filter(
        Q(data_expiracao__isnull=True) | Q(data_expiracao__gte=hoje)
    ).order_by('-data_publicacao')[:5]

    # ── Matrículas dos últimos 6 meses (gráfico) ─
    matriculas_mensal = []
    for i in range(5, -1, -1):
        mes_ref = hoje.replace(day=1) - timedelta(days=i * 30)
        qtd = Matricula.objects.filter(
            escola=escola,
            data_matricula__year=mes_ref.year,
            data_matricula__month=mes_ref.month,
        ).count()
        matriculas_mensal.append({'mes': mes_ref.strftime('%b/%Y'), 'qtd': qtd})

    # ── Distribuição de alunos por curso ───────
    alunos_por_curso = (
        Matricula.objects
        .filter(escola=escola, status='Activa')
        .values('curso__nome')
        .annotate(total=Count('id'))
        .order_by('-total')[:6]
    )

    # ── Média geral de notas (ano lectivo actual) ─
    media_geral = None
    if ano_lectivo:
        media_geral = Nota.objects.filter(
            escola=escola,
            avaliacao__turma__ano_lectivo=ano_lectivo,
        ).aggregate(media=Avg('nota'))['media']

    context = {
        'secao': 'dashboard',
        'diretor': diretor,
        'escola': escola,
        'ano_lectivo': ano_lectivo,
        'periodo': periodo,
        # KPIs
        'total_alunos': total_alunos,
        'total_professores': total_professores,
        'total_turmas': total_turmas,
        'total_disciplinas': total_disciplinas,
        'matriculas_ativas': matriculas_ativas,
        'inscricoes_pendentes': inscricoes_pendentes,
        # Financeiro
        'financeiro': financeiro,
        'contas_atrasadas': contas_atrasadas,
        'contas_bloqueadas': contas_bloqueadas,
        # Listas
        'ultimas_matriculas': ultimas_matriculas,
        'comunicados': comunicados,
        # Gráficos
        'matriculas_mensal': matriculas_mensal,
        'alunos_por_curso': list(alunos_por_curso),
        'media_geral': media_geral,
    }
    return render(request, 'diretor/dashboard.html', context)


# ══════════════════════════════════════════════
# 2. GESTÃO DE TURMAS
# ══════════════════════════════════════════════

@login_required
def lista_turmas(request):
    """Lista todas as turmas da escola com ocupação e professor director."""
    diretor, escola = _get_diretor_escola(request)
    ano_id = request.GET.get('ano_lectivo')
    curso_id = request.GET.get('curso')

    turmas = (
        Turma.objects
        .filter(escola=escola)
        .select_related('curso', 'classe', 'ano_lectivo', 'director_turma')
        .annotate(total_alunos=Count('matriculas', filter=Q(matriculas__status='Activa')))
        .order_by('classe__ordem', 'designacao')
    )

    if ano_id:
        turmas = turmas.filter(ano_lectivo_id=ano_id)
    if curso_id:
        turmas = turmas.filter(curso_id=curso_id)

    anos_lectivos = AnoLectivo.objects.filter(escola=escola).order_by('-data_inicio')
    cursos = Curso.objects.filter(escola=escola, activo=True)

    context = {
        'secao': 'turmas',
        'diretor': diretor,
        'escola': escola,
        'turmas': turmas,
        'anos_lectivos': anos_lectivos,
        'cursos': cursos,
        'filtros': {'ano_id': ano_id, 'curso_id': curso_id},
    }
    return render(request, 'diretor/turmas/lista.html', context)


@login_required
def detalhe_turma(request, turma_id):
    """Detalhes de uma turma: alunos, disciplinas, professores e horários."""
    diretor, escola = _get_diretor_escola(request)
    turma = get_object_or_404(Turma, id=turma_id, escola=escola)

    alunos = Matricula.objects.filter(
        turma=turma, status='Activa'
    ).select_related('aluno').order_by('aluno__nome_completo')

    disciplinas = TurmaDisciplinaProfessor.objects.filter(
        turma=turma
    ).select_related('disciplina', 'professor')

    horarios = HorarioAula.objects.filter(
        turma=turma
    ).select_related('disciplina', 'professor').order_by('dia_semana', 'hora_inicio')

    # Média por disciplina na turma
    medias = (
        Nota.objects.filter(avaliacao__turma=turma)
        .values('avaliacao__disciplina__nome')
        .annotate(media=Avg('nota'))
        .order_by('-media')
    )

    context = {
        'secao': 'turmas',
        'diretor': diretor,
        'escola': escola,
        'turma': turma,
        'alunos': alunos,
        'disciplinas': disciplinas,
        'horarios': horarios,
        'medias': medias,
        'total_alunos': alunos.count(),
    }
    return render(request, 'diretor/turmas/detalhe.html', context)


# ══════════════════════════════════════════════
# 3. GESTÃO DE ALUNOS
# ══════════════════════════════════════════════

@login_required
def lista_alunos(request):
    """Lista de alunos da escola com filtros."""
    diretor, escola = _get_diretor_escola(request)
    status_f = request.GET.get('status', '')
    curso_f  = request.GET.get('curso', '')
    busca    = request.GET.get('q', '')

    alunos = (
        Aluno.objects
        .filter(escola=escola)
        .select_related('escola')
        .order_by('nome_completo')
    )

    if status_f:
        alunos = alunos.filter(status=status_f)
    if curso_f:
        alunos = alunos.filter(matriculas__curso_id=curso_f)
    if busca:
        alunos = alunos.filter(
            Q(nome_completo__icontains=busca) |
            Q(numero_processo__icontains=busca) |
            Q(bi__icontains=busca)
        )

    cursos = Curso.objects.filter(escola=escola, activo=True)
    context = {
        'secao': 'alunos',
        'diretor': diretor,
        'escola': escola,
        'alunos': alunos,
        'cursos': cursos,
        'status_choices': Aluno.STATUS,
        'filtros': {'status': status_f, 'curso': curso_f, 'q': busca},
        'total': alunos.count(),
    }
    return render(request, 'diretor/alunos/lista.html', context)


@login_required
def detalhe_aluno(request, aluno_id):
    """Perfil completo do aluno: dados pessoais, matrículas, notas e documentos."""
    diretor, escola = _get_diretor_escola(request)
    aluno = get_object_or_404(Aluno, id=aluno_id, escola=escola)

    matriculas   = aluno.matriculas.select_related('curso', 'turma', 'ano_lectivo').order_by('-data_matricula')
    documentos   = aluno.documentos.order_by('-data_upload')
    encarregados = AlunoEncarregado.objects.filter(aluno=aluno).select_related('encarregado')
    conta        = ContaAluno.objects.filter(aluno=aluno).select_related('ano_lectivo').first()

    # Notas do aluno agrupadas por disciplina
    notas = (
        Nota.objects
        .filter(aluno=aluno, escola=escola)
        .select_related('avaliacao__disciplina', 'avaliacao__tipo_avaliacao', 'avaliacao__turma')
        .order_by('avaliacao__disciplina__nome', 'avaliacao__data_realizacao')
    )
    media_aluno = notas.aggregate(media=Avg('nota'))['media']

    context = {
        'secao': 'alunos',
        'diretor': diretor,
        'escola': escola,
        'aluno': aluno,
        'matriculas': matriculas,
        'documentos': documentos,
        'encarregados': encarregados,
        'conta': conta,
        'notas': notas,
        'media_aluno': media_aluno,
    }
    return render(request, 'diretor/alunos/detalhe.html', context)


# ══════════════════════════════════════════════
# 4. GESTÃO DE PROFESSORES
# ══════════════════════════════════════════════

@login_required
def lista_professores(request):
    """Lista de professores da escola."""
    diretor, escola = _get_diretor_escola(request)
    status_f = request.GET.get('status', '')
    busca    = request.GET.get('q', '')

    professores = (
        Professor.objects
        .filter(escola=escola)
        .select_related('categoria')
        .annotate(
            total_disciplinas=Count('disciplinas_lecionadas', distinct=True),
            total_turmas=Count('turmas_dirigidas', distinct=True),
        )
        .order_by('nome_completo')
    )

    if status_f:
        professores = professores.filter(status=status_f)
    if busca:
        professores = professores.filter(
            Q(nome_completo__icontains=busca) | Q(numero_agente__icontains=busca)
        )

    context = {
        'secao': 'professores',
        'diretor': diretor,
        'escola': escola,
        'professores': professores,
        'status_choices': Professor.STATUS,
        'filtros': {'status': status_f, 'q': busca},
        'total': professores.count(),
    }
    return render(request, 'diretor/professores/lista.html', context)


@login_required
def detalhe_professor(request, professor_id):
    """Perfil do professor: disciplinas, turmas e carga horária."""
    diretor, escola = _get_diretor_escola(request)
    professor = get_object_or_404(Professor, id=professor_id, escola=escola)

    disciplinas   = DisciplinaProfessor.objects.filter(
        professor=professor
    ).select_related('disciplina')

    turmas_atrib  = TurmaDisciplinaProfessor.objects.filter(
        professor=professor
    ).select_related('turma__classe', 'turma__curso', 'disciplina', 'ano_lectivo')

    horarios = HorarioAula.objects.filter(
        professor=professor, escola=escola
    ).select_related('turma', 'disciplina').order_by('dia_semana', 'hora_inicio')

    context = {
        'secao': 'professores',
        'diretor': diretor,
        'escola': escola,
        'professor': professor,
        'disciplinas': disciplinas,
        'turmas_atrib': turmas_atrib,
        'horarios': horarios,
    }
    return render(request, 'diretor/professores/detalhe.html', context)


# ══════════════════════════════════════════════
# 5. AVALIAÇÕES E NOTAS
# ══════════════════════════════════════════════

@login_required
def painel_avaliacoes(request):
    """Visão geral das avaliações lançadas por turma e período."""
    diretor, escola = _get_diretor_escola(request)
    turma_id   = request.GET.get('turma')
    periodo_id = request.GET.get('periodo')

    avaliacoes = (
        Avaliacao.objects
        .filter(escola=escola)
        .select_related('turma__classe', 'disciplina', 'professor', 'periodo', 'tipo_avaliacao')
        .order_by('-data_realizacao')
    )

    if turma_id:
        avaliacoes = avaliacoes.filter(turma_id=turma_id)
    if periodo_id:
        avaliacoes = avaliacoes.filter(periodo_id=periodo_id)

    # Médias por turma
    medias_turma = (
        Nota.objects
        .filter(escola=escola)
        .values('avaliacao__turma__designacao', 'avaliacao__turma__classe__designacao')
        .annotate(media=Avg('nota'), total_notas=Count('id'))
        .order_by('-media')
    )

    turmas   = Turma.objects.filter(escola=escola, activo=True).select_related('classe', 'curso')
    periodos = PeriodoAvaliativo.objects.filter(ano_lectivo__escola=escola).order_by('numero_periodo')

    context = {
        'secao': 'avaliacoes',
        'diretor': diretor,
        'escola': escola,
        'avaliacoes': avaliacoes[:30],
        'medias_turma': list(medias_turma),
        'turmas': turmas,
        'periodos': periodos,
        'filtros': {'turma_id': turma_id, 'periodo_id': periodo_id},
    }
    return render(request, 'diretor/avaliacoes/painel.html', context)


# ══════════════════════════════════════════════
# 6. MATRÍCULAS E INSCRIÇÕES
# ══════════════════════════════════════════════

@login_required
def painel_matriculas(request):
    """Gestão de matrículas e inscrições da escola."""
    diretor, escola = _get_diretor_escola(request)
    ano_id    = request.GET.get('ano_lectivo')
    status_f  = request.GET.get('status', '')

    matriculas = (
        Matricula.objects
        .filter(escola=escola)
        .select_related('aluno', 'curso', 'turma', 'ano_lectivo')
        .order_by('-data_matricula')
    )

    if ano_id:
        matriculas = matriculas.filter(ano_lectivo_id=ano_id)
    if status_f:
        matriculas = matriculas.filter(status=status_f)

    # Estatísticas rápidas
    stats = {
        'total':       matriculas.count(),
        'ativas':      matriculas.filter(status='Activa').count(),
        'canceladas':  matriculas.filter(status='Cancelada').count(),
        'transferidas':matriculas.filter(status='Transferida').count(),
        'concluidas':  matriculas.filter(status='Concluída').count(),
    }

    por_curso = (
        matriculas.values('curso__nome')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    anos_lectivos = AnoLectivo.objects.filter(escola=escola).order_by('-data_inicio')

    context = {
        'secao': 'matriculas',
        'diretor': diretor,
        'escola': escola,
        'matriculas': matriculas[:50],
        'stats': stats,
        'por_curso': list(por_curso),
        'anos_lectivos': anos_lectivos,
        'status_choices': Matricula.STATUS,
        'filtros': {'ano_id': ano_id, 'status': status_f},
    }
    return render(request, 'diretor/matriculas/painel.html', context)


# ══════════════════════════════════════════════
# 7. FINANCEIRO DA ESCOLA
# ══════════════════════════════════════════════

@login_required
def painel_financeiro(request):
    """Resumo financeiro: contas dos alunos, cobranças e inadimplência."""
    diretor, escola = _get_diretor_escola(request)
    ano_id   = request.GET.get('ano_lectivo')
    status_f = request.GET.get('status', '')

    contas = ContaAluno.objects.filter(escola=escola).select_related('aluno', 'ano_lectivo')

    if ano_id:
        contas = contas.filter(ano_lectivo_id=ano_id)
    if status_f:
        contas = contas.filter(status=status_f)

    resumo = contas.aggregate(
        total_pago    = Sum('total_pago'),
        total_devido  = Sum('total_devido'),
        saldo_devedor = Sum('saldo_devedor'),
    )
    por_status = (
        contas.values('status')
        .annotate(quantidade=Count('id'), valor=Sum('saldo_devedor'))
        .order_by('status')
    )

    # Alunos com maior saldo devedor
    top_devedores = contas.filter(saldo_devedor__gt=0).order_by('-saldo_devedor')[:10]

    anos_lectivos = AnoLectivo.objects.filter(escola=escola).order_by('-data_inicio')

    context = {
        'secao': 'financeiro',
        'diretor': diretor,
        'escola': escola,
        'resumo': resumo,
        'por_status': list(por_status),
        'top_devedores': top_devedores,
        'contas': contas[:40],
        'anos_lectivos': anos_lectivos,
        'status_choices': ContaAluno.STATUS,
        'filtros': {'ano_id': ano_id, 'status': status_f},
    }
    return render(request, 'diretor/financeiro/painel.html', context)


# ══════════════════════════════════════════════
# 8. COMUNICADOS
# ══════════════════════════════════════════════

@login_required
def lista_comunicados(request):
    """Lista e gestão de comunicados da escola."""
    diretor, escola = _get_diretor_escola(request)
    tipo_f = request.GET.get('tipo', '')

    comunicados = Comunicado.objects.filter(escola=escola).select_related(
        'publicado_por', 'turma'
    ).order_by('-data_publicacao')

    if tipo_f:
        comunicados = comunicados.filter(tipo=tipo_f)

    context = {
        'secao': 'comunicados',
        'diretor': diretor,
        'escola': escola,
        'comunicados': comunicados,
        'tipos': Comunicado.TIPOS,
        'total': comunicados.count(),
        'filtros': {'tipo': tipo_f},
    }
    return render(request, 'diretor/comunicados/lista.html', context)


# ══════════════════════════════════════════════
# 9. MATERIAL DIDÁCTICO
# ══════════════════════════════════════════════

@login_required
def lista_materiais(request):
    """Lista de materiais didácticos publicados na escola."""
    diretor, escola = _get_diretor_escola(request)
    disciplina_id = request.GET.get('disciplina')
    tipo_f        = request.GET.get('tipo', '')

    materiais = (
        MaterialDidatico.objects
        .filter(escola=escola, activo=True)
        .select_related('disciplina', 'classe', 'publicado_por')
        .order_by('-data_publicacao')
    )

    if disciplina_id:
        materiais = materiais.filter(disciplina_id=disciplina_id)
    if tipo_f:
        materiais = materiais.filter(tipo=tipo_f)

    disciplinas = Disciplina.objects.filter(escola=escola, activo=True)

    context = {
        'secao': 'materiais',
        'diretor': diretor,
        'escola': escola,
        'materiais': materiais,
        'disciplinas': disciplinas,
        'tipos': MaterialDidatico.TIPOS,
        'total': materiais.count(),
        'filtros': {'disciplina_id': disciplina_id, 'tipo': tipo_f},
    }
    return render(request, 'diretor/materiais/lista.html', context)


# ══════════════════════════════════════════════
# 10. CONFIGURAÇÕES DA ESCOLA
# ══════════════════════════════════════════════

@login_required
def configuracoes_escola(request):
    """Configurações operacionais da escola."""
    diretor, escola = _get_diretor_escola(request)

    try:
        config = escola.configuracao
    except TenantConfiguracao.DoesNotExist:
        config = None

    anos_lectivos = AnoLectivo.objects.filter(escola=escola).order_by('-data_inicio')
    periodos      = PeriodoAvaliativo.objects.filter(
        ano_lectivo__escola=escola
    ).select_related('ano_lectivo').order_by('-ano_lectivo__data_inicio', 'numero_periodo')

    context = {
        'secao': 'configuracoes',
        'diretor': diretor,
        'escola': escola,
        'config': config,
        'anos_lectivos': anos_lectivos,
        'periodos': periodos,
    }
    return render(request, 'diretor/configuracoes.html', context)


# ══════════════════════════════════════════════
# 11. RELATÓRIOS DO DIRECTOR
# ══════════════════════════════════════════════

@login_required
def relatorio_desempenho(request):
    """Relatório de desempenho académico da escola."""
    diretor, escola = _get_diretor_escola(request)
    turma_id   = request.GET.get('turma')
    periodo_id = request.GET.get('periodo')

    notas_qs = Nota.objects.filter(escola=escola)
    if turma_id:
        notas_qs = notas_qs.filter(avaliacao__turma_id=turma_id)
    if periodo_id:
        notas_qs = notas_qs.filter(avaliacao__periodo_id=periodo_id)

    media_escola = notas_qs.aggregate(media=Avg('nota'))['media']

    por_disciplina = (
        notas_qs.values('avaliacao__disciplina__nome')
        .annotate(media=Avg('nota'), total=Count('id'))
        .order_by('-media')
    )
    por_turma = (
        notas_qs.values(
            'avaliacao__turma__designacao',
            'avaliacao__turma__classe__designacao',
        )
        .annotate(media=Avg('nota'), total_alunos=Count('aluno', distinct=True))
        .order_by('-media')
    )
    # Taxa de aprovação (nota >= nota_minima_aprovacao)
    try:
        nota_min = float(escola.configuracao.nota_minima_aprovacao)
    except Exception:
        nota_min = 10.0

    total_notas    = notas_qs.count()
    notas_aprovadas = notas_qs.filter(nota__gte=nota_min).count()
    taxa_aprovacao  = (notas_aprovadas / total_notas * 100) if total_notas else 0

    turmas   = Turma.objects.filter(escola=escola, activo=True).select_related('classe', 'curso')
    periodos = PeriodoAvaliativo.objects.filter(
        ano_lectivo__escola=escola
    ).select_related('ano_lectivo')

    context = {
        'secao': 'relatorios',
        'diretor': diretor,
        'escola': escola,
        'media_escola': media_escola,
        'taxa_aprovacao': taxa_aprovacao,
        'por_disciplina': list(por_disciplina),
        'por_turma': list(por_turma),
        'turmas': turmas,
        'periodos': periodos,
        'filtros': {'turma_id': turma_id, 'periodo_id': periodo_id},
    }
    return render(request, 'diretor/relatorios/desempenho.html', context)


# ══════════════════════════════════════════════
# 12. ENDPOINT JSON — gráficos AJAX
# ══════════════════════════════════════════════

@login_required
def api_stats_diretor(request):
    """Dados JSON para os gráficos do dashboard do director."""
    diretor, escola = _get_diretor_escola(request)
    hoje = date.today()

    matriculas_mensal = []
    for i in range(5, -1, -1):
        mes_ref = hoje.replace(day=1) - timedelta(days=i * 30)
        qtd = Matricula.objects.filter(
            escola=escola,
            data_matricula__year=mes_ref.year,
            data_matricula__month=mes_ref.month,
        ).count()
        matriculas_mensal.append({'mes': mes_ref.strftime('%b/%Y'), 'qtd': qtd})

    alunos_curso = list(
        Matricula.objects.filter(escola=escola, status='Activa')
        .values('curso__nome')
        .annotate(total=Count('id'))
        .order_by('-total')[:6]
    )

    data = {
        'escola': escola.nome,
        'totais': {
            'alunos':      Aluno.objects.filter(escola=escola, status='Matriculado').count(),
            'professores': Professor.objects.filter(escola=escola, status='Activo').count(),
            'turmas':      Turma.objects.filter(escola=escola, activo=True).count(),
        },
        'matriculas_mensal': matriculas_mensal,
        'alunos_por_curso':  alunos_curso,
    }
    return JsonResponse(data)
