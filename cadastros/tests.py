from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from .models import (
    PessoaJuridica, EmpresaParceira, AgenciaFomento, ProjetoPDI, 
    PlanoDeTrabalho, RubricaOrcamentariaPT, AtividadePlanoAcao,
    CotaBolsaPT, TermoBolsa, Parcela, ContaBancaria
)


class PlanoDeTrabalhoTestCase(TestCase):
    """Testes de invariantes de aportes globais do Plano de Trabalho."""
    
    def setUp(self):
        # Cria entidades básicas para os testes
        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Teste LTDA",
            cnpj="12.345.678/0001-90",
            natureza_juridica="LTDA",
            representante_legal="Teste Representante",
            cargo_representante="Diretor"
        )
        
        self.agencia = AgenciaFomento.objects.create(
            nome="Agência Teste",
            cnpj="98.765.432/0001-10",
            natureza_juridica="Associação",
            representante_legal="Agência Rep",
            cargo_representante="Presidente"
        )
        
        self.projeto_empresa = ProjetoPDI.objects.create(
            nome="Projeto Empresa",
            fase="PROSPECCAO",
            concedente=self.empresa
        )
        
        self.projeto_agencia = ProjetoPDI.objects.create(
            nome="Projeto Agência",
            fase="PROSPECCAO",
            concedente=self.agencia
        )
    
    def test_embrapii_minimo_10_porcento_erro(self):
        """Testa erro quando aporte EMBRAPII é menor que 10% (9.99%)."""
        plano = PlanoDeTrabalho(
            projeto=self.projeto_empresa,
            aporte_empresa=Decimal('45000.00'),
            aporte_embrapii=Decimal('9999.00'),  # 9.99%
            aporte_sebrae=Decimal('0.00'),
            aporte_contrapartida=Decimal('45001.00'),
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=365)
        )
        
        with self.assertRaises(ValidationError) as context:
            plano.clean()
        
        self.assertIn('aporte_embrapii', str(context.exception))
    
    def test_embrapii_minimo_10_porcento_sucesso(self):
        """Testa sucesso quando aporte EMBRAPII é exatamente 10%."""
        plano = PlanoDeTrabalho(
            projeto=self.projeto_empresa,
            aporte_empresa=Decimal('45000.00'),
            aporte_embrapii=Decimal('10000.00'),  # 10.00%
            aporte_sebrae=Decimal('0.00'),
            aporte_contrapartida=Decimal('45000.00'),
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=365)
        )
        
        # Não deve levantar ValidationError
        plano.clean()
    
    def test_empresa_minimo_10_porcento_erro(self):
        """Testa erro quando aporte Empresa é menor que 10% com EmpresaParceira."""
        plano = PlanoDeTrabalho(
            projeto=self.projeto_empresa,
            aporte_empresa=Decimal('9999.00'),  # 9.99%
            aporte_embrapii=Decimal('45000.00'),
            aporte_sebrae=Decimal('0.00'),
            aporte_contrapartida=Decimal('45001.00'),
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=365)
        )
        
        with self.assertRaises(ValidationError) as context:
            plano.clean()
        
        self.assertIn('aporte_empresa', str(context.exception))
    
    def test_empresa_minimo_10_porcento_sucesso(self):
        """Testa sucesso quando aporte Empresa é exatamente 10% com EmpresaParceira."""
        plano = PlanoDeTrabalho(
            projeto=self.projeto_empresa,
            aporte_empresa=Decimal('10000.00'),  # 10.00%
            aporte_embrapii=Decimal('45000.00'),
            aporte_sebrae=Decimal('0.00'),
            aporte_contrapartida=Decimal('45000.00'),
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=365)
        )
        
        # Não deve levantar ValidationError
        plano.clean()
    
    def test_empresa_zero_com_agencia_fomento(self):
        """Testa que projeto com Agência de Fomento pode ter aporte Empresa zero."""
        plano = PlanoDeTrabalho(
            projeto=self.projeto_agencia,
            aporte_empresa=Decimal('0.00'),  # Zero com Agência de Fomento
            aporte_embrapii=Decimal('50000.00'),
            aporte_sebrae=Decimal('0.00'),
            aporte_contrapartida=Decimal('50000.00'),
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=365)
        )
        
        # Não deve levantar ValidationError
        plano.clean()
    
    def test_data_inicio_posterior_data_fim_erro(self):
        """Testa erro quando data_inicio é posterior a data_fim."""
        plano = PlanoDeTrabalho(
            projeto=self.projeto_empresa,
            aporte_empresa=Decimal('33333.33'),
            aporte_embrapii=Decimal('33333.33'),
            aporte_sebrae=Decimal('0.00'),
            aporte_contrapartida=Decimal('33333.34'),
            data_inicio=date.today() + timedelta(days=365),  # Início após fim
            data_fim=date.today()
        )
        
        with self.assertRaises(ValidationError) as context:
            plano.clean()
        
        self.assertIn('data_fim', str(context.exception))
    
    def test_datas_validas_sucesso(self):
        """Testa sucesso quando data_inicio é anterior ou igual a data_fim."""
        plano = PlanoDeTrabalho(
            projeto=self.projeto_empresa,
            aporte_empresa=Decimal('33333.33'),
            aporte_embrapii=Decimal('33333.33'),
            aporte_sebrae=Decimal('0.00'),
            aporte_contrapartida=Decimal('33333.34'),
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=365)
        )
        
        # Não deve levantar ValidationError
        plano.clean()


