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
        projeto = relatorio.bolsista.projeto
        atividades_vinculadas = list(projeto.atividades_plano.all().order_by('numero'))

    # Dicionário mapeando rigorosamente as seções do documento oficial
    total_parcelas = termo.quantidade_parcelas if termo else relatorio.bolsista.total_parcelas_previstas
    
    conta_final = relatorio.conta_pagamento
    
    if not conta_final and termo:
        # Se for um relatório antigo sem a conta gravada, tenta achar dinamicamente
        from cadastros.models import DistribuicaoContaCota
        dist = DistribuicaoContaCota.objects.filter(
            cota_pt=termo.cota_pt,
            parcela_inicio__lte=relatorio.parcela_referencia.numero,
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
            'bolsista_nome': bolsista.nome_completo,
            'bolsista_cpf': bolsista.cpf,
            'bolsista_rg': bolsista.rg,
            'bolsista_email': bolsista.email,
            'bolsista_fone': bolsista.telefone,
            'bolsista_funcao': bolsista.funcao,
            'bolsista_termodebolsa': bolsista.termo_bolsa,
            'bolsista_contratacao': f"{bolsista.data_inicio.strftime('%d/%m/%Y')} a {bolsista.data_fim.strftime('%d/%m/%Y')}",
            'bolsista_ch': bolsista.carga_horaria_total,
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
        tarefas = relatorio.itens_atividade.filter(atividade_mae=atv)
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
    ).order_by('termo_bolsa__cota_pt__projeto__convenio', 'termo_bolsa__pessoa__nome', 'parcela_referencia__numero', 'versao')

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
        bolsista_nome = relatorio.termo_bolsa.bolsista.nome
        total_parcelas = relatorio.termo_bolsa.quantidade_parcelas
    else:
        bolsista_nome = relatorio.bolsista.nome_completo
        total_parcelas = getattr(relatorio.bolsista, 'total_parcelas_previstas', '?')

    nome_arquivo = f"Relatorio_Atividades_{bolsista_nome.replace(' ', '_')}_Parcela_{relatorio.parcela_referencia.numero}_de_{total_parcelas}.docx"
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
    
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
                bolsista_nome = relatorio.bolsista.nome_completo
                total_parcelas = getattr(relatorio.bolsista, 'total_parcelas_previstas', '?')

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
