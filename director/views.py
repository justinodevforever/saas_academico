from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import date, timedelta, timezone
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from academico.decorators import *
from .forms import *
from academico.models import *
import json
from django.db.utils import IntegrityError

@escola_ativa_required
def _get_diretor_escola(request):

    diretor = get_object_or_404(Diretor, utilizador=request.user, escola__status_ensino='activa')
    return diretor, diretor.escola

def _get_ano_atual(escola):

    ano = AnoLectivo.objects.filter(escola=escola, e_atual=True).first()

    return ano

@login_required
@escola_ativa_required
@role_required('director')
def dashboard_diretor(request):

    diretor, escola = _get_diretor_escola(request)
    hoje = timezone.now().date()

    try:
        config = escola.configuracao
        ano_lectivo = config.ano_lectivo_activo
        periodo     = config.periodo_activo
    except TenantConfiguracao.DoesNotExist:
        ano_lectivo = AnoLectivo.objects.filter(escola=escola, e_atual=True).first()
        periodo     = None

    total_alunos        = Aluno.objects.filter(escola=escola, status='Matriculado').count()
    total_professores   = Funcionario.objects.filter(escola=escola, tipo_funcionario='Professor', status='Activo').count()
    total_turmas        = Turma.objects.filter(escola=escola, activo=True).count()
    total_disciplinas   = Disciplina.objects.filter(escola=escola, activo=True).count()

    matriculas_ativas   = Matricula.objects.filter(escola=escola, status='Activa').count()
    inscricoes_pendentes = Inscricao.objects.filter(
        escola=escola, ano_lectivo=ano_lectivo
    ).count() if ano_lectivo else 0

    financeiro = ContaAluno.objects.filter(escola=escola).aggregate(
        total_pago     = Sum('total_pago'),
        total_devido   = Sum('total_devido'),
        saldo_devedor  = Sum('saldo_devedor'),
    )
    contas_atrasadas  = ContaAluno.objects.filter(escola=escola, status='Atrasado').count()
    contas_bloqueadas = ContaAluno.objects.filter(escola=escola, status='Bloqueado').count()

    ultimas_matriculas = Matricula.objects.filter(escola=escola).select_related(
        'aluno', 'turma', 'ano_lectivo'
    ).order_by('-data_matricula')[:10]

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
        .values('turma__curso__nome')
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

    
    print(matriculas_mensal)

    context = {
        'secao': 'dashboard',
        'diretor': diretor,
        'escola': escola,
        'ano_lectivo': ano_lectivo,
        'periodo': periodo,
        'hoje': hoje,
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
        'secao': 'dashboard_director'
    }
    return render(request, 'director/index.html', context)


@login_required
def financeiro_dashboard(request):
  
    diretor, escola = _get_diretor_escola(request)
    ano_lectivo_activo = escola.configuracao.ano_lectivo_activo
    
    contas = ContaAluno.objects.filter(
        aluno__escola=escola,
        ano_lectivo=ano_lectivo_activo
    )
    
    total_a_receber = contas.aggregate(total=Sum('total_devido'))['total'] or Decimal('0')
    total_recebido = contas.aggregate(total=Sum('total_pago'))['total'] or Decimal('0')
    total_pendente = contas.aggregate(total=Sum('saldo_devedor'))['total'] or Decimal('0')
    
    contas_por_status = contas.values('status').annotate(
        total=Count('id'),
        valor=Sum('saldo_devedor')
    )
    
    hoje = timezone.now()
    meses_anteriores = []
    for i in range(6):
        mes = hoje - timedelta(days=30*i)
        meses_anteriores.append(mes.strftime('%Y-%m'))
    
    context = {
        'total_a_receber': total_a_receber,
        'total_recebido': total_recebido,
        'total_pendente': total_pendente,
        'contas_por_status': contas_por_status,
        'ano_lectivo_activo': ano_lectivo_activo,
    }
    
    return render(request, 'financeiro/dashboard.html', context)


@login_required
def financeiro_contas_list(request):
    
    diretor, escola = _get_diretor_escola(request)
    ano_lectivo_activo = escola.configuracao.ano_lectivo_activo
    
    contas = ContaAluno.objects.filter(
        aluno__escola=escola,
        ano_lectivo=ano_lectivo_activo
    ).select_related('aluno')
    
    status = request.GET.get('status')
    if status:
        contas = contas.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        contas = contas.filter(
            Q(aluno__nome_completo__icontains=search) |
            Q(aluno__numero_processo__icontains=search)
        )
    
    paginator = Paginator(contas, 20)
    page = request.GET.get('page')
    contas_page = paginator.get_page(page)
    
    context = {
        'contas': contas_page,
        'ano_lectivo_activo': ano_lectivo_activo,
    }
    
    return render(request, 'financeiro/contas_list.html', context)


@login_required
def financeiro_conta_detail(request, conta_id):
   
    conta = get_object_or_404(
        ContaAluno.objects.select_related('aluno', 'ano_lectivo'),
        id=conta_id
    )
    
    context = {
        'conta': conta,
    }
    
    return render(request, 'financeiro/conta_detail.html', context)


@login_required
def lista_turmas(request):
 
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



