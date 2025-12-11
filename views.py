# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods
from datetime import datetime
from .models import *
from casos.models import *
from usuario.models import *
from .forms import *
from evidencias.models import *
import json
from django.views.decorators.http import require_http_methods
import tempfile
import os
from django.core.files import File
from django.core.files.base import ContentFile
from django.core import serializers

def list_suspect(request):

    suspeitos = EnvolvimentoCaso.objects.filter(tipo_envolvimento='suspeito')

    page = request.GET.get('page')
    per_page = request.GET.get('per_page', 20)
    bi = request.GET.get('bi')
    order_by = request.GET.get('order_by', 'caso__numero_caso')

    if bi:
        suspeitos = suspeitos.filter(pessoa__bi=bi)
    
    suspeitos = suspeitos.order_by(order_by)

    paginator = Paginator(suspeitos, per_page)
    objec = paginator.get_page(page)

    context = {
        'suspeitos': objec,
        'per_page': per_page,
        'bi': bi,
        'order_by': order_by
    }

    return render(request, 'caso/suspect.html', context)
    
def detail_suspect(request, id):

    suspeito = EnvolvimentoCaso.objects.get(tipo_envolvimento='suspeito', id=id)
    enderecos = Endereco.objects.filter(pessoa=suspeito.pessoa)
    print(suspeito.pessoa)

    return render(request, 'caso/detail_suspect.html', {'suspeito': suspeito, 'enderecos': enderecos})

def caso(request):
    
    form = EventoTimelineForm()
    return render(request, 'casos.html', {'form': form})

@login_required
def caso_create(request):
    
    if request.method == 'post':
        form = CasoForm(request.post)
        if form.is_valid():
            caso = form.save(commit=False)
            caso.criado_por = request.user
            caso.save()
            form.save_m2m()
            
            messages.success(request, f'caso {caso.numero_caso} criado com sucesso!')
            return redirect('caso_detail', pk=caso.pk)
    else:
        form = CasoForm()
    
    return render(request, 'investigation/caso_form.html', {
        'form': form,
        'title': 'novo caso'
    })

@login_required
def caso_update(request, pk):
    
    caso = get_object_or_404(Caso, pk=pk)
    
    if request.method == 'post':
        form = CasoForm(request.post, instance=caso)
        if form.is_valid():
            form.save()
            messages.success(request, f'caso {caso.numero_caso} atualizado com sucesso!')
            return redirect('caso_detail', pk=caso.pk)
    else:
        form = CasoForm(instance=caso)
    
    return render(request, 'investigation/caso_form.html', {
        'form': form,
        'caso': caso,
        'title': f'editar caso {caso.numero_caso}'
    })

@login_required
def timeline_caso(request, caso_id):
    
    caso = get_object_or_404(caso, pk=caso_id)
    eventos = caso.eventos_timeline.all().order_by('data_hora')
    
    return render(request, 'investigation/timeline_caso.html', {
        'caso': caso,
        'eventos': eventos
    })

@login_required
def add_evento_timeline(request, caso_id):
    
    caso = get_object_or_404(caso, pk=caso_id)
    
    if request.method == 'post':
        form = EventoTimelineForm(request.post)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.caso = caso
            evento.criado_por = request.user
            evento.save()
            form.save_m2m()
            
            messages.success(request, 'evento adicionado à timeline!')
            return redirect('timeline_caso', caso_id=caso.pk)
    else:
        form = EventoTimelineForm()
    
    return render(request, 'investigation/evento_form.html', {
        'form': form,
        'caso': caso,
        'title': 'adicionar evento'
    })


@login_required
def relatorio_caso(request, caso_id):
    
    caso = get_object_or_404(caso, pk=caso_id)
    
    context = {
        'caso': caso,
        'suspeitos': caso.envolvimentos.filter(tipo_envolvimento='suspeito', ativo=True),
        'vitimas': caso.envolvimentos.filter(tipo_envolvimento='vitima', ativo=True),
        'testemunhas': caso.envolvimentos.filter(tipo_envolvimento='testemunha', ativo=True),
        'evidencias': caso.evidencias.all().order_by('-data_coleta'),
        'timeline': caso.eventos_timeline.all().order_by('data_hora'),
        'arquivos': caso.arquivos.all().order_by('-data_upload'),
    }
    
    return render(request, 'investigation/relatorio_caso.html', context)

@login_required
@require_http_methods(["post"])
def alterar_status_caso(request, caso_id):
    
    caso = get_object_or_404(Caso, pk=caso_id)
    novo_status = request.post.get('status')
    
    if novo_status in dict(caso.status_choices):
        caso.status = novo_status
        if novo_status == 'concluido':
            caso.data_conclusao = datetime.now()
        caso.save()
        
        return JsonResponse({
            'success': True,
            'message': f'status alterado para {caso.get_status_display()}'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'status inválido'
    })


# @login_required
# def busca_avancada(request):
    
#     if request.method == 'post':
#         form = buscaavancadaform(request.post)
#         if form.is_valid():
#             # processar busca
#             resultados = processar_busca_avancada(form.cleaned_data)
            
#             return render(request, 'investigation/resultados_busca.html', {
#                 'resultados': resultados,
#                 'form': form
#             })
#     else:
#         form = buscaavancadaform()
    
#     return render(request, 'investigation/busca_avancada.html', {
#         'form': form
#     })

def processar_busca_avancada(dados):
    
    resultados = {
        'casos': [],
        'pessoas': [],
        'evidencias': []
    }
    
    termo = dados.get('termo')
    if termo:
       
        resultados['casos'] = Caso.objects.filter(
            Q(numero_caso__icontains=termo) |
            Q(titulo__icontains=termo) |
            Q(descricao__icontains=termo)
        )[:10]
        
       
        resultados['pessoas'] = Pessoa.objects.filter(
            Q(nome_completo__icontains=termo) |
            Q(nome_social__icontains=termo) |
            Q(cpf__icontains=termo)
        )[:10]
 
        resultados['evidencias'] = Evidencia.objects.filter(
            Q(numero_evidencia__icontains=termo) |
            Q(descricao__icontains=termo)
        )[:10]
    
    return resultados