class RubricaOrcamentariaPTTestCase(TestCase):
    """Testes de invariantes de rubricas orçamentárias."""
    
    def setUp(self):
        # Cria estrutura básica para testes de rubricas
        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Teste LTDA",
            cnpj="12.345.678/0001-90",
            natureza_juridica="LTDA",
            representante_legal="Teste Representante",
            cargo_representante="Diretor"
        )
        
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto Teste",
            fase="PROSPECCAO",
            concedente=self.empresa
        )
        
        self.plano = PlanoDeTrabalho.objects.create(
            projeto=self.projeto,
            aporte_empresa=Decimal('25000.00'),
            aporte_embrapii=Decimal('25000.00'),
            aporte_sebrae=Decimal('0.00'),
            aporte_contrapartida=Decimal('50000.00'),
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=365)
        )
    
    def test_capital_com_embrapii_erro(self):
        """Testa erro quando CAPITAL usa fonte EMBRAPII."""
        rubrica = RubricaOrcamentariaPT(
            plano_trabalho=self.plano,
            categoria='CAPITAL',
            descricao='Equipamento Teste',
            valor_previsto=Decimal('10000.00'),
            fonte_recurso='EMBRAPII'
        )
        
        with self.assertRaises(ValidationError) as context:
            rubrica.clean()
        
        self.assertIn('fonte_recurso', str(context.exception))
    
    def test_capital_com_sebrae_erro(self):
        """Testa erro quando CAPITAL usa fonte SEBRAE."""
        rubrica = RubricaOrcamentariaPT(
            plano_trabalho=self.plano,
            categoria='CAPITAL',
            descricao='Equipamento Teste',
            valor_previsto=Decimal('10000.00'),
            fonte_recurso='SEBRAE'
        )
        
        with self.assertRaises(ValidationError) as context:
            rubrica.clean()
        
        self.assertIn('fonte_recurso', str(context.exception))
    
    def test_capital_com_empresa_sucesso(self):
        """Testa sucesso quando CAPITAL usa fonte EMPRESA."""
        rubrica = RubricaOrcamentariaPT(
            plano_trabalho=self.plano,
            categoria='CAPITAL',
            descricao='Equipamento Teste',
            valor_previsto=Decimal('10000.00'),
            fonte_recurso='EMPRESA'
        )
        
        # Não deve levantar ValidationError
        rubrica.clean()
    
    def test_suporte_com_embrapii_erro(self):
        """Testa erro quando SUPORTE usa fonte EMBRAPII."""
        rubrica = RubricaOrcamentariaPT(
            plano_trabalho=self.plano,
            categoria='SUPORTE',
            descricao='Administrativo',
            valor_previsto=Decimal('5000.00'),
            fonte_recurso='EMBRAPII'
        )
        
        with self.assertRaises(ValidationError) as context:
            rubrica.clean()
        
        self.assertIn('fonte_recurso', str(context.exception))
    
    def test_suporte_com_sebrae_erro(self):
        """Testa erro quando SUPORTE usa fonte SEBRAE."""
        rubrica = RubricaOrcamentariaPT(
            plano_trabalho=self.plano,
            categoria='SUPORTE',
            descricao='Administrativo',
            valor_previsto=Decimal('5000.00'),
            fonte_recurso='SEBRAE'
        )
        
        with self.assertRaises(ValidationError) as context:
            rubrica.clean()
        
        self.assertIn('fonte_recurso', str(context.exception))
    
    def test_suporte_max_15_porcento_erro(self):
        """Testa erro quando SUPORTE excede 15% do valor global."""
        # Valor global = 100.000, 15% = 15.000
        rubrica = RubricaOrcamentariaPT(
            plano_trabalho=self.plano,
            categoria='SUPORTE',
            descricao='Administrativo',
            valor_previsto=Decimal('15001.00'),  # 15.001% - erro
            fonte_recurso='EMPRESA'
        )
        
        with self.assertRaises(ValidationError) as context:
            rubrica.clean()
        
        self.assertIn('valor_previsto', str(context.exception))
    
    def test_suporte_max_15_porcento_sucesso(self):
        """Testa sucesso quando SUPORTE é exatamente 15% do valor global."""
        rubrica = RubricaOrcamentariaPT(
            plano_trabalho=self.plano,
            categoria='SUPORTE',
            descricao='Administrativo',
            valor_previsto=Decimal('15000.00'),  # 15.00% - sucesso
            fonte_recurso='EMPRESA'
        )
        
        # Não deve levantar ValidationError
        rubrica.clean()
    
    def test_terceiros_max_30_porcento_erro(self):
        """Testa erro quando TERCEIROS excede 30% do valor global."""
        # Valor global = 100.000, 30% = 30.000
        rubrica = RubricaOrcamentariaPT(
            plano_trabalho=self.plano,
            categoria='TERCEIROS',
            descricao='Consultoria',
            valor_previsto=Decimal('30001.00'),  # 30.001% - erro
            fonte_recurso='EMPRESA'
        )
        
        with self.assertRaises(ValidationError) as context:
            rubrica.clean()
        
        self.assertIn('valor_previsto', str(context.exception))
    
    def test_terceiros_max_30_porcento_sucesso(self):
        """Testa sucesso quando TERCEIROS é exatamente 30% do valor global."""
        rubrica = RubricaOrcamentariaPT(
            plano_trabalho=self.plano,
            categoria='TERCEIROS',
            descricao='Consultoria',
            valor_previsto=Decimal('30000.00'),  # 30.00% - sucesso
            fonte_recurso='EMPRESA'
        )
        
        # Não deve levantar ValidationError
        rubrica.clean()
    
    def test_suporte_acumulado_excede_15_porcento(self):
        """Testa erro quando soma de rubricas SUPORTE excede 15% acumuladamente."""
        # Cria primeira rubrica SUPORTE de 10.000
        rubrica1 = RubricaOrcamentariaPT.objects.create(
            plano_trabalho=self.plano,
            categoria='SUPORTE',
            descricao='Administrativo 1',
            valor_previsto=Decimal('10000.00'),
            fonte_recurso='EMPRESA'
        )
        
        # Tenta criar segunda rubrica que faria o total exceder 15%
        rubrica2 = RubricaOrcamentariaPT(
            plano_trabalho=self.plano,
            categoria='SUPORTE',
            descricao='Administrativo 2',
            valor_previsto=Decimal('5001.00'),  # Total seria 15.001
            fonte_recurso='EMPRESA'
        )
        
        with self.assertRaises(ValidationError) as context:
            rubrica2.clean()
        
        self.assertIn('valor_previsto', str(context.exception))


