from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from django.http import JsonResponse
from datetime import date, timedelta

from .models import (
    TenantEscola, AnoLectivo, Aluno, Professor, Turma, Matricula,
    Inscricao, Curso, Disciplina, Nota, Avaliacao, ContaAluno,
    Comunicado, PeriodoAvaliativo, HorarioAula, MaterialDidatico,
    DocumentoAluno, TipoAvaliacao, Role, Permissao, UsuarioRole,
    PlanoSubscricao, Diretor, Classe, EncarregadoEducacao,
)


@login_required
def dashboard_admin(request):

    hoje = date.today()

    total_escolas = TenantEscola.objects.filter(activo=True).count()
    total_alunos = Aluno.objects.filter(status='Matriculado').count()
    total_professores = Professor.objects.filter(status='Activo').count()
    total_turmas = Turma.objects.filter(activo=True).count()

    matriculas_ativas = Matricula.objects.filter(status='Activa').count()
    matriculas_mes = Matricula.objects.filter(
        data_matricula__month=hoje.month,
        data_matricula__year=hoje.year
    ).count()

    inscricoes_recentes = Inscricao.objects.select_related(
        'aluno', 'escola', 'ano_lectivo', 'curso'
    ).order_by('-data_inscricao')[:10]

    financeiro = ContaAluno.objects.aggregate(
        total_pago=Sum('total_pago'),
        total_devido=Sum('total_devido'),
        saldo_devedor=Sum('saldo_devedor'),
    )
    
    contas_em_atraso = ContaAluno.objects.filter(status='Atrasado').count()
    contas_bloqueadas = ContaAluno.objects.filter(status='Bloqueado').count()

    # ── Comunicados ativos ─────────────────────
    comunicados_ativos = Comunicado.objects.filter(
        activo=True
    ).filter(
        Q(data_expiracao__isnull=True) | Q(data_expiracao__gte=hoje)
    ).select_related('escola').order_by('-data_publicacao')[:5]

    # ── Distribuição de alunos por status ──────
    alunos_por_status = (
        Aluno.objects
        .values('status')
        .annotate(total=Count('id'))
        .order_by('status')
    )

    # ── Escolas com plano a expirar (30 dias) ──
    limite = hoje + timedelta(days=30)
    escolas_expirando = TenantEscola.objects.filter(
        data_expiracao_plano__lte=limite,
        data_expiracao_plano__gte=hoje,
        activo=True,
    ).select_related('plano_subscricao').order_by('data_expiracao_plano')

    # ── Matrículas dos últimos 6 meses (gráfico) ─
    matriculas_mensal = []
    for i in range(5, -1, -1):
        mes_ref = hoje.replace(day=1) - timedelta(days=i * 30)
        qtd = Matricula.objects.filter(
            data_matricula__year=mes_ref.year,
            data_matricula__month=mes_ref.month,
        ).count()
        matriculas_mensal.append({'mes': mes_ref.strftime('%b/%Y'), 'qtd': qtd})

    context = {
        'secao': 'dashboard',
        # Totais
        'total_escolas': total_escolas,
        'total_alunos': total_alunos,
        'total_professores': total_professores,
        'total_turmas': total_turmas,
        # Matrículas
        'matriculas_ativas': matriculas_ativas,
        'matriculas_mes': matriculas_mes,
        'inscricoes_recentes': inscricoes_recentes,
        # Financeiro
        'financeiro': financeiro,
        'contas_em_atraso': contas_em_atraso,
        'contas_bloqueadas': contas_bloqueadas,
        # Comunicados
        'comunicados_ativos': comunicados_ativos,
        # Gráficos
        'alunos_por_status': list(alunos_por_status),
        'matriculas_mensal': matriculas_mensal,
        # Alertas
        'escolas_expirando': escolas_expirando,
    }
    return render(request, 'admin/dashboard.html', context)


# ──────────────────────────────────────────────
# GESTÃO DE ESCOLAS (TENANTS)
# ──────────────────────────────────────────────

@login_required
def lista_escolas(request):
    """Lista todas as escolas registadas no sistema."""
    escolas = (
        TenantEscola.objects
        .select_related('plano_subscricao')
        .annotate(
            total_alunos=Count('aluno', distinct=True),
            total_professores=Count('professor', distinct=True),
        )
        .order_by('nome')
    )
    planos = PlanoSubscricao.objects.filter(activo=True)
    context = {
        'secao': 'escolas',
        'escolas': escolas,
        'planos': planos,
        'total': escolas.count(),
    }
    return render(request, 'admin/escolas/lista.html', context)