@login_required
def list_case(request):
   
    casos = Caso.objects.filter(ativo=True).select_related(
        'tipo_crime', 'investigador_principal', 'delegado_responsavel'
    )
    
    filter1 = request.GET.get('filter1')
   
    filter2 = request.GET.get('filter2')
    search = request.GET.get('search')
    per_page = request.GET.get('per_page', 20)
    page = request.GET.get('page')

    if filter1:

        try:
            filter1 = int(filter1)
            casos = casos.filter(
                prioridade=filter1
            )

        except Exception as e:
            casos = casos.filter(
                status=filter1
            )
   
    if filter2:
        casos = casos.filter(investigador_principal__bi__icontains=filter2)
    
    if search:
        casos = casos.filter(
            Q(numero_caso__icontains=search) |
            Q(titulo__icontains=search) |
            Q(descricao__icontains=search)
        )
    
    order_by = request.GET.get('order_by', '-data_abertura')
    casos = casos.order_by(order_by)
    
    paginator = Paginator(casos, per_page)
    casos = paginator.get_page(page)
    
    tipos_crime = TipoCrime.objects.filter(ativo=True)
    from .models import Usuario
    investigadores = Usuario.objects.filter(cargo__in=['investigador', 'delegado'])
    
    context = {
        'casos': casos,
        'tipos_crime': tipos_crime,
        'investigadores': investigadores,
        'status_choices': Caso.STATUS_CHOICES,
        'prioridade_choices': Caso.PRIORIDADE_CHOICES,
        'per_page': per_page,
        
        'filter1': filter1,
        'filter2': filter2,
        'search': search,
        
    }
    
    return render(request, 'caso/list_case.html', context)

@login_required
def detail_case(request, caso_id):
 
    caso = get_object_or_404(Caso, id=caso_id, ativo=True)

    
    caso = get_object_or_404(Caso, id=caso_id)
    
    eventos_caso = (
        EventoTimeline.objects
        .filter(caso=caso)
        .select_related('investigador_responsavel')
        .prefetch_related('evidencias_relacionadas', 'pessoas_envolvidas')
        .order_by('data_hora')
    )

    
    envolvimentos = EnvolvimentoCaso.objects.filter(
        caso=caso, ativo=True
    ).select_related('pessoa')
    
    evidencias = Evidencia.objects.filter(
        caso=caso
    ).select_related('tipo', 'custodia_atual')
    
    eventos = EventoTimeline.objects.filter(
        caso=caso
    ).order_by('data_hora')
    
    comentarios = Comentario.objects.filter(
        caso=caso
    ).select_related('autor').order_by('-data_comentario')


    paginator = Paginator(envolvimentos, 1)
    page = request.GET.get('page')
    objs = paginator.get_page(page)


    dados = []
    
    image = PessoaReconhecimento.objects.filter(pessoa=objs.object_list[0].pessoa)
  
    foto = None

    for f in image:
        foto = f.foto.url

    for v in objs.object_list:
        dados.append(
            {
            'image': foto,
            'tipo_envolvimento': v.tipo_envolvimento,
            'descricao': v.descricao,
            'ativo': v.ativo,
            'caso':{
                'id': v.caso.id,
                'titulo': v.caso.titulo
            },
            'pessoa': {
                'id': v.pessoa.id,
                'nome_completo':v.pessoa.nome_completo,
                'nome_social':v.pessoa.nome_social,
                'bi':v.pessoa.bi,
                'data_nascimento':v.pessoa.data_nascimento,
                'genero':v.pessoa.genero, 
                'estado_civil':v.pessoa.estado_civil,
                'cor_olhos':v.pessoa.cor_olhos,
                'altura':v.pessoa.altura,
                'peso':v.pessoa.peso,
                'cor_cabelo':v.pessoa.cor_cabelo,
                'profissao':v.pessoa.profissao,
                'escolaridade':v.pessoa.escolaridade,
                'nacionalidade':v.pessoa.nacionalidade,
                'telefone_principal':v.pessoa.telefone_principal,
                'telefone_secundario':v.pessoa.telefone_secundario,
                'email':v.pessoa.email,
                'observacoes':v.pessoa.observacoes,
                'idade': v.pessoa.idade
            },
            'paginacao':{
                'has_next': objs.has_next(),
                'has_previous': objs.has_previous(),
                'page_atual': objs.number,
            }
            }
        )

    paginator1 = Paginator(evidencias, 1)
    page1 = request.GET.get('page')
    objs1 = paginator1.get_page(page1)
    
    image_evidence = Arquivo.objects.filter(evidencia=objs1.object_list[0])

    foto1 = None

    for f in image_evidence:
        foto1 = f.arquivo.url
    print(foto1)

    evidencia_obj = []
    for ev in objs1.object_list:

        evidencia_obj.append({
            'foto1': foto1,
            'numero_evidencia' : ev.numero_evidencia,
            'caso' :{
                'titulo': ev.caso.titulo,
                'numero_caso': ev.caso.numero_caso
                },
            'tipo' : {
                'nome': ev.tipo.nome,
                'requer_pericia': ev.tipo.requer_pericia
            },
            'descricao' : ev.descricao,
            
            'data_coleta' : ev.data_coleta,
            'local_coleta' : ev.local_coleta,
            'coletado_por' : {
                'first_name' : ev.coletado_por.first_name,
                'last_name' : ev.coletado_por.last_name,
                },
            
            'status' : ev.status,
            'custodia_atual' : {
                'first_name' : ev.custodia_atual.first_name,
                'last_name' : ev.custodia_atual.last_name,
                
            },
            'local_armazenamento' : ev.local_armazenamento,
            
            'peso' : ev.peso,
            'dimensoes' : ev.dimensoes,
            'cor' : ev.cor,
            'material' : ev.material,
            'estado_conservacao' : ev.estado_conservacao,
            
            'observacoes' : ev.observacoes,
            'valor_estimado' : ev.valor_estimado,
            
            'lacrada' : ev.lacrada,
            'numero_lacre' : ev.numero_lacre,
            'data_criacao' : ev.data_criacao,

            'paginacao':{
                'has_next': objs1.has_next(),
                'has_previous': objs1.has_previous(),
                'page_atual': objs1.number,
            },
            'dados': dados
        })

    if page:

        return JsonResponse({ 'evidencia_obj': evidencia_obj}, safe=False)

    if request.method == 'POST' and 'comentario' in request.POST:
        comentario_form = ComentarioForm(request.POST)
        if comentario_form.is_valid():
            comentario = comentario_form.save(commit=False)
            comentario.caso = caso
            comentario.autor = request.user
            comentario.save()
            messages.success(request, 'Comentário adicionado com sucesso!')
            return redirect('caso_detalhes', caso_id=caso.id)
    else:
        context = {
            'caso': caso,
            'eventos_caso': eventos_caso,
            'envolvimentos': objs,
            'evidencia_obj': objs1,
            'eventos': eventos,
            'tamanho_caso': len(envolvimentos),
            'tamanho_evidencia': len(evidencias),
        }

        return render(request, 'caso/detail_case.html', context)

@login_required
def create_case(request):
    delegados = Usuario.objects.filter(
        cargo='delegado'
    )
    investigadores = Usuario.objects.filter(
        cargo='investigador'
    )

    if request.method == 'POST':
        form = CasoForm(request.POST)

        if form.is_valid():
            caso = form.save()
            caso.criado_por = request.user

            caso.save()
            
            LogAuditoria.objects.create(
                usuario=request.user,
                acao='create',
                modelo='Caso',
                objeto_id=str(caso.id),
                descricao=f'Caso criado: {caso.numero_caso}',
                ip_origem=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, 'Sucesso')
            return render(request, 'caso/create_case.html',{'form': form, 'sucesso': 'sucesso',
             
                'delegados': delegados, 'investigadores': investigadores
            })
        else:
            return render(request, 'caso/create_case.html',{'form': form, 'erro': 'erro',
             
                'delegados': delegados, 'investigadores': investigadores})
    else:
        form = CasoForm()
    
    return render(request, 'caso/create_case.html', {'form': form, 
    'delegados': delegados, 'investigadores': investigadores})

