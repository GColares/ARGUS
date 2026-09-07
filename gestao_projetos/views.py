# gestao_projetos/views.py
import os
from datetime import date
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
import io
import zipfile
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from docxtpl import DocxTemplate
from .models import RelatorioAtividade, ItemAtividade
from cadastros.models import BolsistaProjeto, ProjetoPDI, MembroEquipe, AtividadePlanoAcao
from docxtpl import DocxTemplate
from docx import Document
from django.contrib import messages
from django.forms import modelformset_factory
from .forms import AtividadePlanoAcaoForm
from .utils import extrair_atividades_texto_docx
from dateutil.relativedelta import relativedelta
from cadastros.models import Macroentrega


@login_required
def home_gestao_projetos(request):
    """
    Renderiza o painel central (hub) do módulo de Gestão de Projetos,
    oferecendo os atalhos operacionais para relatórios, bolsistas e entregas.
    """
    return render(request, 'gestao_projetos/home_gestao_projetos.html')

def montar_contexto_relatorio(relatorio_id):
    """
    Constrói o dicionário de contexto exato para o modelo institucional,
    injetando os dados do TermoBolsa e as Atividades vinculadas ao perfil (cota).
    Garante a injeção estrita de {{ atividade_1 }} até {{ atividade_15 }} com apenas os nomes das atividades.
    """
    relatorio = get_object_or_404(RelatorioAtividade, id=relatorio_id)
    
    # Suporte legado temporário ou novo suporte a TermoBolsa
    if relatorio.termo_bolsa:
        termo = relatorio.termo_bolsa
        projeto = termo.cota_pt.projeto
        atividades_vinculadas = list(termo.cota_pt.atividades_vinculadas.all().order_by('numero'))
    else:
        termo = None
        # pyrefly: ignore [missing-attribute]
        projeto = relatorio.bolsista.projeto
        atividades_vinculadas = list(projeto.atividades_plano.all().order_by('numero'))

    # Dicionário mapeando rigorosamente as seções do documento oficial
    # pyrefly: ignore [missing-attribute]
    total_parcelas = termo.quantidade_parcelas if termo else relatorio.bolsista.total_parcelas_previstas
    
    conta_final = relatorio.conta_pagamento
    
    if not conta_final and termo:
        # Se for um relatório antigo sem a conta gravada, tenta achar dinamicamente
        from cadastros.models import DistribuicaoContaCota
        dist = DistribuicaoContaCota.objects.filter(
            cota_pt=termo.cota_pt,
            # pyrefly: ignore [missing-attribute]
            parcela_inicio__lte=relatorio.parcela_referencia.numero,
            # pyrefly: ignore [missing-attribute]
            parcela_fim__gte=relatorio.parcela_referencia.numero
        ).first()
        if dist:
            conta_final = dist.conta_pagamento

    if not conta_final:
        # Fallback de segurança: pega a primeira conta do projeto
        conta_final = projeto.contas.first()
        
    if conta_final:
        projeto_conta = f"{conta_final.conta}-{conta_final.dv}: Conta {conta_final.fonte_recurso}"
    else:
        projeto_conta = 'N/I'
        
    contexto = {
        # Seção 1: Identificação do Projeto
        'convenio_numero': getattr(projeto, 'convenio', None) or getattr(projeto, 'processo', 'N/I') or 'N/I',
        'projeto_conta': projeto_conta,
        'projeto_nome': projeto.nome,
        
        # Seção 3: Identificação do Período e Parcela
        'parcelas_previstas': total_parcelas,
        # pyrefly: ignore [missing-attribute]
        'parcela': str(relatorio.parcela_referencia.numero),
        'periodo_inicio': relatorio.periodo_inicio.strftime('%d/%m/%Y'),
        'periodo_fim': relatorio.periodo_fim.strftime('%d/%m/%Y'),
        'carga_horaria_total': relatorio.carga_horaria_periodo,
        'macroentrega_numero': ', '.join([str(m.numero) for m in relatorio.macroentregas.all()]) if relatorio.macroentregas.exists() else 'N/I',
        'macroentregas_objs': relatorio.macroentregas.all(),

        # Seção 5: Ocorrências
        'ocorrencias': relatorio.ocorrencias or 'Nenhuma ocorrência de não conformidade registrada no período.',

        # Seção 6: Parecer do Coordenador
        'coordenador_sim': 'X' if getattr(relatorio, 'cumpriu_carga_horaria', True) else ' ',
        'coordenador_nao': ' ' if getattr(relatorio, 'cumpriu_carga_horaria', True) else 'X',
        'parecer_coordenador': getattr(relatorio, 'parecer_coordenador', 'Desempenho satisfatório alinhado às metas do projeto.'),

        # Seção 7: Assinaturas e Data
        'data_geracao': date.today().strftime('%d/%m/%Y'),
        'assinatura_coordenador': 'Coordenador do Projeto (SIAPE: _______)',
    }

    # Preenchimento Dados do Bolsista (Seção 2 e Assinatura)
    if termo:
        pessoa_bolsista = getattr(termo, 'pessoa', None) or getattr(termo, 'bolsista', None)
        cpf_bolsista = pessoa_bolsista.cpf if pessoa_bolsista else ''
        nome_bolsista = pessoa_bolsista.nome if pessoa_bolsista else 'N/I'
        bolsista_antigo = BolsistaProjeto.objects.filter(cpf=cpf_bolsista).first() if cpf_bolsista else None
        ch_total = (
            bolsista_antigo.carga_horaria_total
            if (bolsista_antigo and getattr(bolsista_antigo, 'carga_horaria_total', None))
            else (getattr(termo, 'carga_horaria_total', 0) or (termo.cota_pt.carga_horaria_semanal * 4 if hasattr(termo.cota_pt, 'carga_horaria_semanal') else 0))
        )
        contexto.update({
            'bolsista_nome': nome_bolsista,
            'bolsista_cpf': cpf_bolsista,
            'bolsista_rg': bolsista_antigo.rg if bolsista_antigo else 'N/I',
            'bolsista_email': (getattr(pessoa_bolsista, 'email', None) or (bolsista_antigo.email if bolsista_antigo else 'N/I')),
            'bolsista_fone': (getattr(pessoa_bolsista, 'telefone', None) or (bolsista_antigo.telefone if bolsista_antigo else 'N/I')),
            'bolsista_funcao': termo.cota_pt.perfil_funcao if termo.cota_pt else 'Pesquisador',
            'bolsista_termodebolsa': termo.numero_termo,
            'bolsista_contratacao': f"{termo.vigencia_inicio.strftime('%d/%m/%Y')} a {termo.vigencia_fim.strftime('%d/%m/%Y')}" if (termo.vigencia_inicio and termo.vigencia_fim) else 'N/I',
            'bolsista_ch': ch_total,
            'assinatura_bolsita': nome_bolsista,
        })
    else:
        bolsista = relatorio.bolsista
        contexto.update({
            # pyrefly: ignore [missing-attribute]
            'bolsista_nome': bolsista.nome_completo,
            # pyrefly: ignore [missing-attribute]
            'bolsista_cpf': bolsista.cpf,
            # pyrefly: ignore [missing-attribute]
            'bolsista_rg': bolsista.rg,
            # pyrefly: ignore [missing-attribute]
            'bolsista_email': bolsista.email,
            # pyrefly: ignore [missing-attribute]       
            'bolsista_fone': bolsista.telefone,
            # pyrefly: ignore [missing-attribute]
            'bolsista_funcao': bolsista.funcao, 
            # pyrefly: ignore [missing-attribute]
            'bolsista_termodebolsa': bolsista.termo_bolsa,
            # pyrefly: ignore [missing-attribute]
            'bolsista_contratacao': f"{bolsista.data_inicio.strftime('%d/%m/%Y')} a {bolsista.data_fim.strftime('%d/%m/%Y')}",
            # pyrefly: ignore [missing-attribute]
            'bolsista_ch': bolsista.carga_horaria_total,
            # pyrefly: ignore [missing-attribute]
            'assinatura_bolsita': bolsista.nome_completo,   
        })
        
    # Injeta variáveis de atividade (1 a 15) para liberdade no DOCX
    for i in range(1, 16):
        if i <= len(atividades_vinculadas):
            contexto[f'atividade_{i}'] = atividades_vinculadas[i-1].nome
        else:
            contexto[f'atividade_{i}'] = ""

    # Mantém um texto_atividades geral para caso queiram fallback
    texto_atividades = ""
    for atv in atividades_vinculadas:
        # pyrefly: ignore [missing-attribute]
        tarefas = relatorio.itens_atividade.filter(atividade_mae=atv)
        # pyrefly: ignore [missing-attribute]
        desc = " | ".join(t.descricao for t in tarefas) if tarefas.exists() else "Não se aplica"
        texto_atividades += f"- {atv.nome}: {desc}\n"
    contexto['atividade_mae_nome'] = texto_atividades

    return contexto

@login_required
def gerar_documento_relatorio(request, relatorio_id):
    """
    Injeta os dados no template institucional .docx utilizando docxtpl.
    Garante que a rastreabilidade patrimonial e administrativa siga as normas do IFAM.
    """
    relatorio = get_object_or_404(RelatorioAtividade, id=relatorio_id)
    contexto = montar_contexto_relatorio(relatorio.id) # type: ignore

    # Caminho seguro do template ajustado para a pasta "modelos"
    template_path = os.path.join(
        settings.BASE_DIR, 
        'gestao_projetos', 
        'modelos', 
        'Modelo_Relatório_Atividades.docx'
    )
    
    doc = DocxTemplate(template_path)
    doc.render(contexto)

    # Resposta HTTP configurada para download direto
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    # Calcula total de parcelas
    total_parcelas = relatorio.termo_bolsa.quantidade_parcelas if relatorio.termo_bolsa else getattr(relatorio.bolsista, 'total_parcelas_previstas', '?')
    # pyrefly: ignore [missing-attribute]
    nome_arquivo = f"Relatorio_Parcela_{relatorio.parcela_referencia.numero}_de_{total_parcelas}_{relatorio.bolsista.nome_completo.replace(' ', '_')}.docx"
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
    
    doc.save(response) # type: ignore
    return response

def auditar_pendencias_projeto(projeto):
    """
    Gera um relatório de conformidade do projeto.
    Retorna uma lista de pendências críticas que impedem a emissão de relatórios,
    garantindo que não haja liquidação de bolsas sem o devido lastro no Plano de Trabalho.
    """
    pendencias = []
    
    if not hasattr(projeto, 'planotrabalho') or not projeto.planotrabalho.arquivo_pdf:
        pendencias.append("O arquivo físico do Plano de Trabalho (PT) vigente não foi anexado.")
    
    if not projeto.vigencia_inicio or not projeto.vigencia_fim:
        pendencias.append("O período de vigência oficial do projeto não está definido.")
        
    if not projeto.atividades_plano.exists():
        pendencias.append("O Plano de Ação (Cronograma de Atividades) não foi desdobrado no sistema.")
        
    return pendencias

@login_required
def visualizar_relatorio(request, relatorio_id):
    """
    Gera o espelho HTML do relatório para pré-visualização.
    """
    relatorio = get_object_or_404(RelatorioAtividade, id=relatorio_id)
    
    # Trava de RBAC
    if relatorio.termo_bolsa:
        projeto = relatorio.termo_bolsa.cota_pt.projeto
    else:
        # pyrefly: ignore [missing-attribute]
        projeto = relatorio.bolsista.projeto
        
    if not request.user.is_superuser:
        if not MembroEquipe.objects.filter(projeto=projeto, usuario=request.user).exists():
            return HttpResponseForbidden("Acesso negado: Você não possui permissão administrativa neste projeto.")
        
    contexto = montar_contexto_relatorio(relatorio.id) # type: ignore
    contexto['relatorio_obj'] = relatorio # Passar objeto base
    
    # Estruturar atividades para renderização limpa no HTML
    atividades_html = []
    if relatorio.termo_bolsa:
        atvs = relatorio.termo_bolsa.cota_pt.atividades_vinculadas.all().order_by('numero')
    else:
        # pyrefly: ignore [missing-attribute]
        atvs = relatorio.bolsista.projeto.atividades_plano.all().order_by('numero')
        
    for atv in atvs:
        itens = relatorio.itens_atividade.filter(atividade_mae=atv) # type: ignore
        # Sempre incluir a atividade, mesmo se não houver tarefas (para mostrar no preview)
        atividades_html.append({
            'titulo': atv.nome,
            'itens': [{'descricao': i.descricao, 'carga': i.carga_horaria_percentual} for i in itens] if itens.exists() else []
        })
    contexto['atividades_html'] = atividades_html
    
    return render(request, 'gestao_projetos/visualizar_relatorio.html', contexto)

def alterar_relatorio(request, relatorio_id):
    from django.contrib import messages  # garante escopo em toda a função
    relatorio = get_object_or_404(RelatorioAtividade, id=relatorio_id)

    # ── Trava de Congelamento (Passo 6): relatório submetido ou homologado é imutável ──
    if relatorio.status in ['EM_ANALISE', 'CONCLUIDO']:
        messages.warning(
            request,
            "Este Relatório de Atividades já foi submetido ou homologado e está congelado. "
            "Não é possível realizar alterações após a submissão ou atesto do servidor."
        )
        return redirect('gestao_projetos:visualizar_relatorio', relatorio_id=relatorio_id)

    if request.method == 'POST':
        if 'arquivo_pdf' in request.FILES:
            relatorio.arquivo_pdf = request.FILES['arquivo_pdf']
        else:
            relatorio.arquivo_pdf = None # Se quiserem limpar
        relatorio.save()
        messages.success(request, 'Relatório atualizado com sucesso!')
        return redirect('gestao_projetos:listar_relatorios')
        
    return render(request, 'gestao_projetos/alterar_relatorio.html', {'relatorio': relatorio})

