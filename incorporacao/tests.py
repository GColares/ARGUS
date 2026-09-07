from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from cadastros.models import (
    ContaBancaria,
    EmpresaParceira,
    FonteDeRecurso,
    MembroEquipe,
    OrigemDoacao,
    Processo,
    ProjetoPDI,
    TipoProcesso,
)
from incorporacao.models import ItemPatrimonial, TermoDoacao
from patrimonio.models import BemPatrimonial


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class MinutaTermoDoacaoProjetoTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create_superuser('admin_inc', 'admin@inc.com', 'senha123')
        self.membro_user = User.objects.create_user(
            'membro_inc',
            'membro@inc.com',
            'senha123',
        )
        User.objects.create_user('leigo_inc', 'leigo@inc.com', 'senha123')

        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Doacao",
            cnpj="33.444.555/0001-66",
            natureza_juridica="LTDA",
            representante_legal="Rep Doacao",
            cargo_representante="Dir",
        )
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto Incorporacao Teste",
            fase="PRESTACAO_CONTAS",
            concedente=self.empresa,
        )
        MembroEquipe.objects.create(
            projeto=self.projeto,
            usuario=self.membro_user,
            papel='GESTOR',
        )

        BemPatrimonial.objects.create(
            projeto=self.projeto,
            patrimonio_ifam="IFAM-2001",
            descricao="Servidor Rack 2U",
            valor=Decimal("12000.00"),
        )
        self.url = reverse(
            'incorporacao:gerar_termo_doacao_projeto',
            args=[self.projeto.id],
        )

    def test_rbac_acesso_leigo_bloqueado(self):
        self.client.login(username='leigo_inc', password='senha123')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_minuta_doacao_renderizacao_sucesso(self):
        self.client.login(username='membro_inc', password='senha123')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_itens'], 1)
        self.assertEqual(response.context['valor_total'], Decimal("12000.00"))
        self.assertContains(response, "Servidor Rack 2U")
        self.assertContains(response, "TERMO DE DOAÇÃO")


