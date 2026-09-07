from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from .models import (
    PessoaJuridica, EmpresaParceira, AgenciaFomento, ProjetoPDI,
    PlanoDeTrabalho, RubricaOrcamentariaPT, AtividadePlanoAcao,
    CotaBolsaPT, TermoBolsa, Parcela, ContaBancaria,
    PessoaFisica, PerfilServidor, Macroentrega,
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


class TravaAcumuloBolsasTestCase(TestCase):
    """Testes do RN-12: teto de projetos, cargos de direção e carga horária semanal."""

    def setUp(self):
        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Fomento Bolsas",
            cnpj="77.888.999/0001-11",
            natureza_juridica="LTDA",
            representante_legal="Diretor Empresa",
            cargo_representante="Diretor",
        )
        self.projeto_a = ProjetoPDI.objects.create(nome="Projeto P&I Alpha", fase="EXECUCAO", concedente=self.empresa)
        self.projeto_b = ProjetoPDI.objects.create(nome="Projeto P&I Beta", fase="EXECUCAO", concedente=self.empresa)
        self.projeto_c = ProjetoPDI.objects.create(nome="Projeto P&I Gamma", fase="EXECUCAO", concedente=self.empresa)

        self.cota_a = CotaBolsaPT.objects.create(projeto=self.projeto_a, perfil_funcao="Pesquisador A", quantidade_vagas=2, parcelas_previstas=12, valor_global_previsto=Decimal("60000.00"))
        self.cota_b = CotaBolsaPT.objects.create(projeto=self.projeto_b, perfil_funcao="Pesquisador B", quantidade_vagas=2, parcelas_previstas=12, valor_global_previsto=Decimal("60000.00"))
        self.cota_c = CotaBolsaPT.objects.create(projeto=self.projeto_c, perfil_funcao="Pesquisador C", quantidade_vagas=2, parcelas_previstas=12, valor_global_previsto=Decimal("60000.00"))

        self.pf_docente = PessoaFisica.objects.create(nome="Prof. Carlos Silva", cpf="111.222.333-44", data_nascimento="1980-05-10")
        PerfilServidor.objects.create(pessoa=self.pf_docente, siape="1234567", cargo="Professor EBTT", lotacao="Campus Manaus Centro", cargo_direcao="NENHUM")

        self.pf_gestor_cd1 = PessoaFisica.objects.create(nome="Diretor Reitor", cpf="222.333.444-55", data_nascimento="1975-02-15")
        PerfilServidor.objects.create(pessoa=self.pf_gestor_cd1, siape="2345678", cargo="Professor EBTT", lotacao="Reitoria", cargo_direcao="CD1")

        self.pf_gestor_cd3 = PessoaFisica.objects.create(nome="Chefe Departamento", cpf="333.444.555-66", data_nascimento="1985-08-20")
        PerfilServidor.objects.create(pessoa=self.pf_gestor_cd3, siape="3456789", cargo="Professor EBTT", lotacao="Campus Manaus Distrito", cargo_direcao="CD3")

    def test_01_bolsa_individual_legitima_sucesso(self):
        termo = TermoBolsa(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-001/2026", vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2026, 6, 30),
            quantidade_parcelas=6, valor_parcela=Decimal("2500.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        termo.full_clean()
        termo.save()
        self.assertEqual(termo.status, "ATIVO")

    def test_02_rejeita_bolsa_para_servidor_cd01_vedacao_absoluta(self):
        termo = TermoBolsa(
            cota_pt=self.cota_a, pessoa=self.pf_gestor_cd1, modalidade_bolsa="Pesquisa",
            numero_termo="TB-002/2026", vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2026, 6, 30),
            quantidade_parcelas=6, valor_parcela=Decimal("2500.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        with self.assertRaises(ValidationError) as ctx:
            termo.full_clean()
        self.assertIn("pessoa", ctx.exception.message_dict)
        self.assertIn("CD-01", str(ctx.exception))

    def test_03_limita_servidor_cd02_a_cd04_a_um_projeto_ativo(self):
        TermoBolsa.objects.create(
            cota_pt=self.cota_a, pessoa=self.pf_gestor_cd3, modalidade_bolsa="Pesquisa",
            numero_termo="TB-CD3-1/2026", vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2026, 6, 30),
            quantidade_parcelas=6, valor_parcela=Decimal("2000.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        termo_segundo = TermoBolsa(
            cota_pt=self.cota_b, pessoa=self.pf_gestor_cd3, modalidade_bolsa="Pesquisa",
            numero_termo="TB-CD3-2/2026", vigencia_inicio=date(2026, 2, 1), vigencia_fim=date(2026, 7, 31),
            quantidade_parcelas=6, valor_parcela=Decimal("2000.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        with self.assertRaises(ValidationError) as ctx:
            termo_segundo.full_clean()
        self.assertIn("pessoa", ctx.exception.message_dict)
        self.assertIn("CD-02, CD-03 ou CD-04", str(ctx.exception))

    def test_04_permite_ate_dois_projetos_distintos_concorrentes(self):
        TermoBolsa.objects.create(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-P1/2026", vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2026, 6, 30),
            quantidade_parcelas=6, valor_parcela=Decimal("1500.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        termo_p2 = TermoBolsa(
            cota_pt=self.cota_b, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-P2/2026", vigencia_inicio=date(2026, 2, 1), vigencia_fim=date(2026, 5, 31),
            quantidade_parcelas=4, valor_parcela=Decimal("1500.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        termo_p2.full_clean()
        termo_p2.save()
        self.assertEqual(termo_p2.status, "ATIVO")

    def test_05_rejeita_terceiro_projeto_concorrente_sem_excecao(self):
        TermoBolsa.objects.create(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-P1/2026", vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2026, 6, 30),
            quantidade_parcelas=6, valor_parcela=Decimal("1000.00"), carga_horaria_semanal=5, status="ATIVO"
        )
        TermoBolsa.objects.create(
            cota_pt=self.cota_b, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-P2/2026", vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2026, 6, 30),
            quantidade_parcelas=6, valor_parcela=Decimal("1000.00"), carga_horaria_semanal=5, status="ATIVO"
        )
        termo_p3 = TermoBolsa(
            cota_pt=self.cota_c, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-P3/2026", vigencia_inicio=date(2026, 3, 1), vigencia_fim=date(2026, 8, 31),
            quantidade_parcelas=6, valor_parcela=Decimal("1000.00"), carga_horaria_semanal=5, status="ATIVO"
        )
        with self.assertRaises(ValidationError) as ctx:
            termo_p3.full_clean()
        self.assertIn("pessoa", ctx.exception.message_dict)
        self.assertIn("mais de dois (02) projetos", str(ctx.exception))

    def test_06_rejeita_duplicidade_de_bolsa_no_mesmo_projeto(self):
        TermoBolsa.objects.create(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-DUP1/2026", vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2026, 6, 30),
            quantidade_parcelas=6, valor_parcela=Decimal("2000.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        termo_dup2 = TermoBolsa(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-DUP2/2026", vigencia_inicio=date(2026, 2, 1), vigencia_fim=date(2026, 5, 31),
            quantidade_parcelas=4, valor_parcela=Decimal("2000.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        with self.assertRaises(ValidationError) as ctx:
            termo_dup2.full_clean()
        self.assertIn("pessoa", ctx.exception.message_dict)
        self.assertIn("neste mesmo projeto", str(ctx.exception))

    def test_07_rejeita_soma_carga_horaria_semanal_superior_a_20h(self):
        TermoBolsa.objects.create(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-CH1/2026", vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2026, 6, 30),
            quantidade_parcelas=6, valor_parcela=Decimal("2000.00"), carga_horaria_semanal=15, status="ATIVO"
        )
        termo_ch2 = TermoBolsa(
            cota_pt=self.cota_b, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-CH2/2026", vigencia_inicio=date(2026, 2, 1), vigencia_fim=date(2026, 5, 31),
            quantidade_parcelas=4, valor_parcela=Decimal("1500.00"), carga_horaria_semanal=10, status="ATIVO"
        )
        with self.assertRaises(ValidationError) as ctx:
            termo_ch2.full_clean()
        self.assertIn("carga_horaria_semanal", ctx.exception.message_dict)
        self.assertIn("excede o teto legal de 20h", str(ctx.exception))

    def test_08_autorizacao_excepcional_permite_terceiro_projeto_se_justificado(self):
        TermoBolsa.objects.create(
            cota_pt=self.cota_a, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-EXC1/2026", vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2026, 6, 30),
            quantidade_parcelas=6, valor_parcela=Decimal("1000.00"), carga_horaria_semanal=5, status="ATIVO"
        )
        TermoBolsa.objects.create(
            cota_pt=self.cota_b, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-EXC2/2026", vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2026, 6, 30),
            quantidade_parcelas=6, valor_parcela=Decimal("1000.00"), carga_horaria_semanal=5, status="ATIVO"
        )
        termo_p3_excepcional = TermoBolsa(
            cota_pt=self.cota_c, pessoa=self.pf_docente, modalidade_bolsa="Pesquisa",
            numero_termo="TB-EXC3/2026", vigencia_inicio=date(2026, 3, 1), vigencia_fim=date(2026, 8, 31),
            quantidade_parcelas=6, valor_parcela=Decimal("1000.00"), carga_horaria_semanal=5, status="ATIVO",
            autorizacao_excepcional=True,
            justificativa_excepcional="Despacho PROPESP/IFAM nº 42/2026 autorizando atuação estratégica em projeto prioritário."
        )
        termo_p3_excepcional.full_clean()
        termo_p3_excepcional.save()
        self.assertEqual(termo_p3_excepcional.status, "ATIVO")
        self.assertTrue(termo_p3_excepcional.autorizacao_excepcional)


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




# ==============================================================================
# AUDITORIA INDEPENDENTE (Four-Eyes / SoD) — RNF-02 LGPD Crypto-Shredding
# Revisor Técnico: Kiro (AWS Bedrock) — Squad ARGUS
# ==============================================================================

@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class AuditoriaCryptoShreddingLGPDTestCase(TestCase):
    """
    Bateria de estresse e casos de borda para excluir_pessoa_fisica.

    Cenários auditados:
    (a) GET não mutaciona o banco — proteção POST-only implícita.
    (b) Idempotência: segunda chamada em registro já anonimizado não corrompe dados.
    (c) Vínculo via coordenador de projeto (sem TermoBolsa) aciona anonimização.
    (d) Vínculo via MembroEquipe (pessoa.user) aciona anonimização.
    (e) Conta de usuário é desativada e desvinculada na anonimização.
    (f) Múltiplos dados bancários são todos destruídos.
    (g) Acesso não autenticado é bloqueado (redirect para login).
    (h) estado_civil e nacionalidade permanecem (lacuna de cobertura — documentada).
    (i) CPF anonimizado preserva unicidade de banco (hash determinístico).
    """

    def setUp(self):
        from django.contrib.auth.models import User
        from cadastros.models import PessoaFisica, PerfilServidor, DadoBancario, EmpresaParceira

        self.superuser = User.objects.create_superuser(
            username='auditor_lgpd',
            password='senha_auditoria',
        )
        self.client.login(username='auditor_lgpd', password='senha_auditoria')

        self.empresa = EmpresaParceira.objects.create(
            nome='Empresa Auditoria LGPD',
            cnpj='22.333.444/0001-55',
            natureza_juridica='LTDA',
            representante_legal='Rep Auditoria',
            cargo_representante='Diretor',
        )

        # Pessoa com todos os campos PII preenchidos
        self.pf = PessoaFisica.objects.create(
            nome='Ana Auditoria LGPD',
            cpf='010.203.040-50',
            rg='9876543 SSP/AM',
            orgao_emissor_rg='SSP/AM',
            data_nascimento='1990-05-15',
            telefone='(92) 98888-7777',
            email='ana.lgpd@example.com',
            endereco='Rua da Privacidade, 42',
            cep='69000-000',
            estado_civil='Casado',
            nacionalidade='Brasileiro',
        )
        PerfilServidor.objects.create(
            pessoa=self.pf,
            siape='9999991',
            cargo='Pesquisador',
            lotacao='Polo de Inovação',
            ativo=True,
        )
        # Múltiplos dados bancários
        from cadastros.models import DadoBancario
        DadoBancario.objects.create(
            pessoa=self.pf, finalidade='PAGAMENTO_BOLSA',
            banco_codigo='001', agencia='0001', conta='11111-1', ativo=True,
        )
        DadoBancario.objects.create(
            pessoa=self.pf, finalidade='HONORARIOS',
            banco_codigo='237', agencia='0002', conta='22222-2', ativo=False,
        )

    def _url(self, pessoa_id=None):
        from django.urls import reverse
        return reverse('cadastros:excluir_pessoa_fisica',
                       kwargs={'id': pessoa_id or self.pf.id})

    def _cria_projeto_com_bolsa(self, pessoa, cpf_empresa_suffix='01'):
        """Helper: cria cadeia mínima ProjetoPDI → CotaBolsaPT → TermoBolsa."""
        from cadastros.models import ProjetoPDI, CotaBolsaPT, TermoBolsa
        from datetime import date
        from decimal import Decimal

        proj = ProjetoPDI.objects.create(
            nome=f'Projeto Audit {cpf_empresa_suffix}',
            fase='EXECUCAO',
            concedente=self.empresa,
        )
        cota = CotaBolsaPT.objects.create(
            projeto=proj,
            perfil_funcao='Bolsista Audit',
            quantidade_vagas=1,
            parcelas_previstas=3,
            valor_global_previsto=Decimal('3000.00'),
        )
        TermoBolsa.objects.create(
            cota_pt=cota,
            pessoa=pessoa,
            numero_termo=f'TB-AUDIT-{cpf_empresa_suffix}',
            vigencia_inicio=date(2026, 1, 1),
            vigencia_fim=date(2026, 3, 31),
            quantidade_parcelas=3,
            valor_parcela=Decimal('1000.00'),
        )
        return proj

    # ------------------------------------------------------------------
    # (a) GET não muta o banco
    # ------------------------------------------------------------------
    def test_get_nao_muta_banco(self):
        """GET em excluir_pessoa_fisica deve renderizar confirmação sem alterar dados."""
        self._cria_projeto_com_bolsa(self.pf, '00')
        nome_original = self.pf.nome
        cpf_original = self.pf.cpf

        response = self.client.get(self._url())

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cadastros/confirmar_exclusao_pf.html')

        self.pf.refresh_from_db()
        self.assertEqual(self.pf.nome, nome_original,
                         "GET não deve alterar o nome da pessoa.")
        self.assertEqual(self.pf.cpf, cpf_original,
                         "GET não deve alterar o CPF da pessoa.")

    # ------------------------------------------------------------------
    # (b) Idempotência: segunda chamada não corrompe dados
    # ------------------------------------------------------------------
    def test_anonimizacao_e_idempotente(self):
        """Segunda chamada POST em pessoa já anonimizada deve ser inofensiva."""
        self._cria_projeto_com_bolsa(self.pf, '02')

        # 1ª anonimização
        self.client.post(self._url())
        self.pf.refresh_from_db()
        cpf_apos_primeira = self.pf.cpf
        self.assertTrue(cpf_apos_primeira.startswith('ANON-'))

        # 2ª chamada — pessoa já anonimizada, sem TermoBolsa PROTEGIDO ativo
        # mas o registro ainda existe; a view não deve lançar exceção
        response = self.client.post(self._url())
        self.assertIn(response.status_code, [200, 302],
                      "Segunda chamada não deve gerar erro HTTP.")

        self.pf.refresh_from_db()
        # CPF não deve ter sido re-hasheado para um valor diferente do já anonimizado
        # (o hash de "ANON-XXXX" seria diferente do hash do CPF real)
        self.assertTrue(self.pf.cpf.startswith('ANON-'),
                        "CPF deve continuar anonimizado após segunda chamada.")

    # ------------------------------------------------------------------
    # (c) Vínculo como coordenador de projeto dispara anonimização
    # ------------------------------------------------------------------
    def test_coordenador_de_projeto_aciona_anonimizacao(self):
        """Pessoa coordenadora de projeto (sem TermoBolsa) deve ser anonimizada, não deletada."""
        from cadastros.models import PessoaFisica, ProjetoPDI

        pf_coord = PessoaFisica.objects.create(
            nome='Coordenador Auditoria',
            cpf='060.707.080-90',
            email='coord@example.com',
        )
        ProjetoPDI.objects.create(
            nome='Projeto Coord Audit',
            fase='EXECUCAO',
            concedente=self.empresa,
            coordenador=pf_coord,
        )

        url = self._url(pf_coord.id)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        # Deve existir (não foi deletada)
        self.assertTrue(PessoaFisica.objects.filter(id=pf_coord.id).exists(),
                        "Coordenador de projeto não deve ser deletado fisicamente.")

        pf_coord.refresh_from_db()
        self.assertTrue(pf_coord.nome.startswith('Cidadão Anonimizado LGPD #'),
                        "Coordenador de projeto deve ter nome anonimizado.")
        self.assertTrue(pf_coord.cpf.startswith('ANON-'),
                        "Coordenador de projeto deve ter CPF anonimizado.")

    # ------------------------------------------------------------------
    # (d) Vínculo via MembroEquipe (pessoa.user) aciona anonimização
    # ------------------------------------------------------------------
    def test_membro_equipe_via_user_aciona_anonimizacao(self):
        """Pessoa com User vinculado a MembroEquipe deve ser anonimizada."""
        from django.contrib.auth.models import User
        from cadastros.models import PessoaFisica, ProjetoPDI, MembroEquipe

        user_membro = User.objects.create_user(
            username='membro_audit_lgpd',
            password='senha123',
        )
        pf_membro = PessoaFisica.objects.create(
            nome='Membro Equipe Auditoria',
            cpf='120.340.560-78',
            user=user_membro,
        )
        proj = ProjetoPDI.objects.create(
            nome='Projeto Membro Audit',
            fase='EXECUCAO',
            concedente=self.empresa,
        )
        MembroEquipe.objects.create(
            projeto=proj,
            usuario=user_membro,
            papel='ANALISTA',
        )

        url = self._url(pf_membro.id)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(PessoaFisica.objects.filter(id=pf_membro.id).exists(),
                        "Membro de equipe não deve ser deletado fisicamente.")
        pf_membro.refresh_from_db()
        self.assertTrue(pf_membro.cpf.startswith('ANON-'),
                        "Membro de equipe deve ter CPF anonimizado.")

    # ------------------------------------------------------------------
    # (e) Conta de usuário é desativada e desvinculada
    # ------------------------------------------------------------------
    def test_user_desativado_e_desvinculado_na_anonimizacao(self):
        """Após anonimização, o User vinculado deve ser desativado e desvinculado."""
        from django.contrib.auth.models import User
        from cadastros.models import PessoaFisica

        user_vinculado = User.objects.create_user(
            username='user_anon_test',
            password='senha123',
            is_active=True,
        )
        pf_com_user = PessoaFisica.objects.create(
            nome='Pessoa Com User',
            cpf='001.002.003-04',
            email='comuser@example.com',
            user=user_vinculado,
        )
        # Cria bolsa para forçar anonimização
        self._cria_projeto_com_bolsa(pf_com_user, '05')

        url = self._url(pf_com_user.id)
        self.client.post(url)

        pf_com_user.refresh_from_db()
        user_vinculado.refresh_from_db()

        self.assertIsNone(pf_com_user.user,
                          "user deve ser desvinculado após anonimização.")
        self.assertFalse(user_vinculado.is_active,
                         "User vinculado deve ser desativado após anonimização.")
        self.assertEqual(user_vinculado.email, '',
                         "E-mail do User deve ser expurgado na anonimização.")
        self.assertTrue(user_vinculado.username.startswith('anon_'),
                        "Username do User deve ser anonimizado para liberar login civil.")

    # ------------------------------------------------------------------
    # (f) Múltiplos dados bancários são TODOS destruídos
    # ------------------------------------------------------------------
    def test_multiplos_dados_bancarios_destruidos(self):
        """Todos os DadoBancario (ativos e inativos) são deletados na anonimização."""
        self._cria_projeto_com_bolsa(self.pf, '06')

        # Confirma que há 2 dados bancários antes
        self.assertEqual(self.pf.dados_bancarios.count(), 2)

        self.client.post(self._url())
        self.pf.refresh_from_db()

        self.assertEqual(self.pf.dados_bancarios.count(), 0,
                         "Todos os dados bancários (ativos e inativos) devem ser destruídos.")

    # ------------------------------------------------------------------
    # (g) Acesso não autenticado é bloqueado (redirect para login)
    # ------------------------------------------------------------------
    def test_acesso_nao_autenticado_bloqueado(self):
        """Requisição sem login deve ser redirecionada para a tela de login."""
        from django.test import Client as AnonClient
        client_anonimo = AnonClient()

        response = client_anonimo.get(self._url())
        self.assertEqual(response.status_code, 302,
                         "GET sem autenticação deve redirecionar.")
        self.assertIn('/login', response.url,
                      "Redirecionamento deve apontar para a URL de login.")

        response_post = client_anonimo.post(self._url())
        self.assertEqual(response_post.status_code, 302,
                         "POST sem autenticação deve redirecionar.")
        # Não deve ter deletado nem anonimizado nada
        self.pf.refresh_from_db()
        self.assertFalse(self.pf.cpf.startswith('ANON-'),
                         "POST sem autenticação não deve anonimizar dados.")

    def test_rbac_exclusao_usuario_comum_bloqueado(self):
        """Usuário sem staff/superuser não tem acesso à rota de exclusão/anonimização."""
        from django.contrib.auth.models import User

        User.objects.create_user('user_comum_lgpd', password='senha123')
        self.client.login(username='user_comum_lgpd', password='senha123')

        response = self.client.post(self._url())

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    # ------------------------------------------------------------------
    # (h) Anonimização de dados civis (estado_civil e nacionalidade) e perfis
    # ------------------------------------------------------------------
    def test_estado_civil_nacionalidade_e_perfis_anonimizados(self):
        """
        Garante conformidade estrita com a LGPD (RNF-02): estado_civil e nacionalidade
        são ofuscados e perfis associados (aluno, terceiro, etc) são inativados.
        """
        from cadastros.models import PerfilAluno
        PerfilAluno.objects.create(
            pessoa=self.pf,
            matricula='2026AUDIT999',
            nivel='Graduacao',
            curso='Sistemas de Informacao'
        )

        self._cria_projeto_com_bolsa(self.pf, '08')
        self.client.post(self._url())
        self.pf.refresh_from_db()

        self.assertTrue(self.pf.cpf.startswith('ANON-'))
        self.assertEqual(self.pf.estado_civil, 'Outro')
        self.assertEqual(self.pf.nacionalidade, 'Não Informado')
        self.assertFalse(self.pf.perfil_servidor.ativo)
        self.assertFalse(self.pf.perfil_aluno.ativo)
        self.assertTrue(self.pf.perfil_servidor.siape.startswith('ANON-'),
                        "SIAPE do servidor deve ser ofuscado irreversivelmente.")
        self.assertTrue(self.pf.perfil_aluno.matricula.startswith('ANON-'),
                        "Matrícula do aluno deve ser ofuscada irreversivelmente.")

    # ------------------------------------------------------------------
    # (i) CPF anonimizado preserva unicidade (hash determinístico)
    # ------------------------------------------------------------------
    def test_cpf_anonimizado_e_deterministico_e_unico(self):
        """
        O hash do CPF deve ser determinístico (mesmo input → mesmo output)
        e não deve colidir com CPFs reais ou outros hashes em situações normais.
        """
        import hashlib
        from cadastros.models import PessoaFisica

        cpf_original = self.pf.cpf
        cpf_hash_esperado = f"ANON-{hashlib.sha256(cpf_original.encode()).hexdigest()[:8].upper()}"

        self._cria_projeto_com_bolsa(self.pf, '09')
        self.client.post(self._url())
        self.pf.refresh_from_db()

        self.assertEqual(self.pf.cpf, cpf_hash_esperado,
                         "Hash do CPF deve ser determinístico: mesmo CPF → mesmo ANON-XXXXXXXX.")

        # Unicidade: nenhum outro registro deve ter o mesmo CPF anonimizado
        duplicatas = PessoaFisica.objects.filter(cpf=cpf_hash_esperado).count()
        self.assertEqual(duplicatas, 1,
                         "Deve existir exatamente 1 registro com o hash gerado.")


# ==============================================================================
# FASE 6.1 — IDENTIDADE CANÔNICA & GESTÃO DE PESSOAS FÍSICAS (PARTY-ROLE)
# Revisor: Bob (Squad IA ARGUS) | SoD / Four-Eyes
# Achados cobertos: R-01 (403), R-02 (user expurgo), R-03 (SIAPE único),
#                   R-04 (upsert), R-05 (clean_cpf exclude), R-06 (@login_required)
# ==============================================================================
from django.contrib.auth.models import Group, User
from django.test import Client


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class PessoaFisicaGestaoTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # 1. Superuser
        self.super_user = User.objects.create_superuser('admin_pf', 'admin@argus.com', 'senha123')
        # 2. Usuário com Grupo GESTOR
        self.gestor_user = User.objects.create_user('gestor_pf', 'gestor@argus.com', 'senha123')
        grupo_gestor, _ = Group.objects.get_or_create(name='GESTOR')
        self.gestor_user.groups.add(grupo_gestor)
        # 3. Usuário Leigo (sem grupo nem staff)
        self.leigo_user = User.objects.create_user('leigo_pf', 'leigo@argus.com', 'senha123')

        from django.urls import reverse
        self.url_listar = reverse('cadastros:listar_pessoas_fisicas')
        self.url_cadastrar = reverse('cadastros:cadastrar_pessoa_fisica')

        # CPFs válidos (Módulo 11 verificado algoritmicamente)
        self.cpf_valido_1 = "529.982.247-25"
        self.cpf_valido_2 = "712.345.678-57"   # corrigido: 853.473.840-02 falha no Módulo 11
        self.cpf_invalido = "123.456.789-00"

    def test_01_acesso_formulario_cadastro_bloqueia_usuario_comum(self):
        """R-01: Usuário comum sem permissão recebe 403 Forbidden (não 302 redirect)."""
        self.client.login(username='leigo_pf', password='senha123')
        response = self.client.get(self.url_cadastrar)
        self.assertEqual(response.status_code, 403)

    def test_02_acesso_formulario_cadastro_permite_gestor_autorizado(self):
        """Gestor com grupo institucional acessa o formulário de cadastro com status 200."""
        self.client.login(username='gestor_pf', password='senha123')
        response = self.client.get(self.url_cadastrar)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cadastrar Nova Pessoa Física")

    def test_03_validacao_cpf_invalido_matematica_rejeita(self):
        """Rejeita CPF com dígito verificador matematicamente incorreto."""
        self.client.login(username='gestor_pf', password='senha123')
        payload = {
            'nome': 'Cidadão Inválido',
            'cpf': self.cpf_invalido,
        }
        response = self.client.post(self.url_cadastrar, payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CPF inválido")
        from cadastros.models import PessoaFisica
        self.assertFalse(PessoaFisica.objects.filter(nome='Cidadão Inválido').exists())

    def test_04_validacao_cpf_duplicado_rejeita(self):
        """R-05: Rejeita cadastro de CPF que já existe no banco de dados."""
        from cadastros.models import PessoaFisica
        PessoaFisica.objects.create(nome="Pessoa Existente", cpf=self.cpf_valido_1)
        self.client.login(username='gestor_pf', password='senha123')
        payload = {
            'nome': 'Pessoa Clone',
            'cpf': self.cpf_valido_1,
        }
        response = self.client.post(self.url_cadastrar, payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "já está cadastrado")

    def test_05_cadastro_pessoa_fisica_simples_sucesso(self):
        """Cadastra pessoa física básica com sucesso e redireciona para detalhe."""
        from cadastros.models import PessoaFisica
        from django.urls import reverse
        self.client.login(username='gestor_pf', password='senha123')
        payload = {
            'nome': 'Ana Silva Santos',
            'cpf': self.cpf_valido_1,
            'email': 'ana.silva@ifam.edu.br',
            'estado_civil': 'Solteiro',
            'nacionalidade': 'Brasileiro',
        }
        response = self.client.post(self.url_cadastrar, payload)
        pf = PessoaFisica.objects.filter(nome='Ana Silva Santos').first()
        self.assertIsNotNone(pf)
        self.assertRedirects(response, reverse('cadastros:visualizar_pessoa_fisica', args=[pf.id]))

    def test_06_cadastro_com_perfil_servidor_atomico(self):
        """R-03: Cria Pessoa Física + PerfilServidor com SIAPE único atomicamente."""
        from cadastros.models import PessoaFisica
        self.client.login(username='gestor_pf', password='senha123')
        payload = {
            'nome': 'Prof. Carlos Alberto',
            'cpf': self.cpf_valido_2,
            'tem_perfil_servidor': '1',
            'servidor-siape': 'SIAPE-T06',
            'servidor-cargo': 'Professor EBTT',
            'servidor-lotacao': 'Polo de Inovação',
            'servidor-interno': 'on',
            'servidor-ativo': 'on',
        }
        response = self.client.post(self.url_cadastrar, payload)
        pf = PessoaFisica.objects.filter(nome='Prof. Carlos Alberto').first()
        self.assertIsNotNone(pf)
        self.assertTrue(hasattr(pf, 'perfil_servidor'))
        self.assertEqual(pf.perfil_servidor.siape, 'SIAPE-T06')

    def test_07_cadastro_com_perfil_aluno_e_dado_bancario(self):
        """Cria Pessoa Física com PerfilAluno e DadoBancario simultaneamente."""
        from cadastros.models import PessoaFisica
        self.client.login(username='gestor_pf', password='senha123')
        payload = {
            'nome': 'Mariana Aluna Bolsista',
            'cpf': self.cpf_valido_1,
            'tem_perfil_aluno': '1',
            'aluno-matricula': 'MAT-T07',
            'aluno-nivel': 'Graduacao',
            'aluno-curso': 'Engenharia de Software',
            'aluno-interno': 'on',
            'aluno-ativo': 'on',
            'tem_dado_bancario': '1',
            'banco-finalidade': 'PAGAMENTO_BOLSA',
            'banco-banco_codigo': '001',
            'banco-agencia': '1234',
            'banco-conta': '98765-4',
        }
        response = self.client.post(self.url_cadastrar, payload)
        pf = PessoaFisica.objects.filter(nome='Mariana Aluna Bolsista').first()
        self.assertIsNotNone(pf)
        self.assertEqual(pf.perfil_aluno.matricula, 'MAT-T07')
        self.assertEqual(pf.dados_bancarios.count(), 1)
        self.assertEqual(pf.dados_bancarios.first().conta, '98765-4')

    def test_08_edicao_atualiza_dados_civis_e_perfil_existente(self):
        """R-04: Edição atualiza dados civis e perfil sem duplicar registro."""
        from cadastros.models import PessoaFisica, PerfilServidor
        from django.urls import reverse
        pf = PessoaFisica.objects.create(nome="Lucas Oliveira", cpf=self.cpf_valido_1)
        perfil = PerfilServidor.objects.create(
            pessoa=pf, siape="SIAPE-T08", cargo="Assistente", lotacao="Reitoria"
        )
        url_editar = reverse('cadastros:editar_pessoa_fisica', args=[pf.id])
        self.client.login(username='gestor_pf', password='senha123')
        payload = {
            'nome': 'Lucas Oliveira Modificado',
            'cpf': self.cpf_valido_1,
            'endereco': 'Nova Rua 100',
            'tem_perfil_servidor': '1',
            'servidor-siape': 'SIAPE-T08',
            'servidor-cargo': 'Coordenador',
            'servidor-lotacao': 'Polo de Inovação',
            'servidor-ativo': 'on',
        }
        self.client.post(url_editar, payload)
        pf.refresh_from_db()
        perfil.refresh_from_db()
        self.assertEqual(pf.nome, 'Lucas Oliveira Modificado')
        self.assertEqual(pf.endereco, 'Nova Rua 100')
        self.assertEqual(perfil.cargo, 'Coordenador')
        self.assertEqual(PerfilServidor.objects.filter(pessoa=pf).count(), 1)

    def test_09_edicao_adiciona_novo_perfil_a_pessoa_existente(self):
        """Adiciona PerfilAluno a uma PessoaFisica que antes não tinha perfil."""
        from cadastros.models import PessoaFisica
        from django.urls import reverse
        pf = PessoaFisica.objects.create(nome="Juliana Santos", cpf=self.cpf_valido_1)
        url_editar = reverse('cadastros:editar_pessoa_fisica', args=[pf.id])
        self.client.login(username='gestor_pf', password='senha123')
        payload = {
            'nome': 'Juliana Santos',
            'cpf': self.cpf_valido_1,
            'tem_perfil_aluno': '1',
            'aluno-matricula': 'MAT-T09',
            'aluno-nivel': 'Graduacao',
            'aluno-curso': 'Sistemas de Informação',
            'aluno-ativo': 'on',
        }
        self.client.post(url_editar, payload)
        pf.refresh_from_db()
        self.assertTrue(hasattr(pf, 'perfil_aluno'))
        self.assertEqual(pf.perfil_aluno.matricula, 'MAT-T09')

    def test_10_vinculo_auth_user_restrito_a_superuser(self):
        """R-02: Gestor comum não consegue vincular conta de login (campo expurgado e ignorado)."""
        from cadastros.models import PessoaFisica
        alvo_user = User.objects.create_user('alvo_pf', 'alvo@argus.com', 'senha123')
        self.client.login(username='gestor_pf', password='senha123')
        # GET não deve expor o campo 'user' para gestores comuns
        response_get = self.client.get(self.url_cadastrar)
        self.assertNotContains(response_get, 'Conta de Usuário Django')
        # POST tentando injetar 'user' deve ser neutralizado pelo form
        payload = {
            'nome': 'Tentativa Injecao User',
            'cpf': self.cpf_valido_1,
            'user': alvo_user.id,
        }


# =====================================================================
# FASE 6 — ETAPA 6.4: Travas Regulatórias de Planejamento Físico & Congelamento de Escopo (RN-07 e RN-10)
# =====================================================================

class TravaPlanejamentoFisicoTestCase(TestCase):
    """
    Bateria de testes de conformidade regulatória para RN-07 e RN-10:
    - RN-07: Não-Sobreposição Temporal de Macroentregas (Sequenciamento Estrito)
    - RN-10: Congelamento do Escopo em Execução
    """

    def setUp(self):
        # Estrutura básica do projeto
        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Planejamento Físico LTDA",
            cnpj="12.345.678/0001-90",
            natureza_juridica="LTDA",
            representante_legal="Gestor Planejamento",
            cargo_representante="Diretor"
        )
        self.projeto_prospeccao = ProjetoPDI.objects.create(
            nome="Projeto em Prospecção",
            fase="PROSPECCAO",
            concedente=self.empresa,
        )
        self.projeto_execucao = ProjetoPDI.objects.create(
            nome="Projeto em Execução",
            fase="EXECUCAO",
            concedente=self.empresa,
        )
        self.plano_prospeccao = PlanoDeTrabalho.objects.create(
            projeto=self.projeto_prospeccao,
            versao=1,
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 12, 31),
            total_meses=12,
            valor_global=Decimal('100000.00'),
            aporte_empresa=Decimal('50000.00'),
            aporte_embrapii=Decimal('50000.00'),
        )
        self.plano_execucao = PlanoDeTrabalho.objects.create(
            projeto=self.projeto_execucao,
            versao=1,
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 12, 31),
            total_meses=12,
            valor_global=Decimal('100000.00'),
            aporte_empresa=Decimal('50000.00'),
            aporte_embrapii=Decimal('50000.00'),
        )

    def test_01_macroentrega_cronologia_invalida_rejeitada(self):
        """Data fim < data início gera ValidationError({'data_fim': ...})."""
        macro = Macroentrega(
            plano_trabalho=self.plano_prospeccao,
            numero=1,
            nome="Macroentrega Inválida",
            data_inicio=date(2026, 6, 1),
            data_fim=date(2026, 5, 31),
        )
        with self.assertRaises(ValidationError) as ctx:
            macro.full_clean()
        self.assertIn('data_fim', ctx.exception.message_dict)

    def test_02_macroentregas_sequenciais_validas(self):
        """M1 (Jan-Mar) e M2 (Mar-Jun) aceitas perfeitamente."""
        m1 = Macroentrega.objects.create(
            plano_trabalho=self.plano_prospeccao,
            numero=1,
            nome="Macroentrega 1",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 3, 31),
        )
        m2 = Macroentrega(
            plano_trabalho=self.plano_prospeccao,
            numero=2,
            nome="Macroentrega 2",
            data_inicio=date(2026, 4, 1),
            data_fim=date(2026, 6, 30),
        )
        # Não deve levantar ValidationError
        m2.full_clean()

    def test_03_macroentregas_sobrepostas_rejeitadas(self):
        """M2 iniciando antes do término de M1 é rejeitada pela RN-07."""
        Macroentrega.objects.create(
            plano_trabalho=self.plano_prospeccao,
            numero=1,
            nome="Macroentrega 1",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 3, 31),
        )
        m2 = Macroentrega(
            plano_trabalho=self.plano_prospeccao,
            numero=2,
            nome="Macroentrega 2 Sobreposta",
            data_inicio=date(2026, 3, 15),  # Inicia antes do término de M1
            data_fim=date(2026, 6, 30),
        )
        with self.assertRaises(ValidationError) as ctx:
            m2.full_clean()
        self.assertIn('data_inicio', ctx.exception.message_dict)
        self.assertIn('RN-07', str(ctx.exception))

    def test_04_macroentrega_posterior_sobreposta_rejeitada(self):
        """M1 editada com data fim ultrapassando início de M2 é rejeitada."""
        m1 = Macroentrega.objects.create(
            plano_trabalho=self.plano_prospeccao,
            numero=1,
            nome="Macroentrega 1",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 3, 31),
        )
        Macroentrega.objects.create(
            plano_trabalho=self.plano_prospeccao,
            numero=2,
            nome="Macroentrega 2",
            data_inicio=date(2026, 4, 1),
            data_fim=date(2026, 6, 30),
        )
        # Tenta estender M1 para ultrapassar o início de M2
        m1.data_fim = date(2026, 4, 15)
        with self.assertRaises(ValidationError) as ctx:
            m1.full_clean()
        self.assertIn('data_fim', ctx.exception.message_dict)
        self.assertIn('RN-07', str(ctx.exception))

    def test_05_projeto_prospeccao_permite_edicao_livre(self):
        """Projeto em fase='PROSPECCAO' permite adicionar, editar e excluir macroentregas sem restrição de congelamento."""
        # Adicionar nova macroentrega
        m1 = Macroentrega(
            plano_trabalho=self.plano_prospeccao,
            numero=1,
            nome="Nova Macroentrega",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 3, 31),
        )
        m1.full_clean()
        m1.save()

        # Editar macroentrega existente
        m1.nome = "Macroentrega Editada"
        m1.full_clean()
        m1.save()

        # Excluir macroentrega
        m1.delete()
        self.assertEqual(Macroentrega.objects.filter(plano_trabalho=self.plano_prospeccao).count(), 0)

    def test_06_projeto_execucao_bloqueia_nova_macroentrega(self):
        """Projeto em fase='EXECUCAO' rejeita adição de nova macroentrega com erro RN-10."""
        macro = Macroentrega(
            plano_trabalho=self.plano_execucao,
            numero=1,
            nome="Nova Macroentrega em Execução",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 3, 31),
        )
        with self.assertRaises(ValidationError) as ctx:
            macro.full_clean()
        self.assertIn('RN-10', str(ctx.exception))

    def test_07_projeto_execucao_bloqueia_mutacao_macroentrega_existente(self):
        """Tentar alterar nome, TRL ou datas de macroentrega existente em projeto em execução é rejeitado pela RN-10."""
        m1 = Macroentrega.objects.create(
            plano_trabalho=self.plano_execucao,
            numero=1,
            nome="Macroentrega Original",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 3, 31),
            trl=3,
        )
        # Tenta alterar nome
        m1.nome = "Macroentrega Alterada"
        with self.assertRaises(ValidationError) as ctx:
            m1.full_clean()
        self.assertIn('RN-10', str(ctx.exception))

        # Tenta alterar TRL
        m1.nome = "Macroentrega Original"  # Restaura nome
        m1.trl = 4
        with self.assertRaises(ValidationError) as ctx:
            m1.full_clean()
        self.assertIn('RN-10', str(ctx.exception))

        # Tenta alterar datas
        m1.trl = 3  # Restaura TRL
        m1.data_inicio = date(2026, 1, 15)
        with self.assertRaises(ValidationError) as ctx:
            m1.full_clean()
        self.assertIn('RN-10', str(ctx.exception))

    def test_08_projeto_execucao_bloqueia_delecao_macroentrega(self):
        """Tentar chamar .delete() em macroentrega de plano congelado levanta ValidationError."""
        m1 = Macroentrega.objects.create(
            plano_trabalho=self.plano_execucao,
            numero=1,
            nome="Macroentrega para Deleção",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 3, 31),
        )
        with self.assertRaises(ValidationError) as ctx:
            m1.delete()
        self.assertIn('RN-10', str(ctx.exception))


class CicloVidaProjetoTestCase(TestCase):
    """
    Suíte de testes da Etapa 6.6: Máquina de Estados e Governança do Ciclo de Vida (RF-05 / RF-06).
    Testa gateways de transição, rastro indelével de auditoria, anti-bypass e RBAC estrito.
    """

    def setUp(self):
        from django.contrib.auth.models import User
        from cadastros.models import (
            ProjetoPDI, TermoDeParceria, PlanoDeTrabalho, Macroentrega,
            ContaBancaria, HistoricoTransicaoFase, MembroEquipe, PessoaFisica,
            EmpresaParceira, ICT, FundacaoApoio, CotaBolsaPT, TermoBolsa, Parcela
        )
        from decimal import Decimal

        # Usuários
        self.user_admin = User.objects.create_superuser(username='admin_ciclo', password='pass', email='admin@test.com')
        self.user_coord = User.objects.create_user(username='coord_ciclo', password='pass')
        self.user_gestor = User.objects.create_user(username='gestor_ciclo', password='pass')
        self.user_alheio = User.objects.create_user(username='alheio_ciclo', password='pass')

        # Pessoas Jurídicas
        self.empresa = EmpresaParceira.objects.create(nome="Empresa Financiadora PDI", cnpj="11.222.333/0001-44")
        self.ict = ICT.objects.create(nome="Polo de Inovação IFAM", cnpj="22.333.444/0001-55")
        self.fundacao = FundacaoApoio.objects.create(nome="FAEPI Apoio", cnpj="33.444.555/0001-66")

        # Coordenador PF
        self.pf_coord = PessoaFisica.objects.create(
            nome="Coordenador do Projeto",
            cpf="111.222.333-44",
            user=self.user_coord
        )

        # Projeto PDI na fase PROSPECCAO
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto Ciclo de Vida PDI",
            fase='PROSPECCAO',
            coordenador=self.pf_coord,
            concedente=self.empresa,
            convenente=self.ict,
            interveniente=self.fundacao,
            vigencia_inicio=date(2026, 1, 1),
            vigencia_fim=date(2026, 12, 31),
        )

        # Membro Equipe Gestor
        MembroEquipe.objects.create(
            projeto=self.projeto,
            usuario=self.user_gestor,
            papel='GESTOR'
        )

    def test_01_gateway_execucao_sem_termo_ou_plano_bloqueado(self):
        """Gateway 1: Tentar transicionar PROSPECCAO -> EXECUCAO sem termo, plano ou conta deve falhar com lista de pendências."""
        pendencias = self.projeto.validar_transicao_fase('EXECUCAO')
        self.assertTrue(len(pendencias) >= 3)
        self.assertTrue(any("Termo de Parceria" in p for p in pendencias))
        self.assertTrue(any("Macroentregas" in p for p in pendencias))
        self.assertTrue(any("Conta Bancária" in p for p in pendencias))

        with self.assertRaises(ValidationError):
            self.projeto.transicionar_fase('EXECUCAO', self.user_admin)

    def test_02_gateway_execucao_com_sucesso_ativa_congelamento(self):
        """Gateway 1: Com termo assinado, macroentregas e conta, transiciona para EXECUCAO, grava auditoria e ativa congelamento."""
        from cadastros.models import TermoDeParceria, PlanoDeTrabalho, Macroentrega, ContaBancaria, HistoricoTransicaoFase

        termo = TermoDeParceria.objects.create(
            projeto=self.projeto,
            numero="TP-2026/01",
            data_assinatura=date(2026, 1, 10),
            concedente=self.empresa,
            convenente=self.ict,
            interveniente=self.fundacao,
            ativo=True
        )
        plano = PlanoDeTrabalho.objects.create(
            projeto=self.projeto,
            versao=1,
            objetivo_geral="Plano Operacional"
        )
        Macroentrega.objects.create(
            plano_trabalho=plano,
            numero=1,
            nome="Macroentrega 1",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 6, 30),
            trl=4
        )
        ContaBancaria.objects.create(
            projeto=self.projeto,
            banco="Banco do Brasil",
            agencia="1234-5",
            conta="54321",
            dv="0"
        )

        self.projeto.transicionar_fase('EXECUCAO', self.user_coord, justificativa="Formalização completa.")
        self.projeto.refresh_from_db()
        self.assertEqual(self.projeto.fase, 'EXECUCAO')

        # Auditoria gravada
        historico = HistoricoTransicaoFase.objects.filter(projeto=self.projeto).first()
        self.assertIsNotNone(historico)
        self.assertEqual(historico.fase_anterior, 'PROSPECCAO')
        self.assertEqual(historico.fase_nova, 'EXECUCAO')
        self.assertEqual(historico.usuario, self.user_coord)
        self.assertEqual(historico.justificativa, "Formalização completa.")

        # Trava RN-10 ativa (propriedade calculada e campos persistidos no banco)
        plano.refresh_from_db()
        self.assertTrue(plano.esta_congelado)
        self.assertTrue(plano.congelado)
        self.assertEqual(plano.status, 'CONGELADO_VIGENTE')

    def test_03_anti_bypass_save_direto_bloqueado(self):
        """Tentativa de mudar projeto.fase diretamente via .save() é interceptada e bloqueada por ValidationError."""
        self.projeto.fase = 'ENCERRADO'
        with self.assertRaises(ValidationError) as ctx:
            self.projeto.save()
        self.assertIn("transicionar_fase()", str(ctx.exception))

        # Testa que a flag _permitir_mudanca_fase é um token efêmero de uso único consumido imediatamente
        self.projeto.refresh_from_db()
        self.projeto._permitir_mudanca_fase = True
        self.projeto.fase = 'EXECUCAO'
        self.projeto.save()
        self.assertFalse(getattr(self.projeto, '_permitir_mudanca_fase', False))

        # Reutilização da mesma instância em memória para nova alteração sem transição deve ser barrada
        self.projeto.fase = 'ENCERRADO'
        with self.assertRaises(ValidationError) as ctx:
            self.projeto.save()
        self.assertIn("transicionar_fase()", str(ctx.exception))


    def test_04_gateway_encerrado_bloqueia_se_houver_parcelas_pendentes(self):
        """Gateway 3: Transicionar PRESTACAO_CONTAS -> ENCERRADO bloqueia se existirem parcelas de bolsas não liquidadas."""
        from cadastros.models import PlanoDeTrabalho, CotaBolsaPT, TermoBolsa, Parcela, PessoaFisica, PerfilServidor
        from decimal import Decimal

        # Coloca projeto em PRESTACAO_CONTAS via transicionar_fase
        self.projeto._permitir_mudanca_fase = True
        self.projeto.fase = 'PRESTACAO_CONTAS'
        self.projeto.save()

        pf_bolsista = PessoaFisica.objects.create(nome="Bolsista Teste", cpf="222.333.444-55")
        PerfilServidor.objects.create(pessoa=pf_bolsista, siape="1234567", cargo="Docente")
        cota = CotaBolsaPT.objects.create(
            projeto=self.projeto,
            perfil_funcao="Pesquisador",
            quantidade_vagas=1,
            parcelas_previstas=6,
            valor_global_previsto=Decimal("6000.00")
        )
        tb = TermoBolsa.objects.create(
            cota_pt=cota, pessoa=pf_bolsista, modalidade_bolsa="Pesquisa",
            numero_termo="TB-01/2026", vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2026, 3, 31),
            quantidade_parcelas=2, valor_parcela=Decimal("1500.00"), carga_horaria_semanal=20
        )
        p1 = tb.parcelas.get(numero=1)
        p1.status = 'PAGO'
        p1.save()
        p2 = tb.parcelas.get(numero=2)
        p2.status = 'EM_ANALISE'
        p2.save()

        pendencias = self.projeto.validar_transicao_fase('ENCERRADO')
        self.assertTrue(any("não liquidadas" in p for p in pendencias))

        with self.assertRaises(ValidationError):
            self.projeto.transicionar_fase('ENCERRADO', self.user_admin)

    def test_05_gateway_encerrado_sucesso_quando_parcelas_pagas(self):
        """Gateway 3: Transicionar PRESTACAO_CONTAS -> ENCERRADO tem sucesso quando todas as parcelas estão PAGO ou CANCELADO."""
        from cadastros.models import PlanoDeTrabalho, CotaBolsaPT, TermoBolsa, Parcela, PessoaFisica, PerfilServidor
        from decimal import Decimal

        self.projeto._permitir_mudanca_fase = True
        self.projeto.fase = 'PRESTACAO_CONTAS'
        self.projeto.save()

        pf_bolsista = PessoaFisica.objects.create(nome="Bolsista Teste 2", cpf="333.444.555-66")
        PerfilServidor.objects.create(pessoa=pf_bolsista, siape="7654321", cargo="Docente")
        cota = CotaBolsaPT.objects.create(
            projeto=self.projeto,
            perfil_funcao="Pesquisador",
            quantidade_vagas=1,
            parcelas_previstas=6,
            valor_global_previsto=Decimal("6000.00")
        )
        tb = TermoBolsa.objects.create(
            cota_pt=cota, pessoa=pf_bolsista, modalidade_bolsa="Pesquisa",
            numero_termo="TB-02/2026", vigencia_inicio=date(2026, 1, 1), vigencia_fim=date(2026, 2, 28),
            quantidade_parcelas=2, valor_parcela=Decimal("1500.00"), carga_horaria_semanal=20
        )
        p1 = tb.parcelas.get(numero=1)
        p1.status = 'PAGO'
        p1.save()
        p2 = tb.parcelas.get(numero=2)
        p2.status = 'CANCELADO'
        p2.save()

        self.projeto.transicionar_fase('ENCERRADO', self.user_admin, justificativa="Prestação de contas aprovada integralmente.")
        self.projeto.refresh_from_db()
        self.assertEqual(self.projeto.fase, 'ENCERRADO')

    def test_06_cancelamento_exige_justificativa_e_salva_historico(self):
        """Cancelamento de projeto em PROSPECCAO exige justificativa; em PRESTACAO_CONTAS é rejeitado."""
        # Sem justificativa: falha
        with self.assertRaises(ValidationError) as ctx:
            self.projeto.transicionar_fase('CANCELADO', self.user_coord, justificativa="")
        self.assertIn("justificativa formal", str(ctx.exception))

        # Com justificativa: sucesso
        self.projeto.transicionar_fase('CANCELADO', self.user_coord, justificativa="Cancelado por desistência do parceiro.")
        self.projeto.refresh_from_db()
        self.assertEqual(self.projeto.fase, 'CANCELADO')

    def test_07_estados_terminais_bloqueiam_novas_transicoes(self):
        """Estados terminais (ENCERRADO e CANCELADO) rejeitam qualquer nova transição posterior."""
        self.projeto._permitir_mudanca_fase = True
        self.projeto.fase = 'ENCERRADO'
        self.projeto.save()

        pendencias = self.projeto.validar_transicao_fase('EXECUCAO')
        self.assertTrue(any("estado terminal" in p for p in pendencias))

        with self.assertRaises(ValidationError):
            self.projeto.transicionar_fase('EXECUCAO', self.user_admin)

    def test_08_rbac_estrito_view_transicionar_fase(self):
        """View transicionar_fase_projeto: Coordenador/Gestor têm permissão (200/302); usuário alheio recebe 403 Forbidden."""
        from django.urls import reverse
        url = reverse('cadastros:transicionar_fase_projeto', args=[self.projeto.id])

        # Usuário alheio: 403
        self.client.force_login(self.user_alheio)
        resp = self.client.post(url, {'nova_fase': 'EXECUCAO'})
        self.assertEqual(resp.status_code, 403)

        # Coordenador do projeto: tem permissão (não recebe 403, pode receber 302 redirecionando com mensagens)
        self.client.force_login(self.user_coord)
        resp = self.client.post(url, {'nova_fase': 'EXECUCAO'})
        self.assertEqual(resp.status_code, 302)

        # Gestor do projeto: tem permissão (não recebe 403, pode receber 302 redirecionando com mensagens)
        self.client.force_login(self.user_gestor)
        resp = self.client.post(url, {'nova_fase': 'EXECUCAO'})
        self.assertEqual(resp.status_code, 302)

        # Superusuário: tem permissão (não recebe 403)
        self.client.force_login(self.user_admin)
        resp = self.client.post(url, {'nova_fase': 'EXECUCAO'})
        self.assertEqual(resp.status_code, 302)