def sincronizar_macroentregas_relatorio(relatorio, request=None):
    """
    Calcula a intersecção temporal entre o período do relatório e as Macroentregas
    do projeto, vinculando-as automaticamente.
    """
    if relatorio.termo_bolsa:
        projeto = relatorio.termo_bolsa.cota_pt.projeto
    elif relatorio.bolsista:
        projeto = relatorio.bolsista.projeto
    else:
        return

    # Tenta obter a data de início real do plano de trabalho
    if not hasattr(projeto, 'planotrabalho') or not projeto.planotrabalho.data_inicio:
        if request:
            messages.warning(request, f"Relatório {relatorio.id}: O Projeto/Plano de Trabalho não possui Data de Início definida. Não foi possível calcular as Macroentregas automaticamente.")
        return

    data_inicio_plano = projeto.planotrabalho.data_inicio
    macroentregas_vinculadas = []

    # Busca todas as macroentregas do projeto
    macroentregas = Macroentrega.objects.filter(plano_trabalho=projeto.planotrabalho)
    
    if not macroentregas.exists():
        if request:
            messages.warning(request, f"Relatório {relatorio.id}: O Projeto não possui Macroentregas cadastradas no Cronograma.")
        return

    for m in macroentregas:
        # Calcula datas absolutas da macroentrega
        m_inicio = data_inicio_plano + relativedelta(months=m.mes_inicio_relativo - 1)
        m_fim = data_inicio_plano + relativedelta(months=m.mes_fim_relativo) - relativedelta(days=1)
        
        # Checa intersecção de datas
        if relatorio.periodo_inicio <= m_fim and m_inicio <= relatorio.periodo_fim:
            macroentregas_vinculadas.append(m)
            
    if macroentregas_vinculadas:
        relatorio.macroentregas.set(macroentregas_vinculadas)
    else:
        if request:
            messages.info(request, f"Relatório {relatorio.id}: Nenhuma Macroentrega coincidiu com o período ({relatorio.periodo_inicio.strftime('%d/%m/%Y')} a {relatorio.periodo_fim.strftime('%d/%m/%Y')}).")

@login_required
def criar_relatorio(request):
    """
    Interface unificada para geração de registros de relatórios (Individual ou em Lote).
    Permite escolher múltiplos Bolsistas (Termos) e múltiplas Parcelas.
    As datas de início e fim são extraídas automaticamente do Excel (Painel_bolsas.xlsx).
    """
    from cadastros.models import TermoBolsa, ProjetoPDI
    from .utils import obter_dados_parcela_excel
    from django.db.models import Max, Q
    
    projetos_permitidos = MembroEquipe.objects.filter(
        usuario=request.user
    ).values_list('projeto_id', flat=True)
    
    projetos = ProjetoPDI.objects.filter(id__in=projetos_permitidos).annotate(
        max_parcelas=Max('cotas_bolsas__termos_vinculados__quantidade_parcelas', filter=Q(cotas_bolsas__termos_vinculados__status='ATIVO'))
    )
    termos = TermoBolsa.objects.filter(
        cota_pt__projeto_id__in=projetos_permitidos,
        status='ATIVO'
    ).select_related('cota_pt__projeto').order_by('bolsista__nome')

    contexto = {
        'projetos': projetos,
        'termos': termos
    }

    if request.method == 'POST':
        termo_ids = request.POST.getlist('termo_id')
        parcela_nums = request.POST.getlist('parcela_num')
        
        if not termo_ids or not parcela_nums:
            messages.error(request, "Selecione pelo menos um Bolsista e uma Parcela.")
            return redirect('gestao_projetos:criar_relatorio')
            
        relatorios_criados = 0
        erros = []
        
        from cadastros.models import DistribuicaoContaCota
        
        for termo_id in termo_ids:
            termo = get_object_or_404(TermoBolsa, id=termo_id, cota_pt__projeto_id__in=projetos_permitidos)
            
            for p_str in parcela_nums:
                try:
                    p = int(p_str)
                except ValueError:
                    continue
                    
                if p > termo.quantidade_parcelas:
                    erros.append(f"Parcela {p} excede o limite do termo {termo.numero_termo}.")
                    continue
                    
                # Verifica se já existe para este termo e parcela
                if RelatorioAtividade.objects.filter(termo_bolsa=termo, parcela_referencia__numero=p).exists():
                    continue
                    
                dt_inicio, dt_fim, carga_horaria = obter_dados_parcela_excel(termo.numero_termo, p)
                if not dt_inicio or not dt_fim:
                    erros.append(f"Datas da Parcela {p} não encontradas no Excel para o Termo {termo.numero_termo}.")
                    continue
                    
                # Resolve a conta de pagamento
                conta_pagamento = None
                dist = DistribuicaoContaCota.objects.filter(
                    cota_pt=termo.cota_pt,
                    parcela_inicio__lte=p,
                    parcela_fim__gte=p
                ).first()
                if dist:
                    conta_pagamento = dist.conta_pagamento

                novo_relatorio = RelatorioAtividade.objects.create(
                    termo_bolsa=termo,
                    # pyrefly: ignore [missing-attribute]
                    parcela_referencia=termo.parcelas.get(numero=p),
                    versao=1,
                    periodo_inicio=dt_inicio,
                    periodo_fim=dt_fim,
                    carga_horaria_periodo=carga_horaria,
                    status='PENDENTE',
                    criado_por=request.user,
                    conta_pagamento=conta_pagamento
                )
                # Sincroniza as Macroentregas automaticamente
                sincronizar_macroentregas_relatorio(novo_relatorio, request)
                relatorios_criados += 1
                
        if relatorios_criados > 0:
            if erros:
                messages.warning(request, f"{relatorios_criados} relatório(s) gerado(s) com sucesso, mas ocorreram {len(erros)} erros (veja os logs ou tente novamente).")
            else:
                messages.success(request, f"{relatorios_criados} relatório(s) gerado(s) com sucesso!")
        else:
            if erros:
                messages.error(request, f"Nenhum relatório foi gerado. Erros encontrados: {', '.join(erros[:3])}")
            else:
                messages.info(request, "Nenhum novo relatório foi gerado. É possível que todos já existam.")
                
        return redirect('gestao_projetos:listar_relatorios')

    return render(request, 'gestao_projetos/criar_relatorio.html', contexto)

@login_required
def excluir_relatorio(request, relatorio_id):
    """
    Exclui fisicamente o rascunho do relatório.
    Trava de governança: Impede a exclusão de relatórios já concluídos/atestados.
    """
    relatorio = get_object_or_404(RelatorioAtividade, id=relatorio_id)
    
    # Trava de RBAC
    if relatorio.termo_bolsa:
        projeto = relatorio.termo_bolsa.cota_pt.projeto
    else:
        # pyrefly: ignore [missing-attribute]
        projeto = relatorio.bolsista.projeto
        
    if not MembroEquipe.objects.filter(projeto=projeto, usuario=request.user).exists():
        return HttpResponseForbidden("Acesso negado: Você não possui permissão neste projeto.")
        
    # Trava de Auditoria removida temporariamente a pedido da gestão,
    # pois o status "Concluído" ainda se refere à geração do DOCX, 
    # e não ao upload do PDF assinado.

    if request.method == 'POST':
        relatorio.delete()
        messages.success(request, "Rascunho excluído com sucesso.")
        return redirect('gestao_projetos:listar_relatorios')
        
    return render(request, 'gestao_projetos/confirmar_exclusao_relatorio.html', {'relatorio': relatorio})

@login_required
def listar_relatorios(request):
    """
    Exibe a listagem geral de relatórios com suporte a filtros dinâmicos
    por termo, número da parcela e status de tramitação.
    """
    relatorios = RelatorioAtividade.objects.select_related(
        'termo_bolsa', 
        'termo_bolsa__cota_pt__projeto'
    ).order_by('termo_bolsa__cota_pt__projeto__nome', 'termo_bolsa__pessoa__nome', 'parcela_referencia__numero', 'versao')

    # Captura dos parâmetros de filtro da URL (GET) com suporte a múltiplos valores
    if 'clear' in request.GET:
        if 'relatorios_filtros' in request.session:
            del request.session['relatorios_filtros']
        return redirect('gestao_projetos:listar_relatorios')

    if 'filter_applied' in request.GET:
        termo_ids = [t for t in request.GET.getlist('termo') if t.strip()]
        parcelas = [p for p in request.GET.getlist('parcela') if p.strip()]
        status_list = [s for s in request.GET.getlist('status') if s.strip()]
        request.session['relatorios_filtros'] = {
            'termo': termo_ids,
            'parcela': parcelas,
            'status': status_list
        }
    else:
        filtros = request.session.get('relatorios_filtros', {})
        termo_ids = filtros.get('termo', [])
        parcelas = filtros.get('parcela', [])
        status_list = filtros.get('status', [])

    # Aplicação incremental de filtros no queryset
    if termo_ids:
        relatorios = relatorios.filter(termo_bolsa_id__in=termo_ids)
    if parcelas:
        relatorios = relatorios.filter(parcela_referencia__numero__in=parcelas)
    if status_list:
        relatorios = relatorios.filter(status__in=status_list)

    from cadastros.models import TermoBolsa
    termos = TermoBolsa.objects.all().order_by('pessoa__nome')

    contexto = {
        'relatorios': relatorios,
        'termos': termos,
        'total_relatorios': relatorios.count(),
        'total_rascunhos': relatorios.filter(status='PENDENTE').count(),
        'total_concluidos': relatorios.filter(status='CONCLUIDO').count(),
        # Retorno dos estados atuais para manter a persistência visual nos selects (agora são listas)
        'filtro_termo': termo_ids,
        'filtro_parcela': parcelas,
        'filtro_status': status_list,
    }
    
    return render(request, 'gestao_projetos/listar_relatorios.html', contexto)

@login_required
def extrair_tabelas_docx_poc(request):
    """
    Prova de Conceito (PoC) para leitura de matrizes institucionais em .docx.
    Recebe o arquivo em memória e lista o conteúdo das tabelas no terminal
    para validar a viabilidade de extração do Plano de Ação (Cronograma).
    """
    contexto = {}
    
    if request.method == 'POST' and request.FILES.get('arquivo_docx'):
        arquivo = request.FILES['arquivo_docx']
        
        # Validação rígida de formato para segurança
        if not arquivo.name.endswith('.docx'):
            contexto['erro'] = "Formato inválido. Envie apenas arquivos .docx."
            return render(request, 'gestao_projetos/poc_upload.html', contexto)

        try:
            # Instancia o documento diretamente do arquivo em memória (InMemoryUploadedFile)
            documento = Document(arquivo)
            
            print(f"\n--- INÍCIO DA EXTRAÇÃO: {arquivo.name} ---")
            
            # Itera sobre todas as tabelas encontradas no documento
            for indice, tabela in enumerate(documento.tables, start=1):
                print(f"\n[ Tabela {indice} ]")
                
                for linha in tabela.rows:
                    # Extrai e higieniza o texto de cada célula (remove quebras de linha indesejadas)
                    dados_linha = [celula.text.strip().replace('\n', ' ') for celula in linha.cells]
                    print(" | ".join(dados_linha))
            
            print("--- FIM DA EXTRAÇÃO ---\n")
            
            contexto['sucesso'] = "Leitura concluída. Verifique o terminal do servidor (onde o runserver está rodando)."
            
        except Exception as e:
            contexto['erro'] = f"Erro no processamento do arquivo: {str(e)}"

    return render(request, 'gestao_projetos/poc_upload.html', contexto)

def importar_cronograma_projeto(request, projeto_id):
    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)
    
    # Prepara a fábrica de formsets (extra=0 para não criar linhas vazias sobressalentes)
    AtividadeFormSet = modelformset_factory(
        AtividadePlanoAcao, 
        form=AtividadePlanoAcaoForm, 
        extra=0, 
        can_delete=True
    )
    
    contexto = {'projeto': projeto}

    if request.method == 'POST':
        # ESTADO 2: O usuário enviou o arquivo .docx
        if 'arquivo_docx' in request.FILES:
            arquivo = request.FILES['arquivo_docx']
            resultado = extrair_atividades_texto_docx(arquivo)
            
            if 'erro' in resultado:
                messages.error(request, resultado['erro']) # type: ignore
                return redirect('gestao_projetos:importar_cronograma', projeto_id=projeto.id) # type: ignore
            
            # Recria o formset injetando os dados extraídos do Word
            dados_extraidos = resultado['sucesso']
            AtividadeFormSet = modelformset_factory(
                AtividadePlanoAcao, form=AtividadePlanoAcaoForm, extra=len(dados_extraidos)
            )
            formset = AtividadeFormSet(queryset=AtividadePlanoAcao.objects.none(), initial=dados_extraidos) # type: ignore
            
            contexto['formset'] = formset # type: ignore
            contexto['modo_revisao'] = True # type: ignore
            return render(request, 'gestao_projetos/importar_cronograma.html', contexto)
        
        # ESTADO 3: O usuário revisou o Formset e clicou em "Salvar"
        elif 'form-TOTAL_FORMS' in request.POST:

            formset = AtividadeFormSet(request.POST, queryset=AtividadePlanoAcao.objects.none())
                       
            if formset.is_valid():
                # Limpa as atividades anteriores do projeto para evitar duplicação em reimportações
                AtividadePlanoAcao.objects.filter(projeto=projeto).delete()
                
                atividades = formset.save(commit=False)
                for atividade in atividades:
                    # Amarra a atividade ao projeto antes de salvar no banco
                    atividade.projeto = projeto
                    atividade.save()
                
                # O bloco abaixo não é estritamente necessário agora que limpamos tudo, mas mantemos por segurança
                for atividade_deletada in formset.deleted_objects:
                    # activity is already deleted if it belonged to this project, but deleted_objects might be empty anyway
                    pass
                    
                messages.success(request, "Cronograma importado e salvo com sucesso.")
                return redirect('admin:cadastros_projetopdi_change', projeto.id) # type: ignore # Redireciona para o painel de gestão
            else:
                messages.error(request, "Corrija os erros no formulário antes de prosseguir.")
                contexto['formset'] = formset # type: ignore
                contexto['modo_revisao'] = True # type: ignore

    # ESTADO 1: Acesso inicial via GET (Exibe apenas a tela de upload)
    return render(request, 'gestao_projetos/importar_cronograma.html', contexto)