@login_required
def turma_list(request):
  
    diretor, escola = _get_diretor_escola(request)
    
    turmas = Turma.objects.filter(escola=escola).select_related(
        'ano_lectivo', 'curso', 'classe'
    ).order_by('-ano_lectivo__e_atual', 'classe__ordem', 'designacao')
    
    ano_lectivo_id = request.GET.get('ano_lectivo')
    curso_id = request.GET.get('curso')
    classe_id = request.GET.get('classe')
    order_by = request.GET.get('order_by')
    
    if ano_lectivo_id:
        turmas = turmas.filter(ano_lectivo_id=ano_lectivo_id)
    if curso_id:
        turmas = turmas.filter(curso_id=curso_id)
    if classe_id:
        turmas = turmas.filter(classe_id=classe_id)
    
    if order_by:
        turmas = turmas.order_by(order_by)

    per_page = request.GET.get('per_page', 20)
    page = request.GET.get('page')

    paginator = Paginator(turmas, per_page)
    turmas_page = paginator.get_page(page)
    
    
    
    context = {
        'secao': 'turmas',
        'turmas': turmas_page,
    }
    
    return render(request, 'turmas/list.html', context)

@login_required
def turma_estudante_list(request, turma_id):
  
    diretor, escola = _get_diretor_escola(request)
    
    turmas = Turma.objects.filter(escola=escola).select_related(
        'ano_lectivo', 'curso', 'classe', 'director_turma'
    ).annotate(
        total_alunos=Count('matricula')
    ).order_by('-ano_lectivo__activo', 'classe__ordem', 'designacao')
    
    ano_lectivo_id = request.GET.get('ano_lectivo')
    curso_id = request.GET.get('curso')
    classe_id = request.GET.get('classe')
    turno = request.GET.get('turno')
    
    if ano_lectivo_id:
        turmas = turmas.filter(ano_lectivo_id=ano_lectivo_id)
    if curso_id:
        turmas = turmas.filter(curso_id=curso_id)
    if classe_id:
        turmas = turmas.filter(classe_id=classe_id)
    if turno:
        turmas = turmas.filter(turno=turno)
    
    anos_lectivos = AnoLectivo.objects.filter(escola=escola)
    cursos = Curso.objects.filter(escola=escola, activo=True)
    classes = Classe.objects.all()
    
    context = {
        'turmas': turmas,
        'anos_lectivos': anos_lectivos,
        'cursos': cursos,
        'classes': classes,
    }
    
    return render(request, 'turmas/list.html', context)


@login_required
def turma_create(request):

    diretor, escola = _get_diretor_escola(request)

    form = TurmaForm(escola=escola)
    
    if request.method == 'POST':
        form = TurmaForm(request.POST, escola=escola)
        
        
        if form.is_valid():
           
            turma = form.save()

            turma.escola = escola

            turma.save()
            
            return redirect('turma_detail', turma_id=turma.id)
            
        else:
            context = {
                'erro': 'Erro ao Criar turma, corrija os erros abaixo!',
                'secao': 'turmas',
                'form': form
            }
            
            return render(request, 'turmas/create.html', context)
    
    context = {
        'secao': 'turmas',
        'form': form
    }
    
    return render(request, 'turmas/create.html', context)

@login_required
def turma_update(request, turma_id):

    turma = Turma.objects.get(id=turma_id)

    diretor, escola = _get_diretor_escola(request)
    
    form = TurmaEditForm(escola=escola, turma=turma)
    
    if request.method == 'POST':
        form = TurmaEditForm(request.POST, escola=escola, turma=turma)
        
        
        if form.is_valid():
           
            turma = form.save()

            turma.save()
            
            return redirect('turma_detail', turma_id=turma.id)
            
        else:
            context = {
                'erro': 'Erro ao atualizar turma, corrija os erros abaixo!',
                'form': form,
                'secao': 'turmas',
                'turma': turma
            }
            
            return render(request, 'turmas/edit.html', context)
    
    context = {

        'form': form,
        'secao': 'turmas',
        'turma': turma
    }
    
    return render(request, 'turmas/edit.html', context)