@login_required
def detalhe_escola(request, escola_id):
    """Detalhe completo de uma escola específica."""
    escola = get_object_or_404(
        TenantEscola.objects.select_related('plano_subscricao'),
        id=escola_id
    )
    ano_lectivo_atual = AnoLectivo.objects.filter(
        escola=escola, e_atual=True
    ).first()

    stats = {
        'alunos': Aluno.objects.filter(escola=escola, status='Matriculado').count(),
        'professores': Professor.objects.filter(escola=escola, status='Activo').count(),
        'turmas': Turma.objects.filter(escola=escola, activo=True).count(),
        'cursos': Curso.objects.filter(escola=escola, activo=True).count(),
        'matriculas_ativas': Matricula.objects.filter(escola=escola, status='Activa').count(),
    }
    financeiro = ContaAluno.objects.filter(escola=escola).aggregate(
        total_pago=Sum('total_pago'),
        saldo_devedor=Sum('saldo_devedor'),
    )

    context = {
        'secao': 'escolas',
        'escola': escola,
        'ano_lectivo_atual': ano_lectivo_atual,
        'stats': stats,
        'financeiro': financeiro,
    }
    return render(request, 'admin/escolas/detalhe.html', context)


# ──────────────────────────────────────────────
# GESTÃO DE UTILIZADORES E ROLES
# ──────────────────────────────────────────────

@login_required
def lista_roles(request):
    """Lista todos os roles/perfis com contagem de utilizadores."""
    roles = (
        Role.objects
        .annotate(total_utilizadores=Count('usuario_roles', distinct=True))
        .prefetch_related('role_permissoes__permissao')
        .order_by('nome')
    )
    context = {
        'secao': 'roles',
        'roles': roles,
    }
    return render(request, 'admin/roles/lista.html', context)


@login_required
def detalhe_role(request, role_id):
    """Detalhes de um role com suas permissões."""
    role = get_object_or_404(Role, id=role_id)
    permissoes = (
        Permissao.objects
        .filter(role_permissoes__role=role)
        .values('nome', 'acao')
        .order_by('nome', 'acao')
    )
    utilizadores = (
        UsuarioRole.objects
        .filter(role=role)
        .select_related('utilizador', 'atribuido_por')
        .order_by('atribuido_em')
    )
    context = {
        'secao': 'roles',
        'role': role,
        'permissoes': permissoes,
        'utilizadores': utilizadores,
    }
    return render(request, 'admin/roles/detalhe.html', context)


@login_required
def lista_permissoes(request):
    """Lista todas as permissões agrupadas por recurso."""
    permissoes = (
        Permissao.objects
        .values('nome')
        .annotate(total_acoes=Count('id'))
        .order_by('nome')
    )
    todas = Permissao.objects.order_by('nome', 'acao')
    context = {
        'secao': 'permissoes',
        'permissoes_agrupadas': permissoes,
        'todas_permissoes': todas,
    }
    return render(request, 'admin/permissoes/lista.html', context)


# ──────────────────────────────────────────────
# GESTÃO DE PLANOS DE SUBSCRIÇÃO
# ──────────────────────────────────────────────

@login_required
def lista_planos(request):
    """Lista planos com contagem de escolas ativas em cada um."""
    planos = (
        PlanoSubscricao.objects
        .annotate(
            total_escolas=Count('tenantescola', distinct=True),
            escolas_ativas=Count(
                'tenantescola',
                filter=Q(tenantescola__activo=True),
                distinct=True,
            ),
        )
        .order_by('preco_mensal')
    )
    context = {
        'secao': 'planos',
        'planos': planos,
    }
    return render(request, 'admin/planos/lista.html', context)


# ──────────────────────────────────────────────
# GESTÃO DE ALUNOS (visão global)
# ──────────────────────────────────────────────