@login_required
def excluir_todos_relatorios(request):
    from django.shortcuts import redirect
    from django.contrib import messages
    from .models import RelatorioAtividade

    if request.method == 'POST':
        count, _ = RelatorioAtividade.objects.all().delete()
        messages.success(request, f'{count} relatórios foram excluídos com sucesso!')
    return redirect('gestao_projetos:listar_relatorios')

@login_required


@login_required
def baixar_relatorio_docx(request, relatorio_id):
    """
    Gera fisicamente o arquivo .docx baseado nos dados salvos e baixa.
    """
    from docxtpl import DocxTemplate
    
    relatorio = get_object_or_404(RelatorioAtividade, id=relatorio_id)
    
    # Trava de RBAC
    if relatorio.termo_bolsa:
        projeto = relatorio.termo_bolsa.cota_pt.projeto
    else:
        # pyrefly: ignore [missing-attribute]
        projeto = relatorio.bolsista.projeto
        
    if not MembroEquipe.objects.filter(projeto=projeto, usuario=request.user).exists():
        return HttpResponseForbidden("Acesso negado: Você não possui permissão.")

    contexto = montar_contexto_relatorio(relatorio.id)
    
    template_path = os.path.join(
        settings.BASE_DIR, 
        'gestao_projetos', 
        'modelos', 
        'Modelo_Relatório_Atividades.docx'
    )
    
    if not os.path.exists(template_path):
        return HttpResponseForbidden("Erro Interno: O template não foi encontrado.")
    
    doc = DocxTemplate(template_path)
    doc.render(contexto)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    if relatorio.termo_bolsa:
        # pyrefly: ignore [missing-attribute]
        # pyrefly: ignore [missing-attribute]
        bolsista_nome = relatorio.termo_bolsa.bolsista.nome
        # pyrefly: ignore [missing-attribute]
        total_parcelas = relatorio.termo_bolsa.quantidade_parcelas
    else:
        # pyrefly: ignore [missing-attribute]
        bolsista_nome = relatorio.bolsista.nome_completo
        # pyrefly: ignore [missing-attribute]
        total_parcelas = getattr(relatorio.bolsista, 'total_parcelas_previstas', '?')

    # pyrefly: ignore [missing-attribute]
    nome_arquivo = f"Relatorio_Atividades_{bolsista_nome.replace(' ', '_')}_Parcela_{relatorio.parcela_referencia.numero}_de_{total_parcelas}.docx"
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
    
    # pyrefly: ignore [bad-argument-type]
    doc.save(response)
    
    if request.GET.get('concluir') == '1':
        relatorio.status = 'CONCLUIDO'
        relatorio.save()
        
    return response

@login_required
def exportar_relatorios_zip(request):
    """
    Gera um arquivo ZIP contendo os rascunhos em DOCX com base nos filtros da listagem.
    """
    relatorios = RelatorioAtividade.objects.select_related(
        'termo_bolsa', 
        'termo_bolsa__cota_pt__projeto'
    ).order_by('termo_bolsa__cota_pt__projeto__convenio', 'termo_bolsa__bolsista__nome', 'parcela_referencia__numero', 'versao')

    # Captura dos parâmetros de filtro da URL (GET) com suporte a múltiplos valores
    if 'filter_applied' in request.GET:
        termo_ids = [t for t in request.GET.getlist('termo') if t.strip()]
        parcelas = [p for p in request.GET.getlist('parcela') if p.strip()]
        status_list = [s for s in request.GET.getlist('status') if s.strip()]
    else:
        filtros = request.session.get('relatorios_filtros', {})
        termo_ids = filtros.get('termo', [])
        parcelas = filtros.get('parcela', [])
        status_list = filtros.get('status', [])

    if termo_ids:
        relatorios = relatorios.filter(termo_bolsa_id__in=termo_ids)
    if parcelas:
        relatorios = relatorios.filter(parcela_referencia__numero__in=parcelas)
    if status_list:
        relatorios = relatorios.filter(status__in=status_list)
        
    # Trava de RBAC
    projetos_permitidos = MembroEquipe.objects.filter(
        usuario=request.user
    ).values_list('projeto_id', flat=True)
    
    relatorios = relatorios.filter(
        Q(termo_bolsa__cota_pt__projeto_id__in=projetos_permitidos) | 
        Q(bolsista__projeto_id__in=projetos_permitidos)
    )

    if not relatorios.exists():
        messages.warning(request, "Nenhum relatório encontrado para exportar com os filtros atuais.")
        return redirect('gestao_projetos:listar_relatorios')

    zip_buffer = io.BytesIO()
    
    template_path = os.path.join(
        settings.BASE_DIR, 
        'gestao_projetos', 
        'modelos', 
        'Modelo_Relatório_Atividades.docx'
    )
    if not os.path.exists(template_path):
        messages.error(request, "Erro Interno: Template de documento não encontrado.")
        return redirect('gestao_projetos:listar_relatorios')
        
    from docxtpl import DocxTemplate
        
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for relatorio in relatorios:
            contexto = montar_contexto_relatorio(relatorio.id)
            doc = DocxTemplate(template_path)
            doc.render(contexto)
            
            docx_buffer = io.BytesIO()
            doc.save(docx_buffer)
            
            if relatorio.termo_bolsa:
                bolsista_nome = relatorio.termo_bolsa.bolsista.nome
                total_parcelas = relatorio.termo_bolsa.quantidade_parcelas
            else:
                # pyrefly: ignore [missing-attribute]
                bolsista_nome = relatorio.bolsista.nome_completo
                total_parcelas = getattr(relatorio.bolsista, 'total_parcelas_previstas', '?')

            # pyrefly: ignore [missing-attribute]
            nome_arquivo = f"Relatorio_Atividades_{bolsista_nome.replace(' ', '_')}_Parcela_{relatorio.parcela_referencia.numero}_de_{total_parcelas}.docx"
            
            # Adiciona ao ZIP
            zip_file.writestr(nome_arquivo, docx_buffer.getvalue())

    zip_buffer.seek(0)
    
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="Relatorios_Pendentes.zip"'
    return response

from django.db.models import Sum

@login_required
def relatorio_orcamento_financeiro(request):
    from cadastros.models import ProjetoPDI, MembroEquipe, CotaBolsaPT, DistribuicaoContaCota
    
    projetos_permitidos = MembroEquipe.objects.filter(
        usuario=request.user
    ).values_list('projeto_id', flat=True)
    
    projetos = ProjetoPDI.objects.filter(id__in=projetos_permitidos)
    
    projeto_id = request.GET.get('projeto_id')
    projeto_selecionado = None
    cotas_dados = []
    contas_projeto = []
    
    if projeto_id:
        projeto_selecionado = get_object_or_404(ProjetoPDI, id=projeto_id, id__in=projetos_permitidos)
        # pyrefly: ignore [missing-attribute]
        contas_projeto = projeto_selecionado.contas.all()
        cotas = CotaBolsaPT.objects.filter(projeto=projeto_selecionado)
        
        for cota in cotas:
            distribuicoes = DistribuicaoContaCota.objects.filter(cota_pt=cota).order_by('parcela_inicio')
            
            # Organiza as distribuições por conta
            mapa_por_conta = {conta.id: [] for conta in contas_projeto}
            parcelas_mapeadas = 0
            
            for d in distribuicoes:
                parcelas_mapeadas += (d.parcela_fim - d.parcela_inicio + 1)
                texto = f"{d.parcela_inicio} a {d.parcela_fim}" if d.parcela_inicio != d.parcela_fim else f"{d.parcela_inicio}"
                if d.conta_pagamento_id in mapa_por_conta:
                    mapa_por_conta[d.conta_pagamento_id].append(texto)
                    
            # Constrói a lista paralela às contas do projeto para fácil iteração no template
            colunas_contas = []
            for conta in contas_projeto:
                textos = mapa_por_conta.get(conta.id, [])
                colunas_contas.append(", ".join(textos) if textos else "")
                
            status = 'OK'
            if parcelas_mapeadas < cota.parcelas_previstas:
                status = 'ALERTA'
            elif parcelas_mapeadas > cota.parcelas_previstas:
                status = 'ERRO'
                
            cotas_dados.append({
                'cota': cota,
                'colunas_contas': colunas_contas,
                'mapeadas': parcelas_mapeadas,
                'status': status
            })
            
    context = {
        'projetos': projetos,
        'projeto_selecionado': projeto_selecionado,
        'contas_projeto': contas_projeto,
        'cotas_dados': cotas_dados
    }
    
    return render(request, 'gestao_projetos/relatorio_orcamento_financeiro.html', context)

@login_required
def listar_termos_bolsa(request):
    from cadastros.models import TermoBolsa
    termos = TermoBolsa.objects.all().select_related('cota_pt__projeto').order_by('-vigencia_inicio')
    
    return render(request, 'gestao_projetos/listar_termos_bolsa.html', {
        'termos': termos,
    })

@login_required
def editar_termo_bolsa(request, termo_id):
    from cadastros.models import TermoBolsa
    from cadastros.forms import TermoBolsaForm
    termo = get_object_or_404(TermoBolsa, id=termo_id)
    
    if request.method == 'POST':
        form = TermoBolsaForm(request.POST, instance=termo)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Termo de Bolsa atualizado com sucesso!')
                return redirect('gestao_projetos:listar_termos_bolsa')
            except Exception as e:
                messages.error(request, f'Erro ao salvar: {e}')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = TermoBolsaForm(instance=termo)
        
    return render(request, 'gestao_projetos/editar_termo_bolsa.html', {
        'form': form,
        'termo': termo,
    })


# =====================================================================
# FOLHA MENSAL DE PAGAMENTO DE BOLSAS (Passo 2 — Execução Financeira)
# =====================================================================

@login_required
def folha_mensal_pagamentos(request):
    """
    Exibe a folha de pagamento mensal de bolsas por projeto e competência.
    Cruza parcelas, dados bancários da PessoaFisica, status do RA e KPIs financeiros.
    """
    from decimal import Decimal
    from cadastros.models import Parcela, ProjetoPDI, ContaBancaria

    if request.user.is_superuser:
        projetos = ProjetoPDI.objects.all().order_by('nome')
        projetos_permitidos = projetos.values_list('id', flat=True)
    else:
        projetos_permitidos = MembroEquipe.objects.filter(
            usuario=request.user
        ).values_list('projeto_id', flat=True)
        projetos = ProjetoPDI.objects.filter(id__in=projetos_permitidos).order_by('nome')

    # Filtros da requisição
    projeto_id = request.GET.get('projeto_id')
    mes_ano = request.GET.get('mes_ano')  # formato AAAA-MM

    # Padrão: mês corrente
    hoje = date.today()
    if not mes_ano:
        mes_ano = hoje.strftime('%Y-%m')

    try:
        ano, mes = int(mes_ano.split('-')[0]), int(mes_ano.split('-')[1])
    except (ValueError, IndexError):
        ano, mes = hoje.year, hoje.month
        mes_ano = hoje.strftime('%Y-%m')

    projeto_selecionado = None
    linhas_folha = []
    contas_projeto = []

    # KPIs
    total_folha = Decimal('0.00')
    total_liquidado = Decimal('0.00')
    qtd_ras_atestados = 0

    if projeto_id:
        if request.user.is_superuser:
            projeto_selecionado = get_object_or_404(ProjetoPDI, id=projeto_id)
        else:
            projeto_selecionado = get_object_or_404(ProjetoPDI, id=projeto_id, id__in=projetos_permitidos)
        contas_projeto = list(projeto_selecionado.contas.all())

        parcelas = Parcela.objects.filter(
            termo_bolsa__cota_pt__projeto=projeto_selecionado,
            mes_competencia__year=ano,
            mes_competencia__month=mes,
        ).select_related(
            'termo_bolsa__pessoa',
            'termo_bolsa__cota_pt',
            'conta_pagamento',
        ).order_by('termo_bolsa__pessoa__nome', 'numero')

        for parcela in parcelas:
            termo = parcela.termo_bolsa
            pessoa = termo.pessoa  # PessoaFisica

            # Dados bancários ativos (finalidade PAGAMENTO_BOLSA preferencial)
            dados_bancarios = None
            if pessoa:
                dados_bancarios = pessoa.dados_bancarios.filter(
                    ativo=True, finalidade='PAGAMENTO_BOLSA'
                ).first() or pessoa.dados_bancarios.filter(ativo=True).first()

            # Status do RA vinculado a esta parcela
            relatorio = None
            ra_status = None
            ra_status_label = None
            ra_status_badge = 'secondary'
            if hasattr(parcela, 'relatorios'):
                relatorio = parcela.relatorios.first()
                if relatorio:
                    ra_status = relatorio.status
                    if ra_status == 'CONCLUIDO':
                        ra_status_label = 'Atestado'
                        ra_status_badge = 'success'
                        qtd_ras_atestados += 1
                    else:
                        ra_status_label = 'Pendente'
                        ra_status_badge = 'danger'

            total_folha += parcela.valor or Decimal('0.00')
            if parcela.status == 'PAGO':
                total_liquidado += parcela.valor or Decimal('0.00')

            # Ofício mais recente vinculado a esta parcela (para badge de rastreabilidade)
            oficio_obj = parcela.oficios_conveniar.order_by('-criado_em').first() if hasattr(parcela, 'oficios_conveniar') else None

            linhas_folha.append({
                'parcela': parcela,
                'termo': termo,
                'pessoa': pessoa,
                'dados_bancarios': dados_bancarios,
                'relatorio': relatorio,
                'ra_status': ra_status,
                'ra_status_label': ra_status_label,
                'ra_status_badge': ra_status_badge,
                'tem_dados_bancarios': dados_bancarios is not None,
                'em_oficio': oficio_obj is not None,
                'oficio': oficio_obj,
            })

    saldo_pendente = total_folha - total_liquidado

    context = {
        'projetos': projetos,
        'projeto_selecionado': projeto_selecionado,
        'contas_projeto': contas_projeto,
        'linhas_folha': linhas_folha,
        'mes_ano': mes_ano,
        'total_folha': total_folha,
        'total_liquidado': total_liquidado,
        'saldo_pendente': saldo_pendente,
        'qtd_ras_atestados': qtd_ras_atestados,
        'qtd_parcelas': len(linhas_folha),
    }

    return render(request, 'gestao_projetos/folha_pagamento_mensal.html', context)