@login_required
@require_http_methods('POST')
def turma_delete(request, turma_id):

    turma = Turma.objects.get(id=turma_id)

    user = request.user

    dados = json.loads(request.body)
    user = request.user
    password = dados.get('password')

    if not user.check_password(password.strip()):

        return JsonResponse({'error': 'Credenciais inválidas'}, status=403)
    
    
    LogAuditoria.objects.create(
        escola=request.user.escola,
        utilizador=request.user,
        accao='delete',
        modulo='Turma',
        descricao=f'Turma: {turma.designacao} eliminado',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    turma.delete()

    return redirect('turma_list')

@login_required
def turma_detail(request, turma_id):

    director, escola = _get_diretor_escola(request)

    turma = get_object_or_404(
        Turma.objects.select_related(
            'escola', 'ano_lectivo', 'curso', 'classe'
        ),
        id=turma_id,
        escola=escola
    )
    
    total_alunos  = Matricula.objects.filter(
        turma=turma, 
        status='Activa'
    ).select_related('aluno').order_by('aluno__nome_completo').count()
    
    disciplinas_professores = TurmaDisciplina.objects.filter(
        turma=turma
    ).select_related('disciplina', 'professor')

    horarios = turma.horarios.all().select_related('disciplina', 'professor')
    
    context = {
        'turma': turma,
        'secao': 'turmas',
        'disciplinas_professores': disciplinas_professores,
        'horarios': horarios,
        'total_alunos': total_alunos,
    }
    
    return render(request, 'turmas/detail.html', context)


@login_required
def classe_list(request):
  
    diretor, escola = _get_diretor_escola(request)
    
    classes = Classe.objects.filter(escola=escola).order_by('designacao')
    
    designacao = request.GET.get('designacao')
    
    if designacao:
        classes = classes.filter(designacao=designacao)
    
    per_page = request.GET.get('per_page', 20)
    page = request.GET.get('page')

    paginator = Paginator(classes, per_page)
    classes_page = paginator.get_page(page)

    context = {
        'per_page': per_page,
        'secao': 'classes',
        'classes': classes_page,
        
    }
    
    return render(request, 'classes/list.html', context)

@login_required
def classe_create(request):

    diretor, escola = _get_diretor_escola(request)

    form = CriarClasseForm()
    
    if request.method == 'POST':
        form = CriarClasseForm(request.POST)
        
        
        if form.is_valid():
           
            classe = form.save()

            classe.escola = escola

            classe.save()
            
            return redirect('classe_detail', classe_id=classe.id)
            
        else:
            context = {
                'secao': 'classes',
                'erro': 'Erro ao Criar classe, corrija os erros abaixo!',
                'form': form
            }
            
            return render(request, 'classes/create.html', context)
    
    context = {

        'secao': 'classes',
        'form': form
    }
    
    return render(request, 'classes/create.html', context)

@login_required
def classe_update(request, classe_id):

    classe = Classe.objects.get(id=classe_id)

    form = EditarClasseForm( instance=classe)
    
    if request.method == 'POST':
        form = EditarClasseForm(request.POST, instance=classe)
        
        
        if form.is_valid():
           
            classe = form.save()
            classe.save()
            
            return redirect('classe_detail', classe_id=classe.id)
            
        else:
            context = {
                'erro': 'Erro ao atualizar classe, corrija os erros abaixo!',
                'form': form,
                'secao': 'classes',
                'classe': classe
            }
            
            return render(request, 'classes/update.html', context)
    
    context = {

        'form': form,
        'secao': 'classes',
        'classe': classe
    }
    
    return render(request, 'classes/update.html', context)

@login_required
@require_http_methods('POST')
def classe_delete(request, classe_id):

    classe = Classe.objects.get(id=classe_id)

    user = request.user

    dados = json.loads(request.body)
    user = request.user
    password = dados.get('password')

    if not user.check_password(password.strip()):

        return JsonResponse({'error': 'Credenciais inválidas'}, status=403)
    
    
    LogAuditoria.objects.create(
        escola=request.user.escola,
        utilizador=request.user,
        accao='delete',
        modulo='Classe',
        descricao=f'Classe: {classe.designacao} eliminado',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    classe.delete()

    return redirect('classe_list')

@login_required
def classe_detail(request, classe_id):

    classe = Classe.objects.get(id=classe_id)

    alunos = Matricula.objects.filter(turma__classe=classe)
    
    context = {
        'classe': classe,
        'secao': 'classes',
        'alunos': alunos
    }
    
    return render(request, 'classes/detail.html', context)


@login_required
def disciplina_list(request):
    
    diretor, escola = _get_diretor_escola(request)
    
    disciplinas = Disciplina.objects.filter(escola=escola).order_by('nome')
    
    busca = request.GET.get('busca')
    if busca:
        disciplinas = disciplinas.filter(
            Q(nome__icontains=busca) |
            Q(codigo__icontains=busca) |
            Q(nome_abreviado__icontains=busca)
        )
    
    per_page = request.GET.get('per_page', 20)
    page = request.GET.get('page')

    paginator = Paginator(disciplinas, per_page)
    disciplinas_page = paginator.get_page(page)

    context = {
        'disciplinas': disciplinas_page,
    }
    
    return render(request, 'disciplinas/list.html', context)

@login_required
def disciplina_create(request):
   
    diretor, escola = _get_diretor_escola(request)

    form = CriarDisciplinaForm()

    if request.method == 'POST':

        form = CriarDisciplinaForm(request.POST)
        
        if form.is_valid():

            disciplina = form.save()

            disciplina.escola = escola
            disciplina.save()
            
            context = {
                'sucesso': 'Disciplina criada com sucesso!',
                'secao': 'disciplinas',
                'form': form
            }

            return redirect('disciplina_detail', disciplina.id)
            
        else:
            context = {
                'erro': 'Erro ao criar a Disciplina!',
                'secao': 'disciplinas',
                'form': form
            }

            return render(request, 'disciplinas/create.html', context)
    
    return render(request, 'disciplinas/create.html', {'form': form,'secao': 'disciplinas'})

@login_required
def disciplina_edit(request, disciplina_id):

    disciplina = Disciplina.objects.get(id=disciplina_id)
   
    diretor, escola = _get_diretor_escola(request)

    form = EditarDisciplinaForm(instance=disciplina)

    if request.method == 'POST':

        form = EditarDisciplinaForm(request.POST, instance=disciplina)
        
        if form.is_valid():

            disciplina = form.save()

            disciplina.escola = escola
            disciplina.save()
            
            context = {
                'sucesso': 'Disciplina atualizada com sucesso!',
                'form': form,
                'secao': 'disciplinas',
                'disciplina': disciplina,
            }

            return render(request, 'disciplinas/edit.html', context)
            
        else:
            context = {
                'erro': 'Erro ao atualizada a Disciplina!',
                'disciplina': disciplina,
                'secao': 'disciplinas',
                'form': form

            }

            return render(request, 'disciplinas/edit.html', context)
    
    return render(request, 'disciplinas/edit.html', {'form': form,'disciplina': disciplina})


@login_required
def disciplina_detail(request, disciplina_id):

    diretor, escola = _get_diretor_escola(request)
    ano_atual = _get_ano_atual(escola)
   
    disciplina = get_object_or_404(
        Disciplina,
        id=disciplina_id,
        escola=escola
    )

    if request.method == 'POST':

        dados = json.loads(request.body)
        professor = dados.get('professor')
        turma = dados.get('turma')
        carga_horaria = dados.get('carga_horaria')
        action = request.GET.get('action')
        turma_id = request.GET.get('uuid')

        if action == 'edit' and turma_id:

            try:

                turma_disciplina = TurmaDisciplina.objects.get(id=turma_id)
                professor_obj = Funcionario.objects.get(id=professor)
                turma_obj = Turma.objects.get(id=turma)

                turma_disciplina.professor = professor_obj
                turma_disciplina.turma = turma_obj
                turma_disciplina.carga_horaria = carga_horaria


                turma_disciplina.save()

                return JsonResponse({'success': 'A troca de disciplina feita com sucesso'}, status=200)

            except Exception as e:
                print(e)

                return JsonResponse({'error': 'Houve um erro verifica os dados informado'}, status=500)

        else:
            try:

                TurmaDisciplina.objects.create(
                    disciplina=disciplina,
                    professor_id=professor,
                    turma_id=turma,
                    carga_horaria=carga_horaria,
                    escola=escola
                )

                return JsonResponse({'success': 'Disciplina atribuida com sucesso'}, status=200)

            except IntegrityError:

                return JsonResponse({'error': 'Essa disciplina já está associada a um professor!'}, status=500)
            
            except Exception  as e:

                return JsonResponse({'error': 'Houve um erro verifica os dados informado'}, status=500)

        
    else:

        turma_associadas = Turma.objects.filter(
            escola=escola,
            ano_lectivo = ano_atual
        )

        professores = Funcionario.objects.filter(
            escola=escola,
            tipo_funcionario='Professor',
            status='Activo'
        )
        
        
        turmas = TurmaDisciplina.objects.filter(
            disciplina=disciplina,
            escola=escola
        ).select_related('turma', 'professor')
        
        context = {
            'disciplina': disciplina,
            'turmas': turmas,
            'turma_associadas': turma_associadas,
            'professores': professores,
            'secao': 'disciplinas',
        }
        
        return render(request, 'disciplinas/detail.html', context)

@login_required
def curso_list(request):

    diretor, escola = _get_diretor_escola(request)
    
    cursos = Curso.objects.filter(escola=escola).order_by('nome')

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 20)

    paginator = Paginator(cursos, per_page)
    obj = paginator.page(page)

    context = {
        'secao': 'cursos',
        'cursos': obj,
    }
    
    return render(request, 'cursos/list.html', context)

@login_required
def curso_create(request):
   
    diretor, escola = _get_diretor_escola(request)

    form = CriarCursoForm()

    if request.method == 'POST':

        form = CriarCursoForm(request.POST)
        
        if form.is_valid():

            curso = form.save()

            curso.escola = escola
            curso.save()
            
            return redirect('curso_detail', curso.id)
            
        else:
            context = {
                'erro': 'Erro ao criar a curso!',
                'secao': 'cursos',
                'form': form
            }

            return render(request, 'cursos/create.html', context)
    
    return render(request, 'cursos/create.html', {'form': form})

@login_required
def curso_update(request, curso_id):

    curso = Curso.objects.get(id=curso_id)
   
    diretor, escola = _get_diretor_escola(request)

    form = EditarCursoForm(instance=curso)

    if request.method == 'POST':

        form = EditarCursoForm(request.POST, instance=curso)
        
        if form.is_valid():

            curso = form.save()

            curso.escola = escola
            curso.save()
            

            return redirect('curso_detail', curso.id)
            
        else:
            context = {
                'erro': 'Erro ao atualizada curso!',
                'form': form
            }

            return render(request, 'cursos/update.html', context)
    
    return render(request, 'cursos/update.html', {'form': form, 'curso': curso})


@login_required
def curso_detail(request, curso_id):

    diretor, escola = _get_diretor_escola(request)

    ano_atual = _get_ano_atual(escola)
    
    curso = get_object_or_404(
        Curso,
        id=curso_id,
        escola=escola
    )
    
    turmas = Turma.objects.filter(
        curso=curso,
        escola=escola,
        ano_lectivo=ano_atual
    )

    total_alunos = Matricula.objects.filter(
        escola=escola,
        turma__curso = curso,
        ano_lectivo=ano_atual
    ).count()


    order_by = request.GET.get('order_by')

    if order_by:
        turmas = turmas.order_by(order_by)

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 20)

    paginator = Paginator(turmas, per_page)
    obj = paginator.page(page)

    context = {
        'curso': curso,
        'secao': 'cursos',
        'total_alunos': total_alunos,
        'turmas': obj,
    }
    
    return render(request, 'cursos/detail.html', context)

