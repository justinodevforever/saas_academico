from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
from .models import *
from .forms import *
from authenticate.models import *
from .decorator import *



def index(request):

    return render(request, 'home.html')

@login_required
def dashboard_diretor(request):
  
    escola = request.user.escola
    ano_lectivo_activo = escola.configuracao.ano_lectivo_activo
    
    # Estatísticas gerais
    total_alunos = Aluno.objects.filter(escola=escola, status='Matriculado').count()
    print(total_alunos)
    total_professores = Professor.objects.filter(escola=escola, status='Activo').count()
    total_turmas = Turma.objects.filter(escola=escola, ano_lectivo=ano_lectivo_activo, activo=True).count()
    total_cursos = Curso.objects.filter(escola=escola, activo=True).count()
    
    # Matrículas recentes
    matriculas_recentes = Matricula.objects.filter(
        aluno__escola=escola,
        ano_lectivo=ano_lectivo_activo
    ).select_related('aluno', 'turma').order_by('-data_matricula')[:10]
    
    # Alunos por turma
    alunos_por_turma = Turma.objects.filter(
        escola=escola,
        ano_lectivo=ano_lectivo_activo
    ).annotate(total_alunos=Count('matricula')).values('designacao', 'classe__designacao', 'total_alunos')
    
    # Situação financeira
    contas_atrasadas = ContaAluno.objects.filter(
        aluno__escola=escola,
        ano_lectivo=ano_lectivo_activo,
        status='Atrasado'
    ).count()
    
    total_receber = ContaAluno.objects.filter(
        aluno__escola=escola,
        ano_lectivo=ano_lectivo_activo
    ).aggregate(total=Sum('saldo_devedor'))['total'] or Decimal('0')
    
    context = {
        'total_alunos': total_alunos,
        'total_professores': total_professores,
        'total_turmas': total_turmas,
        'total_cursos': total_cursos,
        'matriculas_recentes': matriculas_recentes,
        'alunos_por_turma': alunos_por_turma,
        'contas_atrasadas': contas_atrasadas,
        'total_receber': total_receber,
        'ano_lectivo_activo': ano_lectivo_activo,
    }
    
    return render(request, 'dashboard/diretor.html', context)


@login_required
def dashboard_professor(request):
    
    professor = request.user.professor
    escola = professor.escola
    ano_lectivo_activo = escola.configuracao.ano_lectivo_activo
    
    minhas_turmas = TurmaDisciplinaProfessor.objects.filter(
        professor=professor,
        ano_lectivo=ano_lectivo_activo
    ).select_related('turma', 'disciplina').distinct()
    
    
    hoje = timezone.now()
    dia_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][hoje.weekday()]
    
    aulas_hoje = HorarioAula.objects.filter(
        professor=professor,
        dia_semana=dia_semana
    ).select_related('turma', 'disciplina').order_by('hora_inicio')
    
    avaliacoes_pendentes = Avaliacao.objects.filter(
        professor=professor,
        periodo=escola.configuracao.periodo_activo
    ).annotate(
        notas_lancadas=Count('nota')
    ).order_by('-data_realizacao')[:10]
    
    context = {
        'minhas_turmas': minhas_turmas,
        'aulas_hoje': aulas_hoje,
        'avaliacoes_pendentes': avaliacoes_pendentes,
        'total_turmas': minhas_turmas.count(),
    }
    
    return render(request, 'dashboard/professor.html', context)


@login_required
def dashboard_aluno(request):

    aluno = request.user.aluno
    escola = aluno.escola
    ano_lectivo_activo = escola.configuracao.ano_lectivo_activo
    
    matricula = Matricula.objects.filter(
        aluno=aluno,
        ano_lectivo=ano_lectivo_activo,
        status='Activa'
    ).select_related('turma', 'turma__classe', 'turma__curso').first()
    
    if not matricula:
        messages.warning(request, "Você não possui matrícula ativa neste ano letivo.")
        return render(request, 'dashboard/aluno.html', {'matricula': None})
    
    horario = HorarioAula.objects.filter(
        turma=matricula.turma
    ).select_related('disciplina', 'professor').order_by('dia_semana', 'hora_inicio')
    
    periodo_activo = escola.configuracao.periodo_activo
    notas = Nota.objects.filter(
        aluno=aluno,
        avaliacao__periodo=periodo_activo
    ).select_related('avaliacao', 'avaliacao__disciplina')
    
    conta = ContaAluno.objects.filter(
        aluno=aluno,
        ano_lectivo=ano_lectivo_activo
    ).first()
    
    comunicados = Comunicado.objects.filter(
        Q(destinatario_tipo='Todos') | 
        Q(destinatario_tipo='Alunos') |
        Q(turma=matricula.turma),
        escola=escola,
        activo=True,
        data_publicacao__lte=timezone.now()
    ).filter(
        Q(data_expiracao__isnull=True) | Q(data_expiracao__gte=timezone.now())
    ).order_by('-data_publicacao')[:5]
    
    context = {
        'matricula': matricula,
        'horario': horario,
        'notas': notas,
        'conta': conta,
        'comunicados': comunicados,
    }
    
    return render(request, 'dashboard/aluno.html', context)


@login_required
def dashboard_encarregado(request):
   
    encarregado = request.user.encarregadoeducacao
    escola = encarregado.escola
    
    alunos_vinculados = AlunoEncarregado.objects.filter(
        encarregado=encarregado
    ).select_related('aluno')
    
    dados_alunos = []
    for ae in alunos_vinculados:
        aluno = ae.aluno
        matricula = Matricula.objects.filter(
            aluno=aluno,
            status='Activa'
        ).select_related('turma').first()
        
        conta = ContaAluno.objects.filter(
            aluno=aluno
        ).first()
        
        dados_alunos.append({
            'aluno': aluno,
            'matricula': matricula,
            'conta': conta,
        })
    
    comunicados = Comunicado.objects.filter(
        Q(destinatario_tipo='Todos') | Q(destinatario_tipo='Encarregados'),
        escola=escola,
        activo=True
    ).order_by('-data_publicacao')[:5]
    
    context = {
        'dados_alunos': dados_alunos,
        'comunicados': comunicados,
    }
    
    return render(request, 'dashboard/encarregado.html', context)


