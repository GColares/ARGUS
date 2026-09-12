from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.utils import timezone
from decimal import Decimal
import datetime

from cadastros.models import (
    PessoaFisica,
    PerfilServidor,
    PerfilAluno,
    PerfilColaboradorExterno,
    PerfilTerceirizado,
    TermoBolsa,
    Parcela,
    ProjetoPDI,
    CotaBolsaPT,
    DadoBancario
)

@login_required
def home_rh(request):
    """
    Dashboard Central de Gestão de Capital Humano e Recursos Humanos de PD&I.
    Estruturado no Padrão Almoxarifado em 4 eixos operacionais.
    """
    hoje = timezone.now().date()
    current_year = hoje.year
    current_month = hoje.month

    # Filtros de busca (GET)
    busca = request.GET.get('q', '').strip()
    status_filtro = request.GET.get('status', '').strip()
    projeto_filtro = request.GET.get('projeto', '').strip()
    aba_ativa = request.GET.get('tab', 'pessoas')

    # ----------------------------------------------------
    # 1. KPIs ESTRATÉGICOS (TEMPO REAL)
    # ----------------------------------------------------
    total_pessoas = PessoaFisica.objects.count()
    
    termos_ativos_qs = TermoBolsa.objects.filter(status='ATIVO', vigencia_fim__gte=hoje)
    total_bolsistas_ativos = termos_ativos_qs.values('pessoa').distinct().count()
    
    total_servidores_ifam = PerfilServidor.objects.filter(ativo=True).count()
    
    # Projeção financeira da folha de bolsas no mês
    folha_mensal_soma = termos_ativos_qs.aggregate(total=Sum('valor_parcela'))['total'] or Decimal('0.00')

    # ----------------------------------------------------
    # 2. ABA 1: Dossiê de Pessoas Físicas
    # ----------------------------------------------------
    pessoas_qs = PessoaFisica.objects.select_related(
        'perfil_servidor',
        'perfil_aluno',
        'perfil_colaborador_externo',
        'perfil_terceirizado',
        'user'
    ).prefetch_related('dados_bancarios', 'termos_bolsa').order_by('nome')

    if busca:
        pessoas_qs = pessoas_qs.filter(
            Q(nome__icontains=busca) |
            Q(cpf__icontains=busca) |
            Q(email__icontains=busca)
        )

    # ----------------------------------------------------
    # 3. ABA 2: Bolsistas & Termos de Concessão (FAEPI/Editais)
    # ----------------------------------------------------
    termos_qs = TermoBolsa.objects.select_related(
        'pessoa',
        'cota_pt__projeto',
        'cota_pt'
    ).order_by('-vigencia_fim')

    if busca:
        termos_qs = termos_qs.filter(
            Q(pessoa__nome__icontains=busca) |
            Q(pessoa__cpf__icontains=busca) |
            Q(numero_termo__icontains=busca)
        )
    if status_filtro:
        termos_qs = termos_qs.filter(status=status_filtro)
    if projeto_filtro:
        termos_qs = termos_qs.filter(cota_pt__projeto_id=projeto_filtro)

    # ----------------------------------------------------
    # 4. ABA 3: Conformidade Regulatória (Resolução 015/2023)
    # ----------------------------------------------------
    servidores_qs = PerfilServidor.objects.select_related('pessoa').prefetch_related(
        'pessoa__termos_bolsa__cota_pt__projeto'
    ).order_by('pessoa__nome')

    # ----------------------------------------------------
    # 5. ABA 4: Folha Mensal & Atesto de Parcelas
    # ----------------------------------------------------
    parcelas_qs = Parcela.objects.select_related(
        'termo_bolsa__pessoa',
        'termo_bolsa__cota_pt__projeto',
        'conta_pagamento'
    ).order_by('termo_bolsa__pessoa__nome', 'numero')

    # Filtrar parcelas da competência atual ou mais recentes
    parcelas_mes = parcelas_qs.filter(
        mes_competencia__year=current_year,
        mes_competencia__month=current_month
    )
    # Fallback se não houver parcelas no mês exato
    if not parcelas_mes.exists():
        parcelas_mes = parcelas_qs.filter(status__in=['PENDENTE', 'EM_ANALISE', 'APROVADO'])[:50]

    projetos_disponiveis = ProjetoPDI.objects.all().order_by('nome')

    context = {
        'hoje': hoje,
        'ano_atual': current_year,
        'mes_atual': current_month,
        'total_pessoas': total_pessoas,
        'total_bolsistas_ativos': total_bolsistas_ativos,
        'total_servidores_ifam': total_servidores_ifam,
        'folha_mensal_soma': folha_mensal_soma,
        'pessoas': pessoas_qs[:100],
        'termos_bolsa': termos_qs[:100],
        'servidores': servidores_qs[:100],
        'parcelas_mes': parcelas_mes,
        'projetos': projetos_disponiveis,
        'busca': busca,
        'status_filtro': status_filtro,
        'projeto_filtro': projeto_filtro,
        'aba_ativa': aba_ativa,
    }

    return render(request, 'recursos_humanos/dashboard.html', context)