@login_required
@require_http_methods('POST')
def curso_delete(request, curso_id):

    curso = Curso.objects.get(id=curso_id)

    user = request.user

    dados = json.loads(request.body)
    user = request.user
    password = dados.get('password')

    if not user.check_password(password.strip()):

        return JsonResponse({'error': 'Credenciais inválidas'}, status=403)
    
    
    LogAuditoria.objects.create(
        escola=request.user.escola,
        utilizador=request.user,
        accao='delete',
        modulo='Curso',
        descricao=f'Curso: {curso.nome} eliminado',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    curso.delete()

    return redirect('curso_list')

@login_required
def anoletivo_list(request):

    diretor, escola = _get_diretor_escola(request)
    anoletivos = AnoLectivo.objects.filter(escola=escola).order_by('-designacao')
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 20)

    paginator = Paginator(anoletivos, per_page)
    obj = paginator.page(page)

    context = {
        'secao': 'ano_letivos',
        'per_page': per_page,
        'anoletivos': obj,
    }
    
    return render(request, 'anoletivos/list.html', context)

@login_required
def anoletivo_create(request):
   
    diretor, escola = _get_diretor_escola(request)

    form = CriarAnoLetivoForm()

    if request.method == 'POST':

        form = CriarAnoLetivoForm(request.POST)
        
        if form.is_valid():

            anoletivo = form.save()

            anoletivo.escola = escola
            anoletivo.save()
            
            return redirect('anoletivo_detail', anoletivo.id)
            
        else:
            context = {
                'erro': 'Erro ao criar ano lectivo!',
                'secao': 'ano_letivos',
                'form': form
            }

            return render(request, 'anoletivos/create.html', context)
    
    return render(request, 'anoletivos/create.html', {'form': form, 'secao': 'ano_letivos',})