class AtividadePlanoAcaoTestCase(TestCase):
    """Testes de invariantes de cronograma físico."""
    
    def setUp(self):
        # Cria estrutura básica para testes de atividades
        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Teste LTDA",
            cnpj="12.345.678/0001-90",
            natureza_juridica="LTDA",
            representante_legal="Teste Representante",
            cargo_representante="Diretor"
        )
        
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto Teste",
            fase="PROSPECCAO",
            concedente=self.empresa
        )
        
        self.plano = PlanoDeTrabalho.objects.create(
            projeto=self.projeto,
            aporte_empresa=Decimal('25000.00'),
            aporte_embrapii=Decimal('25000.00'),
            aporte_sebrae=Decimal('0.00'),
            aporte_contrapartida=Decimal('50000.00'),
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=365)
        )
    
    def test_mes_inicio_posterior_mes_fim_erro(self):
        """Testa erro quando mes_inicio é posterior a mes_fim."""
        atividade = AtividadePlanoAcao(
            plano_trabalho=self.plano,
            numero=1,
            nome='Atividade Teste',
            descricao='Descrição teste',
            mes_inicio=10,
            mes_fim=5  # Fim anterior ao início
        )
        
        with self.assertRaises(ValidationError) as context:
            atividade.clean()
        
        self.assertIn('mes_fim', str(context.exception))
    
    def test_meses_validos_sucesso(self):
        """Testa sucesso quando mes_inicio é anterior ou igual a mes_fim."""
        atividade = AtividadePlanoAcao(
            plano_trabalho=self.plano,
            numero=1,
            nome='Atividade Teste',
            descricao='Descrição teste',
            mes_inicio=1,
            mes_fim=6
        )
        
        # Não deve levantar ValidationError
        atividade.clean()
    
    def test_sobreposicao_temporal_erro(self):
        """Testa erro quando há sobreposição temporal entre atividades."""
        # Cria primeira atividade: Mês 1 ao Mês 6
        atividade1 = AtividadePlanoAcao.objects.create(
            plano_trabalho=self.plano,
            numero=1,
            nome='Atividade 1',
            descricao='Primeira atividade',
            mes_inicio=1,
            mes_fim=6
        )
        
        # Tenta criar segunda atividade sobreposta: Mês 5 ao Mês 10
        atividade2 = AtividadePlanoAcao(
            plano_trabalho=self.plano,
            numero=2,
            nome='Atividade 2',
            descricao='Segunda atividade sobreposta',
            mes_inicio=5,  # Inicia durante a primeira atividade
            mes_fim=10
        )
        
        with self.assertRaises(ValidationError) as context:
            atividade2.clean()
        
        self.assertIn('sobrepostos', str(context.exception).lower())
    
    def test_sobreposicao_limite_sucesso(self):
        """Testa sucesso quando atividades iniciam exatamente no fim da anterior (sem sobreposição)."""
        # Cria primeira atividade: Mês 1 ao Mês 6
        atividade1 = AtividadePlanoAcao.objects.create(
            plano_trabalho=self.plano,
            numero=1,
            nome='Atividade 1',
            descricao='Primeira atividade',
            mes_inicio=1,
            mes_fim=6
        )
        
        # Cria segunda atividade iniciando no Mês 6 (limite exato)
        atividade2 = AtividadePlanoAcao(
            plano_trabalho=self.plano,
            numero=2,
            nome='Atividade 2',
            descricao='Segunda atividade sem sobreposição',
            mes_inicio=6,  # Inicia exatamente quando a primeira termina
            mes_fim=10
        )
        
        # Não deve levantar ValidationError
        atividade2.clean()
    
    def test_sobreposicao_posterior_sucesso(self):
        """Testa sucesso quando atividades iniciam após o fim da anterior."""
        # Cria primeira atividade: Mês 1 ao Mês 6
        atividade1 = AtividadePlanoAcao.objects.create(
            plano_trabalho=self.plano,
            numero=1,
            nome='Atividade 1',
            descricao='Primeira atividade',
            mes_inicio=1,
            mes_fim=6
        )
        
        # Cria segunda atividade iniciando no Mês 7 (após o fim da primeira)
        atividade2 = AtividadePlanoAcao(
            plano_trabalho=self.plano,
            numero=2,
            nome='Atividade 2',
            descricao='Segunda atividade posterior',
            mes_inicio=7,  # Inicia após a primeira terminar
            mes_fim=10
        )
        
        # Não deve levantar ValidationError
        atividade2.clean()