class TravaCapitalEmbrapiiTestCase(TestCase):
    """
    Bateria de testes de conformidade regulatória para a RN-06:
    Vedação absoluta de aquisição de Bens de Capital com recursos de subvenção EMBRAPII/SEBRAE.
    """
    def setUp(self):
        self.empresa = EmpresaParceira.objects.create(
            nome="Empresa Teste Capital",
            cnpj="11.222.333/0001-44",
            natureza_juridica="LTDA",
            representante_legal="Gestor Empresa",
            cargo_representante="Diretor",
        )
        self.projeto = ProjetoPDI.objects.create(
            nome="Projeto PD&I Automação",
            fase="EXECUCAO",
            concedente=self.empresa,
        )
        self.origem = OrigemDoacao.objects.create(nome="FAEPI", sigla="FAEPI")
        self.termo = TermoDoacao.objects.create(
            projeto=self.projeto,
            origem=self.origem,
            numero="TD-001",
            ano="2026",
            data="2026-01-15",
        )
        self.tipo_proc = TipoProcesso.objects.create(nome="Compras e Pagamentos")

        self.fonte_empresa = FonteDeRecurso.objects.create(nome="Empresa Parceira")
        self.fonte_embrapii = FonteDeRecurso.objects.create(nome="EMBRAPII")
        self.fonte_sebrae = FonteDeRecurso.objects.create(nome="SEBRAE")

        self.conta_empresa = ContaBancaria.objects.create(
            projeto=self.projeto,
            fonte_recurso=self.fonte_empresa,
            banco="Banco do Brasil",
            agencia="1234",
            conta="10001",
            dv="1",
        )
        self.conta_embrapii = ContaBancaria.objects.create(
            projeto=self.projeto,
            fonte_recurso=self.fonte_embrapii,
            banco="Banco do Brasil",
            agencia="1234",
            conta="20002",
            dv="2",
        )

    def test_01_criacao_legitima_com_conta_empresa_sucesso(self):
        """Item patrimonial com conta bancária da Empresa é válido e passa no clean()."""
        item = ItemPatrimonial(
            termo=self.termo,
            numero_ativo="BEM-001",
            descricao="Osciloscópio Digital",
            valor_bem=Decimal("15000.00"),
            conta_bancaria=self.conta_empresa,
        )
        item.full_clean()
        item.save()
        self.assertEqual(item.conta_bancaria.fonte_recurso.nome, "Empresa Parceira")

    def test_02_rejeita_item_patrimonial_com_conta_direta_embrapii(self):
        """Item patrimonial com conta direta EMBRAPII deve levantar ValidationError no clean()."""
        item = ItemPatrimonial(
            termo=self.termo,
            numero_ativo="BEM-002",
            descricao="Braço Robótico",
            valor_bem=Decimal("45000.00"),
            conta_bancaria=self.conta_embrapii,
        )
        with self.assertRaises(ValidationError) as ctx:
            item.full_clean()
        self.assertIn('conta_bancaria', ctx.exception.message_dict)

    def test_03_rejeita_item_patrimonial_com_processo_compra_embrapii(self):
        """Item patrimonial com processo de compra custeado por conta EMBRAPII deve ser rejeitado."""
        proc_compra = Processo.objects.create(
            projeto=self.projeto,
            tipo=self.tipo_proc,
            numero="00100/2026",
            conta_bancaria=self.conta_embrapii,
        )
        item = ItemPatrimonial(
            termo=self.termo,
            numero_ativo="BEM-003",
            descricao="Torno CNC",
            valor_bem=Decimal("80000.00"),
            processo_compra=proc_compra,
        )
        with self.assertRaises(ValidationError) as ctx:
            item.full_clean()
        self.assertIn('processo_compra', ctx.exception.message_dict)

    def test_04_signal_m2m_bloqueia_adicao_direta_processo_pagamento_embrapii(self):
        """Signal m2m_changed deve bloquear item.processos_pagamento.add(proc_embrapii)."""
        item = ItemPatrimonial.objects.create(
            termo=self.termo,
            numero_ativo="BEM-004",
            descricao="Estação de Solda",
            valor_bem=Decimal("3000.00"),
            conta_bancaria=self.conta_empresa,
        )
        proc_pagamento_embrapii = Processo.objects.create(
            projeto=self.projeto,
            tipo=self.tipo_proc,
            numero="00101/2026",
            conta_bancaria=self.conta_embrapii,
        )
        with self.assertRaises(ValidationError) as ctx:
            item.processos_pagamento.add(proc_pagamento_embrapii)
        self.assertIn("RN-06", str(ctx.exception))

    def test_05_signal_m2m_bloqueia_adicao_reversa_processo_pagamento_embrapii(self):
        """Signal m2m_changed deve bloquear processo_embrapii.itens_pagos.add(item) (Direção Reversa)."""
        item = ItemPatrimonial.objects.create(
            termo=self.termo,
            numero_ativo="BEM-005",
            descricao="Impressora 3D Industrial",
            valor_bem=Decimal("25000.00"),
            conta_bancaria=self.conta_empresa,
        )
        proc_pagamento_embrapii = Processo.objects.create(
            projeto=self.projeto,
            tipo=self.tipo_proc,
            numero="00102/2026",
            conta_bancaria=self.conta_embrapii,
        )
        with self.assertRaises(ValidationError) as ctx:
            proc_pagamento_embrapii.itens_pagos.add(item)
        self.assertIn("RN-06", str(ctx.exception))

    def test_06_processo_bloqueia_mutacao_posterior_para_conta_embrapii(self):
        """Processo já vinculado a item patrimonial não pode ter conta alterada para EMBRAPII (Anti-Tampering)."""
        proc_compra = Processo.objects.create(
            projeto=self.projeto,
            tipo=self.tipo_proc,
            numero="00103/2026",
            conta_bancaria=self.conta_empresa,
        )
        ItemPatrimonial.objects.create(
            termo=self.termo,
            numero_ativo="BEM-006",
            descricao="Sensor Laser LiDAR",
            valor_bem=Decimal("12000.00"),
            processo_compra=proc_compra,
        )
        proc_compra.conta_bancaria = self.conta_embrapii
        with self.assertRaises(ValidationError) as ctx:
            proc_compra.clean()
        self.assertIn('conta_bancaria', ctx.exception.message_dict)

    def test_07_bem_patrimonial_clean_rejeita_conta_embrapii(self):
        """BemPatrimonial no inventário definitivo não aceita conta com fonte EMBRAPII."""
        bem = BemPatrimonial(
            projeto=self.projeto,
            descricao="Servidor de IA GPU",
            valor=Decimal("95000.00"),
            conta_bancaria=self.conta_embrapii,
        )
        with self.assertRaises(ValidationError) as ctx:
            bem.clean()
        self.assertIn('conta_bancaria', ctx.exception.message_dict)
