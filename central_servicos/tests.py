from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from almoxarifado.models import NotaFiscalAlmoxarifado, ProdutoAlmoxarifado
from cadastros.models import Fornecedor
from central_servicos.models import (
    Ambiente,
    Andar,
    CategoriaServico,
    MaterialUtilizado,
    OrdemServico,
    Predio,
    TipoAmbiente,
)


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class CentralServicosOSTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.solicitante = User.objects.create_user(
            username='solicitante_os', password='123'
        )

        self.predio = Predio.objects.create(nome='Prédio Central', sigla='PC')
        self.andar = Andar.objects.create(predio=self.predio, nome='1º Andar')
        self.tipo_ambiente = TipoAmbiente.objects.create(
            nome='Laboratório de Automação'
        )
        self.ambiente = Ambiente.objects.create(
            predio=self.predio,
            andar=self.andar,
            tipo=self.tipo_ambiente,
            nome='Lab 101',
        )
        self.categoria = CategoriaServico.objects.create(nome='Manutenção Elétrica')

        self.fornecedor = Fornecedor.objects.create(
            nome='Fornecedor Insumos LTDA',
            cnpj='99.888.777/0001-66',
            endereco='Manaus/AM',
            representante_legal='Representante',
            cargo_representante='Gerente',
        )
        self.nota = NotaFiscalAlmoxarifado.objects.create(
            numero='NF-OS-01',
            serie='1',
            data_emissao=timezone.now().date(),
            fornecedor=self.fornecedor,
            destinatario_nome='IFAM',
            destinatario_cnpj='10.792.928/0001-00',
        )
        self.produto = ProdutoAlmoxarifado.objects.create(
            nota_fiscal=self.nota,
            numero_item=1,
            descricao='Cabo de Rede Cat6 (m)',
            quantidade=Decimal('100.00'),
            unidade_comercial='METRO',
            valor_unitario=Decimal('5.00'),
            valor_total=Decimal('500.00'),
        )

    def criar_os(self, status='PENDENTE', descricao='Serviço de manutenção'):
        return OrdemServico.objects.create(
            ambiente=self.ambiente,
            categoria=self.categoria,
            descricao_problema=descricao,
            solicitante=self.solicitante,
            status=status,
        )

    def test_01_home_central_servicos_dashboard(self):
        self.client.login(username='solicitante_os', password='123')
        response = self.client.get(reverse('central_servicos:home_central_servicos'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_predios'], 1)
        self.assertEqual(response.context['total_ambientes'], 1)

    def test_02_criar_os_vinculada_ambiente(self):
        ordem = self.criar_os(descricao='Tomada em curto no Lab 101')
        self.assertTrue(ordem.numero.startswith('OS-'))
        self.assertEqual(ordem.ambiente, self.ambiente)
        self.assertFalse(ordem.estoque_baixado)

    def test_03_vinculo_material_utilizado_os(self):
        ordem = self.criar_os(descricao='Instalação de ponto de rede')
        material = MaterialUtilizado.objects.create(
            ordem_servico=ordem,
            produto_almoxarifado=self.produto,
            quantidade=Decimal('15.00'),
        )
        self.assertEqual(ordem.materiais.count(), 1)
        self.assertEqual(material.quantidade, Decimal('15.00'))

    def test_04_conclusao_os_debita_estoque_almoxarifado(self):
        ordem = self.criar_os(status='EM_ANDAMENTO', descricao='Passagem de cabo')
        MaterialUtilizado.objects.create(
            ordem_servico=ordem,
            produto_almoxarifado=self.produto,
            quantidade=Decimal('20.00'),
        )
        ordem.status = 'CONCLUIDA'
        ordem.save()

        self.produto.refresh_from_db()
        ordem.refresh_from_db()
        self.assertEqual(self.produto.quantidade, Decimal('80.00'))
        self.assertTrue(ordem.estoque_baixado)

    def test_05_saldo_insuficiente_impede_baixa(self):
        ordem = self.criar_os(status='EM_ANDAMENTO', descricao='Cabeamento massivo')
        MaterialUtilizado.objects.create(
            ordem_servico=ordem,
            produto_almoxarifado=self.produto,
            quantidade=Decimal('200.00'),
        )
        ordem.status = 'CONCLUIDA'
        with self.assertRaises(ValidationError):
            ordem.save()

        self.produto.refresh_from_db()
        ordem.refresh_from_db()
        self.assertEqual(self.produto.quantidade, Decimal('100.00'))
        self.assertFalse(ordem.estoque_baixado)

    def test_06_cancelamento_estorna_estoque_debitado(self):
        ordem = self.criar_os(status='EM_ANDAMENTO', descricao='Serviço cancelado')
        MaterialUtilizado.objects.create(
            ordem_servico=ordem,
            produto_almoxarifado=self.produto,
            quantidade=Decimal('30.00'),
        )
        ordem.status = 'CONCLUIDA'
        ordem.save()

        ordem.status = 'CANCELADA'
        ordem.save()

        self.produto.refresh_from_db()
        ordem.refresh_from_db()
        self.assertEqual(self.produto.quantidade, Decimal('100.00'))
        self.assertFalse(ordem.estoque_baixado)

    def test_07_cancelar_view_bloqueia_os_concluida_via_web(self):
        ordem = self.criar_os(status='CONCLUIDA', descricao='OS finalizada')
        self.client.login(username='solicitante_os', password='123')
        response = self.client.get(
            reverse('central_servicos:cancelar_os', args=[ordem.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_08_relatorio_os_por_status(self):
        self.criar_os(descricao='OS aberta')
        self.client.login(username='solicitante_os', password='123')
        response = self.client.get(
            reverse('central_servicos:relatorio_os', args=['PENDENTE'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['ordens']), 1)