class ParcelaTestCase(TestCase):
    """Testes da geração e liquidação financeira das parcelas de bolsa."""

    def setUp(self):
        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Bolsa LTDA",
            cnpj="11.222.333/0001-44",
            natureza_juridica="LTDA",
            representante_legal="Representante Bolsa",
            cargo_representante="Diretor"
        )
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto Bolsa",
            fase="PROSPECCAO",
            concedente=self.empresa
        )
        self.cota = CotaBolsaPT.objects.create(
            projeto=self.projeto,
            perfil_funcao="Pesquisador",
            quantidade_vagas=1,
            parcelas_previstas=3,
            valor_global_previsto=Decimal("4500.00")
        )
        self.termo = TermoBolsa.objects.create(
            cota_pt=self.cota,
            numero_termo="TB-2026-001",
            vigencia_inicio=date(2026, 9, 1),
            vigencia_fim=date(2026, 11, 30),
            quantidade_parcelas=3,
            valor_parcela=Decimal("1500.00")
        )

    def test_gera_parcelas_com_atributos_financeiros(self):
        parcelas = list(self.termo.parcelas.order_by("numero"))

        self.assertEqual(len(parcelas), 3)
        self.assertEqual(
            [parcela.valor for parcela in parcelas],
            [Decimal("1500.00")] * 3
        )
        self.assertEqual(
            [parcela.status for parcela in parcelas],
            ["PENDENTE"] * 3
        )
        self.assertEqual(
            [parcela.mes_competencia for parcela in parcelas],
            [date(2026, 9, 1), date(2026, 10, 1), date(2026, 11, 1)]
        )

    def test_confirma_pagamento_e_grava_data(self):
        parcela = self.termo.parcelas.get(numero=1)
        data_pagamento = date(2026, 9, 30)

        parcela.confirmar_pagamento(data_pagamento=data_pagamento)

        parcela.refresh_from_db()
        self.assertEqual(parcela.status, "PAGO")
        self.assertEqual(parcela.data_pagamento, data_pagamento)

    def test_confirma_pagamento_com_conta_pagadora(self):
        conta = ContaBancaria.objects.create(
            projeto=self.projeto,
            conta="12345",
            dv="6"
        )
        parcela = self.termo.parcelas.get(numero=1)

        parcela.confirmar_pagamento(
            data_pagamento=date(2026, 9, 30),
            conta=conta
        )

        parcela.refresh_from_db()
        self.assertEqual(parcela.status, "PAGO")
        self.assertEqual(parcela.conta_pagamento, conta)
        self.assertEqual(parcela.conta_pagamento_id, conta.pk)