@login_required
def edit_case(request, caso_id):
    
    caso = get_object_or_404(Caso, id=caso_id, ativo=True)
    tipos_crime = TipoCrime.objects.filter(ativo=True)

    
    if request.method == 'POST':

        form = CasoForm(request.POST, instance=caso)

        dados_anteriores = serializers.serialize('json', [caso])

        if form.is_valid():
            case = form.save(caso)

            LogAuditoria.objects.create(
                usuario=request.user,
                acao='update',
                modelo='Caso',
                objeto_id=str(case.id),
                descricao=f'Caso atualizado: {case.numero_caso}',
                ip_origem=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                dados_anteriores = dados_anteriores,
                dados_novos = serializers.serialize('json', [case])
            )
            
            if caso.data_ocorrencia:
                caso.data_ocorrencia = caso.data_ocorrencia.strftime('%Y-%m-%dT%H:%M')
            if caso.prazo_conclusao:
                caso.prazo_conclusao = caso.prazo_conclusao.strftime('%Y-%m-%dT%H:%M')
            if caso.data_conclusao:
                caso.data_conclusao = caso.data_conclusao.strftime('%Y-%m-%dT%H:%M')
           
            return render(request, 'caso/edit_case.html', 
            {'form': form, 'caso': case, 'tipos_crime': tipos_crime, 'sucesso': 'Caso atualizado com sucesso'})
        
        else:
            if caso.data_ocorrencia:
                caso.data_ocorrencia = caso.data_ocorrencia.strftime('%Y-%m-%dT%H:%M')
            if caso.prazo_conclusao:
                caso.prazo_conclusao = caso.prazo_conclusao.strftime('%Y-%m-%dT%H:%M')
            if caso.data_conclusao:
                caso.data_conclusao = caso.data_conclusao.strftime('%Y-%m-%dT%H:%M')
           
            return render(request, 'caso/edit_case.html', 
            {'form': form, 'caso': caso, 'tipos_crime': tipos_crime, 'erro': 'Erro, ao atualizar caso!'})
    else:

        if caso.data_ocorrencia:
            caso.data_ocorrencia = caso.data_ocorrencia.strftime('%Y-%m-%dT%H:%M')
        if caso.prazo_conclusao:
            caso.prazo_conclusao = caso.prazo_conclusao.strftime('%Y-%m-%dT%H:%M')
        if caso.data_conclusao:
            caso.data_conclusao = caso.data_conclusao.strftime('%Y-%m-%dT%H:%M')

        form = CasoForm()
    
        return render(request, 'caso/edit_case.html', {'form': form, 'tipos_crime': tipos_crime, 'caso': caso})