@login_required
def anoletivo_update(request, anoletivo_id):

    anoletivo = AnoLectivo.objects.get(id=anoletivo_id)
   
    diretor, escola = _get_diretor_escola(request)

    form = EditarAnoLetivoForm(instance=anoletivo)

    if request.method == 'POST':

        form = EditarAnoLetivoForm(request.POST, instance=anoletivo)
        
        if form.is_valid():

            anoletivo = form.save()

            anoletivo.escola = escola
            anoletivo.save()
            

            return redirect('anoletivo_detail', anoletivo.id)
            
        else:
            context = {
                'secao': 'ano_letivos',
                'erro': 'Erro ao atualizar ano lectivo!',
                'form': form,
                'anoletivo': anoletivo
            }

            return render(request, 'anoletivos/update.html', context)
    
    return render(request, 'anoletivos/update.html', {'form': form, 'anoletivo': anoletivo, 'secao': 'ano_letivos'})


@login_required
def anoletivo_detail(request, anoletivo_id):

    diretor, escola = _get_diretor_escola(request)
   
    anoletivo = get_object_or_404(
        AnoLectivo,
        id=anoletivo_id,
        escola=escola
    )
    
    total_alunos = Matricula.objects.filter(
        ano_lectivo=anoletivo
    ).distinct('aluno').count()

    total_inscricao = Inscricao.objects.filter(
        ano_lectivo=anoletivo
    ).distinct('candidato').count()
    



    context = {
        'anoletivo': anoletivo,
        'total_inscricao': total_inscricao,
        'secao': 'ano_letivos',
        'total_alunos':total_alunos
    }
    
    return render(request, 'anoletivos/detail.html', context)

@login_required
def ano_lectivo_ativar(request, ano_id):
    """Ativar ano letivo"""
    ano_lectivo = get_object_or_404(AnoLectivo, id=ano_id, escola=request.user.escola)
    
    # Desativar outros anos
    AnoLectivo.objects.filter(escola=request.user.escola).update(activo=False)
    
    # Ativar o selecionado
    ano_lectivo.activo = True
    ano_lectivo.save()
    
    # Atualizar configuração
    configuracao = request.user.escola.configuracao
    configuracao.ano_lectivo_activo = ano_lectivo
    configuracao.save()
    
    messages.success(request, f'Ano letivo {ano_lectivo.designacao} ativado com sucesso!')
    return redirect('ano_lectivo_list')

@login_required
@require_http_methods('POST')
def anoletivo_delete(request, anoletivo_id):

    anoletivo = AnoLectivo.objects.get(id=anoletivo_id)

    user = request.user

    dados = json.loads(request.body)
    user = request.user
    password = dados.get('password')

    if not user.check_password(password.strip()):

        return JsonResponse({'error': 'Credenciais inválidas'}, status=403)
    
    
    LogAuditoria.objects.create(
        escola=request.user.escola,
        utilizador=request.user,
        accao='delete',
        modulo='AnoLectivo',
        descricao=f'Ano lectivo: {anoletivo.designacao} eliminado',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    anoletivo.delete()

    return redirect('anoletivo_list')

@login_required
def periodo_list(request):

    diretor, escola = _get_diretor_escola(request)
    periodos = Periodo.objects.filter(escola=escola).order_by('-designacao')

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 20)

    paginator = Paginator(periodos, per_page)
    obj = paginator.page(page)

    context = {
        'secao': 'periodos',
        'per_page': per_page,
        'periodos': obj,
    }
    
    return render(request, 'periodos/list.html', context)

@login_required
def periodo_create(request):
   
    diretor, escola = _get_diretor_escola(request)

    form = CriarPeriodoForm()

    if request.method == 'POST':

        form = CriarPeriodoForm(request.POST)
        
        if form.is_valid():

            periodo = form.save()

            periodo.escola = escola
            periodo.save()
            
            return redirect('periodo_detail', periodo.id)
            
        else:
            context = {
                'erro': 'Houve erro ao criar período!',
                'secao': 'periodos',
                'form': form
            }

            return render(request, 'periodos/create.html', context)
    
    return render(request, 'periodos/create.html', {'form': form, 'secao': 'periodos',})

@login_required
def periodo_detail(request, periodo_id):

    diretor, escola = _get_diretor_escola(request)
   
    periodo = get_object_or_404(
        Periodo,
        id=periodo_id,
        escola=escola
    )
    
    total_alunos = Matricula.objects.filter(
        turma__periodo=periodo
    ).distinct('aluno').count()

    total_inscricao = Inscricao.objects.filter(
        periodo=periodo
    ).distinct('candidato').count()


    context = {
        'periodo': periodo,
        'total_inscricao': total_inscricao,
        'secao': 'periodos',
        'total_alunos':total_alunos
    }
    
    return render(request, 'periodos/detail.html', context)