from django.test import override_settings

@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class PessoaFisicaDetailViewTestCase(TestCase):
    """Testes da visualização de detalhes de Pessoa Física (Party-Role e LGPD)."""

    def setUp(self):
        from django.contrib.auth.models import User
        from cadastros.models import PessoaFisica, PerfilServidor, DadoBancario
        self.user = User.objects.create_user(username='admin_pf', password='password123', is_superuser=True)
        self.client.login(username='admin_pf', password='password123')

        self.pf = PessoaFisica.objects.create(
            nome="Servidor e Bolsista Teste",
            cpf="999.888.777-66",
            rg="1234567 SSP/AM",
            email="servidor@ifam.edu.br",
            telefone="(92) 99999-8888",
            endereco="Av. 7 de Setembro, 1975, Centro"
        )
        self.perfil = PerfilServidor.objects.create(
            pessoa=self.pf,
            siape="1987654",
            cargo="Professor EBTT",
            lotacao="Polo de Inovação",
            interno=True
        )
        self.dado_bancario = DadoBancario.objects.create(
            pessoa=self.pf,
            finalidade="PAGAMENTO_BOLSA",
            banco_codigo="001",
            agencia="0001",
            conta="123456-7",
            chave_pix="servidor@ifam.edu.br"
        )

    def test_visualizar_pessoa_fisica_sucesso(self):
        from django.urls import reverse
        url = reverse('cadastros:visualizar_pessoa_fisica', kwargs={'pk': self.pf.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Servidor e Bolsista Teste")
        self.assertContains(response, "1987654")
        self.assertContains(response, "123456-7")

    def test_excluir_pessoa_fisica_sem_historico_delete_fisico(self):
        """Pessoa sem bolsas nem projetos sofre exclusão física direta."""
        from cadastros.models import PessoaFisica
        from django.urls import reverse

        pf_sem_vinculo = PessoaFisica.objects.create(
            nome="Cidadão Sem Vínculo",
            cpf="111.444.777-99"
        )
        url = reverse('cadastros:excluir_pessoa_fisica', kwargs={'id': pf_sem_vinculo.id})
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PessoaFisica.objects.filter(id=pf_sem_vinculo.id).exists())

    def test_excluir_pessoa_fisica_com_historico_anonimizacao_lgpd(self):
        """Pessoa com termo de bolsa tem delete físico bloqueado e sofre anonimização (Crypto-Shredding)."""
        from cadastros.models import PessoaFisica, TermoBolsa, CotaBolsaPT, ProjetoPDI, EmpresaParceira
        from django.urls import reverse
        from datetime import date
        from decimal import Decimal

        empresa = EmpresaParceira.objects.create(
            nome="Empresa Teste Anon",
            cnpj="99.000.111/0001-22"
        )
        proj = ProjetoPDI.objects.create(nome="Projeto Teste Anon", fase="EXECUCAO", concedente=empresa)
        cota = CotaBolsaPT.objects.create(
            projeto=proj,
            perfil_funcao="Bolsista Pesquisador",
            quantidade_vagas=1,
            parcelas_previstas=6,
            valor_global_previsto=Decimal("6000.00")
        )
        termo = TermoBolsa.objects.create(
            cota_pt=cota,
            pessoa=self.pf,
            numero_termo="TB-ANON-001",
            vigencia_inicio=date(2026, 1, 1),
            vigencia_fim=date(2026, 6, 30),
            quantidade_parcelas=6,
            valor_parcela=Decimal("1000.00")
        )

        url = reverse('cadastros:excluir_pessoa_fisica', kwargs={'id': self.pf.id})
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)

        # Registro permanece existindo para fins de prestação de contas
        self.pf.refresh_from_db()
        self.assertTrue(self.pf.nome.startswith("Cidadão Anonimizado LGPD #"))
        self.assertTrue(self.pf.cpf.startswith("ANON-"))
        self.assertIsNone(self.pf.rg)
        self.assertIsNone(self.pf.email)
        self.assertIsNone(self.pf.telefone)
        self.assertEqual(self.pf.dados_bancarios.count(), 0)
        self.assertFalse(self.pf.perfil_servidor.ativo)