@login_required
@require_http_methods(["POST"])
def delete_case(request, caso_id):
    if request.method == 'POST':
        
        caso = Caso.objects.get(id=caso_id)

        dados = json.loads(request.body)
        user = request.user
        password = dados.get('password')
    
        if not user.check_password(password.strip()):

            return JsonResponse({'error': 'Credenciais inválidas'}, status=403)

        caso.delete()
        
        LogAuditoria.objects.create(
            usuario=request.user,
            acao='delete',
            modelo='Caso',
            objeto_id=str(caso.id),
            descricao=f'Caso eliminado: {caso.numero_caso}',
            ip_origem=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return redirect('list_case')

@login_required
def criminal_record(request):

    search_bi = request.GET.get('bi')

    pessoas = []
    envolvimentos = []
    if search_bi:
        try:
            pessoas = Pessoa.objects.filter(
                bi=search_bi
            )
            pessoas = pessoas
        except Pessoa.DoesNotExist:
            pass


        for p in pessoas:
            try:
                envolvimentos = EnvolvimentoCaso.objects.filter(pessoa=p)
            except EnvolvimentoCaso.DoesNotExist:
                pass


    context={
        'pessoas': pessoas,
        'envolvimentos': envolvimentos
    }

    return render(request, 'caso/criminal_record.html', context)


@login_required
def list_individual_involved(request):
    
    envolvimentos = EnvolvimentoCaso.objects.filter(pessoa__ativo=True)
   
    
    nome_filter = request.GET.get('nome_filter')
    bi_filter = request.GET.get('bi')
    per_page = request.GET.get('per_page', 20)
    
    if nome_filter:
        envolvimentos = envolvimentos.filter(pessoa__nome_completo__icontains=nome_filter)
    
    if bi_filter:
        envolvimentos = envolvimentos.filter(pessoa__bi=bi_filter)
    
    
    order_by = request.GET.get('order_by', '-criado_por')

    if order_by == 'numero_caso':

        envolvimentos = envolvimentos.order_by(f'caso__{order_by}')

    elif order_by == 'nome_completo':
        envolvimentos = envolvimentos.order_by(f'pessoa__{order_by}')

    else:
       envolvimentos =  envolvimentos.order_by(order_by)
    
    paginator = Paginator(envolvimentos, per_page)
    page = request.GET.get('page')
    obj = paginator.get_page(page)
    
    context = {
        'envolvimentos': obj,
        'per_page': per_page,
        'nome_filter': nome_filter,
        'bi': bi_filter,
    }
    
    return render(request, 'pessoas_envolvida/list_indiidual_involved.html', context)

@login_required
def detail_individual_invalid(request, pessoa_id):

    envolvimento = get_object_or_404(EnvolvimentoCaso, id=pessoa_id, ativo=True)
    pessoa = Pessoa.objects.get(id=envolvimento.pessoa.id)
    
    context = {
        'pessoa': pessoa,
        'envolvimento': envolvimento,
    }
    
    return render(request, 'pessoas_envolvida/detail_individual_invalid.html', context)

@login_required
def create_individual_involved(request, caso_id):

    caso = Caso.objects.get(id=caso_id)
    
    if request.method == 'POST':
        form = PessoaEnvolvidaForm(request.POST)
        if form.is_valid():

            pessoa, envolvimentoCaso = form.save(caso=caso)

            pessoa.criado_por = request.user
            envolvimentoCaso.criado_por = request.user
            envolvimentoCaso.save()
            pessoa.save()

            foto_data = None
            foto_base64 = None
            try:
                foto_data = request.FILES['foto_data']
            except Exception as e:
                pass
            try:
                foto_base64 = request.POST.get('foto_base64')
            except Exception as e:
                pass

            temp_path = None


            if foto_data:
                _, ext = os.path.splitext(foto_data.name)

                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                    for chunk in foto_data.chunks():
                        temp_file.write(chunk)
                    temp_path = temp_file.name 

                

            elif foto_base64:
                format, imgstr = foto_base64.split(';base64,')
                ext = format.split('/')[-1]
                image_content = ContentFile(base64.b64decode(imgstr), name=f"{datetime.now()}.{ext}")

                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_file:
                    temp_file.write(image_content.read())
                    temp_path = temp_file.name


            with open(temp_path, 'rb') as f:
                pessoaReconhecimento = PessoaReconhecimento.objects.create(
                    pessoa=pessoa,
                    nome=pessoa.nome_completo,
                    foto=File(f, name=f"{datetime.now()}.{ext}")
                )

            try:
                faces = DeepFace.extract_faces(img_path=pessoaReconhecimento.foto.path, detector_backend='opencv',enforce_detection=False)
            
                if len(faces) == 0:
                    pessoaReconhecimento.delete()
                    return JsonResponse({'success': False, 'message': 'Nenhum rosto detectado na imagem'})
                
                
                backends = ['opencv', 'ssd', 'dlib', 'mtcnn', 'fastmtcnn',
                    'retinaface', 'mediapipe', 'yolov8n', 'yolov8m', 'yolov8l', 'yolov11n',
                    'yolov11s', 'yolov11m', 'yolov11l', 'yolov12n', 'yolov12s',
                    'yolov12m', 'yolov12l', 'yunet', 'centerface'
                ]
                embedding_obj = DeepFace.represent(
                    img_path=pessoaReconhecimento.foto.path,
                    detector_backend=backends[4],
                    model_name='ArcFace',
                    enforce_detection=False
                )

                pessoaReconhecimento.embedding = embedding_obj[0]['embedding']
                pessoaReconhecimento.save()
                
            except Exception as e:
                pessoaReconhecimento.delete()

            LogAuditoria.objects.create(
                usuario=request.user,
                acao='create',
                modelo='EnvolvimentoCaso',
                objeto_id=str(envolvimentoCaso.id),
                descricao=f'Envolvimento do caso criado: {pessoa.nome_completo}',
                ip_origem=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return render(request, 'pessoas_envolvida/create_indiidual_involved.html', 
                {'form': form, 'caso': caso, 'sucesso': f'{pessoa.nome_completo} Criado(a) com sucesso!'})
        else:
           
            return render(request, 'pessoas_envolvida/create_indiidual_involved.html', 
                {'form': form, 'caso': caso, 'erro': 'Erro ao salva dados da pessoa'})

    else:
        form = PessoaEnvolvidaForm()
    
    return render(request, 'pessoas_envolvida/create_indiidual_involved.html', 
    {'form': form, 'caso': caso})

def edit_individual_involved(request, id):

    envolvimento = EnvolvimentoCaso.objects.get(id=id)
    
    
    if request.method == 'POST':

        form = FormEnvolvimento(request.POST)

        if form.is_valid():

            env = form.save(envolvimento)

            context = {
                'success': 'Atualização dos dados feita com sucesso',
                'envolvimento': envolvimento,
                'form': form
            }
            return render(request, 'pessoas_envolvida/edit_indiidual_involved.html',context)
        else:
            context = {
                'error': 'Erro ao atualizar os dados!',
                'envolvimento': envolvimento,
                'form': form
            }
            return render(request, 'pessoas_envolvida/edit_indiidual_involved.html',context)
    else:
        form = FormEnvolvimento()

        return render(request, 'pessoas_envolvida/edit_indiidual_involved.html',
        {'envolvimento': envolvimento, 'form': form})

@login_required
@require_http_methods(["POST"])
def delete_individual_involved(request, id):
    if request.method == 'POST':
        
        pessoa = Pessoa.objects.get(id=id)

        dados = json.loads(request.body)
        user = request.user
        password = dados.get('password')
    
        if not user.check_password(password.strip()):

            return JsonResponse({'error': 'Credenciais inválidas'}, status=403)

        pessoa.delete()
        
        LogAuditoria.objects.create(
            usuario=request.user,
            acao='delete',
            modelo='Pessoa',
            objeto_id=str(pessoa.id),
            descricao=f'Envolvimento eliminado',
            ip_origem=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return redirect('list_indiidual_involved')

# def pessoa_editar(request, pessoa_id):
#     """Editar pessoa existente"""
#     pessoa = get_object_or_404(Pessoa, id=pessoa_id, ativo=True)
    
#     if request.method == 'POST':
#         form = PessoaForm(request.POST, instance=pessoa)
#         if form.is_valid():
#             pessoa = form.save()
#             messages.success(request, 'Pessoa atualizada com sucesso!')
#             return redirect('pessoa_detalhes', pessoa_id=pessoa.id)
#     else:
#         form = PessoaForm(instance=pessoa)
    
#     return render(request, 'pessoas/editar.html', {'form': form, 'pessoa': pessoa})

# # =============================================================================
# # VIEWS DE EVIDÊNCIAS
# # =============================================================================

# @login_required
# def evidencia_lista(request):
#     """Lista de evidências com filtros"""
#     evidencias = Evidencia.objects.all().select_related(
#         'caso', 'tipo', 'custodia_atual'
#     )
    
#     # Filtros
#     caso_filter = request.GET.get('caso')
#     tipo_filter = request.GET.get('tipo')
#     status_filter = request.GET.get('status')
#     custodia_filter = request.GET.get('custodia')
    
#     if caso_filter:
#         evidencias = evidencias.filter(caso_id=caso_filter)
    
#     if tipo_filter:
#         evidencias = evidencias.filter(tipo_id=tipo_filter)
    
#     if status_filter:
#         evidencias = evidencias.filter(status=status_filter)
    
#     if custodia_filter:
#         evidencias = evidencias.filter(custodia_atual_id=custodia_filter)
    
#     # Ordenação
#     evidencias = evidencias.order_by('-data_coleta')
    
#     # Paginação
#     paginator = Paginator(evidencias, 20)
#     page = request.GET.get('page')
#     evidencias = paginator.get_page(page)
    
#     # Dados para filtros
#     tipos_evidencia = TipoEvidencia.objects.filter(ativo=True)
#     from .models import Usuario
#     usuarios = Usuario.objects.filter(ativo=True)
    
#     context = {
#         'evidencias': evidencias,
#         'tipos_evidencia': tipos_evidencia,
#         'usuarios': usuarios,
#         'status_choices': Evidencia.STATUS_CHOICES,
#         'current_filters': {
#             'caso': caso_filter,
#             'tipo': tipo_filter,
#             'status': status_filter,
#             'custodia': custodia_filter,
#         }
#     }
    
#     return render(request, 'evidencias/lista.html', context)

# @login_required
# def evidencia_detalhes(request, evidencia_id):
#     """Detalhes de uma evidência específica"""
#     evidencia = get_object_or_404(Evidencia, id=evidencia_id)
    
#     # Cadeia de custódia
#     cadeia_custodia = CadeiaCustomia.objects.filter(
#         evidencia=evidencia
#     ).order_by('-data_movimentacao')
    
#     # Arquivos relacionados
#     arquivos = Arquivo.objects.filter(evidencia=evidencia)
    
#     context = {
#         'evidencia': evidencia,
#         'cadeia_custodia': cadeia_custodia,
#         'arquivos': arquivos,
#     }
    
#     return render(request, 'evidencias/detalhes.html', context)

# @login_required
# def evidencia_criar(request):
#     """Criar nova evidência"""
#     caso_id = request.GET.get('caso_id')
#     initial_data = {}
    
#     if caso_id:
#         caso = get_object_or_404(Caso, id=caso_id)
#         initial_data['caso'] = caso
    
#     if request.method == 'POST':
#         form = EvidenciaForm(request.POST, request.FILES)
#         if form.is_valid():
#             evidencia = form.save(commit=False)
#             evidencia.coletado_por = request.user
#             evidencia.custodia_atual = request.user
#             evidencia.save()
            
#             # Criar primeiro registro na cadeia de custódia
#             CadeiaCustomia.objects.create(
#                 evidencia=evidencia,
#                 tipo_movimentacao='coleta',
#                 responsavel_atual=request.user,
#                 local_destino=evidencia.local_armazenamento,
#                 motivo='Coleta inicial da evidência'
#             )
            
#             messages.success(request, 'Evidência cadastrada com sucesso!')
#             return redirect('evidencia_detalhes', evidencia_id=evidencia.id)
#     else:
#         form = EvidenciaForm(initial=initial_data)
    
#     return render(request, 'evidencias/criar.html', {'form': form})

# @login_required
# def evidencia_transferir(request, evidencia_id):
#     """Transferir custódia de evidência"""
#     evidencia = get_object_or_404(Evidencia, id=evidencia_id)
    
#     if request.method == 'POST':
#         novo_custodia_id = request.POST.get('novo_custodia')
#         local_destino = request.POST.get('local_destino')
#         motivo = request.POST.get('motivo')
        
#         from .models import Usuario
#         novo_custodia = get_object_or_404(Usuario, id=novo_custodia_id)
        
#         with transaction.atomic():
#             # Atualizar evidência
#             responsavel_anterior = evidencia.custodia_atual
#             evidencia.custodia_atual = novo_custodia
#             evidencia.local_armazenamento = local_destino
#             evidencia.save()
            
#             # Registrar na cadeia de custódia
#             CadeiaCustomia.objects.create(
#                 evidencia=evidencia,
#                 tipo_movimentacao='transferencia',
#                 responsavel_anterior=responsavel_anterior,
#                 responsavel_atual=novo_custodia,
#                 local_origem=evidencia.local_armazenamento,
#                 local_destino=local_destino,
#                 motivo=motivo
#             )
        
#         messages.success(request, 'Transferência realizada com sucesso!')
#         return redirect('evidencia_detalhes', evidencia_id=evidencia.id)
    
#     from .models import Usuario
#     usuarios = Usuario.objects.filter(ativo=True).exclude(id=evidencia.custodia_atual.id)
    
#     return render(request, 'evidencias/transferir.html', {
#         'evidencia': evidencia,
#         'usuarios': usuarios
#     })

# # =============================================================================
# # VIEWS DE TIMELINE
# # =============================================================================

@login_required
def create_event(request, caso_id):
  
    caso = get_object_or_404(Caso, id=caso_id, ativo=True)

    pessoas = EnvolvimentoCaso.objects.filter(caso=caso)
    evidencias = Evidencia.objects.filter(caso=caso)
    investigadores = Usuario.objects.filter(
        cargo='investigador'
    )

    if request.method == 'POST':

        evento_form = EventoTimelineForm(request.POST, instance=caso)

        context = {
            'form': evento_form,
            'pessoas': pessoas,
            'evidencias': evidencias,
            'investigadores': investigadores,
            'caso': caso
        }


        if evento_form.is_valid():
            evento = evento_form.save()
            evento.criado_por = request.user
            evento.save()

            LogAuditoria.objects.create(
                usuario=request.user,
                acao='create',
                modelo='EventoTimeline',
                objeto_id=str(evento.id),
                descricao=f'Evento timeline criado: {evento.titulo}',
                ip_origem=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            messages.success(request, 'Evento adicionado à timeline!')
            return render(request, 'evento/create_event.html', context)
        
        else:
            messages.error(request, 'Erro ao adicionado evento  à timeline!')
            return render(request, 'evento/create_event.html', context)

    else:
        evento_form = EventoTimelineForm()
    
    context = {
        'caso': caso,
        'form': evento_form,
        'pessoas': pessoas,
        'evidencias': evidencias,
        'investigadores': investigadores,
    }
    
    return render(request, 'evento/create_event.html', context)

@login_required
def list_event(request):

    eventos = EventoTimeline.objects.all()

    numero_caso = request.GET.get('numero_caso')
    order_by = request.GET.get('order_by', '-data_hora')
    page = request.GET.get('page')
    per_page = request.GET.get('per_page', 20)

    if numero_caso:
        eventos = eventos.filter(
            caso__numero_caso=numero_caso
            )
    
    eventos = eventos.order_by(order_by)

    paginator = Paginator(eventos, per_page)
    objs = paginator.get_page(page)
    
    context = {
        'eventos': objs,
        'per_page':per_page,
        'numero_caso': numero_caso,
        'order_by': order_by
    }



    return render(request, 'evento/list_event.html', context)

@login_required
def edit_event(request, id):

    evento = (EventoTimeline.objects
        .filter(id=id)
        .select_related('investigador_responsavel')
        .prefetch_related('evidencias_relacionadas', 'pessoas_envolvidas')
    )[0]

    caso = Caso.objects.get(eventos_timeline=id)
    pessoas = EnvolvimentoCaso.objects.filter(caso=caso)
    evidencias = Evidencia.objects.filter(caso=caso)

    investigadores = Usuario.objects.filter(
        cargo='investigador'
    )

    

    if request.method == 'POST':

        form = EventoTimelineForm(request.POST,instance=caso)
        dados_anteriores = serializers.serialize('json', [evento])

        if form.is_valid():

            event = form.save(evento=evento)

            LogAuditoria.objects.create(
                usuario=request.user,
                acao='update',
                modelo='EventoTimeline',
                objeto_id=str(event.id),
                descricao=f'Evento timeline atualizado: {event.titulo}',
                ip_origem=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                dados_anteriores = dados_anteriores,
                dados_novos = serializers.serialize('json', [event])
            )

            evento.data_hora = evento.data_hora.strftime('%Y-%m-%dT%H:%M')
            context = {
                'form': form,
                'pessoas': pessoas,
                'evidencias': evidencias,
                'evento': evento,
                'investigadores': investigadores,
            }

            messages.success(request, 'Atualização do evento feita com sucesso')
            return render(request, 'evento/edit_event.html', context)
        else:
            evento.data_hora = evento.data_hora.strftime('%Y-%m-%dT%H:%M')
            context = {
                'form': form,
                'pessoas': pessoas,
                'evidencias': evidencias,
                'evento': evento,
                'investigadores': investigadores,
            }

            messages.error(request, 'Erro ao Atualizr evento')
            return render(request, 'evento/edit_event.html', context)
    else:
        form = EventoTimelineForm(initial={
            'coordenadas_lat':evento.coordenadas_lat,
            'coordenadas_lng':evento.coordenadas_lng,
        })
        evento.data_hora = evento.data_hora.strftime('%Y-%m-%dT%H:%M')
        context = {
            'form': form,
            'evento': evento,
            'pessoas': pessoas,
            'evidencias': evidencias,
            'investigadores': investigadores,
        }
        return render(request, 'evento/edit_event.html', context)

@login_required
def detail_event(request, id):

    evento = EventoTimeline.objects.get(id=id)
    print(evento.evidencias_relacionadas.all())

    return render(request, 'evento/detail_event.html', {'evento': evento})

@login_required
@require_http_methods(["POST"])
def delete_event(request, id):

    ev = EventoTimeline.objects.get(id=id)

    dados = json.loads(request.body)
    password = dados.get('password')
    user = request.user

    if not user.check_password(password.strip()):
        return JsonResponse({'erro': 'Credinciais inválidas'}, status=403)

    LogAuditoria.objects.create(
        usuario=request.user,
        acao='delete',
        modelo='EventoTimeline',
        objeto_id=str(ev.id),
        descricao=f'Evento timeline Eliminado: {ev.titulo}',
        ip_origem=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    ev.delete()

    return redirect('/list_event')

@login_required
def create_type_crime(request):

    form = TipoCrimeForm()

    if request.method == 'POST':


        form = TipoCrimeForm(request.POST)
        

        if form.is_valid():

            tipo = form.save()

            messages.success(request, 'Tipo de crime criado com sucesso!')

            return render(request, 'tipo_crime/create_type_crime.html', {'form': form})
        
        else:
            messages.error(request, 'Erro, ao criar tipo de crime!')
            return render(request, 'tipo_crime/create_type_crime.html', {'form': form})


    return render(request, 'tipo_crime/create_type_crime.html', {'form': form})

@login_required
def edit_type_crime(request, id):

    tipo_crime = TipoCrime.objects.get(id=id)
    form = TipoCrimeForm()

    if request.method == 'POST':

        form = TipoCrimeForm(request.POST)
        dados_anteriores = serializers.serialize('json', [tipo_crime])

        if form.is_valid():

            tipo = form.save(tipo_crime)

            LogAuditoria.objects.create(
                usuario=request.user,
                acao='update',
                modelo='tipoCrime',
                objeto_id=str(tipo.id),
                descricao=f'Tipo de crime atualizado: {tipo.nome}',
                ip_origem=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                dados_anteriores = dados_anteriores,
                dados_novos = serializers.serialize('json', [tipo])
            )
            messages.success(request, 'Dados do tipo de crime atualizado com sucesso!')

            return render(request, 'tipo_crime/edit_type_crime.html', {'form': form, 'tipo_crime':tipo})
        
        else:
            messages.error(request, 'Erro, ao atuliazar dados do tipo de crime!')
            return render(request, 'tipo_crime/edit_type_crime.html', {'form': form, 'tipo_crime': tipo_crime})

    return render(request, 'tipo_crime/edit_type_crime.html', {'form': form, 'tipo_crime': tipo_crime})

@login_required
def datail_type_crime(request, id):

    tipo_crime = TipoCrime.objects.get(id=id)


    return render(request, 'tipo_crime/detail_type_crime.html', {'tipo_crime': tipo_crime})

@login_required
def list_type_crime(request):

    tipos_crime = TipoCrime.objects.all()


    per_page = request.GET.get('per_page', 20)
    page = request.GET.get('page', 1)
    order_by = request.GET.get('order_by', 'nome')

    tipos_crime =  tipos_crime.order_by(order_by)

    paginator = Paginator(tipos_crime, per_page)
    obj = paginator.get_page(page)

    context = {
        'tipos_crimes': obj,
        'per_page':per_page,
        'order_by':order_by
    }
    return render(request, 'tipo_crime/list_type_crime.html', context)

@login_required
def delete_typr_crime(request, id):

    crime = TipoCrime.objects.get(id=id)

    dados = json.loads(request.body)

    password = dados.get('password')
    user = request.user

    if not user.check_password(password):
        return JsonResponse({'erro': 'Credinciais inválidas'}, status=403)

    LogAuditoria.objects.create(
        usuario=request.user,
        acao='delete',
        modelo='TipoCrime',
        objeto_id=str(crime.id),
        descricao=f'tipo de crime Eliminado: {crime.nome}',
        ip_origem=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    crime.delete()

    return redirect('list_type_crime')
# # =============================================================================
# # VIEWS DE API (AJAX)
# # =============================================================================

# @login_required
# def api_buscar_pessoas(request):
#     """API para buscar pessoas (autocomplete)"""
#     q = request.GET.get('q', '')
    
#     if len(q) < 2:
#         return JsonResponse({'results': []})
    
#     pessoas = Pessoa.objects.filter(
#         Q(nome_completo__icontains=q) | Q(cpf__icontains=q),
#         ativo=True
#     )[:10]
    
#     results = []
#     for pessoa in pessoas:
#         results.append({
#             'id': pessoa.id,
#             'text': f"{pessoa.nome_completo} - {pessoa.cpf or 'Sem CPF'}"
#         })
    
#     return JsonResponse({'results': results})

# @login_required
# def api_casos_estatisticas(request):
#     """API para estatísticas de casos"""
#     # Casos por mês (últimos 12 meses)
#     from django.utils import timezone
#     from datetime import datetime, timedelta
#     import calendar
    
#     end_date = timezone.now()
#     start_date = end_date - timedelta(days=365)
    
#     casos_por_mes = []
#     for i in range(12):
#         mes_inicio = start_date.replace(day=1) + timedelta(days=32*i)
#         mes_inicio = mes_inicio.replace(day=1)
        
#         if i == 11:
#             mes_fim = end_date
#         else:
#             mes_fim = sta

# import logging
# import hashlib
# import hmac
# from datetime import datetime, timedelta
# from functools import wraps
# from typing import Optional, Dict, Any

# from django.http import JsonResponse
# from django.views.decorators.http import require_http_methods
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator
# from django.views import View
# from django.contrib.auth.models import User
# from django.conf import settings
# from django.core.cache import cache
# from django.db import transaction
# from django.core.exceptions import ValidationError
# from django.utils import timezone

# import jwt
# from rest_framework import status
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response

# # Configuração do logger para auditoria
# logger = logging.getLogger('criminal_investigation')

# # Configurações de segurança
# JWT_SECRET = getattr(settings, 'JWT_SECRET_KEY', 'your-super-secret-key')
# JWT_ALGORITHM = 'HS256'
# JWT_EXPIRATION_HOURS = 8
# MAX_REQUESTS_PER_MINUTE = 60
# MAX_REQUESTS_PER_HOUR = 1000
# SUSPICIOUS_ACTIVITY_THRESHOLD = 50

# class SecurityMiddleware:
    
#     @staticmethod
#     def log_request(request, user_id=None, action=None, sensitive_data=False):
#         log_data = {
#             'timestamp': datetime.now().isoformat(),
#             'ip_address': SecurityMiddleware.get_client_ip(request),
#             'user_agent': request.META.get('HTTP_USER_AGENT', ''),
#             'user_id': user_id,
#             'action': action,
#             'method': request.method,
#             'path': request.path,
#             'sensitive_data': sensitive_data
#         }
        
#         if sensitive_data:
#             logger.critical(f"SENSITIVE_ACCESS: {log_data}")
#         else:
#             logger.info(f"REQUEST: {log_data}")
    
#     @staticmethod
#     def get_client_ip(request):
#         x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#         if x_forwarded_for:
#             ip = x_forwarded_for.split(',')[0]
#         else:
#             ip = request.META.get('REMOTE_ADDR')
#         return ip
    
#     @staticmethod
#     def detect_suspicious_activity(ip_address, user_id=None):

#         cache_key = f"suspicious_activity:{ip_address}:{user_id or 'anonymous'}"
#         attempts = cache.get(cache_key, 0)
        
#         if attempts > SUSPICIOUS_ACTIVITY_THRESHOLD:
#             logger.warning(f"SUSPICIOUS_ACTIVITY_DETECTED: IP {ip_address}, User {user_id}, Attempts: {attempts}")
#             return True
        
#         cache.set(cache_key, attempts + 1, 3600)  # 1 hora
#         return False

# def rate_limit(max_requests_per_minute=MAX_REQUESTS_PER_MINUTE, 
#                max_requests_per_hour=MAX_REQUESTS_PER_HOUR):

#     def decorator(func):
#         @wraps(func)
#         def wrapper(request, *args, **kwargs):
#             ip_address = SecurityMiddleware.get_client_ip(request)
            
#             # Chaves para diferentes períodos
#             minute_key = f"rate_limit_minute:{ip_address}:{datetime.now().strftime('%Y%m%d%H%M')}"
#             hour_key = f"rate_limit_hour:{ip_address}:{datetime.now().strftime('%Y%m%d%H')}"
            
#             # Verificar limite por minuto
#             minute_requests = cache.get(minute_key, 0)
#             if minute_requests >= max_requests_per_minute:
#                 logger.warning(f"RATE_LIMIT_EXCEEDED_MINUTE: IP {ip_address}")
#                 return JsonResponse({
#                     'error': 'Rate limit exceeded – too many requests per minute',
#                     'retry_after': 60
#                 }, status=429)
            
#             # Verificar limite por hora
#             hour_requests = cache.get(hour_key, 0)
#             if hour_requests >= max_requests_per_hour:
#                 logger.warning(f"RATE_LIMIT_EXCEEDED_HOUR: IP {ip_address}")
#                 return JsonResponse({
#                     'error': 'Rate limit exceeded – too many requests per hour',
#                     'retry_after': 3600
#                 }, status=429)
            
#             # Incrementar contadores
#             cache.set(minute_key, minute_requests + 1, 60)
#             cache.set(hour_key, hour_requests + 1, 3600)
            
#             return func(request, *args, **kwargs)
#         return wrapper
#     return decorator

# def jwt_required(func):
  
#     @wraps(func)
#     def wrapper(request, *args, **kwargs):
#         token = None
#         auth_header = request.META.get('HTTP_AUTHORIZATION')
        
#         if auth_header and auth_header.startswith('Bearer '):
#             token = auth_header.split(' ')[1]
        
#         if not token:
#             return JsonResponse({
#                 'error': 'Token de acesso requerido',
#                 'code': 'MISSING_TOKEN'
#             }, status=401)
        
#         try:
#             # Verificar se o token está na blacklist
#             blacklist_key = f"jwt_blacklist:{hashlib.md5(token.encode()).hexdigest()}"
#             if cache.get(blacklist_key):
#                 raise jwt.InvalidTokenError("Token blacklisted")
            
#             # Decodificar e validar token
#             payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
#             # Verificar expiração
#             if payload.get('exp', 0) < datetime.utcnow().timestamp():
#                 raise jwt.ExpiredSignatureError("Token expired")
            
#             # Verificar se o usuário ainda existe e está ativo
#             try:
#                 user = User.objects.get(id=payload['user_id'], is_active=True)
#                 request.user = user
#                 request.jwt_payload = payload
#             except User.DoesNotExist:
#                 raise jwt.InvalidTokenError("Invalid user")
            
#         except jwt.ExpiredSignatureError:
#             return JsonResponse({
#                 'error': 'Token expirado',
#                 'code': 'TOKEN_EXPIRED'
#             }, status=401)
#         except jwt.InvalidTokenError:
#             return JsonResponse({
#                 'error': 'Token inválido',
#                 'code': 'INVALID_TOKEN'
#             }, status=401)
        
#         return func(request, *args, **kwargs)
#     return wrapper

# def permission_required(permissions):

#     def decorator(func):
#         @wraps(func)
#         def wrapper(request, *args, **kwargs):
#             user = getattr(request, 'user', None)
            
#             if not user or not user.is_authenticated:
#                 return JsonResponse({
#                     'error': 'Usuário não autenticado',
#                     'code': 'NOT_AUTHENTICATED'
#                 }, status=401)
            
#             # Verificar permissões
#             if not all(user.has_perm(perm) for perm in permissions):
#                 SecurityMiddleware.log_request(
#                     request, 
#                     user.id, 
#                     f"PERMISSION_DENIED: {permissions}",
#                     sensitive_data=True
#                 )
#                 return JsonResponse({
#                     'error': 'Permissões insuficientes',
#                     'code': 'INSUFFICIENT_PERMISSIONS'
#                 }, status=403)
            
#             return func(request, *args, **kwargs)
#         return wrapper
#     return decorator

# class CriminalInvestigationView(View):

    
#     def dispatch(self, request, *args, **kwargs):
#         # Verificar atividade suspeita
#         ip_address = SecurityMiddleware.get_client_ip(request)
#         user_id = getattr(request, 'user', {}).get('id') if hasattr(request, 'user') else None
        
#         if SecurityMiddleware.detect_suspicious_activity(ip_address, user_id):
#             return JsonResponse({
#                 'error': 'Atividade suspeita detectada',
#                 'code': 'SUSPICIOUS_ACTIVITY'
#             }, status=429)
        
#         return super().dispatch(request, *args, **kwargs)

# @csrf_exempt
# @require_http_methods(["POST"])
# @rate_limit(max_requests_per_minute=10, max_requests_per_hour=100)
# def login_view(request):

#     try:
#         import json
#         data = json.loads(request.body)
        
#         username = data.get('username')
#         password = data.get('password')
        
#         if not username or not password:
#             return JsonResponse({
#                 'error': 'Username e password são obrigatórios',
#                 'code': 'MISSING_CREDENTIALS'
#             }, status=400)
        
#         # Verificar credenciais
#         try:
#             user = User.objects.get(username=username, is_active=True)
#             if not user.check_password(password):
#                 raise User.DoesNotExist()
#         except User.DoesNotExist:
#             SecurityMiddleware.log_request(
#                 request, 
#                 None, 
#                 f"FAILED_LOGIN_ATTEMPT: {username}",
#                 sensitive_data=True
#             )
#             return JsonResponse({
#                 'error': 'Credenciais inválidas',
#                 'code': 'INVALID_CREDENTIALS'
#             }, status=401)
        
#         # Gerar token JWT
#         payload = {
#             'user_id': user.id,
#             'username': user.username,
#             'permissions': list(user.get_all_permissions()),
#             'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
#             'iat': datetime.utcnow(),
#             'ip': SecurityMiddleware.get_client_ip(request)
#         }
        
#         token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
#         # Log do login bem-sucedido
#         SecurityMiddleware.log_request(
#             request, 
#             user.id, 
#             "SUCCESSFUL_LOGIN",
#             sensitive_data=True
#         )
        
#         return JsonResponse({
#             'access_token': token,
#             'token_type': 'Bearer',
#             'expires_in': JWT_EXPIRATION_HOURS * 3600,
#             'user': {
#                 'id': user.id,
#                 'username': user.username,
#                 'permissions': payload['permissions']
#             }
#         })
        
#     except json.JSONDecodeError:
#         return JsonResponse({
#             'error': 'JSON inválido',
#             'code': 'INVALID_JSON'
#         }, status=400)
#     except Exception as e:
#         logger.error(f"LOGIN_ERROR: {str}")
#         return JsonResponse({
#             'error': 'Erro interno do servidor',
#             'code': 'INTERNAL_ERROR'
#         }, status=500)

# @csrf_exempt
# @require_http_methods(["POST"])
# @jwt_required
# @rate_limit()
# def logout_view(request):

#     try:
#         auth_header = request.META.get('HTTP_AUTHORIZATION')
#         token = auth_header.split(' ')[1]
        
#         # Adicionar token à blacklist
#         token_hash = hashlib.md5(token.encode()).hexdigest()
#         blacklist_key = f"jwt_blacklist:{token_hash}"
        
#         # Blacklist pelo tempo restante do token
#         exp_time = request.jwt_payload.get('exp', 0)
#         remaining_time = max(0, int(exp_time - datetime.utcnow().timestamp()))
#         cache.set(blacklist_key, True, remaining_time)
        
#         SecurityMiddleware.log_request(
#             request, 
#             request.user.id, 
#             "LOGOUT",
#             sensitive_data=True
#         )
        
#         return JsonResponse({'message': 'Logout realizado com sucesso'})
        
#     except Exception as e:
#         logger.error(f"LOGOUT_ERROR: {str}")
#         return JsonResponse({
#             'error': 'Erro no logout',
#             'code': 'LOGOUT_ERROR'
#         }, status=500)

# @method_decorator([csrf_exempt, jwt_required, rate_limit()], name='dispatch')
# class CaseView(CriminalInvestigationView):

    
#     @permission_required(['investigation.view_case'])
#     def get(self, request, case_id=None):

#         SecurityMiddleware.log_request(
#             request, 
#             request.user.id, 
#             f"VIEW_CASE: {case_id}",
#             sensitive_data=True
#         )
        
#         # Implementar lógica de busca de casos
#         # Esta é uma implementação exemplo
#         return JsonResponse({
#             'message': 'Casos recuperados com sucesso',
#             'case_id': case_id,
#             'timestamp': datetime.now().isoformat()
#         })
    
#     @permission_required(['investigation.add_case'])
#     def post(self, request):

#         try:
#             import json
#             data = json.loads(request.body)
            
#             # Validação básica
#             required_fields = ['title', 'description', 'priority']
#             missing_fields = [field for field in required_fields if not data.get(field)]
            
#             if missing_fields:
#                 return JsonResponse({
#                     'error': f'Campos obrigatórios faltando: {", ".join(missing_fields)}',
#                     'code': 'MISSING_FIELDS'
#                 }, status=400)
            
#             # Log da criação
#             SecurityMiddleware.log_request(
#                 request, 
#                 request.user.id, 
#                 "CREATE_CASE",
#                 sensitive_data=True
#             )
            
#             # Implementar lógica de criação
#             return JsonResponse({
#                 'message': 'Caso criado com sucesso',
#                 'case_id': 'generated_case_id',
#                 'timestamp': datetime.now().isoformat()
#             }, status=201)
            
#         except json.JSONDecodeError:
#             return JsonResponse({
#                 'error': 'JSON inválido',
#                 'code': 'INVALID_JSON'
#             }, status=400)
#         except Exception as e:
#             logger.error(f"CREATE_CASE_ERROR: {str}")
#             return JsonResponse({
#                 'error': 'Erro ao criar caso',
#                 'code': 'CREATE_ERROR'
#             }, status=500)

# @method_decorator([csrf_exempt, jwt_required, rate_limit(max_requests_per_minute=30)], name='dispatch')
# class EvidenceView(CriminalInvestigationView):
    
#     @permission_required(['investigation.view_evidence'])
#     def get(self, request, evidence_id=None):

#         SecurityMiddleware.log_request(
#             request, 
#             request.user.id, 
#             f"VIEW_EVIDENCE: {evidence_id}",
#             sensitive_data=True
#         )
        
#         return JsonResponse({
#             'message': 'Evidência recuperada com sucesso',
#             'evidence_id': evidence_id
#         })
    
#     @permission_required(['investigation.add_evidence'])
#     def post(self, request):

#         SecurityMiddleware.log_request(
#             request, 
#             request.user.id, 
#             "ADD_EVIDENCE",
#             sensitive_data=True
#         )
        
#         # Implementar upload e processamento de evidências
#         return JsonResponse({
#             'message': 'Evidência adicionada com sucesso'
#         }, status=201)

# @csrf_exempt
# @require_http_methods(["GET"])
# @jwt_required
# @rate_limit(max_requests_per_minute=120)
# @permission_required(['investigation.view_dashboard'])
# def dashboard_view(request):
  
#     SecurityMiddleware.log_request(
#         request, 
#         request.user.id, 
#         "VIEW_DASHBOARD"
#     )
    
#     return JsonResponse({
#         'message': 'Dashboard carregado com sucesso',
#         'user': request.user.username,
#         'timestamp': datetime.now().isoformat(),
#         'stats': {
#             'active_cases': 0,  # Implementar contagem real
#             'pending_evidence': 0,
#             'recent_activities': []
#         }
#     })