@login_required
def encarregado_list(request):

    diretor, escola = _get_diretor_escola(request)
    encarregados = EncarregadoEducacao.objects.filter(escola=escola).order_by('nome_completo')
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 20)

    paginator = Paginator(encarregados, per_page)
    obj = paginator.page(page)

    context = {
        'encarregados': obj,
    }
    
    return render(request, 'encarregados/list.html', context)

@login_required
def encarregado_create(request, aluno_id):
   
    diretor, escola = _get_diretor_escola(request)

    form = EncarregadoForm()
    aluno = Aluno.objects.get(id=aluno_id)

    if request.method == 'POST':

        form = EncarregadoForm(request.POST)
        
        if form.is_valid():

            encarregado = form.save()

            encarregado.escola = escola
            encarregado.save()

            AlunoEncarregado.objects.create(
                aluno = aluno,
                encarregado=encarregado
            )
            
            return redirect('encarregado_detail', encarregado.id)
            
        else:
            context = {
                'erro': 'Erro ao criar Encarregado!',
                'form': form,
                'aluno_id': aluno_id
            }

            return render(request, 'encarregados/create.html', context)
    
    return render(request, 'encarregados/create.html', {'form': form, 'aluno_id': aluno_id})

@login_required
def encarregado_update(request, encarregado_id):

    encarregado = EncarregadoEducacao.objects.get(id=encarregado_id)
   
    diretor, escola = _get_diretor_escola(request)

    form = EncarregadoForm(encarregado=encarregado)

    if request.method == 'POST':

        form = EncarregadoForm(request.POST, encarregado=encarregado)
        
        if form.is_valid():

            encarregado = form.save()

            encarregado.escola = escola
            encarregado.save()
            

            return redirect('encarregado_detail', encarregado.id)
            
        else:
            context = {
                'erro': 'Erro ao atualizar encarregado!',
                'form': form
            }

            return render(request, 'encarregados/update.html', context)
    
    return render(request, 'encarregados/update.html', {'form': form, 'encarregado': encarregado})


@login_required
def encarregado_detail(request, encarregado_id):
   
    encarregado = get_object_or_404(
        EncarregadoEducacao,
        id=encarregado_id,
        escola=request.user.escola
    )
    
    aluno_encarregados = AlunoEncarregado.objects.filter(
        encarregado=encarregado
    )
    
    context = {
        'encarregado': encarregado,
        'aluno_encarregados': aluno_encarregados,
    }
    
    return render(request, 'encarregados/detail.html', context)

