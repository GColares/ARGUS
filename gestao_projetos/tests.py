from datetime import date
from decimal import Decimal

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