@login_required
def lista_alunos_global(request):
    """Lista global de alunos de todas as escolas com filtros."""
    escola_id = request.GET.get('escola')
    status_filtro = request.GET.get('status', '')
    busca = request.GET.get('q', '')

    alunos = Aluno.objects.select_related('escola').order_by('nome_completo')

    if escola_id:
        alunos = alunos.filter(escola_id=escola_id)
    if status_filtro:
        alunos = alunos.filter(status=status_filtro)
    if busca:
        alunos = alunos.filter(
            Q(nome_completo__icontains=busca) |
            Q(numero_processo__icontains=busca) |
            Q(bi__icontains=busca)
        )

    escolas = TenantEscola.objects.filter(activo=True).order_by('nome')
    context = {
        'secao': 'alunos',
        'alunos': alunos,
        'escolas': escolas,
        'status_choices': Aluno.STATUS,
        'filtros': {
            'escola_id': escola_id,
            'status': status_filtro,
            'q': busca,
        },
        'total': alunos.count(),
    }
    return render(request, 'admin/alunos/lista.html', context)


# ──────────────────────────────────────────────
# GESTÃO DE PROFESSORES (visão global)
# ──────────────────────────────────────────────

@login_required
def lista_professores_global(request):
    """Lista global de professores com filtros."""
    escola_id = request.GET.get('escola')
    status_filtro = request.GET.get('status', '')
    busca = request.GET.get('q', '')

    professores = (
        Professor.objects
        .select_related('escola', 'categoria')
        .annotate(total_disciplinas=Count('disciplinas_lecionadas', distinct=True))
        .order_by('nome_completo')
    )

    if escola_id:
        professores = professores.filter(escola_id=escola_id)
    if status_filtro:
        professores = professores.filter(status=status_filtro)
    if busca:
        professores = professores.filter(
            Q(nome_completo__icontains=busca) |
            Q(numero_agente__icontains=busca) |
            Q(bi__icontains=busca)
        )

    escolas = TenantEscola.objects.filter(activo=True).order_by('nome')
    context = {
        'secao': 'professores',
        'professores': professores,
        'escolas': escolas,
        'status_choices': Professor.STATUS,
        'filtros': {
            'escola_id': escola_id,
            'status': status_filtro,
            'q': busca,
        },
        'total': professores.count(),
    }
    return render(request, 'admin/professores/lista.html', context)


# ──────────────────────────────────────────────
# RELATÓRIOS E ESTATÍSTICAS
# ──────────────────────────────────────────────

@login_required
def relatorio_matriculas(request):
    """Relatório de matrículas por escola, curso e ano lectivo."""
    ano_id = request.GET.get('ano_lectivo')
    escola_id = request.GET.get('escola')

    matriculas = Matricula.objects.select_related(
        'escola', 'aluno', 'curso', 'turma', 'ano_lectivo'
    )

    if ano_id:
        matriculas = matriculas.filter(ano_lectivo_id=ano_id)
    if escola_id:
        matriculas = matriculas.filter(escola_id=escola_id)

    por_status = (
        matriculas.values('status')
        .annotate(total=Count('id'))
        .order_by('status')
    )
    por_tipo = (
        matriculas.values('tipo_matricula')
        .annotate(total=Count('id'))
        .order_by('tipo_matricula')
    )
    por_curso = (
        matriculas.values('curso__nome')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )

    anos_lectivos = AnoLectivo.objects.order_by('-data_inicio')
    escolas = TenantEscola.objects.filter(activo=True).order_by('nome')

    context = {
        'secao': 'relatorios',
        'total_matriculas': matriculas.count(),
        'por_status': list(por_status),
        'por_tipo': list(por_tipo),
        'por_curso': list(por_curso),
        'anos_lectivos': anos_lectivos,
        'escolas': escolas,
        'filtros': {'ano_id': ano_id, 'escola_id': escola_id},
    }
    return render(request, 'admin/relatorios/matriculas.html', context)