@login_required
@require_http_methods('POST')
def encarregado_delete(request, encarregado_id):

    encarregado = EncarregadoEducacao.objects.get(id=encarregado_id)

    user = request.user

    dados = json.loads(request.body)
    user = request.user
    password = dados.get('password')

    if not user.check_password(password.strip()):

        return JsonResponse({'error': 'Credenciais inválidas'}, status=403)
    
    
    LogAuditoria.objects.create(
        escola=request.user.escola,
        utilizador=request.user,
        accao='delete',
        modulo='Encarregado',
        descricao=f'Encarregado: {encarregado.nome_completo} eliminado',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    encarregado.delete()

    return redirect('encarregado_list')


@login_required
def aluno_list(request):
    
    diretor, escola = _get_diretor_escola(request)
    
    alunos = Aluno.objects.filter(escola=escola).select_related('utilizador').order_by('nome_completo')
    
    search = request.GET.get('search')
    if search:
        alunos = alunos.filter(
            Q(nome_completo__icontains=search) |
            Q(numero_processo__icontains=search) |
            Q(bi__icontains=search)
        )
    
    per_page = request.GET.get('per_page', 20)
    paginator = Paginator(alunos, per_page)
    page = request.GET.get('page', 1)
    alunos_page = paginator.get_page(page)
    
    context = {
        'alunos': alunos_page,
        'per_page': per_page,
        'search': search,
        'total_alunos': alunos.count(),
    }
    
    return render(request, 'alunos/list.html', context)


@login_required
def aluno_create(request):

    diretor, escola = _get_diretor_escola(request)

    form = AlunoForm()

    if request.method == 'POST':

        form = AlunoForm(request.POST)

        if form.is_valid():

            aluno = form.save()

            aluno.escola = escola

            aluno.save()
       
            context = {
                'sucesso': 'Aluno criado com sucesso!',
                 'form': form
            }

            return render(request, 'alunos/create.html', context)
        else:

            context = {
                'erro': 'Erro ao criar o Aluno!',
                 'form': form
            }

            return render(request, 'alunos/create.html', context)
        
    context = {
        'form': form
    }

    return render(request, 'alunos/create.html', context)


@login_required
def aluno_detail(request, aluno_id):

    aluno = get_object_or_404(Aluno, id=aluno_id, escola=request.user.escola)
    
    matriculas = Matricula.objects.filter(aluno=aluno, status='Activa').select_related(
        'ano_lectivo', 'turma'
    ).order_by('-ano_lectivo__data_inicio')
    
    encarregados = AlunoEncarregado.objects.filter(aluno=aluno).select_related('encarregado')
    
    documentos = DocumentoAluno.objects.filter(aluno=aluno).order_by('-data_upload')
    
    conta = ContaAluno.objects.filter(aluno=aluno).first()
    
    context = {
        'aluno': aluno,
        'matriculas': matriculas,
        'encarregados': encarregados,
        'documentos': documentos,
        'conta': conta,
    }
    
    return render(request, 'alunos/detail.html', context)


@login_required
def aluno_update(request, aluno_id):

    aluno = get_object_or_404(Aluno, id=aluno_id, escola=request.user.escola)

    form = AlunoEditForm(aluno=aluno)
    
    if request.method == 'POST':

        form = AlunoEditForm(request.POST, aluno=aluno)

        if form.is_valid():

            aluno = form.save()
            aluno.save()

            
            return redirect('aluno_detail', aluno_id=aluno.id)
        
        else:

            context = {
                'aluno': aluno,
                'form': form,
                'erro': 'Erro ao atualizar dados do aluno!'
                }
            
            return render(request, 'alunos/update.html', context)
        
    context = {
        'aluno': aluno,
        'form': form,
        }
    return render(request, 'alunos/update.html', context)


@login_required
@require_http_methods('POST')
def aluno_delete(request, aluno_id):

    aluno = get_object_or_404(Aluno, id=aluno_id, escola=request.user.escola)
    
    if request.method == 'POST':
        aluno.status = 'Desistente'
        aluno.save()
        messages.success(request, 'Aluno desativado com sucesso!')
        return redirect('aluno_list')
    
    context = {'aluno': aluno}
    return render(request, 'alunos/delete.html', context)

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

@login_required
def funcionario_create(request):

    form = FuncionarioForm()

    diretor, escola = _get_diretor_escola(request)

    if request.method == 'POST':

        form = FuncionarioForm(request.POST)

        if form.is_valid():

            funcionario = form.save()
            
            funcionario.escola = escola
            funcionario.save()

            if escola.plano_subscricao.nome == 'plus' and funcionario.tipo_funcionario == 'Professor':

                role = Role.objects.filter(nome='professor').first()

                utilizador = Utilizador(
                    email=funcionario.email,
                    username=funcionario.email,
                    nome_completo=funcionario.nome_completo
                )

                utilizador.set_password('123')
                utilizador.save()

                userRole = UsuarioRole(
                    role=role,
                    utilizador=utilizador
                )

                userRole.atribuido_por = request.user

                userRole.save()

                funcionario.utilizador = utilizador

                funcionario.save()
       
            context = {
                'secao': 'funcionarios',
                'sucesso': 'Funcionário criado com sucesso!',
                 'form': form
            }

            return render(request, 'funcionarios/create.html', context)
        else:

            context = {
                'secao': 'funcionarios',
                'erro': 'Erro ao criar o funcionário!',
                 'form': form
            }

            return render(request, 'funcionarios/create.html', context)
        
    context = {
        'secao': 'funcionarios',
        'form': form
    }

    return render(request, 'funcionarios/create.html', context)

@login_required
def funcionario_list(request):
   
    diretor, escola = _get_diretor_escola(request)
    
    funcionarios = (
        Funcionario.objects
        .filter(escola=escola)
        .annotate(
            total_disciplinas=Count('turma_disciplinas__disciplina', distinct=True),
            total_turmas=Count('turma_disciplinas', distinct=True),
        )
        .order_by('nome_completo')
    )
    
   
    search = request.GET.get('search')
    if search:
        funcionarios = funcionarios.filter(
            Q(nome_completo__icontains=search) |
            Q(numero_agente__icontains=search) |
            Q(especialidade__icontains=search)
        )
    
    per_page = request.GET.get('per_page', 20)
    paginator = Paginator(funcionarios, per_page)
    page = request.GET.get('page', 1)
    funcionarios_page = paginator.get_page(page)
    
    context = {
        'secao': 'funcionarios',
        'diretor': diretor,
        'escola': escola,
        'funcionarios': funcionarios,
        'status_choices': Funcionario.Status,
        'total': funcionarios.count(),
    }
    
    return render(request, 'funcionarios/list.html', context)



@login_required
def funcionario_edit(request, funcionario_id):

    funcionario = Funcionario.objects.get(id=funcionario_id)

    form = FuncionarioEditForm(funcionario=funcionario)

    if request.method == 'POST':

        form = FuncionarioEditForm(request.POST,funcionario=funcionario)

        if form.is_valid():

            funcionario = form.save()

            funcionario.save()
       
            context = {
                'secao': 'funcionarios',
                'sucesso': 'Funcionário atualizado com sucesso!',
                'form': form,
                'funcionario': funcionario,
            }

            return redirect('funcionario_list')
        else:

            context = {
                'secao': 'funcionarios',
                'erro': 'Erro ao atualizar o funcionário!',
                'funcionario': funcionario,
                'form': form
            }

            return render(request, 'funcionarios/edit.html', context)
        
    context = {
        'secao': 'funcionarios',
        'funcionario': funcionario,
        'form': form
    }

    return render(request, 'funcionarios/edit.html', context)

@login_required
def funcionario_detail(request, funcionario_id):

    diretor, escola = _get_diretor_escola(request)

    funcionario = get_object_or_404(Funcionario, escola=escola, id=funcionario_id)
    
    
    disciplinas = TurmaDisciplina.objects.filter(professor=funcionario).select_related('disciplina')

    config = TenantConfiguracao.objects.filter(escola=escola).first()
    
    ano_lectivo_activo = config.ano_lectivo_activo
   
    # turmas = TurmaDisciplinaProfessor.objects.filter(
    #     professor=professor,
    #     ano_lectivo=ano_lectivo_activo
    # ).select_related('turma', 'disciplina')
    
    horario = HorarioAula.objects.filter(professor=funcionario).select_related(
        'turma', 'disciplina'
    ).order_by('dia_semana', 'hora_inicio')
    
    context = {
        'secao': 'funcionarios',
        'funcionario': funcionario,
        'disciplinas': disciplinas,
        #'turmas': turmas,
        'horario': horario,
    }
    
    return render(request, 'funcionarios/detail.html', context)

@login_required
@require_http_methods('POST')
def funcionario_delete(request, funcionario_id):

    professor = Professor.objects.get(id=funcionario_id)

    user = request.user

    dados = json.loads(request.body)
    user = request.user
    password = dados.get('password')

    if not user.check_password(password.strip()):

        return JsonResponse({'error': 'Credenciais inválidas'}, status=403)
    
    
    LogAuditoria.objects.create(
        escola=request.user.escola,
        utilizador=request.user,
        accao='delete',
        modulo='Professor',
        descricao=f'Professor: {professor.nome_completo} eliminado',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    professor.delete()

    return redirect('professor_list')


@login_required
def detalhe_professor(request, funcionario_id):
    """Perfil do professor: disciplinas, turmas e carga horária."""
    diretor, escola = _get_diretor_escola(request)
    professor = get_object_or_404(Professor, id=funcionario_id, escola=escola)

    disciplinas   = DisciplinaProfessor.objects.filter(
        professor=professor
    ).select_related('disciplina')

    total_alunos = Matricula.objects.filter(
        escola=escola,
        turma__curso=curso
    ).count()

    context = {
        'secao': 'professores',
        'total_alunos': total_alunos,
        'escola': escola,
        'professor': professor,
        'disciplinas': disciplinas,
        'turmas_atrib': turmas_atrib,
    }
    return render(request, 'diretor/funcionarios/detalhe.html', context)


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



@login_required
def horario_turma(request, turma_id):
    """Horário da turma"""
    turma = get_object_or_404(Turma, id=turma_id, escola=request.user.escola)
    
    horarios = HorarioAula.objects.filter(turma=turma).select_related(
        'disciplina', 'professor'
    ).order_by('dia_semana', 'hora_inicio')
    
    # Organizar por dia da semana
    dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
    horario_organizado = {}
    
    for dia in dias:
        horario_organizado[dia] = horarios.filter(dia_semana=dia)
    
    context = {
        'turma': turma,
        'horario_organizado': horario_organizado,
    }
    
    return render(request, 'horarios/turma.html', context)


@login_required
def horario_professor(request, professor_id=None):
    """Horário do professor"""
    if professor_id:
        professor = get_object_or_404(Professor, id=professor_id, escola=request.user.escola)
    else:
        if not hasattr(request.user, 'professor'):
            messages.error(request, 'Você não é um professor.')
            return redirect('dashboard_admin')
        professor = request.user.professor
    
    horarios = HorarioAula.objects.filter(professor=professor).select_related(
        'turma', 'disciplina'
    ).order_by('dia_semana', 'hora_inicio')
    
    # Organizar por dia da semana
    dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
    horario_organizado = {}
    
    for dia in dias:
        horario_organizado[dia] = horarios.filter(dia_semana=dia)
    
    context = {
        'professor': professor,
        'horario_organizado': horario_organizado,
    }
    
    return render(request, 'horarios/professor.html', context)


@login_required
def horario_create(request, turma_id):
    """Criar horário para turma"""
    turma = get_object_or_404(Turma, id=turma_id, escola=request.user.escola)
    
    if request.method == 'POST':
        # Processar criação de múltiplos horários
        messages.success(request, 'Horário criado com sucesso!')
        return redirect('horario_turma', turma_id=turma.id)
    
    # Disciplinas e professores da turma
    disciplinas_professores = TurmaDisciplinaProfessor.objects.filter(
        turma=turma
    ).select_related('disciplina', 'professor')
    
    context = {
        'turma': turma,
        'disciplinas_professores': disciplinas_professores,
    }
    
    return render(request, 'horarios/create.html', context)


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

@login_required
def periodo_avaliativo_list(request, ano_id):
    """Lista de períodos avaliativos"""
    ano_lectivo = get_object_or_404(AnoLectivo, id=ano_id, escola=request.user.escola)
    periodos = PeriodoAvaliativo.objects.filter(ano_lectivo=ano_lectivo).order_by('numero_periodo')
    
    context = {
        'ano_lectivo': ano_lectivo,
        'periodos': periodos,
    }
    
    return render(request, 'configuracoes/periodo_list.html', context)


@login_required
def periodo_avaliativo_create(request, ano_id):
    """Criar período avaliativo"""
    ano_lectivo = get_object_or_404(AnoLectivo, id=ano_id, escola=request.user.escola)
    
    if request.method == 'POST':
        # Processar criação
        messages.success(request, 'Período avaliativo criado com sucesso!')
        return redirect('periodo_avaliativo_list', ano_id=ano_lectivo.id)
    
    context = {
        'ano_lectivo': ano_lectivo,
    }
    
    return render(request, 'configuracoes/periodo_create.html', context)


@login_required
def tipo_avaliacao_list(request):
    """Lista de tipos de avaliação"""
    diretor, escola = _get_diretor_escola(request)
    tipos = TipoAvaliacao.objects.filter(escola=escola).order_by('designacao')
    
    context = {
        'tipos': tipos,
    }
    
    return render(request, 'configuracoes/tipo_avaliacao_list.html', context)


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
