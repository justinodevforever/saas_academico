from django.contrib.auth.decorators import login_required
@login_required
def relatorio_alunos(request):
    """Relatório de alunos"""
    escola = request.user.escola
    
    # Estatísticas
    total_alunos = Aluno.objects.filter(escola=escola).count()
    alunos_por_status = Aluno.objects.filter(escola=escola).values('status').annotate(total=Count('id'))
    alunos_por_genero = Aluno.objects.filter(escola=escola).values('genero').annotate(total=Count('id'))
    alunos_por_provincia = Aluno.objects.filter(escola=escola).values('provincia').annotate(total=Count('id')).order_by('-total')[:10]
    
    context = {
        'total_alunos': total_alunos,
        'alunos_por_status': alunos_por_status,
        'alunos_por_genero': alunos_por_genero,
        'alunos_por_provincia': alunos_por_provincia,
    }
    
    return render(request, 'relatorios/alunos.html', context)


@login_required
def relatorio_professores(request):
    """Relatório de professores"""
    escola = request.user.escola
    
    total_professores = Professor.objects.filter(escola=escola).count()
    professores_por_status = Professor.objects.filter(escola=escola).values('status').annotate(total=Count('id'))
    professores_por_nivel = Professor.objects.filter(escola=escola).values('nivel_academico').annotate(total=Count('id'))
    professores_por_contrato = Professor.objects.filter(escola=escola).values('tipo_contrato').annotate(total=Count('id'))
    
    context = {
        'total_professores': total_professores,
        'professores_por_status': professores_por_status,
        'professores_por_nivel': professores_por_nivel,
        'professores_por_contrato': professores_por_contrato,
    }
    
    return render(request, 'relatorios/professores.html', context)


@login_required
def relatorio_turmas(request):
    """Relatório de turmas"""
    escola = request.user.escola
    ano_lectivo_activo = escola.configuracao.ano_lectivo_activo
    
    turmas = Turma.objects.filter(
        escola=escola,
        ano_lectivo=ano_lectivo_activo
    ).annotate(
        total_alunos=Count('matricula')
    ).select_related('classe', 'curso')
    
    context = {
        'turmas': turmas,
        'ano_lectivo_activo': ano_lectivo_activo,
    }
    
    return render(request, 'relatorios/turmas.html', context)