@login_required
def aluno_list(request):
    
    escola = request.user.escola
    
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

    escola = request.user.escola

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
    
    matriculas = Matricula.objects.filter(aluno=aluno).select_related(
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
def professor_list(request):
   
    escola = request.user.escola
    
    professores = Professor.objects.filter(escola=escola).select_related(
        'utilizador', 'categoria'
    )
    
   
    search = request.GET.get('search')
    if search:
        professores = professores.filter(
            Q(nome_completo__icontains=search) |
            Q(numero_agente__icontains=search) |
            Q(especialidade__icontains=search)
        )
    
    per_page = request.GET.get('per_page', 20)
    paginator = Paginator(professores, per_page)
    page = request.GET.get('page', 1)
    professores_page = paginator.get_page(page)
    
    context = {
        'professores': professores_page,
        'total_professores': professores.count(),
        'per_page': per_page,
        'search': search
    }
    
    return render(request, 'professores/list.html', context)

@login_required
def professor_create(request):

    form = ProfessorForm()

    escola = request.user.escola

    if request.method == 'POST':
        print('Ola')

        form = ProfessorForm(request.POST)

        if form.is_valid():

            professor = form.save()
            
            professor.escola = escola
            professor.save()
       
            context = {
                'sucesso': 'Professor criado com sucesso!',
                 'form': form
            }

            return render(request, 'Professores/create.html', context)
        else:

            context = {
                'erro': 'Erro ao criar o professor!',
                 'form': form
            }

            return render(request, 'Professores/create.html', context)
        
    context = {
        'form': form
    }

    return render(request, 'Professores/create.html', context)

@login_required
def professor_edit(request, professor_id):

    professor = Professor.objects.get(id=professor_id)

    form = ProfessorEditForm(professor=professor)

    if request.method == 'POST':

        form = ProfessorEditForm(request.POST,professor=professor)

        if form.is_valid():

            professor = form.save()

            professor.save()
       
            context = {
                'sucesso': 'Professor atualizado com sucesso!',
                'form': form,
                'professor': professor,
            }

            return render(request, 'Professores/edit.html', context)
        else:

            context = {
                'erro': 'Erro ao atualizar o professor!',
                'professor': professor,
                'form': form
            }

            return render(request, 'Professores/edit.html', context)
        
    context = {
        'professor': professor,
        'form': form
    }

    return render(request, 'Professores/edit.html', context)

@login_required
def professor_detail(request, professor_id):

    professor = get_object_or_404(Professor, id=professor_id, escola=request.user.escola)
    
    
    disciplinas = DisciplinaProfessor.objects.filter(professor=professor).select_related('disciplina')
    
    ano_lectivo_activo = request.user.escola.configuracao.ano_lectivo_activo
   
    turmas = TurmaDisciplinaProfessor.objects.filter(
        professor=professor,
        ano_lectivo=ano_lectivo_activo
    ).select_related('turma', 'disciplina')
    
    horario = HorarioAula.objects.filter(professor=professor).select_related(
        'turma', 'disciplina'
    ).order_by('dia_semana', 'hora_inicio')
    
    context = {
        'professor': professor,
        'disciplinas': disciplinas,
        'turmas': turmas,
        'horario': horario,
    }
    
    return render(request, 'professores/detail.html', context)

@login_required
@require_http_methods('POST')
def professor_delete(request, professor_id):

    professor = Professor.objects.get(id=professor_id)

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
def matricula_list(request):
   
    escola = request.user.escola 
    
    matriculas = Matricula.objects.filter(
        aluno__escola=escola
    ).select_related(
        'aluno', 'ano_lectivo', 'turma', 'turma__curso', 'turma__classe'
    ).order_by('-data_matricula')
    
    ano_lectivo_id = request.GET.get('ano_lectivo')
    turma_id = request.GET.get('turma')
    busca = request.GET.get('busca')
    
    if ano_lectivo_id:
        matriculas = matriculas.filter(ano_lectivo_id=ano_lectivo_id)

    if turma_id:
        matriculas = matriculas.filter(turma_id=turma_id)
    
    if busca:
        matriculas = matriculas.filter(
            Q(aluno__nome_completo__icontains=busca) |
            Q(numero_matricula__icontains=busca) |
            Q(aluno__numero_processo__icontains=busca)
        )
    
    order_by = request.GET.get('nome_completo', '-data_matricula')
    matriculas = matriculas.order_by(order_by)

    per_page = request.GET.get('per_page', 20)
    page = request.GET.get('page')

    paginator = Paginator(matriculas, per_page)
    matriculas_page = paginator.get_page(page)

    anos_lectivos = AnoLectivo.objects.filter(escola=escola)
    turmas = Turma.objects.filter(escola=escola, activo=True)
    

    context = {
        'matriculas': matriculas_page,
        'anos_lectivos': anos_lectivos,
        'turmas': turmas,
        'total': matriculas.count(),
        'per_page': per_page,
        'busca': busca,
        'ano_lectivo_id': ano_lectivo_id,
        'turma_id': turma_id,
    }
    
    return render(request, 'matriculas/list.html', context)


@login_required
def matricula_create(request):
   
    escola = request.user.escola
    form = MatriculaForm(escola=escola)
    
    if request.method == 'POST':
        form = MatriculaForm(request.POST, escola=escola)
        
        if form.is_valid():

            matricula, aluno = form.save()

            ano_lectivo = AnoLectivo.objects.get(id=matricula.ano_lectivo.id, escola=escola)
            turma = Turma.objects.get(id=matricula.turma.id, escola=escola)
            
            ano = ano_lectivo.designacao.split('/')[0]
            ultimo_numero = Matricula.objects.filter(
                numero_matricula__startswith=f'MAT-{ano}'
            ).count()
            numero_matricula = f'MAT-{ano}-{str(ultimo_numero + 1).zfill(5)}'
            
            aluno.save()

            matricula.numero_matricula = numero_matricula
            matricula.matriculado_por = request.user
            matricula.aluno = aluno
            matricula.escola = escola

            matricula.save()

            turma.vagas_disponiveis -= 1
            turma.save()
            context = {
                'sucesso': f'Matrícula {matricula.numero_matricula} criada com sucesso!',
                'form': form
            }
            return render( request, 'matriculas/create.html', context)
            
        else:
            context = {
                'erro': f'Erro, ao realizar matrícula!',
                'form': form
            }
            return render( request, 'matriculas/create.html', context)
    
    context = {
        'form': form,
        
    }
    
    return render(request, 'matriculas/create.html', context)

@login_required
def matricula_update(request, matricula_id):
   
    matricula = Matricula.objects.get(id=matricula_id)
    form = MatriculaEditForm(matricula=matricula)
    
    if request.method == 'POST':
        form = MatriculaEditForm(request.POST, matricula=matricula)
        
        if form.is_valid():

            turma = Turma.objects.get(id=matricula.turma.id, escola=matricula.escola)

            matr, aluno = form.save()



            print(matr.turma.id, turma.id)
            
            
            aluno.save()

            matr.save()

            if matr.turma.id != turma.id:
                turma_nova = Turma.objects.get(id=matr.turma.id, escola=matricula.escola)
                turma.vagas_disponiveis += 1
                turma_nova.vagas_disponiveis -= 1

                turma_nova.save()
                turma.save()

            context = {
                'sucesso': f'Erro, ao atualizar a matrícula!',
                'matricula': matricula,
                'form': form
            }
            return redirect('matricula_detail', matricula_id=matricula.id)
            
        else:
            context = {
                'erro': f'Erro, ao atualizar a matrícula!',
                'matricula': matricula,
                'form': form,
            }
            return render( request, 'matriculas/update.html', context)
    
    context = {
        'form': form,
        'matricula': matricula,
        
    }
    
    return render(request, 'matriculas/update.html', context)


@login_required
def matricula_detail(request, matricula_id):
   
    matricula = get_object_or_404(
        Matricula.objects.select_related(
            'aluno', 'ano_lectivo', 'turma', 'turma__curso', 
            'turma__classe', 'matriculado_por'
        ),
        id=matricula_id,
        aluno__escola=request.user.escola
    )
    
    encarregados = matricula.aluno.encarregados.all()
    
    context = {
        'matricula': matricula,
        'encarregados': encarregados,
    }
    
    return render(request, 'matriculas/detail.html', context)


@login_required
def turma_list(request):
  
    escola = request.user.escola
    
    turmas = Turma.objects.filter(escola=escola).select_related(
        'ano_lectivo', 'curso', 'classe', 'director_turma'
    ).annotate(
        total_alunos=Count('matricula')
    ).order_by('-ano_lectivo__activo', 'classe__ordem', 'designacao')
    
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
    
    anos_lectivos = AnoLectivo.objects.filter(escola=escola)
    cursos = Curso.objects.filter(escola=escola, activo=True)
    classes = Classe.objects.filter(escola=escola)

    ano_lectivo = AnoLectivo.objects.get(
        Q(escola=escola) and
        Q(activo=True)
    )

    if ano_lectivo_id:
        ano_lectivo = AnoLectivo.objects.get(
        Q(id=ano_lectivo_id)
    )
    
    
    context = {
        'turmas': turmas,
        'anos_lectivos': anos_lectivos,
        'cursos': cursos,
        'classes': classes,
        'ano_letivo':ano_lectivo,
        'ano_lectivo': ano_lectivo_id,
        'curso': curso_id,
        'classe': classe_id
    }
    
    return render(request, 'turmas/list.html', context)

@login_required
def turma_estudante_list(request, turma_id):
  
    escola = request.user.escola
    
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

    escola = request.user.escola

    form = TurmaForm(escola=escola)
    
    if request.method == 'POST':
        form = TurmaForm(request.POST, escola=escola)
        
        
        if form.is_valid():
           
            turma = form.save()
            
            return redirect('turma_detail', turma_id=turma.id)
            
        else:
            context = {
                'erro': 'Erro ao Criar turma, corrija os erros abaixo!',
                'form': form
            }
            
            return render(request, 'turmas/create.html', context)
    
    context = {

        'form': form
    }
    
    return render(request, 'turmas/create.html', context)

@login_required
def turma_update(request, turma_id):

    turma = Turma.objects.get(id=turma_id)

    escola = request.user.escola
    
    form = TurmaEditForm(escola=escola, turma=turma)
    
    if request.method == 'POST':
        form = TurmaEditForm(request.POST, escola=escola, turma=turma)
        
        
        if form.is_valid():
           
            turma = form.save()
            
            return redirect('turma_detail', turma_id=turma.id)
            
        else:
            context = {
                'erro': 'Erro ao atualizar turma, corrija os erros abaixo!',
                'form': form,
                'turma': turma
            }
            
            return render(request, 'turmas/update.html', context)
    
    context = {

        'form': form,
        'turma': turma
    }
    
    return render(request, 'turmas/update.html', context)

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

    turma = get_object_or_404(
        Turma.objects.select_related(
            'escola', 'ano_lectivo', 'curso', 'classe', 'director_turma'
        ).annotate(
            total_alunos=Count('matricula')
        ),
        id=turma_id,
        escola=request.user.escola
    )
    
    total_alunos  = Matricula.objects.filter(
        turma=turma, 
        status='Activa'
    ).select_related('aluno').order_by('aluno__nome_completo').count()
    
    disciplinas_professores = TurmaDisciplinaProfessor.objects.filter(
        turma=turma
    ).select_related('disciplina', 'professor')

    horarios = turma.horarios.all().select_related('disciplina', 'professor')
    
    context = {
        'turma': turma,
        'disciplinas_professores': disciplinas_professores,
        'horarios': horarios,
        'total_alunos': total_alunos,
    }
    
    return render(request, 'turmas/detail.html', context)



@login_required
def disciplina_list(request):
    
    escola = request.user.escola
    
    disciplinas = Disciplina.objects.filter(escola=escola).order_by('nome')
    
    busca = request.GET.get('busca')
    if busca:
        disciplinas = disciplinas.filter(
            Q(nome__icontains=busca) |
            Q(codigo__icontains=busca) |
            Q(nome_abreviado__icontains=busca)
        )
    
    context = {
        'disciplinas': disciplinas,
    }
    
    return render(request, 'disciplinas/list.html', context)


@login_required
def disciplina_create(request):
   
    escola = request.user.escola

    form = DisciplinaForm(escola=escola)

    if request.method == 'POST':

        form = DisciplinaForm(request.POST)
        
        if form.is_valid():

            disciplina = form.save()

            disciplina.escola = escola
            disciplina.save()
            
            context = {
                'sucesso': 'Disciplina criada com sucesso!',
                'form': form
            }

            return render(request, 'disciplinas/create.html', context)
            
        else:
            context = {
                'erro': 'Erro ao criar a Disciplina!',
                'form': form
            }

            return render(request, 'disciplinas/create.html', context)
    
    return render(request, 'disciplinas/create.html', {'form': form})

@login_required
def disciplina_edit(request, disciplina_id):

    disciplina = Disciplina.objects.get(id=disciplina_id)
   
    escola = request.user.escola

    form = DisciplinaEditForm(instance=disciplina)

    if request.method == 'POST':

        form = DisciplinaEditForm(request.POST, instance=disciplina)
        
        if form.is_valid():

            disciplina = form.save()

            disciplina.escola = escola
            disciplina.save()
            
            context = {
                'sucesso': 'Disciplina atualizada com sucesso!',
                'form': form,
                'disciplina': disciplina,
            }

            return render(request, 'disciplinas/edit.html', context)
            
        else:
            context = {
                'erro': 'Erro ao atualizada a Disciplina!',
                'disciplina': disciplina,
                'form': form
            }

            return render(request, 'disciplinas/edit.html', context)
    
    return render(request, 'disciplinas/edit.html', {'form': form,'disciplina': disciplina})


@login_required
def disciplina_detail(request, disciplina_id):
   
    disciplina = get_object_or_404(
        Disciplina,
        id=disciplina_id,
        escola=request.user.escola
    )
    
    professores = DisciplinaProfessor.objects.filter(
        disciplina=disciplina
    ).select_related('professor')
    
    turmas = TurmaDisciplinaProfessor.objects.filter(
        disciplina=disciplina
    ).select_related('turma', 'professor')
    
    context = {
        'disciplina': disciplina,
        'professores': professores,
        'turmas': turmas,
    }
    
    return render(request, 'disciplinas/detail.html', context)


@login_required
def avaliacao_list(request):
   
    escola = request.user.escola
    
    avaliacoes = Avaliacao.objects.filter(
        turma__escola=escola
    ).select_related(
        'turma', 'disciplina', 'professor', 'periodo', 'tipo_avaliacao'
    ).order_by('-data_realizacao')
    
    turma_id = request.GET.get('turma')
    disciplina_id = request.GET.get('disciplina')
    periodo_id = request.GET.get('periodo')
    
    if turma_id:
        avaliacoes = avaliacoes.filter(turma_id=turma_id)
    if disciplina_id:
        avaliacoes = avaliacoes.filter(disciplina_id=disciplina_id)
    if periodo_id:
        avaliacoes = avaliacoes.filter(periodo_id=periodo_id)
    
    paginator = Paginator(avaliacoes, 20)
    page = request.GET.get('page')
    avaliacoes_page = paginator.get_page(page)
    
    turmas = Turma.objects.filter(escola=escola, activo=True)
    disciplinas = Disciplina.objects.filter(escola=escola, activo=True)
    periodos = PeriodoAvaliativo.objects.filter(ano_lectivo__escola=escola)
    
    context = {
        'avaliacoes': avaliacoes_page,
        'turmas': turmas,
        'disciplinas': disciplinas,
        'periodos': periodos,
    }
    
    return render(request, 'avaliacoes/lista.html', context)


@login_required
def avaliacao_create(request):
  
    escola = request.user.escola
    
    if request.method == 'POST':
        turma_id = request.POST.get('turma')
        disciplina_id = request.POST.get('disciplina')
        periodo_id = request.POST.get('periodo')
        tipo_avaliacao_id = request.POST.get('tipo_avaliacao')
        designacao = request.POST.get('designacao')
        data_realizacao = request.POST.get('data_realizacao')
        nota_maxima = request.POST.get('nota_maxima', 20)
        observacoes = request.POST.get('observacoes', '')
        
        try:
            tdp = TurmaDisciplinaProfessor.objects.filter(
                turma_id=turma_id,
                disciplina_id=disciplina_id
            ).first()
            
            avaliacao = Avaliacao.objects.create(
                turma_id=turma_id,
                disciplina_id=disciplina_id,
                professor=tdp.professor if tdp else None,
                periodo_id=periodo_id,
                tipo_avaliacao_id=tipo_avaliacao_id if tipo_avaliacao_id else None,
                designacao=designacao,
                data_realizacao=data_realizacao,
                nota_maxima=nota_maxima,
                observacoes=observacoes,
                criado_por=request.user
            )
            
            messages.success(request, 'Avaliação criada com sucesso!')
            return redirect('lancar_notas', avaliacao_id=avaliacao.id)
            
        except Exception as e:
            messages.error(request, f'Erro ao criar avaliação: {str(e)}')
    
    turmas = Turma.objects.filter(escola=escola, activo=True)
    disciplinas = Disciplina.objects.filter(escola=escola, activo=True)
    periodos = PeriodoAvaliativo.objects.filter(ano_lectivo__escola=escola)
    tipos_avaliacao = TipoAvaliacao.objects.filter(escola=escola)
    
    context = {
        'turmas': turmas,
        'disciplinas': disciplinas,
        'periodos': periodos,
        'tipos_avaliacao': tipos_avaliacao,
    }
    
    return render(request, 'avaliacoes/criar.html', context)



@login_required
def avaliacao_lancar_notas(request, avaliacao_id):
 
    avaliacao = get_object_or_404(
        Avaliacao.objects.select_related(
            'turma', 'disciplina', 'periodo'
        ),
        id=avaliacao_id,
        turma__escola=request.user.escola
    )
    
    if request.method == 'POST':
        try:
            for key, value in request.POST.items():
                if key.startswith('nota_'):
                    aluno_id = key.replace('nota_', '')
                    nota_valor = value.strip()
                    
                    if nota_valor:
                        aluno = Aluno.objects.get(id=aluno_id)
                        observacao = request.POST.get(f'obs_{aluno_id}', '')
                        
                        nota_obj, created = Nota.objects.get_or_create(
                            avaliacao=avaliacao,
                            aluno=aluno,
                            defaults={
                                'nota': float(nota_valor),
                                'observacao': observacao,
                                'lancado_por': request.user.professor if hasattr(request.user, 'professor') else None
                            }
                        )
                        
                        if not created:
                            nota_obj.nota = float(nota_valor)
                            nota_obj.observacao = observacao
                            nota_obj.save()
            
            messages.success(request, 'Notas lançadas com sucesso!')
            return redirect('lancar_notas', avaliacao_id=avaliacao_id)
            
        except Exception as e:
            messages.error(request, f'Erro ao lançar notas: {str(e)}')
    
    matriculas = Matricula.objects.filter(
        turma=avaliacao.turma,
        status='Activa'
    ).select_related('aluno').order_by('aluno__nome_completo')
    
    # Buscar notas já lançadas
    notas_lancadas = {
        nota.aluno_id: nota 
        for nota in Nota.objects.filter(avaliacao=avaliacao)
    }
    
    # Preparar dados para o template
    alunos_notas = []
    for matricula in matriculas:
        aluno = matricula.aluno
        nota = notas_lancadas.get(aluno.id)
        alunos_notas.append({
            'aluno': aluno,
            'nota': nota.nota if nota else '',
            'observacao': nota.observacao if nota else '',
        })
    
    context = {
        'avaliacao': avaliacao,
        'alunos_notas': alunos_notas,
    }
    
    return render(request, 'notas/lancar.html', context)


@login_required
def avaliacao_pauta(request, turma_id, periodo_id):
  
    turma = get_object_or_404(Turma, id=turma_id, escola=request.user.escola)
    periodo = get_object_or_404(PeriodoAvaliativo, id=periodo_id)
    
    disciplinas = TurmaDisciplinaProfessor.objects.filter(
        turma=turma
    ).select_related('disciplina', 'professor')
    
    matriculas = Matricula.objects.filter(
        turma=turma,
        status='Activa'
    ).select_related('aluno').order_by('aluno__nome_completo')
    
    # Preparar dados da pauta
    pauta_dados = []
    for matricula in matriculas:
        aluno = matricula.aluno
        notas_disciplinas = {}
        
        for tdp in disciplinas:
            # Buscar avaliações da disciplina no período
            avaliacoes = Avaliacao.objects.filter(
                turma=turma,
                disciplina=tdp.disciplina,
                periodo=periodo
            )
            
            # Calcular média das notas
            notas = Nota.objects.filter(
                avaliacao__in=avaliacoes,
                aluno=aluno
            )
            
            if notas.exists():
                media = notas.aggregate(Avg('nota'))['nota__avg']
                notas_disciplinas[tdp.disciplina.id] = round(media, 2) if media else 0
            else:
                notas_disciplinas[tdp.disciplina.id] = None
        
        # Calcular média geral
        notas_validas = [n for n in notas_disciplinas.values() if n is not None]
        media_geral = sum(notas_validas) / len(notas_validas) if notas_validas else 0
        
        pauta_dados.append({
            'aluno': aluno,
            'notas': notas_disciplinas,
            'media_geral': round(media_geral, 2)
        })
    
    context = {
        'turma': turma,
        'periodo': periodo,
        'disciplinas': disciplinas,
        'pauta_dados': pauta_dados,
    }
    
    return render(request, 'notas/pauta.html', context)


@login_required
def boletim_aluno(request, aluno_id, ano_lectivo_id):
   
    aluno = get_object_or_404(Aluno, id=aluno_id, escola=request.user.escola)
    ano_lectivo = get_object_or_404(AnoLectivo, id=ano_lectivo_id)
    
    # Buscar matrícula do aluno
    matricula = get_object_or_404(
        Matricula,
        aluno=aluno,
        ano_lectivo=ano_lectivo
    )
    
    turma = matricula.turma
    
    # Buscar períodos
    periodos = PeriodoAvaliativo.objects.filter(ano_lectivo=ano_lectivo)
    
    # Buscar disciplinas da turma
    disciplinas = TurmaDisciplinaProfessor.objects.filter(
        turma=turma
    ).select_related('disciplina', 'professor')
    
    # Preparar dados do boletim
    boletim_dados = []
    for tdp in disciplinas:
        notas_periodos = {}
        
        for periodo in periodos:
            # Buscar avaliações e notas
            avaliacoes = Avaliacao.objects.filter(
                turma=turma,
                disciplina=tdp.disciplina,
                periodo=periodo
            )
            
            notas = Nota.objects.filter(
                avaliacao__in=avaliacoes,
                aluno=aluno
            )
            
            if notas.exists():
                media = notas.aggregate(Avg('nota'))['nota__avg']
                notas_periodos[periodo.numero_periodo] = round(media, 2) if media else 0
            else:
                notas_periodos[periodo.numero_periodo] = None
        
        # Calcular média final da disciplina
        notas_validas = [n for n in notas_periodos.values() if n is not None]
        media_final = sum(notas_validas) / len(notas_validas) if notas_validas else 0
        
        boletim_dados.append({
            'disciplina': tdp.disciplina,
            'professor': tdp.professor,
            'notas_periodos': notas_periodos,
            'media_final': round(media_final, 2)
        })
    
    context = {
        'aluno': aluno,
        'matricula': matricula,
        'ano_lectivo': ano_lectivo,
        'turma': turma,
        'periodos': periodos,
        'boletim_dados': boletim_dados,
    }
    
    return render(request, 'notas/boletim.html', context)


@login_required
def financeiro_dashboard(request):
    """Dashboard financeiro"""
    escola = request.user.escola
    ano_lectivo_activo = escola.configuracao.ano_lectivo_activo
    
    # Estatísticas gerais
    contas = ContaAluno.objects.filter(
        aluno__escola=escola,
        ano_lectivo=ano_lectivo_activo
    )
    
    total_a_receber = contas.aggregate(total=Sum('total_devido'))['total'] or Decimal('0')
    total_recebido = contas.aggregate(total=Sum('total_pago'))['total'] or Decimal('0')
    total_pendente = contas.aggregate(total=Sum('saldo_devedor'))['total'] or Decimal('0')
    
    # Contas por status
    contas_por_status = contas.values('status').annotate(
        total=Count('id'),
        valor=Sum('saldo_devedor')
    )
    
    # Evolução mensal (últimos 6 meses)
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
    """Lista de contas de alunos"""
    escola = request.user.escola
    ano_lectivo_activo = escola.configuracao.ano_lectivo_activo
    
    contas = ContaAluno.objects.filter(
        aluno__escola=escola,
        ano_lectivo=ano_lectivo_activo
    ).select_related('aluno')
    
    # Filtros
    status = request.GET.get('status')
    if status:
        contas = contas.filter(status=status)
    
    # Busca
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
    """Detalhes da conta do aluno"""
    conta = get_object_or_404(
        ContaAluno.objects.select_related('aluno', 'ano_lectivo'),
        id=conta_id
    )
    
    context = {
        'conta': conta,
    }
    
    return render(request, 'financeiro/conta_detail.html', context)


# ==================== COMUNICADOS VIEWS ====================

@login_required
def comunicado_list(request):
    """Lista de comunicados"""
    escola = request.user.escola
    
    comunicados = Comunicado.objects.filter(escola=escola).select_related(
        'publicado_por', 'turma'
    ).order_by('-data_publicacao')
    
    # Filtros
    tipo = request.GET.get('tipo')
    if tipo:
        comunicados = comunicados.filter(tipo=tipo)
    
    destinatario = request.GET.get('destinatario')
    if destinatario:
        comunicados = comunicados.filter(destinatario_tipo=destinatario)
    
    activo = request.GET.get('activo')
    if activo:
        comunicados = comunicados.filter(activo=activo == 'true')
    
    paginator = Paginator(comunicados, 20)
    page = request.GET.get('page')
    comunicados_page = paginator.get_page(page)
    
    context = {
        'comunicados': comunicados_page,
    }
    
    return render(request, 'comunicados/list.html', context)


@login_required
def comunicado_create(request):
    """Criar novo comunicado"""
    escola = request.user.escola
    
    if request.method == 'POST':
        # Processar criação
        messages.success(request, 'Comunicado publicado com sucesso!')
        return redirect('comunicado_list')
    
    context = {
        'turmas': Turma.objects.filter(escola=escola, activo=True),
    }
    
    return render(request, 'comunicados/create.html', context)


@login_required
def comunicado_detail(request, comunicado_id):
    """Detalhes do comunicado"""
    comunicado = get_object_or_404(
        Comunicado.objects.select_related('escola', 'turma', 'publicado_por'),
        id=comunicado_id,
        escola=request.user.escola
    )
    
    context = {
        'comunicado': comunicado,
    }
    
    return render(request, 'comunicados/detail.html', context)


@login_required
def comunicado_toggle_status(request, comunicado_id):
    """Ativar/desativar comunicado"""
    comunicado = get_object_or_404(Comunicado, id=comunicado_id, escola=request.user.escola)
    
    comunicado.activo = not comunicado.activo
    comunicado.save()
    
    status_texto = "ativado" if comunicado.activo else "desativado"
    messages.success(request, f'Comunicado {status_texto} com sucesso!')
    
    return redirect('comunicado_list')


# ==================== MATERIAIS DIDÁTICOS VIEWS ====================

@login_required
def material_list(request):
    """Lista de materiais didáticos"""
    escola = request.user.escola
    
    materiais = MaterialDidatico.objects.filter(
        escola=escola,
        activo=True
    ).select_related('disciplina', 'classe', 'curso', 'publicado_por')
    
    # Filtros
    disciplina_id = request.GET.get('disciplina')
    if disciplina_id:
        materiais = materiais.filter(disciplina_id=disciplina_id)
    
    classe_id = request.GET.get('classe')
    if classe_id:
        materiais = materiais.filter(classe_id=classe_id)
    
    tipo = request.GET.get('tipo')
    if tipo:
        materiais = materiais.filter(tipo=tipo)
    
    # Busca
    search = request.GET.get('search')
    if search:
        materiais = materiais.filter(
            Q(titulo__icontains=search) |
            Q(descricao__icontains=search)
        )
    
    # Se for professor, mostrar apenas seus materiais
    if hasattr(request.user, 'professor'):
        materiais = materiais.filter(publicado_por=request.user.professor)
    
    paginator = Paginator(materiais, 20)
    page = request.GET.get('page')
    materiais_page = paginator.get_page(page)
    
    context = {
        'materiais': materiais_page,
        'disciplinas': Disciplina.objects.filter(escola=escola, activo=True),
        'classes': Classe.objects.all(),
    }
    
    return render(request, 'materiais/list.html', context)


@login_required
def material_create(request):
    """Criar novo material didático"""
    escola = request.user.escola
    
    if request.method == 'POST':
        # Processar criação
        messages.success(request, 'Material didático publicado com sucesso!')
        return redirect('material_list')
    
    context = {
        'disciplinas': Disciplina.objects.filter(escola=escola, activo=True),
        'classes': Classe.objects.all(),
        'cursos': Curso.objects.filter(escola=escola, activo=True),
    }
    
    return render(request, 'materiais/create.html', context)


@login_required
def material_detail(request, material_id):
    """Detalhes do material didático"""
    material = get_object_or_404(
        MaterialDidatico.objects.select_related(
            'escola', 'disciplina', 'classe', 'curso', 'publicado_por'
        ),
        id=material_id,
        escola=request.user.escola
    )
    
    # Registrar acesso
    AcessoMaterial.objects.create(
        material=material,
        utilizador=request.user,
        tipo_acesso='Visualização',
        ip_address=request.META.get('REMOTE_ADDR', '')
    )
    
    material.visualizacoes += 1
    material.save()
    
    context = {
        'material': material,
    }
    
    return render(request, 'materiais/detail.html', context)


@login_required
def material_download(request, material_id):
    """Download de material didático"""
    material = get_object_or_404(MaterialDidatico, id=material_id, escola=request.user.escola)
    
    # Registrar download
    AcessoMaterial.objects.create(
        material=material,
        utilizador=request.user,
        tipo_acesso='Download',
        ip_address=request.META.get('REMOTE_ADDR', '')
    )
    
    material.downloads += 1
    material.save()
    
    # Retornar arquivo
    if material.arquivo:
        response = HttpResponse(material.arquivo, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{material.arquivo.name}"'
        return response
    
    messages.error(request, 'Arquivo não encontrado.')
    return redirect('material_detail', material_id=material_id)


# ==================== HORÁRIOS VIEWS ====================

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


# ==================== RELATÓRIOS VIEWS ====================

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

# ==================== CONFIGURAÇÕES VIEWS ====================

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def configuracao_escola(request):
    """Configurações da escola"""
    escola = request.user.escola
    configuracao, created = TenantConfiguracao.objects.get_or_create(escola=escola)
    
    if request.method == 'POST':
        # Processar atualização das configurações
        messages.success(request, 'Configurações atualizadas com sucesso!')
        return redirect('configuracao_escola')
    
    context = {
        'configuracao': configuracao,
        'escola': escola,
        'anos_lectivos': AnoLectivo.objects.filter(escola=escola).order_by('-data_inicio'),
    }
    
    return render(request, 'configuracoes/escola.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def ano_lectivo_list(request):
    """Lista de anos letivos"""
    escola = request.user.escola
    anos_lectivos = AnoLectivo.objects.filter(escola=escola).order_by('-data_inicio')
    
    context = {
        'anos_lectivos': anos_lectivos,
    }
    
    return render(request, 'configuracoes/ano_lectivo_list.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def ano_lectivo_create(request):
    """Criar ano letivo"""
    escola = request.user.escola
    
    if request.method == 'POST':
        # Processar criação
        messages.success(request, 'Ano letivo criado com sucesso!')
        return redirect('ano_lectivo_list')
    
    return render(request, 'configuracoes/ano_lectivo_create.html')


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
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
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
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
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
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
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def curso_list(request):
    """Lista de cursos"""
    escola = request.user.escola
    cursos = Curso.objects.filter(escola=escola).order_by('nome')
    
    context = {
        'cursos': cursos,
    }
    
    return render(request, 'configuracoes/curso_list.html', context)



@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def tipo_avaliacao_list(request):
    """Lista de tipos de avaliação"""
    escola = request.user.escola
    tipos = TipoAvaliacao.objects.filter(escola=escola).order_by('designacao')
    
    context = {
        'tipos': tipos,
    }
    
    return render(request, 'configuracoes/tipo_avaliacao_list.html', context)


# ==================== API VIEWS (JSON) ====================

@login_required
def api_turmas_por_classe(request):
    """API: Retorna turmas filtradas por classe"""
    classe_id = request.GET.get('classe_id')
    escola = request.user.escola
    ano_lectivo_activo = escola.configuracao.ano_lectivo_activo
    
    turmas = Turma.objects.filter(
        escola=escola,
        ano_lectivo=ano_lectivo_activo,
        classe_id=classe_id,
        activo=True
    ).values('id', 'designacao', 'turno', 'vagas_disponiveis')
    
    return JsonResponse(list(turmas), safe=False)


@login_required
def api_disciplinas_por_turma(request):
    """API: Retorna disciplinas de uma turma"""
    turma_id = request.GET.get('turma_id')
    
    disciplinas = TurmaDisciplinaProfessor.objects.filter(
        turma_id=turma_id
    ).select_related('disciplina', 'professor').values(
        'disciplina__id',
        'disciplina__nome',
        'disciplina__nome_abreviado',
        'professor__id',
        'professor__nome_completo'
    )
    
    return JsonResponse(list(disciplinas), safe=False)


@login_required
def api_alunos_por_turma(request):
    """API: Retorna alunos de uma turma"""
    turma_id = request.GET.get('turma_id')
    
    matriculas = Matricula.objects.filter(
        turma_id=turma_id,
        status='Activa'
    ).select_related('aluno').values(
        'aluno__id',
        'aluno__nome_completo',
        'aluno__numero_processo',
        'aluno__foto'
    ).order_by('aluno__nome_completo')
    
    return JsonResponse(list(matriculas), safe=False)


@login_required
def api_verificar_disponibilidade_turma(request):
    """API: Verifica disponibilidade de vagas na turma"""
    turma_id = request.GET.get('turma_id')
    
    try:
        turma = Turma.objects.get(id=turma_id)
        return JsonResponse({
            'disponivel': turma.vagas_disponiveis > 0,
            'vagas_disponiveis': turma.vagas_disponiveis,
            'capacidade_maxima': turma.capacidade_maxima
        })
    except Turma.DoesNotExist:
        return JsonResponse({'erro': 'Turma não encontrada'}, status=404)


@login_required
def api_notas_aluno(request, aluno_id):
    """API: Retorna todas as notas de um aluno"""
    periodo_id = request.GET.get('periodo_id')
    
    notas = Nota.objects.filter(
        aluno_id=aluno_id
    ).select_related('avaliacao', 'avaliacao__disciplina', 'avaliacao__periodo')
    
    if periodo_id:
        notas = notas.filter(avaliacao__periodo_id=periodo_id)
    
    dados = []
    for nota in notas:
        dados.append({
            'disciplina': nota.avaliacao.disciplina.nome,
            'avaliacao': nota.avaliacao.designacao,
            'periodo': nota.avaliacao.periodo.designacao,
            'nota': float(nota.nota),
            'nota_maxima': float(nota.avaliacao.nota_maxima),
            'data': nota.data_lancamento.strftime('%d/%m/%Y')
        })
    
    return JsonResponse(dados, safe=False)


@login_required
def api_estatisticas_dashboard(request):
    """API: Estatísticas para o dashboard"""
    escola = request.user.escola
    ano_lectivo_activo = escola.configuracao.ano_lectivo_activo
    
    dados = {
        'total_alunos': Aluno.objects.filter(escola=escola, status='Matriculado').count(),
        'total_professores': Professor.objects.filter(escola=escola, status='Activo').count(),
        'total_turmas': Turma.objects.filter(escola=escola, ano_lectivo=ano_lectivo_activo, activo=True).count(),
        'total_matriculas': Matricula.objects.filter(
            aluno__escola=escola,
            ano_lectivo=ano_lectivo_activo,
            status='Activa'
        ).count(),
        'contas_atrasadas': ContaAluno.objects.filter(
            aluno__escola=escola,
            ano_lectivo=ano_lectivo_activo,
            status='Atrasado'
        ).count(),
    }
    
    return JsonResponse(dados)


# ==================== VIEWS DE BUSCA E AUTOCOMPLETE ====================

@login_required
def busca_aluno(request):
    """Busca de alunos (autocomplete)"""
    termo = request.GET.get('q', '')
    escola = request.user.escola
    
    if len(termo) < 3:
        return JsonResponse([], safe=False)
    
    alunos = Aluno.objects.filter(
        escola=escola,
        nome_completo__icontains=termo
    ).values('id', 'nome_completo', 'numero_processo', 'foto')[:10]
    
    return JsonResponse(list(alunos), safe=False)


@login_required
def busca_professor(request):
    """Busca de professores (autocomplete)"""
    termo = request.GET.get('q', '')
    escola = request.user.escola
    
    if len(termo) < 3:
        return JsonResponse([], safe=False)
    
    professores = Professor.objects.filter(
        escola=escola,
        nome_completo__icontains=termo,
        status='Activo'
    ).values('id', 'nome_completo', 'numero_agente', 'especialidade')[:10]
    
    return JsonResponse(list(professores), safe=False)


# ==================== VIEWS DE EXPORTAÇÃO ====================

@login_required
def exportar_lista_alunos(request):
    """Exportar lista de alunos para Excel"""
    import openpyxl
    from openpyxl.styles import Font, Alignment
    
    escola = request.user.escola
    
    # Criar workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Lista de Alunos"
    
    # Cabeçalhos
    headers = ['Nº Processo', 'Nome Completo', 'Data Nascimento', 'Gênero', 'Status', 'Província', 'Telefone', 'Email']
    ws.append(headers)
    
    # Estilizar cabeçalhos
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    
    # Dados
    alunos = Aluno.objects.filter(escola=escola).order_by('nome_completo')
    for aluno in alunos:
        ws.append([
            aluno.numero_processo,
            aluno.nome_completo,
            aluno.data_nascimento.strftime('%d/%m/%Y'),
            aluno.get_genero_display(),
            aluno.get_status_display(),
            aluno.provincia,
            aluno.telefone,
            aluno.email
        ])
    
    # Ajustar largura das colunas
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Preparar resposta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=lista_alunos_{escola.nome_abreviado}.xlsx'
    wb.save(response)
    
    return response


@login_required
def exportar_pauta_pdf(request, turma_id, periodo_id):
    """Exportar pauta de avaliação para PDF"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from io import BytesIO
    
    turma = get_object_or_404(Turma, id=turma_id, escola=request.user.escola)
    periodo = get_object_or_404(PeriodoAvaliativo, id=periodo_id)
    
    # Criar PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()
    
    # Título
    titulo = Paragraph(f"<b>PAUTA DE AVALIAÇÃO - {turma.classe.designacao} {turma.designacao}</b>", styles['Title'])
    elements.append(titulo)
    elements.append(Spacer(1, 12))
    
    subtitulo = Paragraph(f"{periodo.designacao} - {turma.ano_lectivo.designacao}", styles['Normal'])
    elements.append(subtitulo)
    elements.append(Spacer(1, 20))
    
    # Preparar dados da tabela
    # ... (implementar lógica de montagem da tabela)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=pauta_{turma.designacao}_{periodo.designacao}.pdf'
    
    return response


# ==================== VIEWS DE NOTIFICAÇÕES ====================

@login_required
def notificacoes_list(request):
    """Lista de notificações do usuário"""
    # Implementar sistema de notificações
    context = {}
    return render(request, 'notificacoes/list.html', context)


@login_required
def marcar_notificacao_lida(request, notificacao_id):
    """Marcar notificação como lida"""
    # Implementar
    return JsonResponse({'status': 'ok'})


# ==================== VIEWS DE PERFIL ====================

@login_required
def meu_perfil(request):
    """Perfil do usuário logado"""
    user = request.user
    
    if request.method == 'POST':
        # Processar atualização do perfil
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('meu_perfil')
    
    context = {
        'user': user,
    }
    
    # Adicionar dados específicos por tipo de usuário
    if hasattr(user, 'professor'):
        context['professor'] = user.professor
    elif hasattr(user, 'aluno'):
        context['aluno'] = user.aluno
    elif hasattr(user, 'encarregadoeducacao'):
        context['encarregado'] = user.encarregadoeducacao
    
    return render(request, 'perfil/meu_perfil.html', context)


@login_required
def alterar_senha(request):
 
    if request.method == 'POST':
        messages.success(request, 'Senha alterada com sucesso!')
        return redirect('meu_perfil')
    
    return render(request, 'perfil/alterar_senha.html')


# ==================== VIEWS DE AJUDA ====================

@login_required
def ajuda_index(request):
    """Página de ajuda"""
    return render(request, 'ajuda/index.html')


@login_required
def ajuda_categoria(request, categoria):
    """Ajuda por categoria"""
    context = {
        'categoria': categoria,
    }
    return render(request, 'ajuda/categoria.html', context)