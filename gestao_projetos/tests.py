from datetime import date
from decimal import Decimal
import hashlib

from django.contrib.auth.models import User
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from cadastros.models import (
    EmpresaParceira, ProjetoPDI, CotaBolsaPT, TermoBolsa,
    Parcela, PessoaFisica, ContaBancaria, MembroEquipe, DadoBancario,
)
from gestao_projetos.models import RelatorioAtividade


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class FolhaPagamentoTestCase(TestCase):
    """
    Testes de integração da Folha Mensal de Pagamentos de Bolsas.
    Cobre: visualização, trava Opção A (sem RA atestado) e liquidação com sucesso.
    """

    def setUp(self):
        # Usuário autenticado membro da equipe
        self.user = User.objects.create_user(
            username='gestor_teste',
            password='senha123'
        )

        # Estrutura hierárquica mínima
        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Folha LTDA",
            cnpj="55.666.777/0001-88",
            natureza_juridica="LTDA",
            representante_legal="Rep Folha",
            cargo_representante="Diretor"
        )
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto Folha Teste",
            fase="EXECUCAO",
            concedente=self.empresa
        )

        # Membro de equipe para autorização RBAC
        MembroEquipe.objects.create(
            projeto=self.projeto,
            usuario=self.user,
            papel='GESTOR'
        )

        # Conta bancária do projeto
        self.conta = ContaBancaria.objects.create(
            projeto=self.projeto,
            conta="99999",
            dv="0"
        )

        # Bolsista com PessoaFisica e dados bancários ativos
        self.pessoa = PessoaFisica.objects.create(
            nome="Bolsista Teste",
            cpf="111.222.333-44"
        )
        DadoBancario.objects.create(
            pessoa=self.pessoa,
            finalidade='PAGAMENTO_BOLSA',
            banco_codigo='001',
            agencia='1234',
            conta='56789-0',
            ativo=True
        )

        # Cota e Termo de Bolsa
        self.cota = CotaBolsaPT.objects.create(
            projeto=self.projeto,
            perfil_funcao="Pesquisador",
            quantidade_vagas=1,
            parcelas_previstas=3,
            valor_global_previsto=Decimal("4500.00")
        )
        self.termo = TermoBolsa.objects.create(
            cota_pt=self.cota,
            pessoa=self.pessoa,
            numero_termo="TB-FOLHA-001",
            vigencia_inicio=date(2026, 9, 1),
            vigencia_fim=date(2026, 11, 30),
            quantidade_parcelas=3,
            valor_parcela=Decimal("1500.00")
        )

        # Obtém a parcela 1 (criada automaticamente pelo TermoBolsa.save())
        self.parcela = self.termo.parcelas.get(numero=1)

        self.client = Client()
        self.client.login(username='gestor_teste', password='senha123')

        # URL da folha de pagamentos
        self.url_folha = reverse('gestao_projetos:folha_mensal_pagamentos')
        self.url_confirmar = reverse(
            'gestao_projetos:confirmar_pagamento_parcela',
            args=[self.parcela.id]
        )

    # ------------------------------------------------------------------ #
    # Teste 1: Visualização da folha por usuário autenticado              #
    # ------------------------------------------------------------------ #
    def test_visualizacao_folha_mensal(self):
        """Usuário autenticado acessa a folha e vê as parcelas do projeto."""
        response = self.client.get(
            self.url_folha,
            {'projeto_id': self.projeto.id, 'mes_ano': '2026-09'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('linhas_folha', response.context)
        self.assertEqual(len(response.context['linhas_folha']), 1)

        linha = response.context['linhas_folha'][0]
        self.assertEqual(linha['parcela'].id, self.parcela.id)
        self.assertEqual(linha['pessoa'].id, self.pessoa.id)

        # KPIs calculados
        self.assertEqual(response.context['total_folha'], Decimal('1500.00'))
        self.assertEqual(response.context['total_liquidado'], Decimal('0.00'))
        self.assertEqual(response.context['saldo_pendente'], Decimal('1500.00'))
        self.assertEqual(response.context['qtd_ras_atestados'], 0)

    # ------------------------------------------------------------------ #
    # Teste 2: Bloqueio de liquidação sem RA atestado (Opção A)           #
    # ------------------------------------------------------------------ #
    def test_bloqueio_pagamento_sem_ra_atestado(self):
        """POST de confirmação deve ser rejeitado quando não há RA CONCLUIDO."""
        # Cria um RA em status PENDENTE (não atestado)
        RelatorioAtividade.objects.create(
            termo_bolsa=self.termo,
            parcela_referencia=self.parcela,
            criado_por=self.user,
            status='PENDENTE',
            periodo_inicio=date(2026, 9, 1),
            periodo_fim=date(2026, 9, 30),
            carga_horaria_periodo=160
        )

        response = self.client.post(self.url_confirmar, {
            'data_pagamento': '2026-09-30',
            'conta_pagamento_id': self.conta.id,
        })

        # Deve redirecionar (não é 200 — processa e volta para folha)
        self.assertEqual(response.status_code, 302)

        # Parcela NÃO deve ter transitado para PAGO
        self.parcela.refresh_from_db()
        self.assertNotEqual(self.parcela.status, 'PAGO')

        # Mensagem de erro deve ter sido emitida
        msgs = list(response.wsgi_request._messages)
        self.assertTrue(
            any('Liquidação bloqueada' in str(m) for m in msgs),
            "Esperava mensagem de bloqueio por RA não atestado"
        )

    # ------------------------------------------------------------------ #
    # Teste 3: Liquidação bem-sucedida com RA CONCLUIDO                   #
    # ------------------------------------------------------------------ #
    def test_sucesso_confirmacao_pagamento_com_ra_concluido(self):
        """POST de confirmação com RA CONCLUIDO efetiva o pagamento da parcela."""
        # Cria RA atestado (CONCLUIDO)
        RelatorioAtividade.objects.create(
            termo_bolsa=self.termo,
            parcela_referencia=self.parcela,
            criado_por=self.user,
            status='CONCLUIDO',
            periodo_inicio=date(2026, 9, 1),
            periodo_fim=date(2026, 9, 30),
            carga_horaria_periodo=160
        )

        response = self.client.post(self.url_confirmar, {
            'data_pagamento': '2026-09-30',
            'conta_pagamento_id': self.conta.id,
        })

        # Deve redirecionar de volta para a folha
        self.assertEqual(response.status_code, 302)

        # Parcela deve ter transitado para PAGO
        self.parcela.refresh_from_db()
        self.assertEqual(self.parcela.status, 'PAGO')
        self.assertEqual(self.parcela.data_pagamento, date(2026, 9, 30))
        self.assertEqual(self.parcela.conta_pagamento_id, self.conta.id)

        # Mensagem de sucesso deve estar presente
        msgs = list(response.wsgi_request._messages)
        self.assertTrue(
            any('confirmado com sucesso' in str(m) for m in msgs),
            "Esperava mensagem de confirmação de pagamento"
        )


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class ReciboBolsaExtratoTestCase(TestCase):
    """Testa emissão, autenticidade e controle de acesso do recibo de bolsa."""

    def setUp(self):
        self.bolsista_user = User.objects.create_user(
            username='bolsista_recibo',
            password='senha123'
        )
        self.terceiro_user = User.objects.create_user(
            username='terceiro_recibo',
            password='senha123'
        )
        empresa = EmpresaParceira.objects.create(
            nome="Empresa Recibo LTDA",
            cnpj="77.888.999/0001-00",
            natureza_juridica="LTDA",
            representante_legal="Rep Recibo",
            cargo_representante="Diretor"
        )
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto Recibo Teste",
            fase="EXECUCAO",
            concedente=empresa
        )
        self.pessoa = PessoaFisica.objects.create(
            nome="Bolsista Recibo",
            cpf="222.333.444-55",
            user=self.bolsista_user
        )
        DadoBancario.objects.create(
            pessoa=self.pessoa,
            finalidade='PAGAMENTO_BOLSA',
            banco_codigo='001',
            agencia='1234',
            conta='56789-0',
            ativo=True
        )
        cota = CotaBolsaPT.objects.create(
            projeto=self.projeto,
            perfil_funcao="Pesquisador",
            quantidade_vagas=1,
            parcelas_previstas=1,
            valor_global_previsto=Decimal("1500.00")
        )
        termo = TermoBolsa.objects.create(
            cota_pt=cota,
            pessoa=self.pessoa,
            numero_termo="TB-RECIBO-001",
            vigencia_inicio=date(2026, 9, 1),
            vigencia_fim=date(2026, 9, 30),
            quantidade_parcelas=1,
            valor_parcela=Decimal("1500.00")
        )
        self.parcela = termo.parcelas.get(numero=1)
        self.parcela.status = 'PAGO'
        self.parcela.data_pagamento = date(2026, 9, 30)
        self.parcela.save()
        self.url = reverse(
            'gestao_projetos:visualizar_recibo_bolsa',
            args=[self.parcela.id]
        )

    def test_bolsista_titular_visualiza_recibo_com_hash(self):
        self.client.login(username='bolsista_recibo', password='senha123')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        esperado = hashlib.sha256(
            f"{self.parcela.id}-{self.parcela.data_pagamento}-"
            f"{self.parcela.valor}-{self.pessoa.cpf}".encode()
        ).hexdigest()[:16].upper()
        self.assertEqual(response.context['hash_doc'], esperado)
        self.assertContains(response, esperado)

    def test_terceiro_recebe_forbidden(self):
        self.client.login(username='terceiro_recibo', password='senha123')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_parcela_nao_paga_redireciona_para_folha(self):
        self.parcela.status = 'PENDENTE'
        self.parcela.save()
        self.client.login(username='bolsista_recibo', password='senha123')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('folha-pagamento', response.url)


from gestao_projetos.models import TemplateDocumentoConveniar, OficioSolicitacao
from gestao_projetos.views import DIRETOR_POLO_NOME, DIRETOR_POLO_CARGO, REITOR_NOME, REITOR_CARGO


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
    MEDIA_ROOT='/tmp/argus_test_media/'
)
class OficiosConveniarTestCase(TestCase):
    """
    Testes de integração da Emissão de Ofícios de Pagamento (Passo 4).
    Cobre: geração de ofício de equipe, bloqueio de duplicidade,
    alçada Reitor vs Diretor do Polo, e integridade do TemplateDocumentoConveniar.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='gestor_oficio', password='senha123')

        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Ofício LTDA",
            cnpj="44.555.666/0001-77",
            natureza_juridica="LTDA",
            representante_legal="Rep Ofício",
            cargo_representante="Gerente"
        )
        # Coordenador do projeto (PessoaFisica separada do bolsista)
        self.coordenador = PessoaFisica.objects.create(
            nome="Coord Projeto",
            cpf="999.888.777-66"
        )
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto Ofício Teste",
            fase="EXECUCAO",
            concedente=self.empresa,
            coordenador=self.coordenador
        )
        MembroEquipe.objects.create(projeto=self.projeto, usuario=self.user, papel='GESTOR')

        self.conta = ContaBancaria.objects.create(projeto=self.projeto, conta="11111", dv="1")

        # Bolsista (diferente do Coordenador)
        self.bolsista = PessoaFisica.objects.create(nome="Bolsista Ofício", cpf="123.456.789-00")
        DadoBancario.objects.create(
            pessoa=self.bolsista, finalidade='PAGAMENTO_BOLSA',
            banco_codigo='001', agencia='0001', conta='12345-6', ativo=True
        )

        self.cota = CotaBolsaPT.objects.create(
            projeto=self.projeto, perfil_funcao="Desenvolvedor",
            quantidade_vagas=1, parcelas_previstas=3,
            valor_global_previsto=Decimal("4500.00")
        )
        self.termo = TermoBolsa.objects.create(
            cota_pt=self.cota, pessoa=self.bolsista,
            numero_termo="TB-OFICIO-001",
            vigencia_inicio=date(2026, 9, 1),
            vigencia_fim=date(2026, 11, 30),
            quantidade_parcelas=3,
            valor_parcela=Decimal("1500.00")
        )
        self.parcela = self.termo.parcelas.get(numero=1)

        # RA CONCLUIDO vinculado à parcela
        self.ra = RelatorioAtividade.objects.create(
            termo_bolsa=self.termo,
            parcela_referencia=self.parcela,
            criado_por=self.user,
            status='CONCLUIDO',
            periodo_inicio=date(2026, 9, 1),
            periodo_fim=date(2026, 9, 30),
            carga_horaria_periodo=160
        )

        self.client = Client()
        self.client.login(username='gestor_oficio', password='senha123')

        self.url_oficio_equipe = reverse('gestao_projetos:gerar_oficio_equipe')
        self.url_oficio_coord = reverse('gestao_projetos:gerar_oficio_coordenador')

    # ------------------------------------------------------------------
    # Teste 1: Geração de Ofício de Equipe — caminho feliz
    # ------------------------------------------------------------------
    def test_gerar_oficio_equipe_sucesso(self):
        """Gera ofício de equipe com parcela válida (RA CONCLUIDO, sem ofício prévio)."""
        response = self.client.post(self.url_oficio_equipe, {
            'projeto_id': self.projeto.id,
            'mes_ano': '2026-09',
            'parcela_ids': [self.parcela.id],
        })
        # Deve redirecionar para download do ofício
        self.assertEqual(response.status_code, 302)

        # OficioSolicitacao criado
        oficio = OficioSolicitacao.objects.filter(projeto=self.projeto, tipo='EQUIPE').first()
        self.assertIsNotNone(oficio)
        self.assertEqual(oficio.numero_sequencial, 1)
        self.assertEqual(oficio.ano, date.today().year)
        self.assertIn(self.parcela, oficio.parcelas.all())

        # Competência correta
        self.assertEqual(oficio.competencia, date(2026, 9, 1))

        # Signatário = coordenador do projeto
        self.assertEqual(oficio.signatario_nome, self.coordenador.nome)

        # Visto = Coordenador de RH (conforme RegrasAlcadaDocumento seed para OFICIO_EQUIPE)
        # A matriz dinâmica define COORD_RH como visto para ofícios de equipe
        self.assertNotEqual(oficio.visto_nome, '')

    # ------------------------------------------------------------------
    # Teste 2: Bloqueio de duplicidade
    # ------------------------------------------------------------------
    def test_bloqueio_duplicidade_oficio(self):
        """Uma parcela já despachada em ofício não pode entrar em novo ofício."""
        # Primeira geração
        self.client.post(self.url_oficio_equipe, {
            'projeto_id': self.projeto.id,
            'mes_ano': '2026-09',
            'parcela_ids': [self.parcela.id],
        })
        self.assertEqual(OficioSolicitacao.objects.filter(projeto=self.projeto).count(), 1)

        # Segunda tentativa com a mesma parcela
        response = self.client.post(self.url_oficio_equipe, {
            'projeto_id': self.projeto.id,
            'mes_ano': '2026-09',
            'parcela_ids': [self.parcela.id],
        })
        # Deve redirecionar com erro (nenhuma parcela válida)
        self.assertEqual(response.status_code, 302)
        # Nenhum ofício adicional criado
        self.assertEqual(OficioSolicitacao.objects.filter(projeto=self.projeto).count(), 1)

        # Mensagem de erro emitida
        msgs = list(response.wsgi_request._messages)
        self.assertTrue(
            any('Nenhuma parcela válida' in str(m) or 'despachada' in str(m) for m in msgs),
            "Esperava mensagem de bloqueio de duplicidade"
        )

    # ------------------------------------------------------------------
    # Teste 3: Alçada — Coordenador é Diretor-Geral de Campus → Reitor assina
    # ------------------------------------------------------------------
    def test_alcada_reitor_quando_coordenador_diretor_campus(self):
        """Quando coordenador_is_diretor_campus=True, Reitor assina como Requisitante."""
        # Precisamos de uma parcela para o coordenador (termo separado)
        termo_coord = TermoBolsa.objects.create(
            cota_pt=self.cota, pessoa=self.coordenador,
            numero_termo="TB-COORD-001",
            vigencia_inicio=date(2026, 9, 1),
            vigencia_fim=date(2026, 11, 30),
            quantidade_parcelas=3,
            valor_parcela=Decimal("1500.00")
        )
        parcela_coord = termo_coord.parcelas.get(numero=1)
        RelatorioAtividade.objects.create(
            termo_bolsa=termo_coord,
            parcela_referencia=parcela_coord,
            criado_por=self.user,
            status='CONCLUIDO',
            periodo_inicio=date(2026, 9, 1),
            periodo_fim=date(2026, 9, 30),
            carga_horaria_periodo=160
        )

        response = self.client.post(self.url_oficio_coord, {
            'projeto_id': self.projeto.id,
            'mes_ano': '2026-09',
            'parcela_coordenador_id': parcela_coord.id,
            'coordenador_is_diretor_campus': '1',
        })
        self.assertEqual(response.status_code, 302)

        oficio = OficioSolicitacao.objects.filter(projeto=self.projeto, tipo='COORDENADOR').first()
        self.assertIsNotNone(oficio)
        self.assertTrue(oficio.coordenador_is_diretor_campus)
        # Reitor é o signatário
        self.assertEqual(oficio.signatario_nome, REITOR_NOME)
        self.assertEqual(oficio.signatario_cargo, REITOR_CARGO)
        # Visto = Diretor do Polo (assiste ao Reitor)
        self.assertEqual(oficio.visto_nome, DIRETOR_POLO_NOME)

    # ------------------------------------------------------------------
    # Teste 4: Alçada padrão — Coordenador é docente → Diretor do Polo assina
    # ------------------------------------------------------------------
    def test_alcada_diretor_polo_quando_coordenador_docente(self):
        """Quando coordenador_is_diretor_campus=False, Diretor do Polo assina."""
        termo_coord = TermoBolsa.objects.create(
            cota_pt=self.cota, pessoa=self.coordenador,
            numero_termo="TB-COORD-002",
            vigencia_inicio=date(2026, 9, 1),
            vigencia_fim=date(2026, 11, 30),
            quantidade_parcelas=3,
            valor_parcela=Decimal("1500.00")
        )
        parcela_coord = termo_coord.parcelas.get(numero=1)
        RelatorioAtividade.objects.create(
            termo_bolsa=termo_coord,
            parcela_referencia=parcela_coord,
            criado_por=self.user,
            status='CONCLUIDO',
            periodo_inicio=date(2026, 9, 1),
            periodo_fim=date(2026, 9, 30),
            carga_horaria_periodo=160
        )

        response = self.client.post(self.url_oficio_coord, {
            'projeto_id': self.projeto.id,
            'mes_ano': '2026-09',
            'parcela_coordenador_id': parcela_coord.id,
            # SEM 'coordenador_is_diretor_campus'
        })
        self.assertEqual(response.status_code, 302)

        oficio = OficioSolicitacao.objects.filter(projeto=self.projeto, tipo='COORDENADOR').first()
        self.assertIsNotNone(oficio)
        self.assertFalse(oficio.coordenador_is_diretor_campus)
        # Diretor do Polo é o signatário
        self.assertEqual(oficio.signatario_nome, DIRETOR_POLO_NOME)
        self.assertEqual(oficio.signatario_cargo, DIRETOR_POLO_CARGO)
        # Sem visto (campo vazio para este caso)
        self.assertEqual(oficio.visto_nome, "")


from gestao_projetos.models import FuncaoInstitucional, OcupacaoFuncao, AfastamentoExercicio


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class GovernancaSuplenciaTestCase(TestCase):
    """
    Testes unitários da lógica de governança institucional e suplência legal.
    Cobre:
    a) Resolução do Titular em data sem afastamento (prioridade 0).
    b) Chaveamento automático para o 1º Substituto em data de afastamento do titular.
    c) Chaveamento para o 2º Substituto em caso de afastamento simultâneo de titular e 1º substituto.
    d) Verificação de que o ofício de equipe usa o substituto em exercício via matriz dinâmica.
    """

    def setUp(self):
        # Função institucional de teste
        self.funcao = FuncaoInstitucional.objects.create(
            codigo='DIRETOR_TESTE',
            nome_cargo='Diretor de Teste',
            ativo=True
        )
        # Titular
        self.ocupacao_titular = OcupacaoFuncao.objects.create(
            funcao=self.funcao,
            nome_externo='Titular Silva',
            prioridade=0,
            portaria_designacao='Portaria 001/2026',
            sufixo_cargo='',
            ativo=True
        )
        # 1º Substituto
        self.ocupacao_sub1 = OcupacaoFuncao.objects.create(
            funcao=self.funcao,
            nome_externo='Substituto 1 Costa',
            prioridade=1,
            portaria_designacao='Portaria 002/2026',
            sufixo_cargo='1º Substituto',
            ativo=True
        )
        # 2º Substituto
        self.ocupacao_sub2 = OcupacaoFuncao.objects.create(
            funcao=self.funcao,
            nome_externo='Substituto 2 Lima',
            prioridade=2,
            portaria_designacao='Portaria 003/2026',
            sufixo_cargo='2º Substituto',
            ativo=True
        )

    # ------------------------------------------------------------------
    # Teste a) Titular em exercício quando não há afastamento
    # ------------------------------------------------------------------
    def test_retorna_titular_sem_afastamento(self):
        """Sem afastamentos, obter_responsavel_em_exercicio deve retornar o Titular."""
        data = date(2026, 9, 15)
        responsavel = self.funcao.obter_responsavel_em_exercicio(data)

        self.assertEqual(responsavel['prioridade'], 0)
        self.assertEqual(responsavel['nome'], 'Titular Silva')
        self.assertEqual(responsavel['cargo_display'], 'Diretor de Teste')

    # ------------------------------------------------------------------
    # Teste b) 1º Substituto quando titular está afastado
    # ------------------------------------------------------------------
    def test_chaveamento_para_substituto_1_em_afastamento_do_titular(self):
        """Com titular afastado na data, deve retornar o 1º Substituto."""
        AfastamentoExercicio.objects.create(
            ocupacao=self.ocupacao_titular,
            data_inicio=date(2026, 9, 10),
            data_fim=date(2026, 9, 20),
            motivo='FERIAS',
            ativo=True
        )
        data = date(2026, 9, 15)
        responsavel = self.funcao.obter_responsavel_em_exercicio(data)

        self.assertEqual(responsavel['prioridade'], 1)
        self.assertEqual(responsavel['nome'], 'Substituto 1 Costa')
        # Cargo deve mencionar "1º Substituto" e a portaria
        self.assertIn('1º Substituto', responsavel['cargo_display'])
        self.assertIn('Portaria 002/2026', responsavel['cargo_display'])

    # ------------------------------------------------------------------
    # Teste c) 2º Substituto quando titular e 1º substituto estão afastados
    # ------------------------------------------------------------------
    def test_chaveamento_para_substituto_2_afastamento_simultaneo(self):
        """Com titular E 1º substituto afastados, deve retornar o 2º Substituto."""
        AfastamentoExercicio.objects.create(
            ocupacao=self.ocupacao_titular,
            data_inicio=date(2026, 9, 1),
            data_fim=date(2026, 9, 30),
            motivo='LICENCA_MEDICA',
            ativo=True
        )
        AfastamentoExercicio.objects.create(
            ocupacao=self.ocupacao_sub1,
            data_inicio=date(2026, 9, 1),
            data_fim=date(2026, 9, 30),
            motivo='MISSAO',
            ativo=True
        )
        data = date(2026, 9, 15)
        responsavel = self.funcao.obter_responsavel_em_exercicio(data)

        self.assertEqual(responsavel['prioridade'], 2)
        self.assertEqual(responsavel['nome'], 'Substituto 2 Lima')
        self.assertIn('2º Substituto', responsavel['cargo_display'])

    # ------------------------------------------------------------------
    # Teste d) Titular retorna fora do período de afastamento
    # ------------------------------------------------------------------
    def test_titular_fora_do_periodo_de_afastamento(self):
        """Afastamento existente mas fora do intervalo — titular deve ser retornado."""
        AfastamentoExercicio.objects.create(
            ocupacao=self.ocupacao_titular,
            data_inicio=date(2026, 9, 1),
            data_fim=date(2026, 9, 14),  # terminou antes da data de referência
            motivo='FERIAS',
            ativo=True
        )
        data = date(2026, 9, 15)  # um dia depois do fim do afastamento
        responsavel = self.funcao.obter_responsavel_em_exercicio(data)

        self.assertEqual(responsavel['prioridade'], 0)
        self.assertEqual(responsavel['nome'], 'Titular Silva')


from cadastros.models import PessoaFisica, PerfilServidor


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class AtestoSIAPETestCase(TestCase):
    """
    Testes de integração do Passo 6 — Atesto SIAPE do Relatório de Atividades.

    Cobre:
    a) Atesto bem-sucedido por servidor SIAPE (campos gravados, status CONCLUIDO).
    b) Bloqueio de auto-atesto: bolsista tenta atestar o próprio relatório.
    c) Bloqueio de edição após CONCLUIDO (alterar_relatorio redirecionado).
    d) Bloqueio de usuário sem SIAPE (não é servidor efetivo).
    e) Idempotência: relatório já CONCLUIDO não muda ao chamar atestar novamente.
    f) Superusuário acessa visualizar_relatorio mesmo sem MembroEquipe.
    """

    def setUp(self):
        # ── Servidor efetivo com SIAPE (atestante) ──
        self.user_servidor = User.objects.create_user(
            username='servidor_siape',
            password='senha123',
            first_name='Ana',
            last_name='Servidora',
        )
        self.pessoa_servidor = PessoaFisica.objects.create(
            nome='Ana Servidora',
            cpf='000.111.222-33',
            user=self.user_servidor,
        )
        PerfilServidor.objects.create(
            pessoa=self.pessoa_servidor,
            siape='1234567',
            cargo='Coordenador de Pesquisa',
            lotacao='IFAM/Manaus',
            ativo=True,
        )

        # ── Bolsista com User vinculado (para teste de SoD) ──
        self.user_bolsista = User.objects.create_user(
            username='bolsista_passo6',
            password='senha123',
        )
        self.pessoa_bolsista = PessoaFisica.objects.create(
            nome='Carlos Bolsista',
            cpf='444.555.666-77',
            user=self.user_bolsista,
        )
        DadoBancario.objects.create(
            pessoa=self.pessoa_bolsista,
            finalidade='PAGAMENTO_BOLSA',
            banco_codigo='001',
            agencia='0001',
            conta='11111-1',
            ativo=True,
        )

        # ── Estrutura do projeto ──
        self.empresa = EmpresaParceira.objects.create(
            nome='Empresa Atesto LTDA',
            cnpj='99.888.777/0001-66',
            natureza_juridica='LTDA',
            representante_legal='Rep Atesto',
            cargo_representante='Diretor',
        )
        self.projeto = ProjetoPDI.objects.create(
            nome='Projeto Atesto Passo 6',
            fase='EXECUCAO',
            concedente=self.empresa,
        )

        # ── RBAC: servidor é membro da equipe ──
        MembroEquipe.objects.create(
            projeto=self.projeto,
            usuario=self.user_servidor,
            papel='GESTOR',
        )
        # Bolsista também é membro (para conseguir chamar URLs)
        MembroEquipe.objects.create(
            projeto=self.projeto,
            usuario=self.user_bolsista,
            papel='COLABORADOR',
        )

        # ── Cota, Termo e Parcela ──
        self.cota = CotaBolsaPT.objects.create(
            projeto=self.projeto,
            perfil_funcao='Pesquisador Junior',
            quantidade_vagas=1,
            parcelas_previstas=2,
            valor_global_previsto=Decimal('3000.00'),
        )
        self.termo = TermoBolsa.objects.create(
            cota_pt=self.cota,
            pessoa=self.pessoa_bolsista,
            numero_termo='TB-ATESTO-001',
            vigencia_inicio=date(2026, 9, 1),
            vigencia_fim=date(2026, 10, 31),
            quantidade_parcelas=2,
            valor_parcela=Decimal('1500.00'),
        )
        self.parcela = self.termo.parcelas.get(numero=1)

        # ── Relatório PENDENTE base ──
        self.relatorio = RelatorioAtividade.objects.create(
            termo_bolsa=self.termo,
            parcela_referencia=self.parcela,
            criado_por=self.user_servidor,
            status='PENDENTE',
            periodo_inicio=date(2026, 9, 1),
            periodo_fim=date(2026, 9, 30),
            carga_horaria_periodo=160,
        )

        # URLs
        self.url_atestar = reverse(
            'gestao_projetos:atestar_relatorio',
            args=[self.relatorio.id],
        )
        self.url_alterar = reverse(
            'gestao_projetos:alterar_relatorio',
            args=[self.relatorio.id],
        )
        self.url_visualizar = reverse(
            'gestao_projetos:visualizar_relatorio',
            args=[self.relatorio.id],
        )

        self.client = Client()

    # ------------------------------------------------------------------ #
    # Teste a) Atesto bem-sucedido por servidor SIAPE                     #
    # ------------------------------------------------------------------ #
    def test_atesto_siape_sucesso(self):
        """Servidor SIAPE ativo atesta o relatório: campos gravados e status=CONCLUIDO."""
        self.client.login(username='servidor_siape', password='senha123')

        response = self.client.post(self.url_atestar, {
            'cumpriu_carga_horaria': '1',
            'parecer_coordenador': 'Desempenho excelente.',
        })

        # Deve redirecionar para visualizar
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            str(self.relatorio.id),
            response['Location'],
            "Deve redirecionar para visualizar_relatorio após atesto."
        )

        # Verifica campos gravados no banco
        self.relatorio.refresh_from_db()
        self.assertEqual(self.relatorio.status, 'CONCLUIDO')
        self.assertEqual(self.relatorio.atestado_por, self.user_servidor)
        self.assertEqual(self.relatorio.siape_atesto, '1234567')
        self.assertIsNotNone(self.relatorio.data_atesto)
        self.assertTrue(self.relatorio.cumpriu_carga_horaria)
        self.assertEqual(self.relatorio.parecer_coordenador, 'Desempenho excelente.')

        # Mensagem de sucesso emitida
        msgs = list(response.wsgi_request._messages)
        self.assertTrue(
            any('homologado com sucesso' in str(m) for m in msgs),
            "Esperava mensagem de homologação bem-sucedida."
        )

    # ------------------------------------------------------------------ #
    # Teste b) Bloqueio de auto-atesto do bolsista (SoD)                  #
    # ------------------------------------------------------------------ #
    def test_bloqueio_auto_atesto_bolsista(self):
        """O próprio bolsista não pode atestar seu relatório (SoD)."""
        self.client.login(username='bolsista_passo6', password='senha123')

        # Precisamos dar SIAPE ao bolsista para que ele passe a verificação de servidor
        # (testamos especificamente a regra de SoD, não a de ausência de SIAPE)
        PerfilServidor.objects.create(
            pessoa=self.pessoa_bolsista,
            siape='9999999',
            cargo='Técnico',
            lotacao='IFAM/Manaus',
            ativo=True,
        )

        response = self.client.post(self.url_atestar, {
            'cumpriu_carga_horaria': '1',
            'parecer_coordenador': 'Auto-atesto indevido.',
        })

        # Deve redirecionar de volta para visualizar (não atestar)
        self.assertEqual(response.status_code, 302)

        # Status NÃO pode ter mudado para CONCLUIDO
        self.relatorio.refresh_from_db()
        self.assertEqual(
            self.relatorio.status, 'PENDENTE',
            "Auto-atesto deve ser bloqueado — relatório deve permanecer PENDENTE."
        )
        self.assertIsNone(
            self.relatorio.atestado_por,
            "atestado_por não deve ser gravado em caso de auto-atesto."
        )

        # Mensagem de erro de SoD emitida
        msgs = list(response.wsgi_request._messages)
        self.assertTrue(
            any('Segregação de Funções' in str(m) for m in msgs),
            "Esperava mensagem de violação de Segregação de Funções."
        )

    # ------------------------------------------------------------------ #
    # Teste c) Bloqueio de edição após CONCLUIDO (trava de congelamento)  #
    # ------------------------------------------------------------------ #
    def test_bloqueio_alterar_relatorio_concluido(self):
        """alterar_relatorio deve bloquear e redirecionar quando status=CONCLUIDO."""
        # Atesta manualmente o relatório
        self.relatorio.status = 'CONCLUIDO'
        self.relatorio.atestado_por = self.user_servidor
        self.relatorio.siape_atesto = '1234567'
        self.relatorio.save()

        self.client.login(username='servidor_siape', password='senha123')

        # POST de alteração (tenta fazer upload de PDF)
        response = self.client.post(self.url_alterar, {})

        # Deve redirecionar (sem 200, pois a view bloqueia antes do processamento)
        self.assertEqual(response.status_code, 302)

        # Relatório deve continuar CONCLUIDO e intacto
        self.relatorio.refresh_from_db()
        self.assertEqual(
            self.relatorio.status, 'CONCLUIDO',
            "Relatório CONCLUIDO não deve poder ser alterado."
        )

        # Mensagem de aviso de congelamento
        msgs = list(response.wsgi_request._messages)
        self.assertTrue(
            any('congelado' in str(m).lower() or 'homologado' in str(m).lower() for m in msgs),
            "Esperava mensagem de congelamento/homologação."
        )

    # ------------------------------------------------------------------ #
    # Teste d) Bloqueio de usuário sem SIAPE                              #
    # ------------------------------------------------------------------ #
    def test_bloqueio_atesto_usuario_sem_siape(self):
        """Usuário sem perfil de servidor SIAPE não pode atestar."""
        # Cria usuário simples sem PerfilServidor
        user_sem_siape = User.objects.create_user(
            username='sem_siape_p6',
            password='senha123',
        )
        pessoa_sem_siape = PessoaFisica.objects.create(
            nome='Pedro Sem SIAPE',
            cpf='777.888.999-00',
            user=user_sem_siape,
        )
        MembroEquipe.objects.create(
            projeto=self.projeto,
            usuario=user_sem_siape,
            papel='COLABORADOR',
        )

        self.client.login(username='sem_siape_p6', password='senha123')

        response = self.client.post(self.url_atestar, {
            'cumpriu_carga_horaria': '1',
        })

        # Deve redirecionar (sem atestar)
        self.assertEqual(response.status_code, 302)

        # Status permanece PENDENTE
        self.relatorio.refresh_from_db()
        self.assertEqual(
            self.relatorio.status, 'PENDENTE',
            "Usuário sem SIAPE não deve conseguir atestar."
        )

        # Mensagem de acesso negado
        msgs = list(response.wsgi_request._messages)
        self.assertTrue(
            any('SIAPE' in str(m) or 'Servidores Efetivos' in str(m) for m in msgs),
            "Esperava mensagem de acesso negado por ausência de SIAPE."
        )

    # ------------------------------------------------------------------ #
    # Teste e) Idempotência: atestar relatório já CONCLUIDO               #
    # ------------------------------------------------------------------ #
    def test_atesto_idempotente_relatorio_ja_concluido(self):
        """Atestar um relatório já CONCLUIDO não deve alterar os dados originais."""
        # Atesta primeiro pelo servidor correto
        self.relatorio.status = 'CONCLUIDO'
        self.relatorio.atestado_por = self.user_servidor
        self.relatorio.siape_atesto = '1234567'
        from django.utils import timezone
        data_original = timezone.now()
        self.relatorio.data_atesto = data_original
        self.relatorio.parecer_coordenador = 'Parecer original.'
        self.relatorio.save()

        self.client.login(username='servidor_siape', password='senha123')

        # Tenta atestar novamente
        response = self.client.post(self.url_atestar, {
            'cumpriu_carga_horaria': '0',
            'parecer_coordenador': 'Tentativa de sobrescrita.',
        })

        self.assertEqual(response.status_code, 302)

        # Dados originais devem ter sido preservados
        self.relatorio.refresh_from_db()
        self.assertEqual(self.relatorio.status, 'CONCLUIDO')
        self.assertEqual(
            self.relatorio.parecer_coordenador, 'Parecer original.',
            "Parecer original não deve ser sobrescrito em atesto idempotente."
        )
        self.assertTrue(
            self.relatorio.cumpriu_carga_horaria,
            "cumpriu_carga_horaria original não deve ser alterado."
        )

        # Mensagem informativa emitida
        msgs = list(response.wsgi_request._messages)
        self.assertTrue(
            any('já está homologado' in str(m) for m in msgs),
            "Esperava mensagem informando que relatório já está homologado."
        )

    # ------------------------------------------------------------------ #
    # Teste f) Superusuário acessa visualizar_relatorio sem MembroEquipe  #
    # ------------------------------------------------------------------ #
    def test_superuser_acessa_visualizar_sem_membro_equipe(self):
        """Superusuário deve acessar visualizar_relatorio mesmo sem MembroEquipe."""
        superuser = User.objects.create_superuser(
            username='super_p6',
            password='senha123',
            email='super_p6@ifam.edu.br',
        )
        self.client.login(username='super_p6', password='senha123')

        response = self.client.get(self.url_visualizar)

        # Deve retornar 200 (acesso permitido)
        self.assertEqual(
            response.status_code, 200,
            "Superusuário deve ter acesso ao visualizar_relatorio sem MembroEquipe."
        )
        self.assertIn('relatorio_obj', response.context)

    # ------------------------------------------------------------------ #
    # Teste g) GET em atestar_relatorio redireciona para visualizar       #
    # ------------------------------------------------------------------ #
    def test_get_atestar_redireciona_para_visualizar(self):
        """GET na URL de atesto deve redirecionar para visualizar (sem atestar)."""
        self.client.login(username='servidor_siape', password='senha123')

        response = self.client.get(self.url_atestar)

        self.assertEqual(response.status_code, 302)
        # Não deve ter atestado
        self.relatorio.refresh_from_db()
        self.assertEqual(self.relatorio.status, 'PENDENTE')

    # ------------------------------------------------------------------ #
    # Teste h) GET em alterar_relatorio quando CONCLUIDO também bloqueia  #
    # ------------------------------------------------------------------ #
    def test_get_alterar_relatorio_concluido_bloqueado(self):
        """GET em alterar_relatorio com status CONCLUIDO deve redirecionar."""
        self.relatorio.status = 'CONCLUIDO'
        self.relatorio.save()

        self.client.login(username='servidor_siape', password='senha123')

        response = self.client.get(self.url_alterar)

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            str(self.relatorio.id),
            response['Location'],
            "Deve redirecionar para visualizar_relatorio."
        )

    # ------------------------------------------------------------------ #
    # Teste i) Atesto com cumpriu=0 grava corretamente False              #
    # ------------------------------------------------------------------ #
    def test_atesto_cumpriu_carga_horaria_nao(self):
        """Atesto com cumpriu_carga_horaria='0' deve gravar False no banco."""
        self.client.login(username='servidor_siape', password='senha123')

        self.client.post(self.url_atestar, {
            'cumpriu_carga_horaria': '0',
            'parecer_coordenador': 'Bolsista não cumpriu a carga horária do período.',
        })

        self.relatorio.refresh_from_db()
        self.assertEqual(self.relatorio.status, 'CONCLUIDO')
        self.assertFalse(
            self.relatorio.cumpriu_carga_horaria,
            "Quando cumpriu_carga_horaria='0', deve gravar False."
        )


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class LiquidacaoFolhaLoteTestCase(TestCase):
    """
    Testes de integração do Passo 7 — Liquidação e Baixa em Lote da Folha de Bolsas.

    Cobre:
    a) Baixa em lote com sucesso (2 parcelas com RA CONCLUIDO).
    b) Trava: parcela com RA PENDENTE aborta toda a operação (fail-fast).
    c) Trava: parcela sem RA aborta toda a operação.
    d) Idempotência: parcelas já PAGAS são ignoradas silenciosamente.
    e) Recálculo dos KPIs da folha após a liquidação.
    f) Bloqueio de usuário sem permissão de equipe (RBAC).
    g) GET na URL redireciona sem efetuar nenhuma baixa.
    h) Lista vazia de parcelas retorna erro sem alterar nada.
    i) Baixa em lote com comprovante — arquivo associado à parcela.
    j) Liquidação parcial: 1 apta + 1 não-apta aborta sem baixar nenhuma.
    """

    def _criar_empresa(self, sufixo):
        """Cria EmpresaParceira única para cada TestCase."""
        import time
        cnpj_n = f"{abs(hash(sufixo)) % 100000000000000:014d}"
        cnpj = f"{cnpj_n[:2]}.{cnpj_n[2:8]}/{cnpj_n[8:12]}-{cnpj_n[12:14]}"
        from cadastros.models import EmpresaParceira as EP
        return EP.objects.create(
            nome=f"Empresa Lote {sufixo}",
            nome_fantasia=f"EL {sufixo}",
            cnpj=cnpj,
            natureza_juridica="LTDA",
            endereco="Rua Lote, 7",
            representante_legal="Rep Lote",
            cargo_representante="Dir",
        )

    def setUp(self):
        # ── Usuário gestor (membro da equipe) ──
        self.user_gestor = User.objects.create_user(
            username='gestor_lote_p7',
            password='senha123',
        )

        # ── Projeto ──
        self.empresa = self._criar_empresa("P7")
        self.projeto = ProjetoPDI.objects.create(
            nome='Projeto Lote Passo 7',
            fase='EXECUCAO',
            concedente=self.empresa,
        )
        MembroEquipe.objects.create(
            projeto=self.projeto,
            usuario=self.user_gestor,
            papel='GESTOR',
        )

        # ── Conta bancária do projeto ──
        self.conta = ContaBancaria.objects.create(
            projeto=self.projeto,
            conta='77777',
            dv='7',
        )

        # ── Bolsista A ──
        self.pessoa_a = PessoaFisica.objects.create(
            nome='Bolsista A Lote',
            cpf='100.200.300-40',
        )
        DadoBancario.objects.create(
            pessoa=self.pessoa_a,
            finalidade='PAGAMENTO_BOLSA',
            banco_codigo='001',
            agencia='0001',
            conta='10001-0',
            ativo=True,
        )

        # ── Bolsista B ──
        self.pessoa_b = PessoaFisica.objects.create(
            nome='Bolsista B Lote',
            cpf='500.600.700-80',
        )
        DadoBancario.objects.create(
            pessoa=self.pessoa_b,
            finalidade='PAGAMENTO_BOLSA',
            banco_codigo='033',
            agencia='0002',
            conta='20002-0',
            ativo=True,
        )

        # ── Cota e Termos ──
        self.cota = CotaBolsaPT.objects.create(
            projeto=self.projeto,
            perfil_funcao='Analista Lote',
            quantidade_vagas=2,
            parcelas_previstas=2,
            valor_global_previsto=Decimal('6000.00'),
        )
        self.termo_a = TermoBolsa.objects.create(
            cota_pt=self.cota,
            pessoa=self.pessoa_a,
            numero_termo='TB-LOTE-A',
            vigencia_inicio=date(2026, 9, 1),
            vigencia_fim=date(2026, 10, 31),
            quantidade_parcelas=2,
            valor_parcela=Decimal('1500.00'),
        )
        self.termo_b = TermoBolsa.objects.create(
            cota_pt=self.cota,
            pessoa=self.pessoa_b,
            numero_termo='TB-LOTE-B',
            vigencia_inicio=date(2026, 9, 1),
            vigencia_fim=date(2026, 10, 31),
            quantidade_parcelas=2,
            valor_parcela=Decimal('1500.00'),
        )

        # Parcela 1 de cada bolsista
        self.parcela_a = self.termo_a.parcelas.get(numero=1)
        self.parcela_b = self.termo_b.parcelas.get(numero=1)

        # ── RAs CONCLUIDOS para ambos ──
        self.ra_a = RelatorioAtividade.objects.create(
            termo_bolsa=self.termo_a,
            parcela_referencia=self.parcela_a,
            criado_por=self.user_gestor,
            status='CONCLUIDO',
            periodo_inicio=date(2026, 9, 1),
            periodo_fim=date(2026, 9, 30),
            carga_horaria_periodo=160,
        )
        self.ra_b = RelatorioAtividade.objects.create(
            termo_bolsa=self.termo_b,
            parcela_referencia=self.parcela_b,
            criado_por=self.user_gestor,
            status='CONCLUIDO',
            periodo_inicio=date(2026, 9, 1),
            periodo_fim=date(2026, 9, 30),
            carga_horaria_periodo=160,
        )

        self.url_lote = reverse(
            'gestao_projetos:liquidar_folha_lote',
            args=[self.projeto.id],
        )
        self.url_folha = reverse('gestao_projetos:folha_mensal_pagamentos')

        self.client = Client()
        self.client.login(username='gestor_lote_p7', password='senha123')

    # ------------------------------------------------------------------ #
    # Teste a) Baixa em lote com sucesso (2 parcelas, RA CONCLUIDO)       #
    # ------------------------------------------------------------------ #
    def test_baixa_lote_sucesso_duas_parcelas(self):
        """2 parcelas com RA CONCLUIDO são liquidadas em lote; status → PAGO."""
        response = self.client.post(self.url_lote, {
            'parcelas_ids': [self.parcela_a.id, self.parcela_b.id],
            'data_pagamento': '2026-09-30',
            'conta_pagamento': self.conta.id,
        })

        self.assertEqual(response.status_code, 302,
                         "Deve redirecionar após liquidação bem-sucedida.")

        self.parcela_a.refresh_from_db()
        self.parcela_b.refresh_from_db()
        self.assertEqual(self.parcela_a.status, 'PAGO',
                         "Parcela A deve estar PAGO após lote.")
        self.assertEqual(self.parcela_b.status, 'PAGO',
                         "Parcela B deve estar PAGO após lote.")
        self.assertEqual(self.parcela_a.data_pagamento, date(2026, 9, 30))
        self.assertEqual(self.parcela_b.data_pagamento, date(2026, 9, 30))
        self.assertEqual(self.parcela_a.conta_pagamento, self.conta)
        self.assertEqual(self.parcela_b.conta_pagamento, self.conta)

        msgs = list(response.wsgi_request._messages)
        self.assertTrue(
            any('2' in str(m) and 'liquidada' in str(m) for m in msgs),
            "Mensagem de sucesso deve mencionar 2 parcelas liquidadas."
        )

    # ------------------------------------------------------------------ #
    # Teste b) Trava: RA PENDENTE aborta toda a operação (fail-fast)      #
    # ------------------------------------------------------------------ #
    def test_trava_ra_pendente_aborta_lote(self):
        """Se uma parcela tem RA PENDENTE, nenhuma parcela do lote é baixada."""
        # Muda RA do bolsista A para PENDENTE
        self.ra_a.status = 'PENDENTE'
        self.ra_a.save()

        response = self.client.post(self.url_lote, {
            'parcelas_ids': [self.parcela_a.id, self.parcela_b.id],
            'data_pagamento': '2026-09-30',
            'conta_pagamento': self.conta.id,
        })

        self.assertEqual(response.status_code, 302)

        # Nenhuma parcela deve ter transitado para PAGO
        self.parcela_a.refresh_from_db()
        self.parcela_b.refresh_from_db()
        self.assertNotEqual(self.parcela_a.status, 'PAGO',
                            "Parcela A não deve ser baixada (RA pendente).")
        self.assertNotEqual(self.parcela_b.status, 'PAGO',
                            "Parcela B não deve ser baixada (operação abortada por fail-fast).")

        msgs = list(response.wsgi_request._messages)
        self.assertTrue(
            any('cancelada' in str(m).lower() or 'não possui RA homologado' in str(m) for m in msgs),
            "Mensagem de erro de trava de integridade deve ser emitida."
        )

    # ------------------------------------------------------------------ #
    # Teste c) Trava: parcela sem RA aborta toda a operação               #
    # ------------------------------------------------------------------ #
    def test_trava_sem_ra_aborta_lote(self):
        """Parcela sem RA nenhum aborta o lote inteiro."""
        self.ra_a.delete()

        response = self.client.post(self.url_lote, {
            'parcelas_ids': [self.parcela_a.id, self.parcela_b.id],
            'data_pagamento': '2026-09-30',
        })

        self.assertEqual(response.status_code, 302)

        self.parcela_a.refresh_from_db()
        self.parcela_b.refresh_from_db()
        self.assertNotEqual(self.parcela_a.status, 'PAGO')
        self.assertNotEqual(self.parcela_b.status, 'PAGO')

        msgs = list(response.wsgi_request._messages)
        self.assertTrue(
            any('cancelada' in str(m).lower() or 'RA homologado' in str(m) for m in msgs),
        )

    # ------------------------------------------------------------------ #
    # Teste d) Idempotência: parcelas já PAGAS são ignoradas              #
    # ------------------------------------------------------------------ #
    def test_idempotencia_parcela_ja_paga_ignorada(self):
        """Parcela já PAGA incluída no lote é ignorada; a outra é baixada normalmente."""
        # Marca parcela_a como já PAGA
        self.parcela_a.status = 'PAGO'
        self.parcela_a.data_pagamento = date(2026, 9, 15)
        self.parcela_a.save()

        response = self.client.post(self.url_lote, {
            'parcelas_ids': [self.parcela_a.id, self.parcela_b.id],
            'data_pagamento': '2026-09-30',
            'conta_pagamento': self.conta.id,
        })

        self.assertEqual(response.status_code, 302)

        # parcela_a permanece com a data original (não regravada)
        self.parcela_a.refresh_from_db()
        self.assertEqual(self.parcela_a.data_pagamento, date(2026, 9, 15),
                         "Data de pagamento original não deve ser sobrescrita.")

        # parcela_b é baixada
        self.parcela_b.refresh_from_db()
        self.assertEqual(self.parcela_b.status, 'PAGO',
                         "Parcela B deve ser baixada normalmente.")

        msgs = list(response.wsgi_request._messages)
        self.assertTrue(
            any('liquidada' in str(m) for m in msgs),
            "Mensagem de sucesso deve ser emitida."
        )

    # ------------------------------------------------------------------ #
    # Teste e) KPIs da folha refletem o estado após liquidação            #
    # ------------------------------------------------------------------ #
    def test_kpis_folha_apos_liquidacao_lote(self):
        """Após baixa em lote, total_liquidado e saldo_pendente refletem o novo estado."""
        # Liquida ambas via lote
        self.client.post(self.url_lote, {
            'parcelas_ids': [self.parcela_a.id, self.parcela_b.id],
            'data_pagamento': '2026-09-30',
            'conta_pagamento': self.conta.id,
        })

        # Acessa a folha e verifica KPIs
        response = self.client.get(
            self.url_folha,
            {'projeto_id': self.projeto.id, 'mes_ano': '2026-09'},
        )
        self.assertEqual(response.status_code, 200)

        total_liquidado = response.context['total_liquidado']
        saldo_pendente = response.context['saldo_pendente']
        total_folha = response.context['total_folha']

        self.assertEqual(total_liquidado, Decimal('3000.00'),
                         "Total liquidado deve ser R$ 3.000,00 após lote.")
        self.assertEqual(saldo_pendente, Decimal('0.00'),
                         "Saldo pendente deve ser zero após liquidação de todas as parcelas.")
        self.assertEqual(total_folha, Decimal('3000.00'))

    # ------------------------------------------------------------------ #
    # Teste f) RBAC — usuário sem permissão recebe 403                    #
    # ------------------------------------------------------------------ #
    def test_rbac_usuario_sem_permissao_bloqueado(self):
        """Usuário não membro da equipe recebe HttpResponseForbidden."""
        outro_user = User.objects.create_user(
            username='intruso_lote_p7',
            password='senha123',
        )
        self.client.login(username='intruso_lote_p7', password='senha123')

        response = self.client.post(self.url_lote, {
            'parcelas_ids': [self.parcela_a.id],
            'data_pagamento': '2026-09-30',
        })

        self.assertEqual(response.status_code, 403,
                         "Usuário sem permissão deve receber 403 Forbidden.")

        # Parcela não deve ter sido alterada
        self.parcela_a.refresh_from_db()
        self.assertNotEqual(self.parcela_a.status, 'PAGO')

    # ------------------------------------------------------------------ #
    # Teste g) GET na URL redireciona sem efetuar baixas                  #
    # ------------------------------------------------------------------ #
    def test_get_redireciona_sem_baixas(self):
        """GET na URL de lote redireciona sem alterar nenhuma parcela."""
        response = self.client.get(self.url_lote)

        self.assertEqual(response.status_code, 302)

        self.parcela_a.refresh_from_db()
        self.parcela_b.refresh_from_db()
        self.assertNotEqual(self.parcela_a.status, 'PAGO')
        self.assertNotEqual(self.parcela_b.status, 'PAGO')

    # ------------------------------------------------------------------ #
    # Teste h) Lista vazia de parcelas retorna erro sem alterar nada      #
    # ------------------------------------------------------------------ #
    def test_lista_vazia_retorna_erro(self):
        """POST sem parcelas_ids retorna mensagem de erro e não altera nada."""
        response = self.client.post(self.url_lote, {
            'parcelas_ids': [],
            'data_pagamento': '2026-09-30',
        })

        self.assertEqual(response.status_code, 302)

        self.parcela_a.refresh_from_db()
        self.assertNotEqual(self.parcela_a.status, 'PAGO')

        msgs = list(response.wsgi_request._messages)
        self.assertTrue(
            any('Selecione pelo menos' in str(m) for m in msgs),
            "Mensagem de erro por lista vazia deve ser emitida."
        )

    # ------------------------------------------------------------------ #
    # Teste i) Baixa em lote com comprovante — arquivo associado          #
    # ------------------------------------------------------------------ #
    def test_baixa_lote_com_comprovante(self):
        """Comprovante enviado é associado às parcelas liquidadas."""
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile

        comprovante = SimpleUploadedFile(
            'comprovante_lote.pdf',
            b'%PDF-1.4 fake content',
            content_type='application/pdf',
        )

        response = self.client.post(self.url_lote, {
            'parcelas_ids': [self.parcela_a.id, self.parcela_b.id],
            'data_pagamento': '2026-09-30',
            'conta_pagamento': self.conta.id,
            'comprovante_pagamento': comprovante,
        })

        self.assertEqual(response.status_code, 302)

        self.parcela_a.refresh_from_db()
        self.parcela_b.refresh_from_db()
        self.assertEqual(self.parcela_a.status, 'PAGO')
        self.assertEqual(self.parcela_b.status, 'PAGO')

        # Comprovante deve estar associado
        self.assertTrue(
            bool(self.parcela_a.comprovante_pagamento) or bool(self.parcela_b.comprovante_pagamento),
            "Pelo menos uma parcela deve ter comprovante associado."
        )

    # ------------------------------------------------------------------ #
    # Teste j) Liquidação parcial: 1 apta + 1 não-apta aborta tudo       #
    # ------------------------------------------------------------------ #
    def test_liquidacao_parcial_aborta_se_uma_nao_apta(self):
        """
        Mesmo que parcela_b tenha RA CONCLUIDO, a presença de parcela_a
        com RA PENDENTE deve abortar toda a operação (fail-fast atômico).
        """
        self.ra_a.status = 'PENDENTE'
        self.ra_a.save()

        response = self.client.post(self.url_lote, {
            'parcelas_ids': [self.parcela_a.id, self.parcela_b.id],
            'data_pagamento': '2026-09-30',
        })

        self.assertEqual(response.status_code, 302)

        # Ambas devem continuar PENDENTES — nenhuma parcela baixada
        self.parcela_a.refresh_from_db()
        self.parcela_b.refresh_from_db()
        self.assertNotEqual(self.parcela_a.status, 'PAGO',
                            "Parcela A não deve ter sido baixada.")
        self.assertNotEqual(self.parcela_b.status, 'PAGO',
                            "Parcela B NÃO deve ser baixada por atomicidade — fail-fast abortou o lote.")


# =====================================================================
# EXTRATO FINANCEIRO E CONCILIAÇÃO BANCÁRIA (Passo 9)
# =====================================================================

@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class ExtratoFinanceiroTestCase(TestCase):
    """
    Suíte de testes de integração do Passo 9 — Extrato Financeiro e
    Conciliação Bancária por Projeto.

    Cobre:
    a) KPIs corretos: aportes, desembolsos, comprometido e saldo disponível.
    b) Acesso permitido ao membro da equipe (RBAC positivo).
    c) Acesso negado a usuário sem vínculo ao projeto (RBAC negativo — 403).
    d) Filtro por conta bancária reduz as movimentações exibidas.
    e) Saldo disponível negativo quando desembolsos + comprometido excedem aportes.
    f) Link de recibo presente apenas para parcelas PAGO.
    """

    def setUp(self):
        # ── Usuários ──
        self.user_gestor = User.objects.create_user(
            username='gestor_extrato_p9',
            password='senha123',
        )
        self.user_intruso = User.objects.create_user(
            username='intruso_extrato_p9',
            password='senha123',
        )

        # ── Estrutura do projeto ──
        self.empresa = EmpresaParceira.objects.create(
            nome='Empresa Extrato P9 LTDA',
            cnpj='11.222.333/0001-44',
            natureza_juridica='LTDA',
            representante_legal='Rep Extrato',
            cargo_representante='Diretor',
        )
        self.projeto = ProjetoPDI.objects.create(
            nome='Projeto Extrato Passo 9',
            fase='EXECUCAO',
            concedente=self.empresa,
        )

        # ── RBAC: gestor é membro da equipe ──
        MembroEquipe.objects.create(
            projeto=self.projeto,
            usuario=self.user_gestor,
            papel='GESTOR',
        )

        # ── Plano de trabalho ativo com aportes ──
        from cadastros.models import PlanoDeTrabalho
        self.plano = PlanoDeTrabalho.objects.create(
            projeto=self.projeto,
            versao=1,
            ativo=True,
            aporte_empresa=Decimal('5000.00'),
            aporte_embrapii=Decimal('3000.00'),
            aporte_sebrae=Decimal('0.00'),
            aporte_contrapartida=Decimal('2000.00'),
        )
        # valor_global calculado automaticamente no save() = 10000.00

        # ── Duas contas bancárias distintas ──
        self.conta_a = ContaBancaria.objects.create(
            projeto=self.projeto,
            conta='11111',
            dv='1',
        )
        self.conta_b = ContaBancaria.objects.create(
            projeto=self.projeto,
            conta='22222',
            dv='2',
        )

        # ── Bolsistas e termos ──
        self.pessoa_a = PessoaFisica.objects.create(
            nome='Bolsista A',
            cpf='010.020.030-40',
        )
        self.pessoa_b = PessoaFisica.objects.create(
            nome='Bolsista B',
            cpf='050.060.070-80',
        )
        DadoBancario.objects.create(
            pessoa=self.pessoa_a, finalidade='PAGAMENTO_BOLSA',
            banco_codigo='001', agencia='0001', conta='11111-1', ativo=True,
        )
        DadoBancario.objects.create(
            pessoa=self.pessoa_b, finalidade='PAGAMENTO_BOLSA',
            banco_codigo='001', agencia='0002', conta='22222-2', ativo=True,
        )

        self.cota = CotaBolsaPT.objects.create(
            projeto=self.projeto,
            perfil_funcao='Pesquisador P9',
            quantidade_vagas=2,
            parcelas_previstas=2,
            valor_global_previsto=Decimal('4000.00'),
        )

        # Termo A — parcela PAGO via conta_a
        self.termo_a = TermoBolsa.objects.create(
            cota_pt=self.cota,
            pessoa=self.pessoa_a,
            numero_termo='TB-P9-001',
            vigencia_inicio=date(2026, 9, 1),
            vigencia_fim=date(2026, 10, 31),
            quantidade_parcelas=2,
            valor_parcela=Decimal('1500.00'),
        )
        self.parcela_a1 = self.termo_a.parcelas.get(numero=1)
        self.parcela_a1.status = 'PAGO'
        self.parcela_a1.data_pagamento = date(2026, 9, 30)
        self.parcela_a1.conta_pagamento = self.conta_a
        self.parcela_a1.save()

        # Parcela 2 permanece PENDENTE
        self.parcela_a2 = self.termo_a.parcelas.get(numero=2)

        # Termo B — parcela APROVADO via conta_b
        self.termo_b = TermoBolsa.objects.create(
            cota_pt=self.cota,
            pessoa=self.pessoa_b,
            numero_termo='TB-P9-002',
            vigencia_inicio=date(2026, 9, 1),
            vigencia_fim=date(2026, 10, 31),
            quantidade_parcelas=2,
            valor_parcela=Decimal('1000.00'),
        )
        self.parcela_b1 = self.termo_b.parcelas.get(numero=1)
        self.parcela_b1.status = 'APROVADO'
        self.parcela_b1.conta_pagamento = self.conta_b
        self.parcela_b1.save()

        self.client = Client()
        self.url = reverse(
            'gestao_projetos:extrato_financeiro_projeto',
            args=[self.projeto.id],
        )

    # ------------------------------------------------------------------ #
    # Teste a) KPIs: aportes, desembolsos, comprometido e saldo           #
    # ------------------------------------------------------------------ #
    def test_kpis_calculados_corretamente(self):
        """KPIs do extrato devem refletir os aportes e o status das parcelas."""
        self.client.login(username='gestor_extrato_p9', password='senha123')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        # Total de Aportes = 5000 + 3000 + 0 + 2000 = 10000
        self.assertEqual(response.context['total_aportes'], Decimal('10000.00'))

        # Total Desembolsado = parcela_a1 (PAGO) = 1500
        self.assertEqual(response.context['total_desembolsos'], Decimal('1500.00'))

        # Saldo Comprometido = parcela_a2 (PENDENTE, 1500)
        #                    + parcela_b1 (APROVADO, 1000)
        #                    + parcela_b2 (PENDENTE, 1000) = 3500
        self.assertEqual(response.context['saldo_comprometido'], Decimal('3500.00'))

        # Saldo Disponível = 10000 - 1500 - 3500 = 5000
        self.assertEqual(response.context['saldo_disponivel'], Decimal('5000.00'))

    # ------------------------------------------------------------------ #
    # Teste b) RBAC positivo — membro da equipe acessa normalmente        #
    # ------------------------------------------------------------------ #
    def test_membro_equipe_acessa_extrato(self):
        """Membro da equipe acessa o extrato e recebe HTTP 200."""
        self.client.login(username='gestor_extrato_p9', password='senha123')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gestao_projetos/extrato_financeiro_projeto.html')
        self.assertEqual(response.context['projeto'].id, self.projeto.id)

    # ------------------------------------------------------------------ #
    # Teste c) RBAC negativo — usuário sem vínculo recebe 403             #
    # ------------------------------------------------------------------ #
    def test_usuario_sem_vinculo_recebe_403(self):
        """Usuário que não é membro da equipe deve receber HTTP 403."""
        self.client.login(username='intruso_extrato_p9', password='senha123')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    # ------------------------------------------------------------------ #
    # Teste d) Filtro por conta reduz movimentações                       #
    # ------------------------------------------------------------------ #
    def test_filtro_conta_bancaria_reduz_movimentacoes(self):
        """Filtrar por conta_a exclui as parcelas vinculadas à conta_b."""
        self.client.login(username='gestor_extrato_p9', password='senha123')

        response = self.client.get(self.url, {'conta_id': self.conta_a.id})

        self.assertEqual(response.status_code, 200)

        # Sem filtro há 4 parcelas + 1 linha de abertura; com filtro deve haver menos
        movimentacoes = response.context['movimentacoes']
        # Apenas parcelas vinculadas à conta_a devem aparecer
        parcelas_exibidas = [
            m['parcela'] for m in movimentacoes if m['parcela'] is not None
        ]
        for parcela in parcelas_exibidas:
            self.assertEqual(
                parcela.conta_pagamento_id, self.conta_a.id,
                "Somente parcelas da conta_a devem aparecer após filtro."
            )

    # ------------------------------------------------------------------ #
    # Teste e) Saldo disponível negativo quando comprometido > disponível  #
    # ------------------------------------------------------------------ #
    def test_saldo_disponivel_negativo_quando_excede_aportes(self):
        """Projeto sem plano de trabalho tem aportes = 0 → saldo negativo."""
        # Cria projeto sem plano ativo
        empresa2 = EmpresaParceira.objects.create(
            nome='Empresa SaldoNeg P9',
            cnpj='99.888.777/0001-11',
            natureza_juridica='LTDA',
            representante_legal='Rep Neg',
            cargo_representante='Sócio',
        )
        projeto_sem_plano = ProjetoPDI.objects.create(
            nome='Projeto Sem Plano P9',
            fase='EXECUCAO',
            concedente=empresa2,
        )
        MembroEquipe.objects.create(
            projeto=projeto_sem_plano,
            usuario=self.user_gestor,
            papel='GESTOR',
        )
        cota2 = CotaBolsaPT.objects.create(
            projeto=projeto_sem_plano,
            perfil_funcao='Pesquisador',
            quantidade_vagas=1,
            parcelas_previstas=1,
            valor_global_previsto=Decimal('2000.00'),
        )
        TermoBolsa.objects.create(
            cota_pt=cota2,
            pessoa=self.pessoa_a,
            numero_termo='TB-P9-NEG-001',
            vigencia_inicio=date(2026, 9, 1),
            vigencia_fim=date(2026, 9, 30),
            quantidade_parcelas=1,
            valor_parcela=Decimal('2000.00'),
        )

        url_neg = reverse(
            'gestao_projetos:extrato_financeiro_projeto',
            args=[projeto_sem_plano.id],
        )
        self.client.login(username='gestor_extrato_p9', password='senha123')
        response = self.client.get(url_neg)

        self.assertEqual(response.status_code, 200)
        # Aportes = 0, comprometido = 2000 → saldo disponível = -2000
        self.assertEqual(response.context['total_aportes'], Decimal('0.00'))
        self.assertLess(
            response.context['saldo_disponivel'],
            Decimal('0.00'),
            "Saldo disponível deve ser negativo quando comprometido > aportes."
        )

    # ------------------------------------------------------------------ #
    # Teste f) Link de recibo presente apenas para parcelas PAGO          #
    # ------------------------------------------------------------------ #
    def test_link_recibo_apenas_para_parcelas_pagas(self):
        """Movimentações com status PAGO devem ter link_recibo; demais devem ser None."""
        self.client.login(username='gestor_extrato_p9', password='senha123')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        movimentacoes = response.context['movimentacoes']

        for mov in movimentacoes:
            parcela = mov.get('parcela')
            if parcela is not None and parcela.status == 'PAGO':
                self.assertIsNotNone(
                    mov['link_recibo'],
                    f"Parcela {parcela.id} está PAGO mas não tem link_recibo."
                )
            elif parcela is not None:
                self.assertIsNone(
                    mov['link_recibo'],
                    f"Parcela {parcela.id} não está PAGO mas tem link_recibo inesperado."
                )

@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class ExportarRecibosLoteZipTestCase(TestCase):
    """
    Testes de integração da Exportação Consolidada de Recibos em ZIP (Passo 9).
    Cobre: RBAC (superusuário vs membro vs negado), filtro de status (PAGO), e retorno do ZIP.
    """

    def setUp(self):
        self.client = Client()
        self.super_user = User.objects.create_superuser('admin_zip', 'admin@zip.com', 'senha123')
        self.membro_user = User.objects.create_user('membro_zip', 'membro@zip.com', 'senha123')
        self.leigo_user = User.objects.create_user('leigo_zip', 'leigo@zip.com', 'senha123')

        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa ZIP", cnpj="99.999.999/0001-99",
            natureza_juridica="LTDA", representante_legal="Rep", cargo_representante="CEO"
        )
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto Export ZIP", fase="EXECUCAO", concedente=self.empresa
        )

        MembroEquipe.objects.create(projeto=self.projeto, usuario=self.membro_user, papel='GESTOR')

        self.pessoa = PessoaFisica.objects.create(nome="Bolsista ZIP", cpf="999.888.777-66")
        self.cota = CotaBolsaPT.objects.create(
            projeto=self.projeto, perfil_funcao="Pesquisador", quantidade_vagas=1,
            parcelas_previstas=3, valor_global_previsto=Decimal("3000.00")
        )
        self.termo = TermoBolsa.objects.create(
            cota_pt=self.cota, pessoa=self.pessoa, numero_termo="TB-ZIP-1",
            vigencia_inicio=date.today(), vigencia_fim=date.today(),
            quantidade_parcelas=3, valor_parcela=Decimal("1000.00")
        )
        self.url = reverse('gestao_projetos:exportar_recibos_lote_zip', args=[self.projeto.id])

    def test_rbac_acesso_leigo_negado(self):
        """Usuário não membro da equipe deve receber 403 Forbidden."""
        self.client.login(username='leigo_zip', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_aviso_quando_nao_ha_pagos(self):
        """Se não houver parcelas PAGO, redireciona com mensagem de warning."""
        self.client.login(username='membro_zip', password='senha123')
        # Por padrão a parcela 1 é PENDENTE
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        # Redireciona para o extrato financeiro
        self.assertTrue(response.url.startswith(reverse('gestao_projetos:extrato_financeiro_projeto', args=[self.projeto.id])))

    def test_geracao_zip_sucesso(self):
        """Se houver parcelas PAGO, deve retornar um arquivo ZIP válido."""
        # Coloca a parcela 1 como PAGO
        parcela = self.termo.parcelas.first()
        parcela.status = 'PAGO'
        parcela.data_pagamento = date.today()
        parcela.save()

        self.client.login(username='admin_zip', password='senha123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename="Recibos_Projeto_'))
        
        # Validar conteúdo do ZIP
        import io, zipfile
        buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(buffer, 'r') as zf:
            files = zf.namelist()
            self.assertEqual(len(files), 1)
            self.assertTrue(files[0].endswith('.html'))
            self.assertTrue("Bolsista_ZIP" in files[0] or "BolsistaZIP" in files[0])
            html_content = zf.read(files[0]).decode('utf-8')
            self.assertIn("999.888.777-66", html_content)


# =====================================================================
# AUDITORIA INDEPENDENTE (Four-Eyes / SoD) — Kiro (AWS Bedrock)
# Suíte: PropertyZipInvariantsTestCase
# Cobre as 5 Invariantes formais do Passo 9 (Exportação de Recibos ZIP)
# =====================================================================

@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class PropertyZipInvariantsTestCase(TestCase):
    """
    Bateria de invariantes de domínio e segurança para exportar_recibos_lote_zip.

    Invariante 1 — Isolamento Financeiro:
        Membro do Projeto A não pode baixar recibos do Projeto B.

    Invariante 2 — Blindagem de Status:
        Parcelas PENDENTE, EM_ANALISE, APROVADO e CANCELADO jamais
        aparecem no ZIP, mesmo que convivam com parcelas PAGO no mesmo projeto.

    Invariante 3 — Consistência Criptográfica:
        A chave SHA-256 no ZIP é matematicamente idêntica à da view unitária
        visualizar_recibo_bolsa para a mesma parcela.

    Invariante 4 — Segurança de Arquivos / Path Traversal:
        Nomes com acentos, barras, espaços e sequências '../' não corrompem
        a árvore do ZIP nem abrem vetores de Path Traversal.

    Invariante 5 — Gestão de Memória:
        100 parcelas PAGO geram um ZIP coerente sem exceção de memória;
        o buffer é fechado corretamente pelo context manager.
    """

    def setUp(self):
        self.client = Client()

        # ── Usuários ──
        self.user_a = User.objects.create_user('user_inv_a', password='senha123')
        self.user_b = User.objects.create_user('user_inv_b', password='senha123')
        self.superuser = User.objects.create_superuser('super_inv', password='senha123')

        # ── Empresa compartilhada ──
        self.empresa = EmpresaParceira.objects.create(
            nome='Empresa Invariantes', cnpj='11.222.333/0001-44',
            natureza_juridica='LTDA', representante_legal='Rep Inv',
            cargo_representante='CEO',
        )

        # ── Projeto A (user_a é membro) ──
        self.projeto_a = ProjetoPDI.objects.create(
            nome='Projeto Invariante A', fase='EXECUCAO', concedente=self.empresa,
        )
        MembroEquipe.objects.create(projeto=self.projeto_a, usuario=self.user_a, papel='GESTOR')

        # ── Projeto B (user_b é membro; user_a NÃO tem acesso) ──
        self.projeto_b = ProjetoPDI.objects.create(
            nome='Projeto Invariante B', fase='EXECUCAO', concedente=self.empresa,
        )
        MembroEquipe.objects.create(projeto=self.projeto_b, usuario=self.user_b, papel='GESTOR')

        # ── Bolsistas ──
        self.pessoa_a = PessoaFisica.objects.create(nome='Bolsista Inv A', cpf='001.001.001-01')
        self.pessoa_b = PessoaFisica.objects.create(nome='Bolsista Inv B', cpf='002.002.002-02')

        # ── Helper: cria cota e termo para um projeto/pessoa ──

    def _criar_parcela_paga(self, projeto, pessoa, numero_cpf=None, valor=Decimal('1500.00'),
                            cpf_suffix=None):
        """Cria a cadeia mínima e retorna uma Parcela com status='PAGO'."""
        if numero_cpf:
            pessoa = PessoaFisica.objects.create(
                nome=f'Bolsista {cpf_suffix}', cpf=numero_cpf,
            )
        cota = CotaBolsaPT.objects.create(
            projeto=projeto, perfil_funcao='Pesquisador',
            quantidade_vagas=1, parcelas_previstas=1,
            valor_global_previsto=valor,
        )
        termo = TermoBolsa.objects.create(
            cota_pt=cota, pessoa=pessoa,
            numero_termo=f'TB-INV-{projeto.id}-{pessoa.id}',
            vigencia_inicio=date(2026, 9, 1), vigencia_fim=date(2026, 9, 30),
            quantidade_parcelas=1, valor_parcela=valor,
        )
        parcela = termo.parcelas.get(numero=1)
        parcela.status = 'PAGO'
        parcela.data_pagamento = date(2026, 9, 30)
        parcela.save()
        return parcela

    def _url(self, projeto):
        return reverse('gestao_projetos:exportar_recibos_lote_zip', args=[projeto.id])

    # ------------------------------------------------------------------
    # INVARIANTE 1 — Isolamento Financeiro
    # ------------------------------------------------------------------
    def test_inv1_membro_projeto_a_nao_acessa_projeto_b(self):
        """
        Invariante 1: user_a (membro do Projeto A) deve receber 403
        ao tentar exportar o ZIP do Projeto B.
        """
        self._criar_parcela_paga(self.projeto_b, self.pessoa_b)
        self.client.login(username='user_inv_a', password='senha123')

        response = self.client.get(self._url(self.projeto_b))

        self.assertEqual(response.status_code, 403,
                         "Membro do Projeto A deve receber 403 ao acessar ZIP do Projeto B.")

    def test_inv1_zip_projeto_a_nao_contem_parcelas_do_projeto_b(self):
        """
        Invariante 1 (profunda): O ZIP do Projeto A não pode conter
        CPF/dados do bolsista do Projeto B, mesmo que ambos estejam PAGO.
        """
        import io, zipfile as _zf

        self._criar_parcela_paga(self.projeto_a, self.pessoa_a)
        self._criar_parcela_paga(self.projeto_b, self.pessoa_b)

        self.client.login(username='user_inv_a', password='senha123')
        response = self.client.get(self._url(self.projeto_a))

        self.assertEqual(response.status_code, 200)
        buf = io.BytesIO(response.content)
        with _zf.ZipFile(buf, 'r') as zf:
            conteudo_total = '\n'.join(
                zf.read(nome).decode('utf-8', errors='replace') for nome in zf.namelist()
            )
        self.assertNotIn(self.pessoa_b.cpf, conteudo_total,
                         "CPF do Bolsista B não pode vazar no ZIP do Projeto A.")
        self.assertIn(self.pessoa_a.cpf, conteudo_total,
                      "CPF do Bolsista A deve estar presente no ZIP do Projeto A.")

    # ------------------------------------------------------------------
    # INVARIANTE 2 — Blindagem de Status
    # ------------------------------------------------------------------
    def test_inv2_apenas_parcelas_pago_no_zip(self):
        """
        Invariante 2: Parcelas PENDENTE, EM_ANALISE, APROVADO e CANCELADO
        não podem aparecer no ZIP — somente PAGO.
        """
        import io, zipfile as _zf

        # Uma parcela PAGO (deve entrar)
        parcela_paga = self._criar_parcela_paga(self.projeto_a, self.pessoa_a)

        # Quatro parcelas com outros status (nunca devem entrar)
        cpf_base = 10
        for status in ['PENDENTE', 'EM_ANALISE', 'APROVADO', 'CANCELADO']:
            cpf_str = f'{cpf_base:03d}.{cpf_base:03d}.{cpf_base:03d}-{cpf_base:02d}'
            pessoa_extra = PessoaFisica.objects.create(
                nome=f'Bolsista {status}', cpf=cpf_str,
            )
            cota = CotaBolsaPT.objects.create(
                projeto=self.projeto_a, perfil_funcao='Extra',
                quantidade_vagas=1, parcelas_previstas=1,
                valor_global_previsto=Decimal('500.00'),
            )
            termo_extra = TermoBolsa.objects.create(
                cota_pt=cota, pessoa=pessoa_extra,
                numero_termo=f'TB-ST-{status}',
                vigencia_inicio=date(2026, 9, 1), vigencia_fim=date(2026, 9, 30),
                quantidade_parcelas=1, valor_parcela=Decimal('500.00'),
            )
            parcela_extra = termo_extra.parcelas.get(numero=1)
            parcela_extra.status = status
            parcela_extra.save()
            cpf_base += 11

        self.client.login(username='user_inv_a', password='senha123')
        response = self.client.get(self._url(self.projeto_a))

        self.assertEqual(response.status_code, 200)
        buf = io.BytesIO(response.content)
        with _zf.ZipFile(buf, 'r') as zf:
            arquivos = zf.namelist()
            # Somente 1 arquivo (a parcela PAGO)
            self.assertEqual(len(arquivos), 1,
                             f"ZIP deve conter exatamente 1 arquivo, mas contém {len(arquivos)}: {arquivos}")
            html = zf.read(arquivos[0]).decode('utf-8', errors='replace')
        # O CPF da parcela PAGO deve estar presente
        self.assertIn(self.pessoa_a.cpf, html,
                      "O CPF da parcela PAGO deve aparecer no recibo.")

    # ------------------------------------------------------------------
    # INVARIANTE 3 — Consistência Criptográfica
    # ------------------------------------------------------------------
    def test_inv3_hash_zip_identico_ao_da_view_unitaria(self):
        """
        Invariante 3: A chave SHA-256 gerada para o recibo dentro do ZIP
        deve ser matematicamente idêntica à chave emitida por
        visualizar_recibo_bolsa para a mesma parcela.
        """
        import io, zipfile as _zf, hashlib, re

        parcela = self._criar_parcela_paga(self.projeto_a, self.pessoa_a)

        # ── Chave esperada (recalculada localmente com o mesmo algoritmo) ──
        cpf_raw = self.pessoa_a.cpf
        payload = (
            f"{parcela.id}-"
            f"{parcela.data_pagamento}-"
            f"{parcela.valor}-"
            f"{cpf_raw}"
        )
        hash_esperado = hashlib.sha256(payload.encode()).hexdigest()[:16].upper()

        # ── Chave presente no ZIP ──
        self.client.login(username='user_inv_a', password='senha123')
        response = self.client.get(self._url(self.projeto_a))
        self.assertEqual(response.status_code, 200)

        buf = io.BytesIO(response.content)
        with _zf.ZipFile(buf, 'r') as zf:
            html = zf.read(zf.namelist()[0]).decode('utf-8', errors='replace')

        self.assertIn(hash_esperado, html,
                      f"Chave SHA-256 '{hash_esperado}' não encontrada no HTML do recibo dentro do ZIP.")

        # ── Chave presente na view unitária ──
        url_unitaria = reverse('gestao_projetos:visualizar_recibo_bolsa', args=[parcela.id])
        # O recibo unitário exige que o User seja o bolsista titular ou superuser
        self.client.login(username='super_inv', password='senha123')
        response_unitario = self.client.get(url_unitaria)
        self.assertEqual(response_unitario.status_code, 200)
        self.assertEqual(response_unitario.context['hash_doc'], hash_esperado,
                         "hash_doc da view unitária deve ser idêntico ao calculado localmente.")

    # ------------------------------------------------------------------
    # INVARIANTE 4 — Segurança de Arquivos / Path Traversal
    # ------------------------------------------------------------------
    def test_inv4_path_traversal_e_caracteres_especiais_no_nome(self):
        """
        Invariante 4: Nomes com '../', barras, acentos e caracteres especiais
        não podem gerar entradas ZIP com Path Traversal nem corrompê-lo.
        """
        import io, zipfile as _zf

        nomes_maliciosos = [
            '../../../etc/passwd',
            'João da Sílva Ação',
            'Bolsista\\Setor\\Arquivo',
            'Nome<script>alert(1)</script>',
            'Arquivo|Pipe?Query#Hash',
            'normal_name',
        ]

        for nome in nomes_maliciosos:
            cpf_seq = str(abs(hash(nome)))[:11]
            # formata como CPF (sem validação de dígito — apenas unicidade no teste)
            cpf_fmt = f'{cpf_seq[:3]}.{cpf_seq[3:6]}.{cpf_seq[6:9]}-{cpf_seq[9:11]}'
            pessoa_maliciosa = PessoaFisica.objects.create(nome=nome, cpf=cpf_fmt)
            cota = CotaBolsaPT.objects.create(
                projeto=self.projeto_a, perfil_funcao='Tester',
                quantidade_vagas=1, parcelas_previstas=1,
                valor_global_previsto=Decimal('100.00'),
            )
            termo = TermoBolsa.objects.create(
                cota_pt=cota, pessoa=pessoa_maliciosa,
                numero_termo=f'TB-TRAV-{abs(hash(nome)) % 100000}',
                vigencia_inicio=date(2026, 9, 1), vigencia_fim=date(2026, 9, 30),
                quantidade_parcelas=1, valor_parcela=Decimal('100.00'),
            )
            parcela = termo.parcelas.get(numero=1)
            parcela.status = 'PAGO'
            parcela.data_pagamento = date(2026, 9, 30)
            parcela.save()

        self.client.login(username='user_inv_a', password='senha123')
        response = self.client.get(self._url(self.projeto_a))

        # Não deve retornar 500 — a view deve ser robusta
        self.assertEqual(response.status_code, 200,
                         "View não deve explodir com nomes maliciosos/especiais.")
        self.assertEqual(response['Content-Type'], 'application/zip')

        buf = io.BytesIO(response.content)
        with _zf.ZipFile(buf, 'r') as zf:
            for nome_arquivo in zf.namelist():
                # Nenhum nome de arquivo dentro do ZIP pode conter barras
                # (sinal claro de Path Traversal bem-sucedido)
                self.assertNotIn('/', nome_arquivo,
                                 f"Nome de arquivo no ZIP contém '/': '{nome_arquivo}' — Path Traversal!")
                self.assertNotIn('\\', nome_arquivo,
                                 f"Nome de arquivo no ZIP contém '\\': '{nome_arquivo}' — Path Traversal!")
                self.assertNotIn('..', nome_arquivo,
                                 f"Nome de arquivo no ZIP contém '..': '{nome_arquivo}' — Path Traversal!")
                # Verificar que o nome só contém caracteres seguros
                import re
                partes_perigosas = re.findall(r'[^A-Za-z0-9._-]', nome_arquivo)
                self.assertEqual(partes_perigosas, [],
                                 f"Nome '{nome_arquivo}' contém caracteres não-seguros: {partes_perigosas}")

    # ------------------------------------------------------------------
    # INVARIANTE 5 — Gestão de Memória (100 parcelas)
    # ------------------------------------------------------------------
    def test_inv5_volume_100_parcelas_sem_estouro(self):
        """
        Invariante 5: 100 parcelas PAGO geram um ZIP coerente (válido e
        com exatamente 100 entradas) sem exceção de memória ou corrupção.
        """
        import io, zipfile as _zf

        N = 100
        for i in range(N):
            # Gera CPF único no formato DDD.DDD.DDD-DD sem colisões no range [0, N)
            cpf = f'{i+1:03d}.{i+1:03d}.{i+1:03d}-{(i % 89) + 10:02d}'
            pessoa = PessoaFisica.objects.create(nome=f'Bolsista Vol {i:04d}', cpf=cpf)
            cota = CotaBolsaPT.objects.create(
                projeto=self.projeto_a, perfil_funcao=f'Perfil {i}',
                quantidade_vagas=1, parcelas_previstas=1,
                valor_global_previsto=Decimal('1000.00'),
            )
            termo = TermoBolsa.objects.create(
                cota_pt=cota, pessoa=pessoa,
                numero_termo=f'TB-VOL-{i:04d}',
                vigencia_inicio=date(2026, 9, 1), vigencia_fim=date(2026, 9, 30),
                quantidade_parcelas=1, valor_parcela=Decimal('1000.00'),
            )
            parcela = termo.parcelas.get(numero=1)
            parcela.status = 'PAGO'
            parcela.data_pagamento = date(2026, 9, 30)
            parcela.save()

        self.client.login(username='user_inv_a', password='senha123')

        # Não deve levantar nenhuma exceção
        try:
            response = self.client.get(self._url(self.projeto_a))
        except Exception as exc:
            self.fail(f"View lançou exceção com {N} parcelas: {exc}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')

        buf = io.BytesIO(response.content)
        with _zf.ZipFile(buf, 'r') as zf:
            arquivos = zf.namelist()
            # ZIP deve ser válido e conter exatamente N entradas
            self.assertEqual(len(arquivos), N,
                             f"ZIP deve conter exatamente {N} arquivos, encontrou {len(arquivos)}.")
            # Todos os arquivos devem ser legíveis (sem corrupção)
            for nome in arquivos:
                conteudo = zf.read(nome)
                self.assertGreater(len(conteudo), 0,
                                   f"Arquivo '{nome}' está vazio — possível corrupção.")
