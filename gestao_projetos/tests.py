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