@login_required
def confirmar_pagamento_parcela(request, parcela_id):
    """
    Endpoint POST para registrar a liquidação financeira de uma parcela.
    Executa parcela.confirmar_pagamento() com data, conta e comprovante.
    """
    from cadastros.models import Parcela, ContaBancaria

    parcela = get_object_or_404(Parcela, id=parcela_id)
    projeto = parcela.termo_bolsa.cota_pt.projeto

    # Verificação de permissão RBAC (superuser tem bypass)
    if not request.user.is_superuser:
        if not MembroEquipe.objects.filter(projeto=projeto, usuario=request.user).exists():
            return HttpResponseForbidden("Acesso negado: Você não possui permissão neste projeto.")

    if request.method != 'POST':
        return redirect('gestao_projetos:folha_mensal_pagamentos')

    # Idempotência: parcela já paga não pode ser liquidada novamente
    if parcela.status == 'PAGO':
        messages.warning(request, f"A Parcela {parcela.numero} já foi liquidada em {parcela.data_pagamento}.")
        return _redirect_folha(request, projeto.id, parcela.mes_competencia)

    # Trava de Backend (Opção A): exige RA atestado (CONCLUIDO) por servidor SIAPE
    if not parcela.relatorios.filter(status='CONCLUIDO').exists():
        messages.error(
            request,
            "Liquidação bloqueada: O Relatório de Atividades (RA) precisa estar atestado por servidor SIAPE."
        )
        return _redirect_folha(request, projeto.id, parcela.mes_competencia)

    # Validação de dados bancários do bolsista
    pessoa = parcela.termo_bolsa.pessoa
    if pessoa and not pessoa.dados_bancarios.filter(ativo=True).exists():
        messages.error(
            request,
            "Liquidação bloqueada: O bolsista não possui dados bancários ativos cadastrados."
        )
        return _redirect_folha(request, projeto.id, parcela.mes_competencia)

    data_pagamento_str = request.POST.get('data_pagamento')
    conta_pagamento_id = request.POST.get('conta_pagamento_id')
    comprovante = request.FILES.get('comprovante_pagamento')

    # Validação da data
    from datetime import datetime
    try:
        data_pagamento = datetime.strptime(data_pagamento_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        messages.error(request, "Data de pagamento inválida.")
        return _redirect_folha(request, projeto.id, parcela.mes_competencia)

    # Validação do comprovante (extensões seguras)
    if comprovante:
        extensao = comprovante.name.rsplit('.', 1)[-1].lower()
        if extensao not in ('pdf', 'png', 'jpg', 'jpeg'):
            messages.error(request, "Formato de comprovante inválido. Use PDF, PNG, JPG ou JPEG.")
            return _redirect_folha(request, projeto.id, parcela.mes_competencia)

    # Conta bancária pagadora (opcional, deve pertencer ao projeto)
    conta = None
    if conta_pagamento_id:
        conta = ContaBancaria.objects.filter(id=conta_pagamento_id, projeto=projeto).first()

    parcela.confirmar_pagamento(
        data_pagamento=data_pagamento,
        conta=conta,
        comprovante=comprovante,
    )

    messages.success(
        request,
        f"Pagamento da Parcela {parcela.numero} de {parcela.termo_bolsa.pessoa.nome} confirmado com sucesso!"
    )
    return _redirect_folha(request, projeto.id, parcela.mes_competencia)


def _redirect_folha(request, projeto_id, mes_competencia):
    """Helper: redireciona de volta para a folha com os filtros preservados."""
    from django.urls import reverse
    mes_ano = mes_competencia.strftime('%Y-%m') if mes_competencia else date.today().strftime('%Y-%m')
    url = reverse('gestao_projetos:folha_mensal_pagamentos')
    return redirect(f"{url}?projeto_id={projeto_id}&mes_ano={mes_ano}")


# =====================================================================
# GERENCIADOR DE MATRIZES DOCX DO CONVENIAR (Passo 4)
# =====================================================================

# Constantes mantidas para compatibilidade retroativa com testes do Passo 4
# (OficiosConveniarTestCase importa estes nomes diretamente).
DIRETOR_POLO_NOME = "Alyson de Jesus dos Santos"
DIRETOR_POLO_CARGO = "Diretor-Geral do Polo de Inovação IFAM/Manaus"
REITOR_NOME = "Jaime Cavalcante Alves"
REITOR_CARGO = "Reitor do IFAM"


def _resolver_signatarios_oficio(tipo_documento, condicao_beneficiario, data_referencia=None):
    """
    Consulta a RegraAlcadaDocumento e resolve dinamicamente os signatários em exercício.
    Retorna (signatario_nome, signatario_cargo, visto_nome, visto_cargo) como strings.
    Fallback para as constantes fixas se a matriz não estiver populada.
    """
    from .models import RegraAlcadaDocumento
    from datetime import date as _date

    if data_referencia is None:
        data_referencia = _date.today()

    regra = RegraAlcadaDocumento.objects.filter(
        tipo_documento=tipo_documento,
        condicao_beneficiario=condicao_beneficiario,
        ativo=True
    ).select_related('funcao_requisitante', 'funcao_visto').first()

    if not regra:
        # Fallback: retorna as constantes fixas de acordo com o tipo
        if tipo_documento == 'OFICIO_COORD_DIRETOR_CAMPUS':
            return REITOR_NOME, REITOR_CARGO, DIRETOR_POLO_NOME, DIRETOR_POLO_CARGO
        return DIRETOR_POLO_NOME, DIRETOR_POLO_CARGO, "", ""

    req = regra.funcao_requisitante.obter_responsavel_em_exercicio(data_referencia)
    signatario_nome = req['nome']
    signatario_cargo = req['cargo_display']

    visto_nome, visto_cargo = "", ""
    if regra.funcao_visto:
        vis = regra.funcao_visto.obter_responsavel_em_exercicio(data_referencia)
        visto_nome = vis['nome']
        visto_cargo = vis['cargo_display']

    return signatario_nome, signatario_cargo, visto_nome, visto_cargo


@login_required
def listar_templates_conveniar(request):
    """Lista todos os templates DOCX cadastrados para o Conveniar/FAEPI."""
    from .models import TemplateDocumentoConveniar
    templates = TemplateDocumentoConveniar.objects.all()
    return render(request, 'gestao_projetos/templates_conveniar_list.html', {
        'templates': templates,
    })


@login_required
def novo_template_conveniar(request):
    """Upload de nova matriz DOCX para o Conveniar."""
    from .forms import TemplateDocumentoConveniarForm
    if request.method == 'POST':
        form = TemplateDocumentoConveniarForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save(commit=False)
            template.atualizado_por = request.user
            template.save()
            messages.success(request, f"Template '{template.nome}' cadastrado com sucesso!")
            return redirect('gestao_projetos:listar_templates_conveniar')
        else:
            messages.error(request, "Corrija os erros abaixo antes de continuar.")
    else:
        form = TemplateDocumentoConveniarForm()

    from .forms import TemplateDocumentoConveniarForm
    return render(request, 'gestao_projetos/templates_conveniar_form.html', {'form': form})


@login_required
def download_template_conveniar(request, template_id):
    """Download direto do arquivo DOCX de um template."""
    from .models import TemplateDocumentoConveniar
    template = get_object_or_404(TemplateDocumentoConveniar, id=template_id)
    if not template.arquivo_docx:
        messages.error(request, "Este template não possui arquivo associado.")
        return redirect('gestao_projetos:listar_templates_conveniar')
    response = HttpResponse(
        template.arquivo_docx.read(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    nome_arquivo = template.arquivo_docx.name.split('/')[-1]
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
    return response


def _proximo_numero_oficio(projeto, ano):
    """Retorna o próximo número sequencial de ofício para o projeto/ano."""
    from .models import OficioSolicitacao
    ultimo = OficioSolicitacao.objects.filter(projeto=projeto, ano=ano).order_by('-numero_sequencial').first()
    return (ultimo.numero_sequencial + 1) if ultimo else 1


@login_required
def gerar_oficio_pagamento_equipe(request):
    """
    Gera o Ofício de Pagamento da Equipe em lote para as parcelas selecionadas.
    Invariantes:
    - Apenas parcelas com RA CONCLUIDO.
    - Parcela ainda não despachada em ofício anterior.
    - Bolsista não é o Coordenador do Projeto.
    - Rateio automático por contas bancárias das fontes.
    """
    from cadastros.models import Parcela, ProjetoPDI
    from .models import TemplateDocumentoConveniar, OficioSolicitacao

    if request.method != 'POST':
        return redirect('gestao_projetos:folha_mensal_pagamentos')

    projeto_id = request.POST.get('projeto_id')
    mes_ano = request.POST.get('mes_ano', date.today().strftime('%Y-%m'))
    parcela_ids = request.POST.getlist('parcela_ids')

    if not projeto_id or not parcela_ids:
        messages.error(request, "Selecione pelo menos uma parcela e um projeto.")
        return redirect('gestao_projetos:folha_mensal_pagamentos')

    # Autorização
    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)
    if not request.user.is_superuser:
        if not MembroEquipe.objects.filter(projeto=projeto, usuario=request.user).exists():
            return HttpResponseForbidden("Acesso negado.")

    parcelas_validas = []
    erros = []
    coordenador_projeto = projeto.coordenador  # PessoaFisica ou None

    for pid in parcela_ids:
        try:
            parcela = Parcela.objects.select_related(
                'termo_bolsa__pessoa', 'termo_bolsa__cota_pt'
            ).get(id=int(pid), termo_bolsa__cota_pt__projeto=projeto)
        except (Parcela.DoesNotExist, ValueError):
            erros.append(f"Parcela ID {pid} não encontrada neste projeto.")
            continue

        pessoa = parcela.termo_bolsa.pessoa

        # Segregação do Coordenador
        if coordenador_projeto and pessoa and pessoa.id == coordenador_projeto.id:
            erros.append(f"Parcela {parcela.numero} ({pessoa.nome}): Coordenador não entra no ofício da equipe.")
            continue

        # Exige RA CONCLUIDO
        if not parcela.relatorios.filter(status='CONCLUIDO').exists():
            erros.append(f"Parcela {parcela.numero} ({pessoa.nome if pessoa else '?'}): RA não atestado.")
            continue

        # Idempotência: não pode estar em ofício anterior
        if parcela.oficios_conveniar.exists():
            erros.append(f"Parcela {parcela.numero} ({pessoa.nome if pessoa else '?'}): já despachada em ofício anterior.")
            continue

        parcelas_validas.append(parcela)

    if not parcelas_validas:
        messages.error(request, f"Nenhuma parcela válida para emissão. Erros: {'; '.join(erros[:3])}")
        return _redirect_folha(request, projeto_id, None)

    # Determina competência (primeiro dia do mês)
    try:
        ano_c, mes_c = int(mes_ano.split('-')[0]), int(mes_ano.split('-')[1])
        competencia = date(ano_c, mes_c, 1)
    except (ValueError, IndexError):
        competencia = date.today().replace(day=1)

    # Signatários via matriz de alçadas (Passo 5 — resolução dinâmica)
    if coordenador_projeto:
        # Quando há coordenador, ele é o requisitante
        signatario_nome = coordenador_projeto.nome
        signatario_cargo = "Coordenador do Projeto"
        _, __, visto_nome, visto_cargo = _resolver_signatarios_oficio(
            'OFICIO_EQUIPE', 'QUALQUER_BOLSISTA', competencia
        )
    else:
        signatario_nome, signatario_cargo, visto_nome, visto_cargo = _resolver_signatarios_oficio(
            'OFICIO_EQUIPE', 'QUALQUER_BOLSISTA', competencia
        )

    # Carrega template DOCX ativo para ofício de equipe (ou fallback)
    template_obj = TemplateDocumentoConveniar.objects.filter(
        tipo='OFICIO_EQUIPE', ativo=True
    ).order_by('-atualizado_em').first()

    # Cria OficioSolicitacao
    ano_oficio = date.today().year
    numero_oficio = _proximo_numero_oficio(projeto, ano_oficio)
    oficio = OficioSolicitacao.objects.create(
        projeto=projeto,
        template_utilizado=template_obj,
        numero_sequencial=numero_oficio,
        ano=ano_oficio,
        tipo='EQUIPE',
        competencia=competencia,
        signatario_nome=signatario_nome,
        signatario_cargo=signatario_cargo,
        coordenador_is_diretor_campus=False,
        visto_nome=visto_nome,
        visto_cargo=visto_cargo,
        criado_por=request.user,
    )
    oficio.parcelas.set(parcelas_validas)

    # Monta DOCX com docxtpl (fallback simples se template não existir)
    contexto_docx = _montar_contexto_oficio_equipe(oficio, parcelas_validas, projeto)
    arquivo_docx_gerado = _gerar_docx_oficio(template_obj, contexto_docx, 'Modelo_Oficio_Pagamento_Equipe.docx')

    if arquivo_docx_gerado:
        from django.core.files.base import ContentFile
        nome_arquivo = f"Oficio_{numero_oficio}_{ano_oficio}_Equipe_{projeto.id}.docx"
        oficio.arquivo_docx.save(nome_arquivo, ContentFile(arquivo_docx_gerado), save=True)

    aviso_erros = f" ({len(erros)} parcela(s) ignorada(s))" if erros else ""
    messages.success(
        request,
        f"Ofício nº {numero_oficio}/{ano_oficio} gerado com {len(parcelas_validas)} parcela(s).{aviso_erros}"
    )
    return redirect('gestao_projetos:download_oficio', oficio_id=oficio.id)


@login_required
def gerar_oficio_pagamento_coordenador(request):
    """
    Gera o Ofício de Pagamento individual do Coordenador do Projeto.
    Alçada:
    - coordenador_is_diretor_campus=True  → Requisitante = Reitor
    - coordenador_is_diretor_campus=False → Requisitante = Diretor do Polo
    """
    from cadastros.models import Parcela, ProjetoPDI
    from .models import TemplateDocumentoConveniar, OficioSolicitacao

    if request.method != 'POST':
        return redirect('gestao_projetos:folha_mensal_pagamentos')

    projeto_id = request.POST.get('projeto_id')
    mes_ano = request.POST.get('mes_ano', date.today().strftime('%Y-%m'))
    parcela_id = request.POST.get('parcela_coordenador_id')
    is_diretor_campus = request.POST.get('coordenador_is_diretor_campus') == '1'

    if not projeto_id or not parcela_id:
        messages.error(request, "Dados insuficientes para geração do ofício do Coordenador.")
        return redirect('gestao_projetos:folha_mensal_pagamentos')

    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)
    if not request.user.is_superuser:
        if not MembroEquipe.objects.filter(projeto=projeto, usuario=request.user).exists():
            return HttpResponseForbidden("Acesso negado.")

    parcela = get_object_or_404(Parcela, id=int(parcela_id), termo_bolsa__cota_pt__projeto=projeto)

    # Exige RA CONCLUIDO
    if not parcela.relatorios.filter(status='CONCLUIDO').exists():
        messages.error(request, "RA da parcela do Coordenador não está atestado.")
        return _redirect_folha(request, projeto_id, parcela.mes_competencia)

    # Idempotência
    if parcela.oficios_conveniar.exists():
        messages.warning(request, "Esta parcela do Coordenador já foi despachada em ofício anterior.")
        return _redirect_folha(request, projeto_id, parcela.mes_competencia)

    # Competência — calculada antes da resolução de alçada
    try:
        ano_c, mes_c = int(mes_ano.split('-')[0]), int(mes_ano.split('-')[1])
        competencia = date(ano_c, mes_c, 1)
    except (ValueError, IndexError):
        competencia = date.today().replace(day=1)

    # Alçada via matriz dinâmica (Passo 5)
    if is_diretor_campus:
        signatario_nome, signatario_cargo, visto_nome, visto_cargo = _resolver_signatarios_oficio(
            'OFICIO_COORD_DIRETOR_CAMPUS', 'COORDENADOR_E_DIRETOR_CAMPUS', competencia
        )
    else:
        signatario_nome, signatario_cargo, visto_nome, visto_cargo = _resolver_signatarios_oficio(
            'OFICIO_COORDENADOR', 'COORDENADOR_PROJETO', competencia
        )

    template_obj = TemplateDocumentoConveniar.objects.filter(
        tipo='OFICIO_COORDENADOR', ativo=True
    ).order_by('-atualizado_em').first()

    ano_oficio = date.today().year
    numero_oficio = _proximo_numero_oficio(projeto, ano_oficio)
    oficio = OficioSolicitacao.objects.create(
        projeto=projeto,
        template_utilizado=template_obj,
        numero_sequencial=numero_oficio,
        ano=ano_oficio,
        tipo='COORDENADOR',
        competencia=competencia,
        signatario_nome=signatario_nome,
        signatario_cargo=signatario_cargo,
        coordenador_is_diretor_campus=is_diretor_campus,
        visto_nome=visto_nome,
        visto_cargo=visto_cargo,
        criado_por=request.user,
    )
    oficio.parcelas.set([parcela])

    contexto_docx = _montar_contexto_oficio_coordenador(oficio, parcela, projeto)
    arquivo_docx_gerado = _gerar_docx_oficio(template_obj, contexto_docx, 'Modelo_Oficio_Pagamento_Coordenador.docx')

    if arquivo_docx_gerado:
        from django.core.files.base import ContentFile
        nome_arquivo = f"Oficio_{numero_oficio}_{ano_oficio}_Coordenador_{projeto.id}.docx"
        oficio.arquivo_docx.save(nome_arquivo, ContentFile(arquivo_docx_gerado), save=True)

    messages.success(request, f"Ofício nº {numero_oficio}/{ano_oficio} do Coordenador gerado com sucesso!")
    return redirect('gestao_projetos:download_oficio', oficio_id=oficio.id)


@login_required
def download_oficio(request, oficio_id):
    """Download do DOCX de um ofício já emitido."""
    from .models import OficioSolicitacao
    oficio = get_object_or_404(OficioSolicitacao, id=oficio_id)

    if not request.user.is_superuser:
        if not MembroEquipe.objects.filter(projeto=oficio.projeto, usuario=request.user).exists():
            return HttpResponseForbidden("Acesso negado.")

    if not oficio.arquivo_docx:
        messages.error(request, "Este ofício não possui arquivo DOCX gerado.")
        return _redirect_folha(request, oficio.projeto.id, oficio.competencia)

    response = HttpResponse(
        oficio.arquivo_docx.read(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    nome = oficio.arquivo_docx.name.split('/')[-1]
    response['Content-Disposition'] = f'attachment; filename="{nome}"'
    return response


# ---- Helpers privados de montagem DOCX --------------------------------

def _montar_contexto_oficio_equipe(oficio, parcelas, projeto):
    """Constrói o dicionário de contexto para o template docxtpl do ofício de equipe."""
    linhas = []
    for parcela in parcelas:
        pessoa = parcela.termo_bolsa.pessoa
        dado_bancario = None
        if pessoa:
            dado_bancario = pessoa.dados_bancarios.filter(ativo=True, finalidade='PAGAMENTO_BOLSA').first() \
                            or pessoa.dados_bancarios.filter(ativo=True).first()
        linhas.append({
            'nome': pessoa.nome if pessoa else '—',
            'cpf': pessoa.cpf if pessoa else '—',
            'funcao': parcela.termo_bolsa.cota_pt.perfil_funcao,
            'numero_termo': parcela.termo_bolsa.numero_termo,
            'parcela': f"{parcela.numero}/{parcela.termo_bolsa.quantidade_parcelas}",
            'valor': f"R$ {parcela.valor:.2f}".replace('.', ','),
            'banco': dado_bancario.banco_codigo if dado_bancario else '—',
            'agencia': dado_bancario.agencia if dado_bancario else '—',
            'conta': dado_bancario.conta if dado_bancario else '—',
            'pix': dado_bancario.chave_pix if dado_bancario else '—',
            'conta_pagadora': str(parcela.conta_pagamento) if parcela.conta_pagamento else '—',
        })

    total = sum(p.valor for p in parcelas)
    return {
        'numero_oficio': f"{oficio.numero_sequencial}/{oficio.ano}",
        'competencia': oficio.competencia.strftime('%B de %Y'),
        'projeto_nome': projeto.nome,
        'signatario_nome': oficio.signatario_nome,
        'signatario_cargo': oficio.signatario_cargo,
        'visto_nome': oficio.visto_nome,
        'visto_cargo': oficio.visto_cargo,
        'linhas': linhas,
        'total_geral': f"R$ {total:.2f}".replace('.', ','),
        'data_geracao': date.today().strftime('%d/%m/%Y'),
    }


def _montar_contexto_oficio_coordenador(oficio, parcela, projeto):
    """Constrói o dicionário de contexto para o template do ofício do coordenador."""
    pessoa = parcela.termo_bolsa.pessoa
    dado_bancario = None
    if pessoa:
        dado_bancario = pessoa.dados_bancarios.filter(ativo=True, finalidade='PAGAMENTO_BOLSA').first() \
                        or pessoa.dados_bancarios.filter(ativo=True).first()
    return {
        'numero_oficio': f"{oficio.numero_sequencial}/{oficio.ano}",
        'competencia': oficio.competencia.strftime('%B de %Y'),
        'projeto_nome': projeto.nome,
        'coordenador_nome': pessoa.nome if pessoa else '—',
        'coordenador_cpf': pessoa.cpf if pessoa else '—',
        'funcao': parcela.termo_bolsa.cota_pt.perfil_funcao,
        'numero_termo': parcela.termo_bolsa.numero_termo,
        'parcela': f"{parcela.numero}/{parcela.termo_bolsa.quantidade_parcelas}",
        'valor': f"R$ {parcela.valor:.2f}".replace('.', ','),
        'banco': dado_bancario.banco_codigo if dado_bancario else '—',
        'agencia': dado_bancario.agencia if dado_bancario else '—',
        'conta': dado_bancario.conta if dado_bancario else '—',
        'pix': dado_bancario.chave_pix if dado_bancario else '—',
        'signatario_nome': oficio.signatario_nome,
        'signatario_cargo': oficio.signatario_cargo,
        'visto_nome': oficio.visto_nome,
        'visto_cargo': oficio.visto_cargo,
        'data_geracao': date.today().strftime('%d/%m/%Y'),
    }


def _gerar_docx_oficio(template_obj, contexto, nome_fallback):
    """
    Tenta renderizar o DOCX com docxtpl a partir do template cadastrado.
    Se não houver template ou arquivo, tenta o fallback estático em gestao_projetos/modelos/.
    Retorna os bytes do arquivo ou None se não houver template disponível.
    """
    import os
    from io import BytesIO

    template_path = None

    if template_obj and template_obj.arquivo_docx:
        template_path = template_obj.arquivo_docx.path
    else:
        fallback = os.path.join(
            settings.BASE_DIR, 'gestao_projetos', 'modelos', nome_fallback
        )
        if os.path.exists(fallback):
            template_path = fallback

    if not template_path:
        return None  # Sem template disponível — ofício gravado sem DOCX

    try:
        from docxtpl import DocxTemplate
        doc = DocxTemplate(template_path)
        doc.render(contexto)
        buf = BytesIO()
        doc.save(buf)
        return buf.getvalue()
    except Exception:
        return None


# =====================================================================
# SUBMISSÃO DO RELATÓRIO DE ATIVIDADES (Passo 6 — Esteira de Prestação de Contas)
# =====================================================================

@login_required
def submeter_relatorio(request, relatorio_id):
    """
    Submissão do relatório pelo bolsista para atesto SIAPE.

    Regras de negócio implementadas:
    1. Método exclusivo POST (redireciona em GET).
    2. RBAC: apenas o bolsista vinculado, criador do relatório ou membro da equipe.
    3. Validação de Conteúdo Mínimo: exige itens de atividade ou PDF assinado.
    4. Transição Atômica: relatorio.status e parcela.status atualizados juntos.
    """
    from django.db import transaction

    relatorio = get_object_or_404(RelatorioAtividade, id=relatorio_id)

    # ── Redireciona em GET ──
    if request.method != 'POST':
        return redirect('gestao_projetos:visualizar_relatorio', relatorio_id=relatorio_id)

    # ── Resolve o projeto para RBAC ──
    if relatorio.termo_bolsa:
        projeto = relatorio.termo_bolsa.cota_pt.projeto
        bolsista_pessoa = relatorio.termo_bolsa.pessoa
    else:
        projeto = relatorio.bolsista.projeto  # type: ignore[union-attr]
        bolsista_pessoa = None  # Fallback legado

    # ── RBAC: bolsista vinculado, criador ou membro da equipe ──
    tem_permissao = False
    if request.user.is_superuser:
        tem_permissao = True
    elif request.user == relatorio.criado_por:
        tem_permissao = True
    elif bolsista_pessoa and bolsista_pessoa.user_id == request.user.pk:
        tem_permissao = True
    elif MembroEquipe.objects.filter(projeto=projeto, usuario=request.user).exists():
        tem_permissao = True

    if not tem_permissao:
        return HttpResponseForbidden("Acesso negado: Você não tem permissão para submeter este relatório.")

    # ── Validação de Conteúdo Mínimo ──
    if not relatorio.itens_atividade.exists() and not relatorio.arquivo_pdf:
        messages.error(
            request,
            "Não é possível submeter um relatório vazio. Adicione itens de atividade ou anexe o PDF assinado."
        )
        return redirect('gestao_projetos:visualizar_relatorio', relatorio_id=relatorio_id)

    # ── Idempotência: já está em análise ou concluído ──
    if relatorio.status in ['EM_ANALISE', 'CONCLUIDO']:
        messages.info(request, "Este relatório já foi submetido ou está homologado.")
        return redirect('gestao_projetos:visualizar_relatorio', relatorio_id=relatorio_id)

    # ── Transição Atômica ──
    with transaction.atomic():
        relatorio.status = 'EM_ANALISE'
        relatorio.save()

        if relatorio.parcela_referencia:
            relatorio.parcela_referencia.status = 'EM_ANALISE'
            relatorio.parcela_referencia.save()

    messages.success(
        request,
        "Relatório submetido com sucesso! Aguardando atesto do servidor SIAPE."
    )
    return redirect('gestao_projetos:visualizar_relatorio', relatorio_id=relatorio_id)


# =====================================================================
# ATESTO SIAPE DO RELATÓRIO DE ATIVIDADES (Passo 6 — Execução Financeira)
# =====================================================================

@login_required
def atestar_relatorio(request, relatorio_id):
    """
    Passo 6 — Homologação do Relatório de Atividades por Servidor Efetivo SIAPE.

    Regras de negócio implementadas:
    1. Decorator @servidor_efetivo_required: apenas servidores com SIAPE ativo podem
       acessar esta view (PermissionDenied para os demais).
    2. Segregação de Funções (SoD): o servidor logado não pode ser o próprio bolsista
       do relatório — auto-atesto é vedado.
    3. Idempotência: relatório já CONCLUIDO não pode ser atestado novamente.
    4. RBAC: apenas membros da equipe do projeto (ou superusuários) têm acesso.
    5. POST recebe cumpriu_carga_horaria e parecer_coordenador; grava atestado_por,
       data_atesto, siape_atesto e muda status para CONCLUIDO.
    6. Sincronização atômica com Parcela: atualiza parcela.status para APROVADO.
    """
    from cadastros.decorators import servidor_efetivo_required
    from django.utils import timezone
    from django.db import transaction

    # Aplica o decorator de servidor SIAPE programaticamente (permite uso em testes)
    relatorio = get_object_or_404(RelatorioAtividade, id=relatorio_id)

    # ── Resolve o projeto para RBAC ──
    if relatorio.termo_bolsa:
        projeto = relatorio.termo_bolsa.cota_pt.projeto
    else:
        projeto = relatorio.bolsista.projeto  # type: ignore[union-attr]

    # ── RBAC: membro da equipe ou superusuário ──
    if not request.user.is_superuser:
        if not MembroEquipe.objects.filter(projeto=projeto, usuario=request.user).exists():
            return HttpResponseForbidden("Acesso negado: Você não é membro da equipe deste projeto.")

    # ── Verificação de Servidor Efetivo SIAPE ──
    siape = None
    pessoa_fisica = getattr(request.user, 'pessoa_fisica', None)
    if pessoa_fisica and pessoa_fisica.is_servidor and pessoa_fisica.siape:
        siape = pessoa_fisica.siape
    else:
        # Fallback legado (PerfilUsuario do almoxarifado)
        perfil = getattr(request.user, 'perfil', None)
        if perfil and perfil.vinculo == 'SERVIDOR' and perfil.siape:
            siape = perfil.siape

    if not siape:
        messages.error(
            request,
            "Acesso Negado: Esta operação é restrita a Servidores Efetivos com matrícula SIAPE ativa."
        )
        return redirect('gestao_projetos:visualizar_relatorio', relatorio_id=relatorio_id)

    # ── Idempotência: já atestado ──
    if relatorio.status == 'CONCLUIDO':
        messages.info(request, "Este Relatório já está homologado.")
        return redirect('gestao_projetos:visualizar_relatorio', relatorio_id=relatorio_id)

    # ── Permite atesto se status for EM_ANALISE ou PENDENTE ──
    if relatorio.status not in ['EM_ANALISE', 'PENDENTE']:
        messages.warning(
            request,
            "Este relatório não está em um estado que permite atesto (status atual: {}).".format(
                relatorio.get_status_display()
            )
        )
        return redirect('gestao_projetos:visualizar_relatorio', relatorio_id=relatorio_id)

    # ── Segregação de Funções: impede auto-atesto do bolsista ──
    bolsista_pessoa_fisica = None
    if relatorio.termo_bolsa:
        bolsista_pessoa_fisica = relatorio.termo_bolsa.pessoa  # PessoaFisica (campo correto)
    if bolsista_pessoa_fisica and bolsista_pessoa_fisica.user_id == request.user.pk:
        messages.error(
            request,
            "Segregação de Funções violada: O servidor logado é o próprio bolsista deste relatório. "
            "O atesto deve ser realizado por um servidor diferente do beneficiário."
        )
        return redirect('gestao_projetos:visualizar_relatorio', relatorio_id=relatorio_id)

    if request.method != 'POST':
        return redirect('gestao_projetos:visualizar_relatorio', relatorio_id=relatorio_id)

    # ── Grava o atesto com transação atômica ──
    cumpriu = request.POST.get('cumpriu_carga_horaria') == '1'
    parecer = request.POST.get('parecer_coordenador', '').strip()

    with transaction.atomic():
        relatorio.cumpriu_carga_horaria = cumpriu
        relatorio.parecer_coordenador = parecer or 'Desempenho satisfatório alinhado às metas do projeto.'
        relatorio.atestado_por = request.user
        relatorio.data_atesto = timezone.now()
        relatorio.siape_atesto = siape
        relatorio.status = 'CONCLUIDO'
        relatorio.save()

        # Sincronização atômica com Parcela
        if relatorio.parcela_referencia:
            relatorio.parcela_referencia.status = 'APROVADO'
            relatorio.parcela_referencia.save()

    messages.success(
        request,
        f"Relatório homologado com sucesso! Atesto registrado pelo servidor SIAPE {siape}."
    )
    return redirect('gestao_projetos:visualizar_relatorio', relatorio_id=relatorio_id)


# =====================================================================
# PAINEL DE GOVERNANÇA DE ALÇADAS (Passo 5)
# =====================================================================

@login_required
def painel_governanca_alcadas(request):
    """
    Painel visual de governança institucional: matriz de alçadas, ocupações
    ativas com substitutos e afastamentos vigentes.
    """
    from .models import (
        FuncaoInstitucional, OcupacaoFuncao,
        AfastamentoExercicio, RegraAlcadaDocumento
    )
    from datetime import date as _date

    hoje = _date.today()

    funcoes = FuncaoInstitucional.objects.filter(ativo=True).prefetch_related(
        'ocupacoes', 'regras_como_requisitante', 'regras_como_visto'
    ).order_by('nome_cargo')

    # Para cada função, resolve quem está em exercício hoje
    funcoes_com_responsavel = []
    for f in funcoes:
        responsavel = f.obter_responsavel_em_exercicio(hoje)
        funcoes_com_responsavel.append({
            'funcao': f,
            'responsavel': responsavel,
        })

    ocupacoes = OcupacaoFuncao.objects.filter(ativo=True).select_related('funcao', 'pessoa').order_by('funcao__nome_cargo', 'prioridade')

    afastamentos_vigentes = AfastamentoExercicio.objects.filter(
        data_inicio__lte=hoje,
        data_fim__gte=hoje,
        ativo=True
    ).select_related('ocupacao__funcao', 'ocupacao__pessoa').order_by('data_fim')

    regras = RegraAlcadaDocumento.objects.filter(ativo=True).select_related(
        'funcao_requisitante', 'funcao_visto'
    ).order_by('tipo_documento', 'condicao_beneficiario')

    context = {
        'funcoes_com_responsavel': funcoes_com_responsavel,
        'ocupacoes': ocupacoes,
        'afastamentos_vigentes': afastamentos_vigentes,
        'regras': regras,
        'hoje': hoje,
    }
    return render(request, 'gestao_projetos/governanca_alcadas.html', context)


# =====================================================================
# LIQUIDAÇÃO E BAIXA EM LOTE DA FOLHA DE BOLSAS (Passo 7)
# =====================================================================

@login_required
def liquidar_folha_lote(request, projeto_id):
    """
    Passo 7 — Liquidação e Baixa em Lote das Parcelas de Bolsas.

    Regras de negócio:
    1. Apenas POST; GET redireciona para a folha.
    2. RBAC: membro da equipe do projeto ou superusuário.
    3. Trava de Integridade: TODAS as parcelas selecionadas devem ter RA
       com status='CONCLUIDO'. Qualquer parcela com RA pendente ou ausente
       aborta toda a operação com mensagem de erro (fail-fast).
    4. Trava de Idempotência: parcelas já PAGAS são silenciosamente ignoradas
       (não contam como erro, apenas puladas).
    5. Validação do arquivo de comprovante (extensões seguras).
    6. Execução dentro de transaction.atomic(): ou tudo é confirmado, ou nada.
    7. Mensagem de sucesso com quantidade e valor total liquidado.
    """
    from decimal import Decimal
    from datetime import datetime
    from django.db import transaction
    from django.urls import reverse as _url_reverse
    from cadastros.models import Parcela, ProjetoPDI, ContaBancaria

    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)

    # ── RBAC ──
    if not request.user.is_superuser:
        if not MembroEquipe.objects.filter(projeto=projeto, usuario=request.user).exists():
            return HttpResponseForbidden("Acesso negado: Você não é membro da equipe deste projeto.")

    # ── Aceita apenas POST ──
    if request.method != 'POST':
        return _redirect_folha_lote(projeto_id)

    # ── Coleta e valida os parâmetros ──
    parcela_ids = request.POST.getlist('parcelas_ids')
    data_pagamento_str = request.POST.get('data_pagamento', '').strip()
    conta_id = request.POST.get('conta_pagamento', '').strip()
    comprovante = request.FILES.get('comprovante_pagamento')

    if not parcela_ids:
        messages.error(request, "Selecione pelo menos uma parcela para liquidar em lote.")
        return _redirect_folha_lote(projeto_id)

    # Valida data
    try:
        data_pagamento = datetime.strptime(data_pagamento_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        messages.error(request, "Data de pagamento inválida.")
        return _redirect_folha_lote(projeto_id)

    # Valida extensão do comprovante
    if comprovante:
        extensao = comprovante.name.rsplit('.', 1)[-1].lower()
        if extensao not in ('pdf', 'png', 'jpg', 'jpeg'):
            messages.error(request, "Formato de comprovante inválido. Use PDF, PNG, JPG ou JPEG.")
            return _redirect_folha_lote(projeto_id)

    # Conta pagadora (opcional)
    conta = None
    if conta_id:
        conta = ContaBancaria.objects.filter(id=conta_id, projeto=projeto).first()

    # ── Carrega parcelas e aplica a Trava de Integridade ──
    try:
        ids_int = [int(pid) for pid in parcela_ids]
    except ValueError:
        messages.error(request, "IDs de parcelas inválidos.")
        return _redirect_folha_lote(projeto_id)

    parcelas_qs = Parcela.objects.filter(
        id__in=ids_int,
        termo_bolsa__cota_pt__projeto=projeto,
    ).select_related('termo_bolsa__pessoa')

    if parcelas_qs.count() != len(ids_int):
        messages.error(request, "Uma ou mais parcelas não pertencem a este projeto.")
        return _redirect_folha_lote(projeto_id)

    # Trava de Integridade: verifica RA CONCLUIDO em TODAS as parcelas não-PAGAS
    parcelas_sem_ra = []
    parcelas_a_liquidar = []

    for parcela in parcelas_qs:
        if parcela.status == 'PAGO':
            continue  # Idempotência: ignora parcelas já liquidadas

        tem_ra_concluido = parcela.relatorios.filter(status='CONCLUIDO').exists()
        if not tem_ra_concluido:
            nome = parcela.termo_bolsa.pessoa.nome if parcela.termo_bolsa.pessoa else '?'
            parcelas_sem_ra.append(f"Parcela {parcela.numero} ({nome})")
        else:
            parcelas_a_liquidar.append(parcela)

    # Fail-fast: qualquer RA pendente aborta toda a operação
    if parcelas_sem_ra:
        messages.error(
            request,
            "Operação cancelada — as seguintes parcelas não possuem RA homologado: "
            + ", ".join(parcelas_sem_ra)
            + ". Ateste todos os Relatórios de Atividades antes de realizar a baixa em lote."
        )
        return _redirect_folha_lote(projeto_id)

    if not parcelas_a_liquidar:
        messages.info(request, "Todas as parcelas selecionadas já estavam liquidadas.")
        return _redirect_folha_lote(projeto_id)

    # ── Executa a liquidação em transação atômica ──
    total_liquidado = Decimal('0.00')
    qtd_liquidadas = 0

    with transaction.atomic():
        for parcela in parcelas_a_liquidar:
            parcela.confirmar_pagamento(
                data_pagamento=data_pagamento,
                conta=conta,
                comprovante=comprovante,
            )
            total_liquidado += parcela.valor or Decimal('0.00')
            qtd_liquidadas += 1

    messages.success(
        request,
        f"{qtd_liquidadas} parcela(s) liquidada(s) com sucesso! "
        f"Valor total baixado: R$ {total_liquidado:,.2f}."
    )
    return _redirect_folha_lote(projeto_id)


def _redirect_folha_lote(projeto_id):
    """Helper: redireciona para a folha de pagamentos preservando o projeto."""
    from django.urls import reverse as _reverse
    url = _reverse('gestao_projetos:folha_mensal_pagamentos')
    return redirect(f"{url}?projeto_id={projeto_id}")


# =====================================================================
# RECIBO INDIVIDUAL DE PAGAMENTO DE BOLSA (Passo 8)
# =====================================================================

@login_required
def visualizar_recibo_bolsa(request, parcela_id):
    """
    Passo 8 — Emissão do Recibo Individual de Pagamento de Bolsa.

    Regras de negócio:
    1. Trava de Status: apenas parcelas com status='PAGO' geram recibo.
       Parcelas PENDENTE/EM_ANALISE/APROVADO/CANCELADO são rejeitadas com
       mensagem de erro e redirecionamento para a folha.
    2. RBAC triplo:
       a) Bolsista titular: parcela.termo_bolsa.pessoa.user_id == request.user.id
       b) Coordenador do projeto: projeto.coordenador.user_id == request.user.id
       c) Superusuário: bypass total
       d) Qualquer outro: 403 Forbidden
    3. Chave de autenticidade SHA-256 (16 hex upper): blindagem documental.
    4. Dados bancários ativos do bolsista são injetados no contexto.
    """
    import hashlib
    from cadastros.models import Parcela

    parcela = get_object_or_404(
        Parcela.objects.select_related(
            'termo_bolsa__pessoa__user',
            'termo_bolsa__cota_pt__projeto__coordenador__user',
            'conta_pagamento',
        ),
        id=parcela_id,
    )

    projeto = parcela.termo_bolsa.cota_pt.projeto
    pessoa = parcela.termo_bolsa.pessoa

    # ── Trava de Status ──
    if parcela.status != 'PAGO':
        messages.error(
            request,
            f"O recibo só pode ser emitido para parcelas liquidadas. "
            f"Esta parcela está com status: {parcela.get_status_display()}."
        )
        mes_ano = parcela.mes_competencia.strftime('%Y-%m') if parcela.mes_competencia else date.today().strftime('%Y-%m')
        from django.urls import reverse as _r
        return redirect(
            f"{_r('gestao_projetos:folha_mensal_pagamentos')}?projeto_id={projeto.id}&mes_ano={mes_ano}"
        )

    # ── RBAC triplo ──
    if not request.user.is_superuser:
        e_bolsista_titular = (
            pessoa is not None
            and pessoa.user_id is not None
            and pessoa.user_id == request.user.id
        )
        e_coordenador = (
            projeto.coordenador is not None
            and projeto.coordenador.user_id is not None
            and projeto.coordenador.user_id == request.user.id
        )
        if not e_bolsista_titular and not e_coordenador:
            return HttpResponseForbidden(
                "Acesso negado: O recibo de pagamento só pode ser acessado pelo "
                "bolsista titular, pelo coordenador do projeto ou por administradores."
            )

    # ── Dados bancários do bolsista ──
    dado_bancario = None
    if pessoa:
        dado_bancario = (
            pessoa.dados_bancarios.filter(finalidade='PAGAMENTO_BOLSA', ativo=True).first()
            or pessoa.dados_bancarios.filter(ativo=True).first()
        )

    # ── Gera chave de autenticidade SHA-256 ──
    cpf_raw = pessoa.cpf if pessoa else 'sem-cpf'
    payload = (
        f"{parcela.id}-"
        f"{parcela.data_pagamento}-"
        f"{parcela.valor}-"
        f"{cpf_raw}"
    )
    chave_autenticidade = hashlib.sha256(payload.encode()).hexdigest()[:16].upper()

    contexto = {
        'parcela': parcela,
        'termo': parcela.termo_bolsa,
        'pessoa': pessoa,
        'projeto': projeto,
        'cota': parcela.termo_bolsa.cota_pt,
        'dado_bancario': dado_bancario,
        'chave_autenticidade': chave_autenticidade,
        'hash_doc': chave_autenticidade,
        'data_emissao': date.today(),
    }
    return render(request, 'gestao_projetos/recibo_bolsa.html', contexto)


# =====================================================================
# EXTRATO FINANCEIRO E CONCILIAÇÃO BANCÁRIA POR PROJETO (Passo 9)
# =====================================================================

@login_required
def extrato_financeiro_projeto(request, projeto_id):
    """
    Passo 9 — Extrato Financeiro e Conciliação Bancária por Projeto.

    Regras de negócio:
    1. RBAC: superusuário ou MembroEquipe do projeto.
    2. KPIs calculados:
       - Total de Aportes: soma dos aportes do PlanoDeTrabalho ativo.
       - Total de Desembolsos: soma de parcelas com status='PAGO'.
       - Saldo Disponível: Aportes - Desembolsos - Comprometido.
       - Saldo Comprometido: parcelas PENDENTE + EM_ANALISE + APROVADO.
    3. Filtros opcionais por conta bancária e intervalo de datas.
    4. Lista cronológica de movimentações com saldo progressivo,
       incluindo links para recibos (Passo 8) das parcelas pagas.
    """
    from decimal import Decimal
    from datetime import datetime
    from django.db.models import Sum, Q
    from cadastros.models import (
        Parcela, ContaBancaria, ProjetoPDI, MembroEquipe, PlanoDeTrabalho,
    )

    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)

    # ── RBAC ──
    if not request.user.is_superuser:
        if not MembroEquipe.objects.filter(projeto=projeto, usuario=request.user).exists():
            return HttpResponseForbidden(
                "Acesso negado: Você não é membro da equipe deste projeto."
            )

    # ── Plano de trabalho ativo e aportes ──
    plano_ativo = projeto.planos_trabalho.filter(ativo=True).first()

    if plano_ativo:
        total_aportes = (
            (plano_ativo.aporte_empresa or Decimal('0.00'))
            + (plano_ativo.aporte_embrapii or Decimal('0.00'))
            + (plano_ativo.aporte_sebrae or Decimal('0.00'))
            + (plano_ativo.aporte_contrapartida or Decimal('0.00'))
        )
        aportes_detalhe = {
            'empresa': plano_ativo.aporte_empresa or Decimal('0.00'),
            'embrapii': plano_ativo.aporte_embrapii or Decimal('0.00'),
            'sebrae': plano_ativo.aporte_sebrae or Decimal('0.00'),
            'contrapartida': plano_ativo.aporte_contrapartida or Decimal('0.00'),
        }
    else:
        total_aportes = Decimal('0.00')
        aportes_detalhe = {
            'empresa': Decimal('0.00'),
            'embrapii': Decimal('0.00'),
            'sebrae': Decimal('0.00'),
            'contrapartida': Decimal('0.00'),
        }

    # ── Contas bancárias do projeto para o filtro ──
    contas_projeto = ContaBancaria.objects.filter(projeto=projeto)

    # ── Leitura dos filtros GET ──
    conta_id_filtro = request.GET.get('conta_id', '').strip()
    data_inicio_str = request.GET.get('data_inicio', '').strip()
    data_fim_str = request.GET.get('data_fim', '').strip()

    conta_filtrada = None
    if conta_id_filtro:
        conta_filtrada = contas_projeto.filter(id=conta_id_filtro).first()

    data_inicio_filtro = None
    data_fim_filtro = None
    try:
        if data_inicio_str:
            data_inicio_filtro = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        if data_fim_str:
            data_fim_filtro = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    except ValueError:
        messages.warning(request, "Intervalo de datas inválido. Filtro de data ignorado.")

    # ── QuerySet base de parcelas do projeto ──
    parcelas_qs = Parcela.objects.filter(
        termo_bolsa__cota_pt__projeto=projeto,
    ).select_related(
        'termo_bolsa__pessoa',
        'conta_pagamento__fonte_recurso',
    ).order_by('data_pagamento', 'mes_competencia', 'id')

    # Aplica filtro de conta
    if conta_filtrada:
        parcelas_qs = parcelas_qs.filter(conta_pagamento=conta_filtrada)

    # Aplica filtro de data (sobre data_pagamento para pagas; mes_competencia para demais)
    if data_inicio_filtro:
        parcelas_qs = parcelas_qs.filter(
            Q(data_pagamento__gte=data_inicio_filtro)
            | Q(data_pagamento__isnull=True, mes_competencia__gte=data_inicio_filtro)
        )
    if data_fim_filtro:
        parcelas_qs = parcelas_qs.filter(
            Q(data_pagamento__lte=data_fim_filtro)
            | Q(data_pagamento__isnull=True, mes_competencia__lte=data_fim_filtro)
        )

    # ── KPIs globais (sem filtro de datas, para não distorcer saldo total) ──
    todas_parcelas = Parcela.objects.filter(
        termo_bolsa__cota_pt__projeto=projeto,
    )
    total_desembolsos = (
        todas_parcelas.filter(status='PAGO')
        .aggregate(t=Sum('valor'))['t'] or Decimal('0.00')
    )
    saldo_comprometido = (
        todas_parcelas.filter(status__in=['PENDENTE', 'EM_ANALISE', 'APROVADO'])
        .aggregate(t=Sum('valor'))['t'] or Decimal('0.00')
    )
    saldo_disponivel = total_aportes - total_desembolsos - saldo_comprometido

    # ── Monta a lista de movimentações com saldo progressivo ──
    # A linha de abertura representa o aporte total (crédito inicial)
    saldo_corrente = total_aportes
    movimentacoes = []

    # Linha sintética de abertura: crédito dos aportes
    movimentacoes.append({
        'tipo': 'CREDITO',
        'data': None,
        'descricao': 'Crédito de Aportes — Plano de Trabalho',
        'beneficiario': '—',
        'conta': '—',
        'valor_credito': total_aportes,
        'valor_debito': None,
        'saldo': saldo_corrente,
        'parcela': None,
        'status_badge': 'success',
        'status_label': 'APORTE',
        'link_recibo': None,
    })

    # Parcelas como linhas de débito
    for parcela in parcelas_qs:
        valor = parcela.valor or Decimal('0.00')
        pessoa = parcela.termo_bolsa.pessoa if parcela.termo_bolsa else None
        beneficiario = pessoa.nome if pessoa else '—'
        conta_str = str(parcela.conta_pagamento) if parcela.conta_pagamento else '—'

        # Apenas parcelas PAGAS debitam o saldo progressivo
        if parcela.status == 'PAGO':
            saldo_corrente -= valor
            valor_debito = valor
            valor_credito = None
        else:
            valor_debito = None
            valor_credito = None

        # Badge de status
        badge_map = {
            'PAGO': ('success', 'PAGO'),
            'APROVADO': ('primary', 'APROVADO'),
            'EM_ANALISE': ('warning', 'EM ANÁLISE'),
            'PENDENTE': ('secondary', 'PENDENTE'),
            'CANCELADO': ('danger', 'CANCELADO'),
        }
        status_badge, status_label = badge_map.get(parcela.status, ('secondary', parcela.status))

        # Link para recibo apenas se PAGO (Passo 8)
        link_recibo = None
        if parcela.status == 'PAGO':
            from django.urls import reverse as _rev
            link_recibo = _rev('gestao_projetos:visualizar_recibo_bolsa', args=[parcela.id])

        data_ref = parcela.data_pagamento or parcela.mes_competencia
        descricao = (
            f"Parcela {parcela.numero} — {parcela.get_status_display()}"
            if not parcela.termo_bolsa
            else f"Parcela {parcela.numero}/{parcela.termo_bolsa.quantidade_parcelas} "
                 f"— {parcela.termo_bolsa.numero_termo}"
        )

        movimentacoes.append({
            'tipo': 'DEBITO' if parcela.status == 'PAGO' else 'COMPROMETIDO',
            'data': data_ref,
            'descricao': descricao,
            'beneficiario': beneficiario,
            'conta': conta_str,
            'valor_credito': valor_credito,
            'valor_debito': valor_debito,
            'saldo': saldo_corrente if parcela.status == 'PAGO' else None,
            'parcela': parcela,
            'status_badge': status_badge,
            'status_label': status_label,
            'link_recibo': link_recibo,
        })

    contexto = {
        'projeto': projeto,
        'plano_ativo': plano_ativo,
        'contas_projeto': contas_projeto,
        'conta_filtrada': conta_filtrada,
        'data_inicio_filtro': data_inicio_filtro,
        'data_fim_filtro': data_fim_filtro,
        # KPIs
        'total_aportes': total_aportes,
        'aportes_detalhe': aportes_detalhe,
        'total_desembolsos': total_desembolsos,
        'saldo_comprometido': saldo_comprometido,
        'saldo_disponivel': saldo_disponivel,
        # Tabela de movimentações
        'movimentacoes': movimentacoes,
        'qtd_movimentacoes': parcelas_qs.count(),
    }
    return render(request, 'gestao_projetos/extrato_financeiro_projeto.html', contexto)


@login_required
def exportar_recibos_lote_zip(request, projeto_id):
    """
    Passo 9 — Exportação Consolidada de Recibos de Bolsas em Lote (.zip)
    
    Regras de negócio:
    1. RBAC: superusuário ou MembroEquipe do projeto.
    2. Apenas parcelas com status='PAGO'.
    3. Gera ZIP em memória contendo o HTML de cada recibo.
    4. Cada recibo mantém a mesma chave de autenticidade (SHA-256) gerada na view individual.
    """
    import io
    import zipfile
    import hashlib
    from datetime import date
    from django.template.loader import render_to_string
    from django.http import HttpResponse, HttpResponseForbidden
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from cadastros.models import ProjetoPDI, MembroEquipe, Parcela

    projeto = get_object_or_404(ProjetoPDI, id=projeto_id)

    # ── RBAC ──
    if not request.user.is_superuser:
        if not MembroEquipe.objects.filter(projeto=projeto, usuario=request.user).exists():
            return HttpResponseForbidden(
                "Acesso negado: Você não é membro da equipe deste projeto."
            )

    parcelas_pagas = Parcela.objects.select_related(
        'termo_bolsa__pessoa__user',
        'termo_bolsa__cota_pt__projeto__coordenador__user',
        'conta_pagamento'
    ).filter(
        termo_bolsa__cota_pt__projeto=projeto,
        status='PAGO'
    ).order_by('data_pagamento', 'id')

    if not parcelas_pagas.exists():
        messages.warning(request, "Não há recibos liquidados (status PAGO) para este projeto.")
        from django.urls import reverse as _r
        return redirect(_r('gestao_projetos:extrato_financeiro_projeto', args=[projeto.id]))

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for parcela in parcelas_pagas:
            pessoa = parcela.termo_bolsa.pessoa
            dado_bancario = None
            if pessoa:
                dado_bancario = (
                    pessoa.dados_bancarios.filter(finalidade='PAGAMENTO_BOLSA', ativo=True).first()
                    or pessoa.dados_bancarios.filter(ativo=True).first()
                )

            cpf_raw = pessoa.cpf if pessoa else 'sem-cpf'
            payload = (
                f"{parcela.id}-"
                f"{parcela.data_pagamento}-"
                f"{parcela.valor}-"
                f"{cpf_raw}"
            )
            chave_autenticidade = hashlib.sha256(payload.encode()).hexdigest()[:16].upper()

            contexto = {
                'parcela': parcela,
                'termo': parcela.termo_bolsa,
                'pessoa': pessoa,
                'projeto': projeto,
                'cota': parcela.termo_bolsa.cota_pt,
                'dado_bancario': dado_bancario,
                'chave_autenticidade': chave_autenticidade,
                'hash_doc': chave_autenticidade,
                'data_emissao': date.today(),
            }
            html_content = render_to_string('gestao_projetos/recibo_bolsa.html', contexto, request=request)
            
            nome_pessoa = pessoa.nome if pessoa else 'Sem_Nome'
            # Remover caracteres inválidos do nome do arquivo (ex: acentos e espaços)
            import re
            nome_limpo = re.sub(r'[^A-Za-z0-9_-]', '', nome_pessoa.replace(' ', '_'))
            
            nome_arquivo = f"Recibo_Parcela_{parcela.id}_{nome_limpo}.html"
            zf.writestr(nome_arquivo, html_content)

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="Recibos_Projeto_{projeto.id}.zip"'
    return response


# ==============================================================================
# FASE 4 — ETAPA 4.1: PAINEL DE INDICADORES OFICIAIS EMBRAPII
# ==============================================================================

@login_required
def painel_indicadores_embrapii(request):
    """
    Dashboard Executivo com Indicadores Oficiais EMBRAPII / SUFRAMA (Etapa 4.1):
    - Alavancagem de recursos privados (Aporte Empresa / Valor Global)
    - Composição orçamentária (Empresa, EMBRAPII, SEBRAE, Contrapartida)
    - Overhead retido para o Fundo de Reserva Institucional (Rubrica SUPORTE)
    - Prevenção de dupla contagem: 1 plano vigente por projeto ativo.
    - RBAC: Superusuários, Staff, ou MembroEquipe (COORDENADOR, GESTOR, ANALISTA).
    """
    from decimal import Decimal
    from django.db.models import Sum, Avg
    from django.core.exceptions import PermissionDenied
    from cadastros.models import PlanoDeTrabalho, RubricaOrcamentariaPT, Macroentrega, ProjetoPDI, MembroEquipe

    # 1. Validação RBAC Canônica
    is_admin = request.user.is_superuser or request.user.is_staff
    is_membro_autorizado = MembroEquipe.objects.filter(
        usuario=request.user,
        papel__in=['COORDENADOR', 'GESTOR', 'ANALISTA']
    ).exists()

    if not (is_admin or is_membro_autorizado):
        raise PermissionDenied("Acesso restrito à coordenação e gestão institucional de projetos.")

    # 2. Seleção de Projetos Elegíveis e Prevenção de Dupla Contagem
    projetos = ProjetoPDI.objects.filter(
        fase__in=['EXECUCAO', 'PRESTACAO_CONTAS', 'ENCERRADO']
    ).select_related('concedente', 'coordenador').order_by('nome')

    total_empresa = Decimal('0.00')
    total_embrapii = Decimal('0.00')
    total_sebrae = Decimal('0.00')
    total_contrapartida = Decimal('0.00')
    total_global = Decimal('0.00')
    total_fundo_reserva = Decimal('0.00')
    total_macros_global = 0
    planos_vigentes_ids = []

    projetos_metricas = []
    for proj in projetos:
        # Seleciona rigorosamente o plano ativo mais recente do projeto
        plano = proj.planos_trabalho.filter(ativo=True).order_by('-versao').first()
        if not plano:
            continue

        planos_vigentes_ids.append(plano.pk)

        v_empresa = plano.aporte_empresa or Decimal('0.00')
        v_embrapii = plano.aporte_embrapii or Decimal('0.00')
        v_sebrae = plano.aporte_sebrae or Decimal('0.00')
        v_contra = plano.aporte_contrapartida or Decimal('0.00')
        v_global = plano.valor_global or (v_empresa + v_embrapii + v_sebrae + v_contra)

        total_empresa += v_empresa
        total_embrapii += v_embrapii
        total_sebrae += v_sebrae
        total_contrapartida += v_contra
        total_global += v_global

        alavancagem_proj = (v_empresa / v_global * Decimal('100.0')) if v_global > Decimal('0.00') else Decimal('0.00')

        # Overhead do projeto (Rubrica SUPORTE)
        overhead_proj = RubricaOrcamentariaPT.objects.filter(
            plano_trabalho=plano,
            categoria='SUPORTE'
        ).aggregate(total=Sum('valor_previsto'))['total'] or Decimal('0.00')
        total_fundo_reserva += overhead_proj

        pct_overhead_proj = (overhead_proj / v_global * Decimal('100.0')) if v_global > Decimal('0.00') else Decimal('0.00')

        macros_proj = Macroentrega.objects.filter(plano_trabalho=plano)
        macros_proj_count = macros_proj.count()
        total_macros_global += macros_proj_count

        # TRL máximo alcançado no projeto
        trl_max = macros_proj.filter(trl__isnull=False).order_by('-trl').values_list('trl', flat=True).first()

        projetos_metricas.append({
            'projeto': proj,
            'plano': plano,
            'v_empresa': v_empresa,
            'v_embrapii': v_embrapii,
            'v_sebrae': v_sebrae,
            'v_contrapartida': v_contra,
            'v_global': v_global,
            'alavancagem': alavancagem_proj,
            'overhead': overhead_proj,
            'pct_overhead': pct_overhead_proj,
            'total_macros': macros_proj_count,
            'trl_max': trl_max,
        })

    # Taxa Global de Alavancagem e Fundo de Reserva
    alavancagem_global = (total_empresa / total_global * Decimal('100.0')) if total_global > Decimal('0.00') else Decimal('0.00')
    pct_fundo_reserva_global = (total_fundo_reserva / total_global * Decimal('100.0')) if total_global > Decimal('0.00') else Decimal('0.00')

    # Percentuais visuais normalizados para barras de progresso Bootstrap
    pct_empresa = float(total_empresa / total_global * Decimal('100.0')) if total_global > Decimal('0.00') else 0.0
    pct_embrapii = float(total_embrapii / total_global * Decimal('100.0')) if total_global > Decimal('0.00') else 0.0
    pct_sebrae = float(total_sebrae / total_global * Decimal('100.0')) if total_global > Decimal('0.00') else 0.0
    pct_contra = float(total_contrapartida / total_global * Decimal('100.0')) if total_global > Decimal('0.00') else 0.0

    # 4. Distribuição e Média de TRL nas Macroentregas da Carteira
    macros_ativas = Macroentrega.objects.filter(plano_trabalho__in=planos_vigentes_ids)
    macros_com_trl = macros_ativas.filter(trl__isnull=False)
    total_macros_com_trl = macros_com_trl.count()

    distribuicao_trl = {
        3: macros_com_trl.filter(trl=3).count(),
        4: macros_com_trl.filter(trl=4).count(),
        5: macros_com_trl.filter(trl=5).count(),
        6: macros_com_trl.filter(trl=6).count(),
    }
    trl_medio = macros_com_trl.aggregate(media=Avg('trl'))['media']

    context = {
        'total_empresa': total_empresa,
        'total_embrapii': total_embrapii,
        'total_sebrae': total_sebrae,
        'total_contrapartida': total_contrapartida,
        'total_global': total_global,
        'alavancagem_global': alavancagem_global,
        'total_fundo_reserva': total_fundo_reserva,
        'pct_fundo_reserva_global': pct_fundo_reserva_global,
        'total_macros_global': total_macros_global,
        'pct_empresa': pct_empresa,
        'pct_embrapii': pct_embrapii,
        'pct_sebrae': pct_sebrae,
        'pct_contra': pct_contra,
        'projetos_metricas': projetos_metricas,
        'total_macros_com_trl': total_macros_com_trl,
        'trl_medio': trl_medio,
        'distribuicao_trl': distribuicao_trl,
    }
    return render(request, 'gestao_projetos/painel_indicadores_embrapii.html', context)


# =====================================================================
# TRILHA DE AUDITORIA TCU/CGU — SIMPLE HISTORY (Passo 4.3)
# =====================================================================

@login_required
def trilha_auditoria_projeto(request, projeto_id):
    """
    Trilha de Auditoria e Conformidade para Órgãos de Controle (TCU, CGU, Auditoria IFAM).

    - Consulta direta aos managers históricos (PlanoDeTrabalho.history,
      CotaBolsaPT.history, RubricaOrcamentariaPT.history).
    - Captura deltas (diff_against) e suporta objetos excluídos (history_type='-').
    - RBAC: Superusuários, Staff, ou MembroEquipe do projeto
      (papéis COORDENADOR, GESTOR ou ANALISTA).
    """
    from django.core.exceptions import PermissionDenied
    from cadastros.models import (
        ProjetoPDI, MembroEquipe,
        PlanoDeTrabalho, CotaBolsaPT, RubricaOrcamentariaPT,
    )

    projeto = get_object_or_404(ProjetoPDI, pk=projeto_id)

    # ── RBAC Estrito ARGUS ──
    is_admin = request.user.is_superuser or request.user.is_staff
    is_coordenador = bool(
        projeto.coordenador_id
        and projeto.coordenador.user_id == request.user.id
    )
    is_membro_autorizado = MembroEquipe.objects.filter(
        projeto=projeto,
        usuario=request.user,
        papel__in=['COORDENADOR', 'GESTOR', 'ANALISTA'],
    ).exists()

    if not (is_admin or is_coordenador or is_membro_autorizado):
        raise PermissionDenied("Acesso restrito à auditoria e equipe gestora deste projeto.")

    # ── IDs de planos (vivos + históricos) para rastrear rubricas deletadas ──
    plano_ids_vivos = list(
        PlanoDeTrabalho.objects.filter(projeto=projeto).values_list('id', flat=True)
    )
    plano_ids_historicos = list(
        PlanoDeTrabalho.history.filter(projeto_id=projeto.id).values_list('id', flat=True)
    )
    todos_plano_ids = list(set(plano_ids_vivos + plano_ids_historicos))

    eventos = []

    # ── A) Planos de Trabalho ──
    historico_planos = PlanoDeTrabalho.history.filter(
        projeto_id=projeto.id
    ).order_by('-history_date')

    for h in historico_planos:
        mudancas = []
        if h.prev_record:
            delta = h.diff_against(h.prev_record)
            for change in delta.changes:
                mudancas.append({
                    'campo': change.field,
                    'antigo': str(change.old) if change.old is not None else '',
                    'novo':   str(change.new) if change.new is not None else '',
                })
        eventos.append({
            'data_hora':    h.history_date,
            'usuario':      (h.history_user.get_full_name() or h.history_user.username)
                            if h.history_user else 'Sistema / Rotina Automática',
            'tipo':         h.get_history_type_display(),
            'tipo_code':    h.history_type,
            'entidade':     'Plano de Trabalho',
            'identificador': f"Plano V{h.versao or 1}",
            'mudancas':     mudancas,
        })

    # ── B) Cotas de Bolsas ──
    historico_cotas = CotaBolsaPT.history.filter(
        projeto_id=projeto.id
    ).order_by('-history_date')

    for h in historico_cotas:
        mudancas = []
        if h.prev_record:
            delta = h.diff_against(h.prev_record)
            for change in delta.changes:
                mudancas.append({
                    'campo': change.field,
                    'antigo': str(change.old) if change.old is not None else '',
                    'novo':   str(change.new) if change.new is not None else '',
                })
        identificador_cota = (
            f"{h.perfil_funcao or 'Perfil não informado'} "
            f"({h.quantidade_vagas or 0} vaga(s))"
        )
        eventos.append({
            'data_hora':    h.history_date,
            'usuario':      (h.history_user.get_full_name() or h.history_user.username)
                            if h.history_user else 'Sistema / Rotina Automática',
            'tipo':         h.get_history_type_display(),
            'tipo_code':    h.history_type,
            'entidade':     'Cota de Bolsa',
            'identificador': identificador_cota,
            'mudancas':     mudancas,
        })

    # ── C) Rubricas Orçamentárias ──
    historico_rubricas = RubricaOrcamentariaPT.history.filter(
        plano_trabalho_id__in=todos_plano_ids
    ).order_by('-history_date')

    for h in historico_rubricas:
        mudancas = []
        if h.prev_record:
            delta = h.diff_against(h.prev_record)
            for change in delta.changes:
                mudancas.append({
                    'campo': change.field,
                    'antigo': str(change.old) if change.old is not None else '',
                    'novo':   str(change.new) if change.new is not None else '',
                })
        categoria_display = (
            h.get_categoria_display()
            if hasattr(h, 'get_categoria_display')
            else h.categoria
        )
        identificador_rubrica = f"{categoria_display} ({h.fonte_recurso or '-'})"
        eventos.append({
            'data_hora':    h.history_date,
            'usuario':      (h.history_user.get_full_name() or h.history_user.username)
                            if h.history_user else 'Sistema / Rotina Automática',
            'tipo':         h.get_history_type_display(),
            'tipo_code':    h.history_type,
            'entidade':     'Rubrica Orçamentária',
            'identificador': identificador_rubrica,
            'mudancas':     mudancas,
        })

    # ── Ordenação cronológica decrescente ──
    eventos.sort(key=lambda x: x['data_hora'], reverse=True)

    # ── Métricas de auditoria ──
    total_eventos    = len(eventos)
    total_criacoes   = sum(1 for e in eventos if e['tipo_code'] == '+')
    total_alteracoes = sum(1 for e in eventos if e['tipo_code'] == '~')
    total_exclusoes  = sum(1 for e in eventos if e['tipo_code'] == '-')
    ultimo_evento    = eventos[0] if eventos else None

    context = {
        'projeto':          projeto,
        'eventos':          eventos,
        'total_eventos':    total_eventos,
        'total_criacoes':   total_criacoes,
        'total_alteracoes': total_alteracoes,
        'total_exclusoes':  total_exclusoes,
        'ultimo_evento':    ultimo_evento,
    }
    return render(request, 'gestao_projetos/trilha_auditoria_projeto.html', context)