@login_required
def relatorio_financeiro(request):
    """Relatório financeiro consolidado."""
    escola_id = request.GET.get('escola')
    ano_id = request.GET.get('ano_lectivo')

    contas = ContaAluno.objects.select_related('escola', 'aluno', 'ano_lectivo')

    if escola_id:
        contas = contas.filter(escola_id=escola_id)
    if ano_id:
        contas = contas.filter(ano_lectivo_id=ano_id)

    resumo = contas.aggregate(
        total_pago=Sum('total_pago'),
        total_devido=Sum('total_devido'),
        saldo_devedor=Sum('saldo_devedor'),
    )
    por_status = (
        contas.values('status')
        .annotate(
            quantidade=Count('id'),
            valor=Sum('saldo_devedor'),
        )
        .order_by('status')
    )
    por_escola = (
        contas.values('escola__nome')
        .annotate(
            total_pago=Sum('total_pago'),
            saldo_devedor=Sum('saldo_devedor'),
        )
        .order_by('-total_pago')[:10]
    )

    escolas = TenantEscola.objects.filter(activo=True).order_by('nome')
    anos_lectivos = AnoLectivo.objects.order_by('-data_inicio')

    context = {
        'secao': 'relatorios',
        'resumo': resumo,
        'por_status': list(por_status),
        'por_escola': list(por_escola),
        'escolas': escolas,
        'anos_lectivos': anos_lectivos,
        'filtros': {'escola_id': escola_id, 'ano_id': ano_id},
    }
    return render(request, 'admin/relatorios/financeiro.html', context)


@login_required
def relatorio_notas(request):
    """Relatório de desempenho académico por escola/turma/disciplina."""
    escola_id = request.GET.get('escola')
    turma_id = request.GET.get('turma')

    notas = Nota.objects.select_related(
        'escola', 'aluno', 'avaliacao__disciplina', 'avaliacao__turma'
    )
    if escola_id:
        notas = notas.filter(escola_id=escola_id)
    if turma_id:
        notas = notas.filter(avaliacao__turma_id=turma_id)

    media_geral = notas.aggregate(media=Avg('nota'))['media']

    por_disciplina = (
        notas.values('avaliacao__disciplina__nome')
        .annotate(
            media=Avg('nota'),
            total_alunos=Count('aluno', distinct=True),
        )
        .order_by('-media')[:10]
    )

    escolas = TenantEscola.objects.filter(activo=True).order_by('nome')
    turmas = Turma.objects.select_related('classe', 'curso').filter(activo=True)

    context = {
        'secao': 'relatorios',
        'media_geral': media_geral,
        'por_disciplina': list(por_disciplina),
        'escolas': escolas,
        'turmas': turmas,
        'filtros': {'escola_id': escola_id, 'turma_id': turma_id},
    }
    return render(request, 'admin/relatorios/notas.html', context)


# ──────────────────────────────────────────────
# COMUNICADOS (visão global do admin)
# ──────────────────────────────────────────────

@login_required
def lista_comunicados(request):
    """Lista de comunicados de todas as escolas."""
    escola_id = request.GET.get('escola')
    tipo_filtro = request.GET.get('tipo', '')

    comunicados = Comunicado.objects.select_related(
        'escola', 'publicado_por', 'turma'
    ).order_by('-data_publicacao')

    if escola_id:
        comunicados = comunicados.filter(escola_id=escola_id)
    if tipo_filtro:
        comunicados = comunicados.filter(tipo=tipo_filtro)

    escolas = TenantEscola.objects.filter(activo=True).order_by('nome')

    context = {
        'secao': 'comunicados',
        'comunicados': comunicados[:50],
        'escolas': escolas,
        'tipos': Comunicado.TIPOS,
        'filtros': {'escola_id': escola_id, 'tipo': tipo_filtro},
        'total': comunicados.count(),
    }
    return render(request, 'admin/comunicados/lista.html', context)


# ──────────────────────────────────────────────
# ENDPOINTS JSON (para gráficos via AJAX)
# ──────────────────────────────────────────────

@login_required
def api_stats_dashboard(request):
    """Retorna estatísticas em JSON para actualização dinâmica dos gráficos."""
    hoje = date.today()

    matriculas_mensal = []
    for i in range(5, -1, -1):
        mes_ref = hoje.replace(day=1) - timedelta(days=i * 30)
        qtd = Matricula.objects.filter(
            data_matricula__year=mes_ref.year,
            data_matricula__month=mes_ref.month,
        ).count()
        matriculas_mensal.append({'mes': mes_ref.strftime('%b/%Y'), 'qtd': qtd})

    alunos_status = list(
        Aluno.objects.values('status').annotate(total=Count('id'))
    )

    data = {
        'totais': {
            'escolas': TenantEscola.objects.filter(activo=True).count(),
            'alunos': Aluno.objects.filter(status='Matriculado').count(),
            'professores': Professor.objects.filter(status='Activo').count(),
            'turmas': Turma.objects.filter(activo=True).count(),
        },
        'matriculas_mensal': matriculas_mensal,
        'alunos_status': alunos_status,
    }
    return JsonResponse(data)
