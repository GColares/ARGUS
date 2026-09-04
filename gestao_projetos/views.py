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
            parcela_fim__gte=relatorio.parcela
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
        'convenio_numero': projeto.convenio,
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
        bolsista_antigo = BolsistaProjeto.objects.filter(cpf=termo.bolsista.cpf).first()
        contexto.update({
            'bolsista_nome': termo.bolsista.nome,
            'bolsista_cpf': termo.bolsista.cpf,
            'bolsista_rg': bolsista_antigo.rg if bolsista_antigo else 'N/I',
            'bolsista_email': bolsista_antigo.email if bolsista_antigo else 'N/I',
            'bolsista_fone': bolsista_antigo.telefone if bolsista_antigo else 'N/I',
            'bolsista_funcao': termo.cota_pt.perfil_funcao,
            'bolsista_termodebolsa': termo.numero_termo,
            'bolsista_contratacao': f"{termo.vigencia_inicio.strftime('%d/%m/%Y')} a {termo.vigencia_fim.strftime('%d/%m/%Y')}",
            'bolsista_ch': bolsista_antigo.carga_horaria_total if bolsista_antigo else (termo.cota_pt.carga_horaria_semanal * 4),
            'assinatura_bolsita': termo.bolsista.nome,
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
    relatorio = get_object_or_404(RelatorioAtividade, id=relatorio_id)
    if request.method == 'POST':
        if 'arquivo_pdf' in request.FILES:
            relatorio.arquivo_pdf = request.FILES['arquivo_pdf']
            relatorio.status = 'CONCLUIDO'
        else:
            relatorio.status = 'PENDENTE'
            relatorio.arquivo_pdf = None # Se quiserem limpar
        relatorio.save()
        from django.contrib import messages
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

# Constantes de alçada institucional (IFAM Polo de Inovação Manaus)
DIRETOR_POLO_NOME = "Alyson de Jesus dos Santos"
DIRETOR_POLO_CARGO = "Diretor-Geral do Polo de Inovação IFAM/Manaus"
REITOR_NOME = "Jaime Cavalcante Alves"
REITOR_CARGO = "Reitor do IFAM"


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

    # Signatários: Coordenador assina como Requisitante; Visto = Diretor do Polo
    if coordenador_projeto:
        signatario_nome = coordenador_projeto.nome
        signatario_cargo = "Coordenador do Projeto"
    else:
        signatario_nome = DIRETOR_POLO_NOME
        signatario_cargo = DIRETOR_POLO_CARGO

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
        visto_nome=DIRETOR_POLO_NOME,
        visto_cargo=DIRETOR_POLO_CARGO,
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

    # Alçada
    if is_diretor_campus:
        signatario_nome = REITOR_NOME
        signatario_cargo = REITOR_CARGO
    else:
        signatario_nome = DIRETOR_POLO_NOME
        signatario_cargo = DIRETOR_POLO_CARGO

    try:
        ano_c, mes_c = int(mes_ano.split('-')[0]), int(mes_ano.split('-')[1])
        competencia = date(ano_c, mes_c, 1)
    except (ValueError, IndexError):
        competencia = date.today().replace(day=1)

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
        visto_nome=DIRETOR_POLO_NOME if is_diretor_campus else "",
        visto_cargo=DIRETOR_POLO_CARGO if is_diretor_campus else "",
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
